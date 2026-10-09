import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
import uuid
from unittest.mock import patch
from actio.common import ContractError,write_json,clean_env,digest
from actio.gateway_contract import template,validate,plan,AUTH
from actio.gateway import execute,scan
from actio.budget import Ledger,verify_snapshot
from actio.transport import TransportPort,PACKAGE
from gateway_stub import GatewayStub

class Gateway(unittest.TestCase):
    def setUp(self):
        self.root=Path('D:/actio-c2b1-tests')/uuid.uuid4().hex[:12];self.root.mkdir(parents=True)
        self.secret='ACTIO_FAKE_'+uuid.uuid4().hex
        self.evidence={'root':str(self.root),'cases':[],'external_requests':0}

    def case(self,name,plans,model='gpt-5.6',runtime_type=None,both=False):
        folder=self.root/name;folder.mkdir();runroot=folder/'run'
        with GatewayStub(folder,[{**p,'model':model} for p in plans],self.secret) as server:
            c=template(model,'tokenkey_rehearsal',server.endpoint);c['plan']=['compatible','conflict'] if both else ['compatible']
            c['authority']={'id':uuid.uuid4().hex,'root':str(folder/'authority')}
            r=execute(c,runroot,self.secret,operation_authorization=AUTH,runtime_type=runtime_type,receives=server.receives)
        l=Ledger(runroot/'budget.sqlite',readonly=True)
        try:snapshot=l.snapshot();verify_snapshot(snapshot)
        finally:l.close()
        out={'case':name,'root':str(folder),'result':r,'ledger':snapshot,'receives':server.receives,'credential_scan':scan(folder,self.secret)}
        self.evidence['cases'].append(out);write_json(folder/'result.json',out)
        self.assertTrue(r['campaign']['valid']);return out

    def test_01_explicit_uncapped_plan_and_no_side_effects(self):
        c=template();self.assertIsNone(c['cost_limit_minor'])
        for k,value in [('spending_policy','uncapped'),('cost_limit_minor',0),('cost_limit_minor',10**30),('authorization_basis','approved=true'),('endpoint','https://api.openai.com/v1'),('schema','pilot-config.v99')]:
            changed=copy.deepcopy(c);changed[k]=value
            with self.assertRaises(ContractError):validate(changed)
        code="""import sys,os
def audit(e,a):
 if e.startswith('socket.') or e=='subprocess.Popen':raise RuntimeError('side effect')
sys.addaudithook(audit)
class NoEnv(dict):
 def get(self,*a):raise RuntimeError('env lookup')
 def __getitem__(self,*a):raise RuntimeError('env lookup')
os.environ=NoEnv()
from actio.gateway_contract import template,plan
from actio.common import canonical
print(canonical(plan(template())))
"""
        r=subprocess.run([sys.executable,'-I','-B','-c',code],cwd=self.root,env=clean_env(self.root),capture_output=True,text=True,encoding='utf8',timeout=20)
        self.assertEqual(r.returncode,0,r.stderr);self.evidence['plan']=json.loads(r.stdout)

    def test_02_official_models_two_cards_usage_and_visibility(self):
        for model in ('gpt-5.6','claude-sonnet-4-6'):
            v=self.case(model,[{'text':'propose:morning','case':'gateway-cost'},{'text':'accept'},{'text':'propose:morning'},{'text':'decline'}],model,both=True)
            self.assertEqual(len(v['receives']),4);self.assertTrue(all(a['state']=='settled' for a in v['ledger']['attempts']))
            self.assertIsNone(v['ledger']['totals']['cost_minor'])
            usage=[a['usage'] for a in v['ledger']['attempts']];self.assertIn('0.000123',[u['gateway_reported_cost_raw'] for u in usage])
            self.assertEqual([r['bundle']['verification']['task_outcome'] for r in v['result']['episodes']],['success','task_failure'])
            for index in (1,3):
                raw=json.loads(v['receives'][index]['raw']);payload=json.loads(raw['messages'][1]['content'])
                self.assertEqual(json.loads(payload['observations'][-1])['public_actions'],[{'seat':'A','action':'propose:morning'}])
                self.assertNotIn('answer',payload);self.assertNotIn('thinking',raw);self.assertNotIn('dsh_plugin_packages',raw)

    def test_03_errors_unknown_length_no_retry(self):
        for name in ('400','401','429','500','missing-done','missing-usage','fractional','model-change','length','illegal'):
            with self.subTest(case=name):
                v=self.case(name,[{'text':'propose:morning'},{'text':'INVALID' if name=='illegal' else 'accept','case':'attached' if name=='illegal' else name}])
                self.assertEqual(len(v['receives']),2)
                b=next(a for a in v['ledger']['attempts'] if a['scope']['seat']=='B')
                self.assertEqual(b['state'],'settled' if name in ('length','illegal') else 'unknown')
                self.assertIsNone(b['usage']['cost_minor'] if b['usage'] else None)
                l=Ledger(Path(v['root'])/'run/budget.sqlite')
                try:
                    with self.assertRaises(ContractError):l.sending(b['id'],b['binding']['wire_hash'])
                finally:l.close()
                with self.assertRaises(FileExistsError):Ledger(Path(v['root'])/'bypass.sqlite',config=v['ledger']['meta']['config'])

    def test_04_deadlines_and_secret_diagnostics(self):
        for name in ('delayed','no-first','stall','never-end'):
            v=self.case(name,[{'text':'propose:morning'},{'text':'accept','case':name}])
            self.assertEqual(len(v['receives']),2)
            self.assertEqual(sum(a['state']=='unknown' for a in v['ledger']['attempts']),0 if name=='delayed' else 1)
        class SplitStderr(TransportPort):
            def prepare(port):
                super().prepare();s=(PACKAGE/'plugins/transport.mjs').read_text(encoding='utf8').replace("'./common.mjs'",repr((PACKAGE/'plugins/common.mjs').as_uri()))
                s=s.replace("  log({kind:'profile'","  const k=process.env[config.credential_env];process.stderr.write(k.slice(0,12));await new Promise(r=>setTimeout(r,25));process.stderr.write(k.slice(12)+'\\n');process.exit(97)\n  log({kind:'profile'")
                p=port.root/'split-test.mjs';p.write_text(s,encoding='utf8');cfg=json.loads((port.root/'profile.patch.yml').read_bytes())
                for item in cfg:
                    for e in item.get('insert',[]):
                        if e['id']=='actio-transport':e['name']=p.as_uri()
                write_json(port.root/'profile.patch.yml',cfg)
        v=self.case('split-stderr',[{'text':'propose:morning'}],runtime_type=SplitStderr)
        self.assertEqual(len(v['receives']),0);self.assertIsNotNone(v['result']['episodes'][0]['error'])

    def test_05_offline_reader_rehash_and_send_boundaries(self):
        class Boundary(TransportPort):
            def prepare(port):
                super().prepare();s=(PACKAGE/'plugins/transport.mjs').read_text(encoding='utf8').replace("'./common.mjs'",repr((PACKAGE/'plugins/common.mjs').as_uri()))
                s=s.replace("  log({kind:'profile'","  for(const url of ['https://api.openai.com/v1/chat/completions',config.endpoint+'/models']){try{await globalThis.fetch(url,{method:'POST',body:'{}'});throw Error('UNEXPECTED_SEND')}catch(e){if(String(e).includes('UNEXPECTED_SEND'))throw e}}\n  log({kind:'profile'")
                s=s.replace('      active=null',"      try{await globalThis.fetch(config.endpoint+'/chat/completions',{method:'POST',body:'{}'});throw Error('DUPLICATE_SEND')}catch(e){if(String(e).includes('DUPLICATE_SEND'))throw e}\n      active=null")
                p=port.root/'boundary.mjs';p.write_text(s,encoding='utf8');cfg=json.loads((port.root/'profile.patch.yml').read_bytes())
                for item in cfg:
                    for e in item.get('insert',[]):
                        if e['id']=='actio-transport':e['name']=p.as_uri()
                write_json(port.root/'profile.patch.yml',cfg)
        v=self.case('boundary',[{'text':'propose:morning'},{'text':'accept'}],runtime_type=Boundary)
        self.assertEqual(len(v['receives']),2)
        for field in ('amount','model','plan'):
            s=copy.deepcopy(v['ledger'])
            if field=='amount':s['attempts'][0]['usage']['cost_minor']=0
            elif field=='model':s['attempts'][0]['usage']['provider_identity']['response_model']='other'
            else:s['registrations'].pop()
            with self.assertRaises(ContractError):verify_snapshot(s)
        code="""import sys
def audit(e,a):
 if e.startswith('socket.') or e=='subprocess.Popen':raise RuntimeError('network/process denied')
 if e=='import' and a[0].split('.')[0] in ('deepseek_harness','concordia'):raise RuntimeError('runtime denied')
 if e=='open' and ((isinstance(a[1],str) and any(c in a[1] for c in 'wax+')) or (isinstance(a[2],int) and a[2]&(1|2|64|512|1024))):raise RuntimeError('write denied')
sys.addaudithook(audit)
from actio.transport_campaign import verify_campaign
from actio.common import canonical
r=verify_campaign(sys.argv[1]);print(canonical(r));assert r['valid']
"""
        r=subprocess.run([sys.executable,'-I','-B','-c',code,str(Path(v['root'])/'run/campaign')],cwd=self.root,env=clean_env(self.root),capture_output=True,text=True,encoding='utf8',timeout=30)
        self.assertEqual(r.returncode,0,r.stderr+r.stdout);self.evidence['portable']=json.loads(r.stdout)

if __name__=='__main__':unittest.main()
