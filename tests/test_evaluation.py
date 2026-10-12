import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import shutil
import unittest
from unittest.mock import patch

from actio.contracts.json import canonical
from actio.contracts.json import digest
from actio.contracts.json import ContractError
from actio.adapters.filesystem.common import clean_env
from actio.evidence.bundles.eval_contract import make_spec
from actio.evidence.bundles.eval_contract import seal
from actio.evidence.bundles.eval_contract import strict_response
from actio.evidence.bundles.eval_contract import deterministic
from actio.interfaces.cli.evaluation import evaluate
from actio.evidence.bundles.evaluation import verify_record
from actio.evidence.bundles.evaluation import source_bundle
from actio.evidence.bundles.evaluation import prepare
from actio.interfaces.cli.evaluation import execute_worker
from actio.interfaces.cli.evaluation import campaign
from actio.evidence.bundles.verify import sha
from test_input_binding import SAMPLES
from test_input_binding import mutate_bundle
from test_input_binding import frozen_edit


def synthetic():
    return seal({'schema':'synthetic-social.v1','fixture':True,'unit':'synthetic-negotiation-1',
        'agents':{'north':{'agent':'SYNTH_NORTH','role':'participant'},'south':{'agent':'SYNTH_SOUTH','role':'participant'}},
        'goals':{'north':'Agree on a shared park cleanup time.','south':'Keep the cleanup within one hour.'},
        'relationships':{'north':'New neighbors; neutral before interaction.','south':'New neighbors; neutral before interaction.'},
        'actions':[{'seat':'south','action':'I can help for one hour.'},{'seat':'north','action':'Agreed, one hour on Saturday.'}],
        'task_outcome':'success'})


def response():
    return {'scores':{'agent_2':{'goal':{'reasoning':'Preset fixture only.','score':8},'relationship':{'reasoning':'Preset fixture only.','score':-2}},
                      'agent_1':{'goal':{'reasoning':'Preset fixture only.','score':3},'relationship':{'reasoning':'Preset fixture only.','score':1}}}}


def invalid_responses():
    cases={f'scores_{name}':canonical({'scores':v}) for name,v in [('null',None),('list',[]),('number',5),('bool',False)]}
    cases.update(empty='',empty_object='{}',empty_list='[]',null='null',duplicate_key='{"scores":{},"scores":{}}',
                 nonfinite='{"scores":{"agent_1":{"goal":{"reasoning":"x","score":NaN}}}}')
    for name,edit in {
        'missing_alias':lambda v:v['scores'].pop('agent_1'),
        'unknown_alias':lambda v:v['scores'].update(alien=v['scores'].pop('agent_1')),
        'extra_alias':lambda v:v['scores'].update(agent_3=v['scores']['agent_1']),
        'missing_dimension':lambda v:v['scores']['agent_1'].pop('goal'),
        'extra_dimension':lambda v:v['scores']['agent_1'].update(secret={'reasoning':'x','score':0}),
        'bool_score':lambda v:v['scores']['agent_1']['goal'].update(score=True),
        'string_score':lambda v:v['scores']['agent_1']['goal'].update(score='5'),
        'float_score':lambda v:v['scores']['agent_1']['goal'].update(score=5.0),
        'goal_range':lambda v:v['scores']['agent_1']['goal'].update(score=11),
        'relationship_range':lambda v:v['scores']['agent_2']['relationship'].update(score=6),
        'pair_container':lambda v:v['scores']['agent_1'].update(goal=[]),
        'rationale_type':lambda v:v['scores']['agent_1']['goal'].update(reasoning=3),
        'rationale_limit':lambda v:v['scores']['agent_1']['goal'].update(reasoning='x'*1025),
    }.items():
        v=response();edit(v);cases[name]=json.dumps(v)
    cases['response_limit']=' '*16385
    cases['duplicate_alias']=json.dumps(response()).replace('"agent_2":','"agent_1":',1)
    return cases


