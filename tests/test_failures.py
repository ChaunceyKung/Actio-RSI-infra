import json
from pathlib import Path
import time
import unittest
from unittest.mock import patch
import uuid

from actio.contracts.json import ContractError
from actio.adapters.filesystem.common import Lines
from actio.adapters.filesystem.common import file_hash
from actio.adapters.filesystem.common import write_json
from actio.adapters.runtime.facts import Facts
from actio.adapters.runtime.runtime import RuntimePort
from actio.adapters.runtime.runtime import TOOL
from actio.adapters.runtime.runtime import synthetic_spec
from actio.interfaces.store import Store
from actio.adapters.runtime.supervisor import Supervisor
from actio.adapters.runtime.supervisor import owned_root
from support import fault_type


class Failures(unittest.TestCase):
    def setUp(self):
        self.root=Path('D:/actio-p1b-tests')/uuid.uuid4().hex[:12];self.root.mkdir(parents=True)
        write_json(self.root/'owner.json',{'test':self.id()})
        self.s=Store(self.root/'ledger.sqlite',create=True);self.s.agent('A',synthetic_spec('A'))
        self.evidence={'root':str(self.root),'cases':[]};self.ports=[]

    def tearDown(self):
        for port in self.ports:
            port.close(force=True)
        self.evidence['workers']=self.s.rows('SELECT * FROM worker')
        self.evidence['operations']=self.s.rows('SELECT * FROM operation')
        for w in self.evidence['workers']:
            if w['report']:
                r=json.loads(w['report']);self.assertEqual(r.get('after',r).get('active'),0)
        self.s.close()
        self.evidence['files']={p.relative_to(self.root).as_posix():file_hash(p) for p in self.root.rglob('*') if p.is_file() and 'node_modules' not in p.parts and p.suffix in {'.json','.jsonl','.sqlite','.log','.yml'}}
        self.evidence['transcripts']={}
        for name in ('bridge.jsonl','mcp.jsonl','test-provider.jsonl'):
            for p in self.root.rglob(name):
                self.evidence['transcripts'][p.relative_to(self.root).as_posix()]=list(Lines(p).poll())

    def new(self,cls=RuntimePort):
        run,_=self.s.begin(uuid.uuid4().hex,{'scenario':'assistant','agents':{'A':self.s.agent('A')['spec_hash']}})
        port=cls(self.s,run,'A',self.root);self.ports.append(port)
        return port

    def finish(self,port):
        port.close(force=True)
        return self.s.finish(port.run['id'],port.epoch,task='unknown',reason='test has no domain effect')

    def rows(self,port,name):
        return list(Lines(port.root/name).poll())

    def test_final_policy_denies_and_registry_rewrite(self):
        variants=[('allow',{},None),('unknown',{},None),('schema',{'registryHash':'wrong'},None),
                  ('scope',{},None),('epoch',{},None),('run',{},None),('session',{},None),('creation',{},None),('expiry',{'expires':0},None),
                  ('budget',{'maxCalls':0},None),('artifact',{'toolHash':'wrong'},None),
                  ('registry',{},'registry'),('rewrite',{},'rewrite')]
        for name,policy,mode in variants:
            with self.subTest(name=name):
                port=self.new(fault_type(mode=mode,policy=policy))
                if name=='allow':
                    port.policy['canonical_vector']={'𐀀':'汉字','\ue000':[True,None,9007199254740991]}
                    write_json(port.root/'policy.json',port.policy)
                if name in {'epoch','run','session','creation'}:
                    port.policy['binding']={**port.binding,name:port.epoch+1 if name=='epoch' else 'wrong'}
                    write_json(port.root/'policy.json',port.policy)
                port.start()
                result=port.submit({'tool':'pwsh' if name=='unknown' else TOOL,'args':{'key':'outside' if name=='scope' else 'ok'},
                                    'callId':'unregistered-arbitrary-'+name,'answer':'done'})
                calls=[r for r in self.rows(port,'mcp.jsonl') if r['kind']=='received']
                self.assertEqual(len(calls),1 if name=='allow' else 0)
                guards=[r for r in self.rows(port,'bridge.jsonl') if r['kind']=='guard']
                from actio.contracts.json import digest
                for guard in guards:self.assertEqual(guard['policyHash'],digest(port.policy))
                if name not in {'allow','unknown'}:
                    self.assertTrue(guards);self.assertTrue(all(not g['allowed'] for g in guards))
                if name=='registry':self.assertTrue(any(g['reason']=='registry/schema drift' for g in guards))
                if name=='rewrite':self.assertTrue(any(g['reason']=='final parameter scope' for g in guards))
                self.evidence['cases'].append({'variant':name,'received':len(calls),'guards':guards,'op':result['op']})
                self.finish(port)

    def test_call_id_dedup_conflict_and_new_creation(self):
        for label,script,keys,expected in [
            ('duplicate',[{'id':'same'},{'id':'same'}],['ok'],'duplicate call'),
            ('conflict',[{'id':'same'},{'id':'same','key':'outside'}],['ok','outside'],'call identity conflict'),
            ('budget',[{'id':'one'},{'id':'two'}],['ok'],'budget exhausted')]:
            with self.subTest(label=label):
                port=self.new(fault_type(script=script,policy={'keys':keys,'maxCalls':1 if label=='budget' else 4}))
                port.start();port.submit({'answer':'done'})
                calls=[r for r in self.rows(port,'mcp.jsonl') if r['kind']=='received']
                guards=[r for r in self.rows(port,'bridge.jsonl') if r['kind']=='guard']
                self.assertEqual(len(calls),1)
                self.assertTrue(any(g['reason']==expected for g in guards),guards)
                self.finish(port)
        streams=[]
        for _ in range(2):
            port=self.new(fault_type(script=[{'id':'same-native-id'}]))
            port.start();port.submit({'answer':'done'})
            self.assertEqual(sum(r['kind']=='received' for r in self.rows(port,'mcp.jsonl')),1)
            streams.append(port.stream['creation']);self.finish(port)
        self.assertNotEqual(*streams)

    def test_stage_deadlines_mcp_hang_and_worker_exit(self):
        for mode in ['init','run','drain','close','mcp-hold','exit']:
            with self.subTest(mode=mode):
                port=self.new(fault_type(mode=mode));start=time.monotonic()
                with self.assertRaises((ContractError,TimeoutError)):
                    port.start()
                    port.submit({'answer':'done','tool':TOOL,'args':{'key':'ok'}})
                    port.close()
                elapsed=time.monotonic()-start
                self.assertLess(elapsed,16)
                if mode=='close':self.assertTrue((port.root/'close-entered').exists())
                if mode=='mcp-hold':self.assertEqual(sum(r['kind']=='received' for r in self.rows(port,'mcp.jsonl')),1)
                run=self.finish(port)
                self.assertNotEqual(run['trajectory'],'complete')
                self.evidence['cases'].append({'mode':mode,'elapsed_ms':int(elapsed*1000),'state':run['state']})

    def test_data_limits_preserve_prefix_and_job_assignment_failure(self):
        for mode,limits in [('oversize',{}),(None,{'count':6})]:
            port=self.new(fault_type(mode=mode,limits=limits))
            with self.assertRaises((ContractError,TimeoutError)):
                port.start();port.submit({'answer':'done'})
            self.assertTrue(list(port.root.glob('*.limit')))
            self.assertTrue(self.s.rows('SELECT * FROM audit WHERE run=?',(port.run['id'],)))
            self.assertNotEqual(self.finish(port)['trajectory'],'complete')
        root=owned_root(self.root,'job-assignment-test')
        supervisor=Supervisor(root,'Local\\Actio-test-'+uuid.uuid4().hex)
        with patch('actio.adapters.runtime.supervisor.Job',side_effect=OSError('injected assignment rejection')):
            with self.assertRaises(OSError):supervisor.start()
        self.assertIsNotNone(supervisor.proc.poll())
        self.assertFalse((root/'host.jsonl').exists())
        self.evidence['cases'].append({'assignment_failure_pid':supervisor.proc.pid,'returncode':supervisor.proc.returncode,'gate_released':False})

    def test_native_flush_before_canonical_readonly_reconcile(self):
        class BeforeCanonical(RuntimePort):
            def drain(self):
                raise RuntimeError('injected C: native flush committed; canonical not started')
        port=self.new(BeforeCanonical);port.start()
        with self.assertRaisesRegex(RuntimeError,'injected C'):
            port.submit({'answer':'done','tool':TOOL,'args':{'key':'ok'}})
        self.assertEqual(self.s.row('SELECT COUNT(*) n FROM occurrence')['n'],0)
        self.finish(port)
        facts=Facts(self.s)
        one=facts.reconcile(port.run['id']);n=self.s.row('SELECT COUNT(*) n FROM occurrence')['n']
        self.assertGreater(n,0)
        two=facts.reconcile(port.run['id'])
        self.assertEqual(one,two);self.assertEqual(self.s.row('SELECT COUNT(*) n FROM occurrence')['n'],n)
        self.assertEqual(sum(r['kind']=='received' for r in self.rows(port,'mcp.jsonl')),1)
        self.assertEqual(self.s.run(port.run['id'])['state'],'needs_reconcile')
        self.evidence['cases'].append({'window':'C','model_or_tool_redispatch':0,'reconciled':one})

    def test_slow_consumer_event_limit_and_explicit_stop(self):
        class SlowConsumer(fault_type(limits={'count':12})):
            def record(self,record):
                if record['kind']=='notification':time.sleep(.04)  # Deliberately slow consumption, not crash timing.
                super().record(record)
        port=self.new(SlowConsumer)
        with self.assertRaises((ContractError,TimeoutError)):
            port.start();port.submit({'answer':'done','tool':TOOL,'args':{'key':'ok'}})
        self.assertTrue(list(port.root.glob('*.limit')))
        self.assertNotEqual(self.finish(port)['trajectory'],'complete')
        port=self.new();port.start()
        port.stop('test explicit policy revocation')
        state=self.finish(port)
        self.assertEqual(state['stop_requested'],1)
        self.assertNotEqual(state['state'],'cancelled')
        self.assertEqual(json.loads(self.s.row('SELECT report FROM worker WHERE id=?',(port.stream['worker'],))['report'])['after']['active'],0)
        port=self.new();port.start();port.supervisor.execution_deadline=time.monotonic()-1
        with self.assertRaises(TimeoutError):port.submit({'answer':'never complete'})
        self.assertNotEqual(self.finish(port)['trajectory'],'complete')


if __name__=='__main__':unittest.main()
