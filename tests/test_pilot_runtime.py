import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
import uuid
from actio.common import canonical
from actio.common import digest
from actio.common import write_json
from actio.common import ContractError
from actio.common import clean_env
from actio.evidence.eval_contract import seal
from actio.evidence.eval_contract import unseal
from actio.profiles.pilot_contract import preregistration
from actio.profiles.pilot_contract import config
from actio.profiles.pilot_contract import AUTH
from actio.interfaces.pilot import run_unit
from actio.interfaces.pilot import execute
from actio.adapters.filesystem.publication import create
from actio.evidence.pilot_measurement import verify
from actio.adapters.filesystem.credentials import scan
from actio.adapters.persistence.ledger import Ledger
from actio.adapters.transport.transport import TransportPort
from actio.adapters.transport.transport import PACKAGE
from gateway_stub import GatewayStub


class PilotRuntime(unittest.TestCase):
    def setUp(self):
        self.root=Path('D:/actio-c2b2-tests')/uuid.uuid4().hex[:12];self.root.mkdir(parents=True)
        self.secret='ACTIO_FAKE_'+uuid.uuid4().hex;self.pre=preregistration()
        self.evidence={'root':str(self.root),'cases':[],'external_requests':0}

    def case(self,name,u,plans,runtime_type=None):
        folder=self.root/name;folder.mkdir()
        with GatewayStub(folder,[{**p,'pilot':True,'model':u['model']} for p in plans],self.secret) as service:
            cfg=config(u['id'],mode='tokenkey_pilot_rehearsal',endpoint=service.endpoint,authority={'id':uuid.uuid4().hex,'root':str(folder/'authority')})
            entry,result=run_unit(folder/'run',cfg,self.secret,receives=service.receives,runtime_type=runtime_type)
        self.evidence['cases'].append({'root':str(folder),'error':result['error'],'counts':result['campaign']['report']['counts'],'scan':scan(folder,self.secret)})
        return entry,result

    def test_01_full_matrix_and_counterfactual_actual_wire(self):
        entries=[];actual={};pairs=0
        reuse=Path(sys.argv[3]) if len(sys.argv)>3 else None
        prior=json.loads(reuse.read_bytes()) if reuse else None
        if prior:
            self.assertEqual(prior['body']['preregistration'],self.pre)
            self.evidence['read_only_reuse']=str(reuse)
        for u in self.pre['body']['units']:
            if u['repeat']!=1:
                entries.append({'unit':u,'evidence':None,'reason':'second repeat excluded from local matrix validation','episode_ms':None});continue
            c=next(c for c in self.pre['body']['cards'] if c['id']==u['card']);a='propose:'+c['available']['A'][0];b='accept' if c['available']['A']==c['available']['B'] else 'decline'
            if prior:
                e=next(e for e in prior['body']['entries'] if e['unit']==u)
                r=json.loads((reuse.parent/u['id']/'run/result.json').read_bytes())
            else:e,r=self.case(u['id'],u,[{'text':a},{'text':b}])
            entries.append(e)
            self.assertIsNone(r['error'],r);self.assertEqual(len(e['evidence']['receives']),2)
            attempts=e['evidence']['ledger']['attempts']
            for seat in ('A','B'):
                at=next(x for x in attempts if x['scope']['seat']==seat);wire=json.loads(at['request']['raw']);payload=json.loads(wire['messages'][1]['content'])
                self.assertEqual(set(payload),{'observations','memory','action_spec'});self.assertEqual(payload['memory'],[])
                self.assertNotIn('task_hash',canonical(wire));self.assertNotIn('ACTOR_',canonical(wire))
                if seat=='B':self.assertEqual(json.loads(payload['observations'][-1])['public_actions'],[{'seat':'A','action':a}])
                # Compare entire prepared and wire payload from actual official serializer.
                key=(u['model'],u['presentation'],seat,c['available'][seat][0],a if seat=='B' else None)
                prepared=copy.deepcopy(at['request']['prepared'])
                for index,message in enumerate(prepared['messages']):
                    self.assertEqual(set(message),{'id','role','source','content'})
                    self.assertNotIn(message['id'],at['request']['raw'])
                    # SDK occurrence IDs are adapter metadata, absent from provider wire.
                    # Hold them constant for the prepared counterfactual comparison.
                    message['id']='FIXED_EXTERNAL_MESSAGE_'+str(index)
                visible={'wire':at['request']['raw'],'prepared_with_fixed_external_ids':prepared}
                if key in actual:self.assertEqual(actual[key],visible);pairs+=1
                actual[key]=visible
        evidence=seal({'schema':'pilot-evidence.v1','preregistration':self.pre,'freeze':None,'entries':entries,'phase_state':'local_validation'})
        result=verify(evidence);self.assertTrue(result['valid'],result);self.assertEqual(result['report']['counts']['sent'],32)
        self.assertEqual(result['report']['counts']['admitted'],32);self.assertGreaterEqual(pairs,8)
        write_json(self.root/'pilot.json',evidence);write_json(self.root/'report.json',result)
        # Full offline verification with denied env, key, runtime, process, network and writes.
        code='''import sys,os,json
def audit(e,a):
 if e.startswith('socket.') or e=='subprocess.Popen':raise RuntimeError('network/process denied')
 if e=='import' and (a[0].split('.')[0] in ('deepseek_harness','concordia') or a[0] in ('actio.adapters.runtime.runtime','actio.adapters.transport.transport','actio.application.gateway','actio.adapters.runtime.eval_worker')):raise RuntimeError('runtime denied')
 if e=='open':
  if 'token_key' in str(a[0]):raise RuntimeError('credential denied')
  if isinstance(a[1],str) and any(c in a[1] for c in 'wax+') or isinstance(a[2],int) and a[2]&(1|2|64|512|1024):raise RuntimeError('write denied')
sys.addaudithook(audit)
class NoEnv(dict):
 def get(self,*a):raise RuntimeError('env denied')
 def __getitem__(self,*a):raise RuntimeError('env denied')
os.environ=NoEnv()
from actio.evidence.pilot_measurement import verify
r=verify(json.load(open(sys.argv[1],encoding='utf8')));assert r['valid'],r;print(json.dumps(r['report']['counts']))
'''
        r=subprocess.run([sys.executable,'-I','-B','-c',code,str(self.root/'pilot.json')],cwd=self.root,env=clean_env(self.root),capture_output=True,text=True,timeout=60)
        self.assertEqual(r.returncode,0,r.stderr);self.evidence.update(offline=json.loads(r.stdout),actual_counterfactual_pairs=pairs)
        # Rehash raw text and every duplicate audit fact; semantic reader still rejects.
        bad=copy.deepcopy(evidence['body']);entry=next(e for e in bad['entries'] if e['evidence']);ledger=entry['evidence']['ledger'];attempt=next(a for a in ledger['attempts'] if a['scope']['seat']=='A')
        original=attempt['response']['raw'];attempt['response']['raw']=original.replace('propose:','WRONG:')
        self.assertNotEqual(original,attempt['response']['raw'])
        import base64
        attempt['response']['raw_base64']=base64.b64encode(attempt['response']['raw'].encode()).decode()
        from actio.evidence.stream_audit import verdict
        attempt['text_integrity']=verdict(attempt['response'])
        for ev in ledger['events']:
            if ev['attempt']==attempt['id'] and ev['kind']=='settled':ev['body'].update(response=attempt['response'],text_integrity=attempt['text_integrity'])
        source=next(iter(entry['evidence']['dataset']['body']['sources'].values()));data=json.loads(source['files']['evidence.json'])
        for row in data['audit']:
            if row['kind']=='transport_attempt' and row['op']==attempt['id']:row['body']=canonical(attempt)
        source['files']['evidence.json']=canonical(data);source['files'].pop('verification.json')
        manifest=json.loads(source['files']['manifest.json']);manifest['files']=[f for f in manifest['files'] if f['path']!='verification.json']
        import hashlib
        for r in entry['evidence']['receives']:
            if r['attempt']==attempt['id']:r['response'].update(raw=attempt['response']['raw'],sha256=hashlib.sha256(attempt['response']['raw'].encode()).hexdigest())
        for f in manifest['files']:
            if f['path']=='evidence.json':f.update(bytes=len(source['files']['evidence.json'].encode()),sha256=hashlib.sha256(source['files']['evidence.json'].encode()).hexdigest())
        source['files']['manifest.json']=canonical(manifest);entry['evidence']['dataset']=seal(entry['evidence']['dataset']['body'])
        rejected=verify(seal(bad));self.assertFalse(rejected['valid']);self.assertIn('rejected text cannot mutate world',rejected['error'])
        self.evidence['rehashed_contradiction']=rejected

    def test_02_failure_unknown_length_illegal_and_one_time_authority(self):
        u=self.pre['body']['units'][0]
        for case in ('missing-done','model-change','length','illegal'):
            e,r=self.case(case,u,[{'text':'INVALID' if case=='illegal' else 'propose:morning','case':'attached' if case=='illegal' else case}])
            attempts=e['evidence']['ledger']['attempts'];self.assertEqual(len(attempts),1)
            self.assertEqual(len(e['evidence']['receives']),1)
            if case=='illegal':self.assertIsNone(r['error']);self.assertEqual(r['bundle_verification']['task_outcome'],'task_failure')
            else:self.assertIsNotNone(r['error'])
            cfg=e['evidence']['ledger']['meta']['config']
            with self.assertRaises(FileExistsError):Ledger(self.root/(case+'-replay.sqlite'),config=cfg)
            l=Ledger(self.root/case/'run/budget.sqlite')
            try:
                with self.assertRaises(ContractError):l.sending(attempts[0]['id'],attempts[0]['binding']['wire_hash'])
            finally:l.close()

    def test_03_full_plan_stops_on_unknown_and_claim_cannot_move(self):
        u=self.pre['body']['units'][0]
        with GatewayStub(self.root,[{'pilot':True,'text':'propose:morning','model':u['model'],'case':'missing-done'}],self.secret) as service:
            report=execute(self.root/'experiment',self.pre,self.secret,endpoint=service.endpoint,authority_root=self.root/'authority',operation_authorization=AUTH,receives=service.receives)
            self.assertEqual(report['counts']['sent'],1);self.assertEqual(report['counts']['unknown'],1);self.assertEqual(report['counts']['not_run'],63)
            with self.assertRaises(FileExistsError):execute(self.root/'replacement',self.pre,self.secret,endpoint=service.endpoint,authority_root=self.root/'authority',operation_authorization=AUTH,receives=service.receives)
        self.evidence['report']=report['counts']

    def test_04_atomic_experiment_claim_race(self):
        code='''import sys,pathlib
from actio.application.pilot import create
try:create(pathlib.Path(sys.argv[1]),{'claim':True});print('claimed')
except FileExistsError:print('denied')
'''
        children=[subprocess.Popen([sys.executable,'-I','-B','-c',code,str(self.root/'claim.json')],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=clean_env(self.root)) for _ in range(2)]
        outputs=[p.communicate(timeout=30) for p in children]
        self.assertEqual(sorted(o[0].decode().strip() for o in outputs),['claimed','denied']);self.assertTrue(all(p.returncode==0 for p in children))

    def test_05_multichoice_usage_separate_and_utf8_byte_boundaries(self):
        u=self.pre['body']['units'][0]
        e,r=self.case('multichoice',u,[{'text':'propose:morning','pilot_multichoice':True}])
        at=e['evidence']['ledger']['attempts'][0]
        self.assertEqual(at['state'],'settled');self.assertEqual(at['text_integrity']['status'],'rejected');self.assertIsNotNone(r['error'])
        data=json.loads(next(iter(e['evidence']['dataset']['body']['sources'].values()))['files']['evidence.json'])
        self.assertEqual(data['world'],[]);self.assertEqual(data['domain_receipts'],[])
        e,r=self.case('utf8-one-byte-writes',u,[{'text':'早上','utf8':True}])
        at=e['evidence']['ledger']['attempts'][0]
        self.assertEqual(at['text_integrity']['text'],'早上');self.assertEqual(at['text_integrity']['status'],'verified')
        self.assertIsNone(r['error']);self.assertEqual(r['bundle_verification']['task_outcome'],'task_failure')

if __name__=='__main__':unittest.main()