class Evaluation(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.det=make_spec('deterministic',digest('synthetic-dataset-test'))
        self.ctl=make_spec('controlled_response',digest('synthetic-dataset-test'))
        self.syn={'kind':'synthetic','input':synthetic()}

    def test_admission_before_evaluator_and_orthogonal_outcomes(self):
        records={}
        for name in ('partial','unknown'):
            with patch('actio.interfaces.cli.evaluation.execute_worker',side_effect=AssertionError('must not call')) as worker:
                record,_=evaluate(self.det,source_bundle(SAMPLES/name)[0],self.root)
                self.assertEqual(worker.call_count,0)
                r=record['body'];self.assertEqual(r['admission']['status'],'insufficient')
                self.assertEqual(r['task_outcome'],'infrastructure_failure');self.assertIsNone(r['measurement']['results'])
                self.assertTrue(verify_record(record)['valid']);records[name]=r['measurement']
        bad=self.root/'contradiction';mutate_bundle(bad,lambda d:frozen_edit(d,lambda m:m['observations'].update(A='edited')))
        with patch('actio.interfaces.cli.evaluation.execute_worker') as worker:
            record,_=evaluate(self.det,source_bundle(bad)[0],self.root);self.assertEqual(worker.call_count,0)
            self.assertEqual(record['body']['admission']['status'],'rejected')
        with patch('actio.interfaces.cli.evaluation.execute_worker') as worker:
            record,_=evaluate(self.ctl,source_bundle(SAMPLES/'social')[0],self.root)
            self.assertEqual(worker.call_count,0);self.assertEqual(record['body']['admission']['status'],'insufficient')
            self.assertIn('goals',record['body']['admission']['reasons'][0])
        self.evidence={'not_run':records,'rejections_have_zero_calls':True}

    def test_active_legacy_corrupt_and_missing_synthetic_context_zero_calls(self):
        results={}
        for case in ('active','legacy','corrupt','missing_context'):
            source=source_bundle(SAMPLES/'social')[0]
            m=json.loads(source['files']['manifest.json'])
            if case=='active':m['source']['active_lease']=True
            elif case=='legacy':
                d=json.loads(source['files']['evidence.json']);d['terminal']=None;d['request_identity']=None;d['legacy_run']=True
                source['files']['evidence.json']=canonical(d);raw=source['files']['evidence.json'].encode()
                next(e for e in m['files'] if e['path']=='evidence.json').update(bytes=len(raw),sha256=sha(raw));m['source']['schema']=0
            elif case=='corrupt':source['files']['evidence.json']='{}'
            source['files']['manifest.json']=canonical(m)
            spec=self.det
            if case=='missing_context':
                source=copy.deepcopy(self.syn);source['input']['body']['relationships'].pop('north');source['input']=seal(source['input']['body']);spec=self.ctl
            with patch('actio.interfaces.cli.evaluation.execute_worker') as worker:
                record,_=evaluate(spec,source,self.root);self.assertEqual(worker.call_count,0)
            r=record['body'];self.assertEqual(r['admission']['status'],'rejected' if case=='corrupt' else 'insufficient')
            self.assertTrue(verify_record(record)['valid']);results[case]={'admission':r['admission'],'measurement':r['measurement']}
        self.evidence={'zero_call_cases':results}

    def test_deterministic_facts_refusal_and_whitelisted_received_view(self):
        results={}
        for name in ('assistant','social','rejected'):
            record,_=evaluate(self.det,source_bundle(SAMPLES/name)[0],self.root);r=record['body'];results[name]=r['measurement']
            self.assertEqual(r['measurement']['status'],'valid_measurement',r['measurement'])
            self.assertTrue(verify_record(record)['valid'])
            view=r['input']['body']['view'];serialized=canonical(view)
            for excluded in ('PRIVATE_ONLY','GM_PRIVATE','PRIVATE_MEMORY','"answer"','"scores"','"candidate"'):
                self.assertNotIn(excluded,serialized)
            self.assertEqual(r['measurement']['view_hash'],digest(view))
            if name=='assistant':
                self.assertEqual(len(view['aliases']),1)
                changed=copy.deepcopy(view);changed['actions'][0]['tool_results'][0]['reference_present']=False
                self.assertEqual(deterministic(changed)[0]['value'],0)
            else:
                self.assertEqual(view['actions'][0]['alias'],'agent_2')
            if name=='rejected':
                self.assertEqual(r['task_outcome'],'task_failure')
                self.assertEqual(r['measurement']['results'][0]['value']['illegal_rejected_before_world'],1)
                self.assertEqual(len(view['actions']),1)
        self.evidence={'actual_worker_results':results}

    def test_invalid_envelopes_persist_no_zero_or_parser_coercion(self):
        results={}
        for name,raw in invalid_responses().items():
            with self.subTest(name=name):
                record,_=evaluate(self.ctl,self.syn,self.root,raw);r=record['body'];m=r['measurement']
                self.assertEqual(m['status'],'invalid_measurement',m)
                self.assertEqual(m['parser_calls'],0);self.assertIsNone(m['results']);self.assertEqual(r['task_outcome'],'success')
                self.assertTrue(verify_record(record)['valid']);results[name]=m
        self.evidence={'invalid_response_records':results,'mode':'CONTROLLED_RESPONSE'}

    def test_idempotency_content_spec_export_metadata_and_atomic_publication(self):
        source=source_bundle(SAMPLES/'assistant')[0]
        first,_=evaluate(self.det,source,self.root)
        changed=copy.deepcopy(source);meta=json.loads(changed['files']['export.json']);meta['exported_at']='changed fixture export time'
        changed['files']['export.json']=canonical(meta);m=json.loads(changed['files']['manifest.json'])
        raw=changed['files']['export.json'].encode()
        next(e for e in m['files'] if e['path']=='export.json').update(bytes=len(raw),sha256=sha(raw))
        changed['files']['manifest.json']=canonical(m)
        with patch('actio.interfaces.cli.evaluation.execute_worker') as worker:
            same,reused=evaluate(self.det,changed,self.root);self.assertTrue(reused);self.assertEqual(same,first);self.assertEqual(worker.call_count,0)
        spec2=make_spec('deterministic',digest('synthetic-dataset-test'),revision=2)
        second,reused=evaluate(spec2,source,self.root);self.assertFalse(reused);self.assertNotEqual(second['sha256'],first['sha256'])
        bad_range=copy.deepcopy(self.ctl);bad_range['body']['metrics']['goal']['range']=[0,100];bad_range=seal(bad_range['body'])
        with self.assertRaisesRegex(ContractError,'unsupported spec'):evaluate(bad_range,self.syn,self.root,canonical(response()))
        control,_=evaluate(self.ctl,self.syn,self.root,canonical(response()))
        syn2=copy.deepcopy(self.syn);syn2['input']['body']['actions'].reverse();syn2['input']=seal(syn2['input']['body'])
        altered,reused=evaluate(self.ctl,syn2,self.root,canonical(response()))
        self.assertFalse(reused);self.assertNotEqual(control['sha256'],altered['sha256'])
        self.assertEqual(control['body']['measurement']['results']['agent_2']['goal']['score'],8)
        self.assertEqual(control['body']['input']['body']['aliases'],altered['body']['input']['body']['aliases'])
        tampered=copy.deepcopy(control);tampered['body']['measurement']['results']['agent_2']['goal']['score']=0
        self.assertFalse(verify_record(seal(tampered['body']))['valid'])
        self.assertFalse(list(self.root.glob('*.staging')))
        self.evidence={'duplicate_export_reused':True,'spec_revision_new_record':True,'changed_input_new_record':True,'range_change':'unsupported range rejected, never reused'}

    def test_internal_error_timeout_and_interrupted_claim_are_preserved(self):
        results={}
        for name,error in [('internal',RuntimeError('fixed internal bug')),('timeout',TimeoutError('fixed deadline'))]:
            folder=self.root/name
            with patch('actio.interfaces.cli.evaluation.execute_worker',side_effect=error):
                record,_=evaluate(self.ctl,self.syn,folder,canonical(response()))
            m=record['body']['measurement'];self.assertEqual(m['status'],'timeout' if name=='timeout' else 'measurement_error')
            self.assertTrue(verify_record(record)['valid']);results[name]=record
            with patch('actio.interfaces.cli.evaluation.execute_worker') as worker:
                retry,reused=evaluate(self.ctl,self.syn,folder,canonical(response()));self.assertTrue(reused);self.assertEqual(worker.call_count,0)
            for pointer in folder.glob('*.request.json'):pointer.unlink()
            with self.assertRaisesRegex(ContractError,'claimed or interrupted'):evaluate(self.ctl,self.syn,folder,canonical(response()))
        # Real subprocess hard deadline, through the same execution boundary.
        original=subprocess.run
        def hung(*args,**kwargs):
            return original([sys.executable,'-I','-c','import time; time.sleep(20)'],**kwargs)
        with patch('actio.adapters.runtime.evaluator.subprocess.run',side_effect=hung):
            with self.assertRaises(TimeoutError):execute_worker({},1)
        self.evidence={'failures':results,'real_child_deadline':'killed and waited after 1 second; no retry'}

    def test_portable_stdlib_verification_and_missing_optional_dependency(self):
        record,_=evaluate(self.ctl,self.syn,self.root/'original',canonical(response()))
        portable=self.root/'portable';portable.mkdir()
        import actio
        shutil.copytree(Path(actio.__file__).parent,portable/'actio',ignore=shutil.ignore_patterns('__pycache__'))
        (portable/'record.json').write_text(canonical(record),encoding='utf8')
        guard='''import sys, pathlib, json
base=pathlib.Path(__file__).parent.resolve();sys.path.insert(0,str(base))
def audit(event,args):
    if event.startswith('socket.') or event=='subprocess.Popen': raise RuntimeError('offline denied')
    if event=='import' and args[0].split('.')[0] in ('deepseek_harness','concordia','redis','litellm','openai'):raise RuntimeError('runtime denied')
    if event=='open' and isinstance(args[0],str):
        p=pathlib.Path(args[0]).resolve()
        if not p.is_relative_to(base) and not p.is_relative_to(pathlib.Path(sys.base_prefix)):raise RuntimeError('original/source path denied')
sys.addaudithook(audit)
'''
        runner=portable/'verify.py';runner.write_text(guard+"from actio.application.evaluation import verify_record\nprint(json.dumps(verify_record(json.loads((base/'record.json').read_bytes()))))\n",encoding='utf8')
        p=subprocess.run([sys.executable,'-I','-S','-B',str(runner)],cwd=portable,env=clean_env(portable),capture_output=True,text=True,timeout=15)
        self.assertEqual(p.returncode,0,p.stderr);self.assertTrue(json.loads(p.stdout)['valid'],p.stdout)
        worker=portable/'worker.py';worker.write_text(guard+"from actio.adapters.runtime.eval_worker import main\nmain()\n",encoding='utf8')
        payload={'mode':'controlled_response','view':record['body']['input']['body']['view'],'raw_response':canonical(response())}
        result=subprocess.run([sys.executable,'-I','-S','-B',str(worker)],input=canonical(payload),cwd=portable,env=clean_env(portable),capture_output=True,text=True,timeout=15)
        actual=json.loads(result.stdout);self.assertEqual(actual['status'],'measurement_error')
        self.assertEqual(actual['error']['type'],'PackageNotFoundError')
        self.evidence={'portable':json.loads(p.stdout),'optional_missing':actual,'guard':'-I -S; original directories inaccessible; socket/process/runtime imports denied'}

    def test_worker_audit_hook_enforces_denials_in_real_child(self):
        script='''import sys, socket, subprocess, json
from actio.adapters.runtime.eval_worker import lockdown
counts=lockdown()
for probe in (lambda: socket.socket(),lambda: subprocess.run([sys.executable,'-c','pass']),lambda: __import__('actio.adapters.runtime.runtime')):
    try:probe()
    except RuntimeError:pass
    else:raise AssertionError('audit hook failed to deny')
print(json.dumps(counts))
'''
        p=subprocess.run([sys.executable,'-I','-B','-c',script],cwd=self.root,env=clean_env(self.root),capture_output=True,text=True,timeout=15)
        self.assertEqual(p.returncode,0,p.stderr)
        counts=json.loads(p.stdout);self.assertEqual(counts,{'network_attempts':1,'process_attempts':1,'runtime_import_attempts':1,'write_attempts':0})
        self.evidence={'denied_before_effect':counts,'actual_evaluation_workers':'zero attempts, recorded separately'}


if __name__=='__main__':unittest.main()
