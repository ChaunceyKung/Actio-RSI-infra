import json
from pathlib import Path
import unittest
from unittest.mock import patch
import uuid

from actio.contracts.json import ContractError
from actio.adapters.filesystem.common import write_json
from actio.adapters.runtime.facts import Facts
from actio.adapters.runtime.runtime import RuntimePort
from actio.adapters.runtime.runtime import synthetic_spec
from actio.application.scenarios import assistant
from actio.application.scenarios import social
from actio.interfaces.store import Store
from actio.application.terminal import check_terminal


class Reliability(unittest.TestCase):
    def setUp(self):
        self.root=Path('D:/actio-p1b1-tests')/uuid.uuid4().hex[:12];self.root.mkdir(parents=True)
        write_json(self.root/'owner.json',{'test':self.id()})
        self.s=Store(self.root/'ledger.sqlite',create=True)
        for agent in ('A','B'):self.s.agent(agent,synthetic_spec(agent))
        self.evidence={'root':str(self.root),'mode':'REAL_ENGINE_DSH_FIXTURE_WITH_TEST_INJECTION'}

    def tearDown(self):
        self.evidence['runs']=self.s.rows('SELECT * FROM run')
        self.evidence['workers']=self.s.rows('SELECT * FROM worker')
        for w in self.evidence['workers']:
            self.assertEqual(w['state'],'reaped')
            self.assertEqual(json.loads(w['report']).get('after',json.loads(w['report'])).get('active'),0)
        self.assertIsNone(self.s.row('SELECT * FROM lease'))
        self.s.close()

    def test_real_first_turn_then_second_entity_initialization_failure(self):
        class SecondFails(RuntimePort):
            def __init__(self,store,run,agent,*args,**kwargs):
                if agent=='A':raise RuntimeError('B1R1 second entity initialization injected')
                super().__init__(store,run,agent,*args,**kwargs)
        with self.assertRaisesRegex(RuntimeError,'second entity'):
            social(self.s,'partial','A','B',self.root,runtime_type=SecondFails)
        run=self.s.run('partial')
        self.assertEqual((run['task'],run['trajectory']),('infrastructure_failure','incomplete'))
        self.assertEqual(len(self.s.rows('SELECT * FROM world')),1)
        self.assertEqual(self.s.row('SELECT state FROM operation')['state'],'execution_complete')
        self.assertIsNone(self.s.row('SELECT * FROM scenario_terminal'))

    def test_disk_scan_handles_atomic_rename_without_hiding_limits_or_errors(self):
        from actio.adapters.runtime.supervisor import Supervisor
        folder=self.root/'disk-scan';folder.mkdir()
        existing=folder/'session.v3.jsonl';existing.write_bytes(b'1234')
        supervisor=Supervisor(folder,'test-no-launch',limits={'disk':4})
        # Reproduce an os.walk entry whose atomic-rename temp has already gone.
        with patch('actio.adapters.runtime.supervisor.os.walk',return_value=[(str(folder),[],['session.v3.jsonl.123.tmp',existing.name])]):
            supervisor.check_disk()
            supervisor.limits['disk']=3
            with self.assertRaisesRegex(ContractError,'disk_limit_exceeded'):supervisor.check_disk()
        with patch('actio.adapters.runtime.supervisor.os.walk',return_value=[(str(folder),[],[existing.name])]):
            with patch.object(Path,'stat',side_effect=PermissionError('denied')):
                with self.assertRaises(PermissionError):supervisor.check_disk()
        self.evidence['mode']='CONTROLLED_DISK_SCAN_ATOMIC_RENAME_NO_RUNTIME_LAUNCH'

    def test_primary_exception_retained_when_cleanup_also_raises(self):
        class TwoFailures(RuntimePort):
            def prepare(self):
                super().prepare()
                raise RuntimeError('primary initialization failure')
            def close(self,force=False):
                super().close(force=force)
                raise OSError('secondary cleanup reporting failure')
        with self.assertRaisesRegex(RuntimeError,'primary initialization') as error:
            assistant(self.s,'primary','A',self.root,runtime_type=TwoFailures)
        self.assertTrue(any('secondary cleanup' in n for n in error.exception.__notes__))
        self.assertIn('primary initialization',self.s.run('primary')['reason'])
        self.assertTrue(self.s.rows("SELECT * FROM audit WHERE kind='cleanup_failure'"))
        self.evidence['mode']='CONTROLLED_CONSTRUCTOR_AND_CLEANUP_EXCEPTIONS_NO_RUNTIME_LAUNCH'

    def test_real_engine_exception_after_first_step_preserves_prefix(self):
        from concordia.environment.engines.sequential import Sequential
        original=Sequential.run_loop
        def injected(engine,*args,**kwargs):
            def callback(step):raise RuntimeError('B1R1 Engine step callback injected')
            kwargs['step_callback']=callback
            return original(engine,*args,**kwargs)
        with patch.object(Sequential,'run_loop',injected):
            with self.assertRaisesRegex(RuntimeError,'Engine step'):
                social(self.s,'engine','A','B',self.root)
        self.assertEqual(self.s.run('engine')['trajectory'],'incomplete')
        self.assertEqual(len(self.s.rows('SELECT * FROM world')),1)

    def test_domain_receipt_missing_and_inconsistent_cannot_seal(self):
        for variant in ('missing','inconsistent'):
            class BadReceipt(RuntimePort):
                def confirm_effect(port):
                    super().confirm_effect()
                    if variant=='missing':port.s.db.execute('DELETE FROM domain_receipt WHERE op=?',(port.op,))
                    else:port.s.db.execute("UPDATE domain_receipt SET body='{}' WHERE op=?",(port.op,))
            with self.assertRaises(ContractError):
                social(self.s,variant,'A','B',self.root,runtime_type=BadReceipt)
            self.assertEqual(self.s.run(variant)['trajectory'],'incomplete')
            self.assertIsNone(self.s.row('SELECT * FROM scenario_terminal WHERE run=?',(self.s.run(variant)['id'],)))

    def test_explicit_replay_overrides_and_missing_snapshot_precede_worker(self):
        original=social(self.s,'original','A','B',self.root)
        n=self.s.row('SELECT COUNT(*) n FROM worker')['n']
        for extra in ({'illegal':True},{'illegal':False},{'as_of':0},{'as_of':None}):
            with self.assertRaisesRegex(ContractError,'override'):
                social(self.s,'override','A','B',self.root,replay=original['id'],**extra)
        for field in ('pins','memory'):
            value=json.loads(original['input']);value.pop(field)
            self.s.db.execute('UPDATE run SET input=? WHERE id=?',(json.dumps(value),original['id']))
            with self.assertRaisesRegex(ContractError,'missing'):
                social(self.s,'missing','A','B',self.root,replay=original['id'])
        self.s.db.execute('UPDATE run SET input=? WHERE id=?',(original['input'],original['id']))
        self.assertEqual(self.s.row('SELECT COUNT(*) n FROM worker')['n'],n)
        self.assertEqual(self.s.row('SELECT COUNT(*) n FROM run')['n'],1)

    def test_request_owner_readable_run_cannot_finish_and_unknown_retry(self):
        request={'scenario':'assistant','agent':'A'}
        run,_=self.s.begin('pending',{'request':request,'scenario':'assistant'})
        other=Store(self.s.path)
        try:
            same=assistant(other,'pending','A',self.root)
            self.assertEqual(same['id'],run['id'])
            with self.assertRaisesRegex(ContractError,'owner claim'):
                other.finish(run['id'],run['epoch'],task='success')
            self.s.finish(run['id'],run['epoch'],task='unknown')
            self.assertEqual(assistant(other,'pending','A',self.root)['id'],run['id'])
            self.assertFalse(self.s.rows('SELECT * FROM worker'))
        finally:other.close()

    def test_targeted_recovery_no_other_job_and_changed_lease_refused(self):
        historical,_=self.s.begin('history',{})
        self.s.finish(historical['id'],historical['epoch'],task='unknown')
        run,_=self.s.begin('active',{})
        worker=self.s.allocate_worker(run['id'],run['epoch'],str(self.root/'unused'),'Local\\Actio-test-'+uuid.uuid4().hex,'A')
        with patch('actio.adapters.runtime.supervisor.reap_named_job') as reap:
            for target in ('missing','history'):
                with self.assertRaises(ContractError):self.s.recover(target)
            with self.assertRaisesRegex(ContractError,'still alive'):self.s.recover('active')
            reap.assert_not_called()
        before=self.s.row('SELECT * FROM lease')
        def changed(name):
            self.s.db.execute('UPDATE lease SET epoch=epoch+1')
            return {'active':0}
        with patch('actio.adapters.runtime.supervisor.process_birth',return_value=None),patch('actio.adapters.runtime.supervisor.reap_named_job',side_effect=changed):
            with self.assertRaisesRegex(ContractError,'changed'):self.s.recover('active')
        self.assertEqual(self.s.row('SELECT state FROM worker')['state'],'waiting')
        self.s.db.execute('UPDATE lease SET epoch=?',(before['epoch'],))
        with patch('actio.adapters.runtime.supervisor.process_birth',return_value=None),patch('actio.adapters.runtime.supervisor.reap_named_job',return_value={'active':0}) as reap:
            self.s.recover('active');reap.assert_called_once()
        self.evidence['mode']='CONTROLLED_SQLITE_RECOVERY_INTERLEAVING; REAL_OWNER_DEATH_IN_PROCESSES_SUITE'
