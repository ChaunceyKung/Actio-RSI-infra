import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid

from actio.common import ContractError
from actio.common import canonical
from actio.common import digest
from actio.common import file_hash
from actio.common import clean_env
from actio.common import Lines
from actio.adapters.runtime.runtime import RuntimePort
from actio.adapters.runtime.runtime import synthetic_spec
from actio.interfaces.store import Store
from actio.application.scenarios import scheduling
from actio.tasks.registry import task_card
from actio.tasks.registry import actor_observation
from actio.interfaces.export import export_bundle
from actio.evidence.verify import verify_bundle
from actio.evidence.verify import sha
from actio.evidence.terminal import terminal_body
from actio.evidence.eval_contract import make_spec
from actio.evidence.eval_contract import seal
from actio.evidence.evaluation import prepare
from actio.interfaces.evaluation import evaluate
from actio.evidence.evaluation import source_bundle
from actio.evidence.evaluation import verify_record
from actio.evidence.campaign import GROUP_RULE
from actio.evidence.campaign import source_group
from actio.interfaces.campaign import run_campaign
from actio.evidence.campaign import verify_campaign
from actio.evidence.campaign import validate_dataset
from actio.evidence.calibration import export_annotations
from actio.evidence.calibration import import_labels
from actio.domain.roles import template
from actio.interfaces.preflight import preflight
from actio.domain.roles import stub_config
from test_evaluation import response


def dataset_for(sources):
    entries=[];indexed={}
    for name,source in sources.items():
        key=digest(source);indexed[key]=source
        for mode in ('deterministic','controlled_response'):
            identity,*_=prepare(make_spec(mode,'0'*64),source)
            entries.append({'id':name+'-'+mode,'source':key,'mode':mode,'raw_response':canonical(response()) if mode=='controlled_response' else None,
                            'aliases':identity.get('aliases',{}),'grouping':source_group(source)})
    entries.append({**entries[0],'id':'same-request-duplicate'})
    control=next(e for e in entries if e['mode']=='controlled_response')
    entries.append({**control,'id':'invalid-response','raw_response':'{}'})
    return seal({'schema':'task-campaign.v1','group_rule':GROUP_RULE,'sources':indexed,'entries':entries})


def rewrite_inventory(root):
    value=json.loads((root/'campaign.json').read_bytes());b=value['body']
    for name,e in b['files'].items():
        p=root/name
        if p.exists():e.update(sha256=file_hash(p),bytes=p.stat().st_size)
    (root/'campaign.json').write_text(canonical(seal(b)),encoding='utf8')


def altered_bundle(original,target,edit):
    shutil.copytree(original,target);data=json.loads((target/'evidence.json').read_bytes());native=copy.deepcopy(data['occurrences'])
    edit(data);assert data['occurrences']==native
    raw=canonical(data).encode();(target/'evidence.json').write_bytes(raw)
    m=json.loads((target/'manifest.json').read_bytes());m['files']=[e for e in m['files'] if e['path']!='verification.json']
    next(e for e in m['files'] if e['path']=='evidence.json').update(bytes=len(raw),sha256=sha(raw))
    (target/'verification.json').unlink();(target/'manifest.json').write_text(canonical(m),encoding='utf8')
    return data


class TaskContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path('D:/actio-p1c1-tests')/uuid.uuid4().hex[:12];cls.root.mkdir(parents=True)
        (cls.root/'owner.json').write_text(canonical({'owner':'phase1c1-tests'}),encoding='utf8')
        print('Task runtime root:',cls.root,flush=True)
        cls.s=Store(cls.root/'ledger.sqlite',create=True)
        cls.addClassCleanup(cls.s.close)
        for a in ('NEW_A','NEW_B'):cls.s.agent(a,synthetic_spec(a))
        cls.bindings={seat:{'agent':a,'spec_hash':cls.s.agent(a)['spec_hash']} for seat,a in [('A','NEW_A'),('B','NEW_B')]}
        cls.tasks={v:task_card(v,cls.bindings) for v in ('compatible','conflict')}
        cls.runs={};cls.sources={}
        for name,variant,script in [('success','compatible',None),('conflict','conflict',None),('decline','compatible',{'A':'propose:morning','B':'decline'}),
                                    ('illegal','compatible',{'A':'INVALID','B':'accept'}),('illegal-second','compatible',{'A':'propose:morning','B':'INVALID'})]:
            args={} if script is None else {'script':script}
            cls.runs[name]=scheduling(cls.s,name,cls.root,task=cls.tasks[variant],**args)
        cls.runs['replay']=scheduling(cls.s,'replay',cls.root,replay=cls.runs['success']['id'])
        cls.runs['swap']=scheduling(cls.s,'swap',cls.root,task=task_card('compatible',{'A':cls.bindings['B'],'B':cls.bindings['A']}))
        class SecondFails(RuntimePort):
            def __init__(self,store,run,agent,*args,**kwargs):
                if agent=='NEW_B':raise RuntimeError('controlled second actor initialization failure')
                super().__init__(store,run,agent,*args,**kwargs)
        try:scheduling(cls.s,'partial',cls.root,task=cls.tasks['compatible'],runtime_type=SecondFails)
        except RuntimeError as e:
            if 'controlled second actor' not in str(e):raise
        else:raise AssertionError('partial injection not exercised')
        cls.runs['partial']=cls.s.run('partial')
        (cls.root/'bundles').mkdir()
        for name,r in cls.runs.items():
            export_bundle(cls.s.path,r['id'],cls.root/'bundles'/name)
            cls.sources[name]=source_bundle(cls.root/'bundles'/name)[0]

    def setUp(self):self.evidence={'root':str(self.root)}

    def test_01_real_results_privacy_public_history_and_cleanup(self):
        results={}
        expected={'success':'success','conflict':'task_failure','decline':'task_failure','illegal':'task_failure','illegal-second':'task_failure','replay':'success','swap':'success','partial':'infrastructure_failure'}
        for name,run in self.runs.items():
            v=verify_bundle(self.root/'bundles'/name);results[name]=v
            self.assertEqual(v['bundle_integrity'],'valid',v);self.assertEqual(v['facts_consistency'],'partial' if name=='partial' else 'consistent',v)
            self.assertEqual(v['recorded_prefix'],'consistent',v)
            self.assertEqual(v['task_outcome'],expected[name],v)
            self.assertEqual(v['scenario_completeness'],'partial' if name=='partial' else 'complete',v)
        self.assertEqual(len(self.s.rows('SELECT * FROM world WHERE run=?',(self.runs['illegal']['id'],))),0)
        self.assertEqual(len(self.s.rows('SELECT * FROM world WHERE run=?',(self.runs['illegal-second']['id'],))),1)
        self.assertEqual(len(self.s.rows('SELECT * FROM world WHERE run=?',(self.runs['partial']['id'],))),1)
        self.assertIsNone(self.s.row('SELECT * FROM scenario_terminal WHERE run=?',(self.runs['partial']['id'],)))
        data=json.loads(self.sources['conflict']['files']['evidence.json']);m=json.loads(data['run']['input'])
        dispatch=[a for a in data['audit'] if a['kind']=='dispatch_intent']
        for i,row in enumerate(dispatch):
            p=json.loads(row['body']);seat=['A','B'][i]
            self.assertEqual(len(p['observations']),i+1)
            self.assertEqual(p['observations'][-1],actor_observation(m,seat,[] if i==0 else ['propose:morning']))
            for obs in p['observations']:
                parsed=json.loads(obs);self.assertEqual(parsed['own'],m['task']['body']['seats'][seat]['private'])
                self.assertNotIn('seats',parsed);self.assertNotIn('GM_PRIVATE',obs)
        # Actual native/fixture provider capture, not only adapter intent.
        for w in self.s.rows('SELECT w.*,s.agent FROM worker w JOIN stream s ON s.worker=w.id WHERE w.run=?',(self.runs['conflict']['id'],)):
            captures=list(Lines(Path(w['root'])/'provider.jsonl').poll());self.assertTrue(captures)
            text=canonical(captures);self.assertNotIn('SCHEDULING_GM_PRIVATE',text)
            if w['agent']=='NEW_B':self.assertIn('propose:morning',text)
        workers=self.s.rows('SELECT * FROM worker')
        self.assertTrue(workers)
        for w in workers:self.assertEqual(json.loads(w['report'])['after']['active'],0)
        self.assertIsNone(self.s.row('SELECT * FROM lease'))
        self.evidence.update(results=results,workers=workers,model_requests=0)

    def test_02_invalid_before_allocation_idempotency_and_replay(self):
        counts=lambda:[self.s.row('SELECT COUNT(*) n FROM '+table)['n'] for table in ('run','worker')]
        before=counts()
        for field in ('seats','relationships','visibility','action_specs'):
            bad=copy.deepcopy(self.tasks['compatible']);bad['body'].pop(field);bad=seal(bad['body'])
            with self.assertRaises(ContractError):scheduling(self.s,'bad-'+field,self.root,task=bad)
        with patch('actio.application.scenarios.run_engine',side_effect=AssertionError('must not rerun')):
            self.assertEqual(scheduling(self.s,'success',self.root,task=self.tasks['compatible'])['id'],self.runs['success']['id'])
        with self.assertRaises(ContractError):scheduling(self.s,'success',self.root,task=self.tasks['conflict'])
        for kw in ({'task':self.tasks['compatible']},{'script':{'A':'propose:morning','B':'accept'}}):
            with self.assertRaises(ContractError):scheduling(self.s,'bad-replay',self.root,replay=self.runs['success']['id'],**kw)
        self.assertEqual(before,counts());self.evidence.update(no_additional_runs_or_workers=True)

    def test_03_rehashed_task_dispatch_world_contradictions(self):
        def manifest_edit(d,edit):
            m=json.loads(d['run']['input']);edit(m);m['task']=seal(m['task']['body']);m['request']['task_hash']=m['task']['sha256']
            d['run']['input']=canonical(m);d['run']['input_hash']=digest(m)
            terminal=json.loads(d['terminal']['body']);terminal['manifest_hash']=digest(m);d['terminal']['body']=canonical(terminal)
        edits={
            'goal':lambda d:manifest_edit(d,lambda m:m['task']['body']['seats']['A']['private'].update(goal='changed')),
            'relationship':lambda d:manifest_edit(d,lambda m:m['task']['body']['relationships'].update(A='friend')),
            'constraint':lambda d:manifest_edit(d,lambda m:m['task']['body']['seats']['A']['private'].update(available=['afternoon'])),
            'seat':lambda d:manifest_edit(d,lambda m:m['entities'].update(A='NEW_B',B='NEW_A')),
            'world':lambda d:d['world'][1].update(resolved='[event] forged agreement')}
        for field in ('action_spec','observations'):
            def alter(d,field=field):
                row=[a for a in d['audit'] if a['kind']=='dispatch_intent'][1];p=json.loads(row['body'])
                if field=='action_spec':p[field]['tag']='changed'
                else:p[field][-1]=p[field][-1].replace('propose:morning','propose:afternoon')
                row['body']=canonical(p)
            edits[field]=alter
        results={}
        with tempfile.TemporaryDirectory() as tmp:
            for name,edit in edits.items():
                target=Path(tmp)/name;d=altered_bundle(self.root/'bundles/success',target,edit);v=verify_bundle(target)
                self.assertEqual(v['bundle_integrity'],'valid',v);self.assertEqual(v['facts_consistency'],'invalid',v);results[name]=v
                with self.assertRaises((ContractError,KeyError)):terminal_body(d['run'],d['streams'],d['operations'],d['domain_receipts'],d['world'],d['audit'],'success')
        self.evidence.update(counterexamples=results,native_raw='unchanged')

    def test_04_evaluation_real_frozen_task_and_absent_actor(self):
        records={}
        for name,source in self.sources.items():
            for mode in ('deterministic','controlled_response'):
                record,_=evaluate(make_spec(mode,'1'*64),source,self.root/'eval',canonical(response()) if mode=='controlled_response' else None)
                self.assertTrue(verify_record(record)['valid']);r=record['body'];records[name+'-'+mode]=r['measurement']
                insufficient=name=='partial' or mode=='controlled_response' and name.startswith('illegal')
                self.assertEqual(r['measurement']['status'],'not_run' if insufficient else 'valid_measurement',r['measurement'])
                if insufficient:self.assertEqual(r['measurement']['evaluator_calls'],0);self.assertIsNone(r['measurement']['results'])
                else:
                    view=r['input']['body']['view'];text=canonical(view)
                    for hidden in ('scripted_actions','SCHEDULING_GM_PRIVATE','"memory"','"scores"'):self.assertNotIn(hidden,text)
                    if mode=='deterministic':
                        expected='illegal_action' if name.startswith('illegal') else 'not_agreed' if name in ('conflict','decline') else 'agreed'
                        self.assertEqual(r['measurement']['results'][0]['value']['status'],expected)
                    else:self.assertEqual(r['measurement']['results']['agent_2']['goal']['score'],8)
        self.evidence.update(measurements=records)

    def test_05_campaign_completeness_readonly_and_grouping(self):
        dataset=dataset_for({k:self.sources[k] for k in ('success','conflict','replay','swap','partial','illegal')})
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'campaign';run_campaign(dataset,root)
            before={p.relative_to(root).as_posix():file_hash(p) for p in root.rglob('*') if p.is_file()}
            with patch('actio.interfaces.evaluation.evaluate',side_effect=AssertionError('readonly')),patch('actio.interfaces.evaluation.execute_worker',side_effect=AssertionError('readonly')):
                result=verify_campaign(root);self.assertTrue(result['valid'],result)
            self.assertEqual(before,{p.relative_to(root).as_posix():file_hash(p) for p in root.rglob('*') if p.is_file()})
            rejected={}
            for case in ('registration','count','source','spec','missing-record','extra-record','history'):
                target=Path(tmp)/case;shutil.copytree(root,target);index=json.loads((target/'campaign.json').read_bytes())['body']
                report_path=target/index['report'];report=json.loads(report_path.read_bytes())
                if case=='registration':report['body']['registrations'].pop()
                elif case=='count':report['body']['counts']['valid_measurement']+=1
                elif case in ('source','spec'):
                    rid=report['body']['registrations'][0]['record'];p=target/'records'/(rid+'.json');v=json.loads(p.read_bytes())
                    if case=='source':v['body']['request']['source']['content']='f'*64
                    else:v['body']['spec']['body']['revision']=2;v['body']['spec']=seal(v['body']['spec']['body'])
                    p.write_text(canonical(seal(v['body'])),encoding='utf8')
                elif case=='missing-record':(target/'records'/(report['body']['registrations'][0]['record']+'.json')).unlink()
                elif case=='extra-record':(target/'records/extra.json').write_text('{}',encoding='utf8')
                else:
                    name='records/'+report['body']['registrations'][0]['record']+'.json';index['historical']=[name]
                    (target/'campaign.json').write_text(canonical(seal(index)),encoding='utf8')
                report_path.write_text(canonical(seal(report['body'])),encoding='utf8');rewrite_inventory(target)
                rejected[case]=verify_campaign(target);self.assertFalse(rejected[case]['valid'],case)
            # Explicit historical extras may remain but cannot affect current totals.
            (root/'old.json').write_text('{}',encoding='utf8');idx=json.loads((root/'campaign.json').read_bytes())['body']
            idx['historical']=['old.json'];idx['files']['old.json']={'sha256':file_hash(root/'old.json'),'bytes':2,'status':'historical'}
            (root/'campaign.json').write_text(canonical(seal(idx)),encoding='utf8');self.assertTrue(verify_campaign(root)['valid'])
        bad=copy.deepcopy(dataset);bad['body']['entries'][1]['grouping']['group']='calibration_pending'
        with self.assertRaises(ContractError):validate_dataset(seal(bad['body']))
        self.assertEqual({e['grouping']['family'] for e in dataset['body']['entries']},{'adult-neighbors-scheduling.v1'})
        self.evidence.update(valid=result,counterexamples=rejected,independent_units=0)

    def test_06_blinded_templates_binding_missing_conflict_and_disagreement(self):
        record,_=evaluate(make_spec('deterministic','2'*64),self.sources['success'],self.root/'annotation-eval')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'annotations';export_annotations([record],root)
            registry=json.loads((root/'internal.json').read_bytes());blank=[json.loads(x) for x in (root/'blank-labels.jsonl').read_text().splitlines()]
            self.assertTrue(all(v['score'] is None for row in blank for s in row['labels'].values() for v in s.values()))
            public=(root/'annotation.md').read_text(encoding='utf8')+(root/'cases.jsonl').read_text(encoding='utf8')
            for excluded in ('NEW_A','NEW_B','scripted_actions','baseline','"task_result"','"scores"','provider'):self.assertNotIn(excluded,public)
            self.assertFalse(import_labels(registry,blank,['r1','r2'])['valid'])
            rows=[]
            for i,rater in enumerate(('r1','r2')):
                row=copy.deepcopy(blank[0]);row.update(rater=rater,provenance='synthetic_label_fixture')
                for s in row['labels'].values():
                    s['goal']={'status':'scored','score':7+i,'reason':'Synthetic parser test only.'}
                    s['relationship']={'status':'cannot_judge','score':None,'reason':'Symbolic exchange has insufficient relational evidence.'}
                rows.append(row)
            good=import_labels(registry,rows,['r1','r2']);self.assertTrue(good['valid']);self.assertEqual(len(good['disagreements']),2)
            errors={}
            for field in ('task','episode','trace','rubric','view','alias','group'):
                wrong=copy.deepcopy(rows);wrong[0]['binding'][field]='f'*64;result=import_labels(registry,wrong,['r1','r2']);self.assertFalse(result['valid']);errors[field]=result['errors']
            self.assertFalse(import_labels(registry,rows[:1],['r1','r2'])['valid'])
            duplicate=import_labels(registry,rows+[rows[0]],['r1','r2']);self.assertFalse(duplicate['valid'])
            conflict=copy.deepcopy(rows[0]);conflict['labels']['seat_1']['goal']['score']=1
            self.assertTrue(import_labels(registry,rows+[conflict],['r1','r2'])['duplicates'][0]['conflict'])
            self.evidence.update(synthetic_import=good,binding_errors=errors,blank_real_labels=0)

    def test_07_preflight_blocks_before_credentials_clients_workers(self):
        config=template();zero=preflight(config);self.assertEqual(zero['status'],'BLOCKED')
        config=stub_config('http://127.0.0.1:23456')
        config['authorization_ref']='synthetic positive-config fixture, not spend permission'
        runner='''import json,sys,os
from actio.interfaces.preflight import preflight
config=json.loads(sys.stdin.read())
'codec warmup'.encode('utf-16be')
def audit(event,args):
    if event.startswith('socket.') or event in ('subprocess.Popen','open'):raise RuntimeError('side effect denied '+event)
    if event=='import':raise RuntimeError('late import denied '+args[0])
class NoEnvironment(dict):
    def __getitem__(self,key):raise RuntimeError('credential read denied')
    def get(self,*a):raise RuntimeError('credential read denied')
    def __iter__(self):raise RuntimeError('environment enumeration denied')
os.environ=NoEnvironment();sys.addaudithook(audit)
result=preflight(config);print(json.dumps(result));sys.exit(2)
'''
        p=subprocess.run([sys.executable,'-I','-B','-c',runner],input=canonical(config),capture_output=True,text=True,env=clean_env(self.root),timeout=15)
        self.assertEqual(p.returncode,2,p.stderr);positive=json.loads(p.stdout);self.assertTrue(positive['configuration_valid']);self.assertFalse(positive['live_ready'])
        self.evidence.update(zero=zero,positive=positive,guard='denied environment access/open/socket/process/late imports after module import')


if __name__=='__main__':unittest.main()
