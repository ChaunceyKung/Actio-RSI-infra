import copy
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import unittest
from unittest.mock import patch
import uuid

from actio.contracts.json import ContractError
from actio.adapters.filesystem.common import clean_env
from actio.adapters.filesystem.common import file_hash
from actio.adapters.filesystem.common import write_json
from actio.contracts.json import digest
from actio.interfaces.export import export_bundle
from actio.adapters.runtime.runtime import RuntimePort
from actio.adapters.runtime.runtime import synthetic_spec
from actio.application.scenarios import assistant
from actio.application.scenarios import social
from actio.interfaces.store import Store
from actio.evidence.bundles.verify import verify_bundle
from actio.evidence.bundles.verify import sha


class Evidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=(Path(__file__).resolve().parents[2]/'t')/uuid.uuid4().hex[:12];cls.root.mkdir(parents=True)
        write_json(cls.root/'owner.json',{'test':'evidence-real-fixtures'})
        cls.db=cls.root/'ledger.sqlite';s=Store(cls.db,create=True)
        try:
            for name in ('A','B','UNREFERENCED_IDENTITY'):s.agent(name,synthetic_spec(name))
            assistant(s,'assistant','A',cls.root)
            social(s,'social','A','B',cls.root,as_of=1)
            social(s,'rejected','A','B',cls.root,illegal=True)
            class FailSecond(RuntimePort):
                def __init__(self,store,run,agent,*args,**kwargs):
                    if agent=='A':raise RuntimeError('evidence fixture second initialization')
                    super().__init__(store,run,agent,*args,**kwargs)
            try:social(s,'partial','A','B',cls.root,runtime_type=FailSecond)
            except RuntimeError:pass
            class BeforeCanonical(RuntimePort):
                def drain(self):raise RuntimeError('evidence fixture unknown after flush')
            try:assistant(s,'unknown','A',cls.root,runtime_type=BeforeCanonical)
            except RuntimeError:pass
            cls.workers=s.rows('SELECT * FROM worker')
            for w in cls.workers:assert json.loads(w['report'])['after']['active']==0
        finally:s.close()
        cls.bundles={}
        for key in ('assistant','social','rejected','partial','unknown'):
            cls.bundles[key]=cls.root/key
            export_bundle(cls.db,key,cls.bundles[key])

    def setUp(self):
        self.evidence={'root':str(self.root),'workers':self.workers,
                       'mode':'REAL_ENGINE_DSH_FIXTURE_EXPORT_AND_OFFLINE_MUTATION',
                       'bundles':{k:str(p) for k,p in self.bundles.items()}}

    def edited(self,key,edit):
        target=self.root/('mutated-'+uuid.uuid4().hex[:8]);shutil.copytree(self.bundles[key],target)
        data=json.loads((target/'evidence.json').read_text(encoding='utf8'));edit(data)
        raw=json.dumps(data,ensure_ascii=False,separators=(',',':')).encode();(target/'evidence.json').write_bytes(raw)
        manifest=json.loads((target/'manifest.json').read_text());manifest['files'][0].update(sha256=sha(raw),bytes=len(raw))
        manifest['files']=[e for e in manifest['files'] if e['path']!='verification.json']
        (target/'manifest.json').write_text(json.dumps(manifest),encoding='utf8')
        (target/'verification.json').unlink()  # Force independent semantics, not stored report comparison.
        return target

    def test_complete_refusal_partial_unknown_are_separate_dimensions(self):
        expected={'assistant':('complete','success'),'social':('complete','success'),
                  'rejected':('complete','task_failure'),'partial':('partial','infrastructure_failure'),'unknown':('partial','infrastructure_failure')}
        results={}
        for key,p in self.bundles.items():
            v=verify_bundle(p);results[key]=v
            self.assertEqual(v['bundle_integrity'],'valid',v)
            self.assertEqual((v['scenario_completeness'],v['task_outcome']),expected[key],v)
            if key in ('assistant','social','rejected'):self.assertEqual(v['facts_consistency'],'consistent',v)
            self.assertEqual(v['execution_mode'],'fixture')
        self.evidence['results']=results

    def test_rehashed_internal_contradictions_and_missing_memory_are_not_complete(self):
        def contradict_gm(d):
            w=d['world'][0];w['resolved']+=' invented world change'
            for receipt in d['domain_receipts']:
                if receipt['stream']==w['stream']:
                    body=json.loads(receipt['body']);body['resolved']=w['resolved'];receipt['body']=json.dumps(body)
            terminal=json.loads(d['terminal']['body'])
            terminal['world_hash']=digest(sorted(d['world'],key=lambda w:w['step']))
            terminal['domain_hash']=digest(sorted(d['domain_receipts'],key=lambda r:r['op']))
            d['terminal']['body']=json.dumps(terminal)
        variants={
            'duplicate_seq':lambda d:d['occurrences'].append(copy.deepcopy(d['occurrences'][0])),
            'gap':lambda d:d['occurrences'].pop(1),
            'barrier':lambda d:d['operations'][0].update(barrier=json.dumps({**json.loads(d['operations'][0]['barrier']),'through':99999})),
            'missing_memory_source':lambda d:d['memory_proofs'].clear(),
            'domain_source':lambda d:d['domain_receipts'][0].update(seq=0),
            'world_entity':lambda d:d['world'][0].update(agent='A'),
            'conflict':lambda d:d['conflicts'].append({'stream':d['streams'][0]['id'],'seq':0,'old_hash':'a','new_hash':'b','raw':'{}'}),
            'projection':lambda d:d['projections'][0].update(value='{"type":"wrong","source_hash":"wrong"}'),
            'missing_projection':lambda d:d['projections'].clear(),
            'rehashed_gm_contradiction':contradict_gm,
        }
        results={}
        for label,edit in variants.items():
            p=self.edited('social',edit);v=verify_bundle(p);results[label]=v
            self.assertEqual(v['bundle_integrity'],'valid',v)
            self.assertNotEqual(v['scenario_completeness'],'complete',v)
            self.assertIn(v['facts_consistency'],('invalid','partial'))
        self.evidence['tampering']=results

    def test_missing_file_changed_hash_unknown_format_rejected(self):
        results={}
        for label in ('missing','hash','version','metadata_hash'):
            target=self.root/('invalid-'+label);shutil.copytree(self.bundles['assistant'],target)
            if label=='missing':(target/'evidence.json').unlink()
            elif label=='hash':(target/'evidence.json').write_bytes(b'{}')
            elif label=='metadata_hash':(target/'export.json').write_bytes(b'{}')
            else:
                m=json.loads((target/'manifest.json').read_text());m['version']=99;(target/'manifest.json').write_text(json.dumps(m))
            v=verify_bundle(target);results[label]=v
            self.assertEqual(v['bundle_integrity'],'invalid')
        self.evidence['tampering']=results

    def test_portable_stdlib_process_denies_source_roots_runtime_and_network(self):
        portable=self.root/'portable';portable.mkdir()
        bundle=portable/'bundle';shutil.copytree(self.bundles['social'],bundle)
        library=portable/'actio';library.mkdir()
        import actio.evidence.bundles.verify
        installed=Path(actio.evidence.bundles.verify.__file__).parents[2]
        shutil.copyfile(installed/'__init__.py',library/'__init__.py')
        shutil.copytree(installed/'contracts',library/'contracts',ignore=shutil.ignore_patterns('__pycache__'))
        (library/'evidence/bundles').mkdir(parents=True)
        shutil.copyfile(installed/'evidence/__init__.py',library/'evidence/__init__.py')
        for name in ('__init__.py','terminal.py','verify.py'):
            shutil.copyfile(installed/'evidence/bundles'/name,library/'evidence/bundles'/name)
        runner=portable/'check.py'
        runner.write_text('''import sys, pathlib, json
base=pathlib.Path(__file__).parent.resolve()
sys.path.insert(0,str(base))
def guard(event,args):
    if event.startswith('socket.') or event=='subprocess.Popen':raise RuntimeError('offline operation denied')
    if event=='import' and args[0].split('.')[0] in ('deepseek_harness','concordia'):raise RuntimeError('runtime import denied')
    if event=='open' and isinstance(args[0],str):
        p=pathlib.Path(args[0]).resolve()
        if not p.is_relative_to(base) and not p.is_relative_to(pathlib.Path(sys.base_prefix)):
            raise RuntimeError('author/source file access denied: '+str(p))
sys.addaudithook(guard)
from actio.evidence.bundles.verify import verify_bundle
print(json.dumps(verify_bundle(base/'bundle')))
''',encoding='utf8')
        command=[sys.executable,'-I','-S',str(runner)]
        p=subprocess.run(command,cwd=portable,env=clean_env(portable),capture_output=True,text=True,timeout=15)
        self.assertEqual(p.returncode,0,p.stderr)
        actual=json.loads(p.stdout);self.assertEqual(actual,verify_bundle(self.bundles['social']))
        self.evidence['portable']={'command':command,'exit_code':p.returncode,'result':actual,'mode':'PYTHON_ISOLATED_NO_SITE_WITH_SOURCE_PATH_IMPORT_NETWORK_GUARD'}

    def test_stable_scoped_readonly_export_and_atomic_failure(self):
        s=Store(self.db,readonly=True)
        try:before=list(s.db.iterdump())
        finally:s.close()
        target=self.root/'repeat';r=export_bundle(self.db,'social',target)
        for name in ('evidence.json','verification.json'):
            self.assertEqual(file_hash(target/name),file_hash(self.bundles['social']/name))
        def stable_inventory(path):
            m=json.loads((path/'manifest.json').read_text())
            m['files']=[f for f in m['files'] if f['path']!='export.json']
            return m
        self.assertEqual(stable_inventory(target),stable_inventory(self.bundles['social']))
        data=json.loads((target/'evidence.json').read_text(encoding='utf8'))
        self.assertEqual({a['id'] for a in data['agents']},{'A','B'})
        self.assertNotIn('UNREFERENCED_IDENTITY',json.dumps(data))
        self.assertEqual(len(data['memory_proofs']),1)
        self.assertTrue(all(o['run']==data['run']['id'] for o in data['operations']))
        s=Store(self.db,readonly=True)
        try:self.assertEqual(before,list(s.db.iterdump()))
        finally:s.close()
        failure=self.root/'never-published'
        with patch('actio.application.export.MAX_ROWS',1):
            with self.assertRaisesRegex(ContractError,'limit'):export_bundle(self.db,'social',failure)
        self.assertFalse(failure.exists())
        attempts=list(self.root.glob('.never-published.staging-*'))
        self.assertEqual(len(attempts),1);self.assertEqual(json.loads((attempts[0]/'failure.json').read_text())['status'],'failed')
        self.evidence['stable_content_hash']=r['verification']['content_sha256']

    def test_missing_receipt_legacy_complete_and_active_prefix_not_promoted(self):
        out=self.root/'missing-receipt.sqlite'
        src=sqlite3.connect(self.db);dest=sqlite3.connect(out);src.backup(dest);src.close();dest.close()
        s=Store(out);run=s.run('social')
        s.db.execute('DELETE FROM domain_receipt WHERE op=(SELECT id FROM operation WHERE run=? LIMIT 1)',(run['id'],));s.close()
        result=export_bundle(out,'social',self.root/'missing-receipt')['verification']
        self.assertEqual(result['bundle_integrity'],'valid');self.assertEqual(result['scenario_completeness'],'partial')
        self.assertEqual(result['historical_claim']['trajectory'],'complete')
        # Known legacy schema fixture, preserving every original pre-versioned table.
        legacy=self.root/'legacy.sqlite';src=sqlite3.connect(self.db);dest=sqlite3.connect(legacy);src.backup(dest);src.close()
        for table in ('request_identity','scenario_terminal','migration'):dest.execute('DROP TABLE '+table)
        dest.execute('PRAGMA user_version=0');dest.commit();dest.close()
        result=export_bundle(legacy,'social',self.root/'legacy-bundle')['verification']
        self.assertEqual(result['scenario_completeness'],'legacy_unverified',result)
        self.assertEqual(result['historical_claim']['trajectory'],'complete')
        s=Store(self.db)
        frozen=json.loads(s.run('assistant')['input'])
        run,fresh=s.begin('active',frozen)
        try:
            result=export_bundle(self.db,'active',self.root/'active-bundle')['verification']
            self.assertEqual(result['bundle_integrity'],'valid')
            self.assertEqual(result['facts_consistency'],'partial')
            self.assertEqual(result['scenario_completeness'],'partial')
            self.assertIn('run active at snapshot',result['missing'])
        finally:s.finish(run['id'],run['epoch'],task='unknown');s.close()

    def test_read_snapshot_excludes_mid_export_mutation_and_new_verification_preserves_claim(self):
        out=self.root/'snapshot.sqlite'
        src=sqlite3.connect(self.db);dest=sqlite3.connect(out);src.backup(dest);src.close();dest.close()
        with sqlite3.connect(out) as db:db.execute('PRAGMA journal_mode=WAL')
        original=Store.run;changed=False
        def after_snapshot(store,target):
            nonlocal changed
            row=original(store,target)
            if not changed:
                changed=True
                with sqlite3.connect(out) as writer:
                    writer.execute('DELETE FROM domain_receipt WHERE op=(SELECT id FROM operation WHERE run=? LIMIT 1)',(row['id'],))
            return row
        with patch.object(Store,'run',after_snapshot):
            before=export_bundle(out,'social',self.root/'snapshot-before')['verification']
        after=export_bundle(out,'social',self.root/'snapshot-after')['verification']
        self.assertEqual(before['scenario_completeness'],'complete',before)
        self.assertEqual(after['scenario_completeness'],'partial',after)
        self.assertEqual(before['historical_claim'],after['historical_claim'])
        self.evidence['consistent_snapshot']={'before':before,'after':after,'injection':'separate WAL writer after first SELECT in read transaction'}
