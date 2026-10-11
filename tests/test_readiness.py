import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
import uuid

from actio.common import canonical
from actio.common import write_json
from actio.common import clean_env
from actio.common import ContractError
from actio.adapters.persistence.ledger import Ledger
from actio.evidence.accounting import verify_snapshot
from actio.profiles.readiness_contract import rehearsal
from actio.profiles.readiness_contract import reservation
from actio.adapters.transport.transport import TransportPort
from actio.adapters.transport.transport import PACKAGE
from actio.interfaces.transport_export import export_campaign
from actio.evidence.transport_campaign import analyze
from actio.evidence.eval_contract import unseal
from readiness_stub import ReadyStub
from readiness_stub import scan_secret
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from support.priced_case import run


class Readiness(unittest.TestCase):
    def setUp(self):
        self.root=Path('D:/actio-c2b0-tests')/uuid.uuid4().hex[:12];self.root.mkdir(parents=True)
        self.secret='ACTIO_FAKE_'+uuid.uuid4().hex
        self.evidence={'root':str(self.root),'cases':[],'model_requests':0,'external_provider_requests':0,'real_cost':0}

    def case(self,name,plans,*,calls=2,variant='compatible',runtime_type=None):
        root=self.root/name;root.mkdir()
        with ReadyStub(root,plans,self.secret) as service:
            cfg=rehearsal(service.endpoint,root/'authority',uuid.uuid4().hex,calls)
            path=root/'budget.sqlite';l=Ledger(path,config=cfg);l.close()
            result=run(root,cfg,path,self.secret,variant,runtime_type)
        l=Ledger(path,readonly=True)
        try:snapshot=l.snapshot();verify_snapshot(snapshot)
        finally:l.close()
        campaign=export_campaign(path,[root/'bundle'],service.receives,root/'campaign')
        v={'case':name,'root':str(root),'result':result,'budget':snapshot,'receives':service.receives,'campaign':campaign,
           'credential_scan':scan_secret(root,self.secret)}
        write_json(root/'result.json',v);self.evidence['cases'].append(v)
        self.assertTrue(all(r['credential_matched'] for r in service.receives));self.assertTrue(campaign['valid'])
        return v

    def test_01_success_delayed_cache_and_wire_privacy(self):
        for name,variant,second in [('delayed','compatible','accept'),('no-cache','conflict','accept'),('illegal','compatible','INVALID')]:
            case=name if name!='illegal' else 'attached'
            v=self.case(name,[{'text':'propose:morning','case':case},{'text':second}],variant=variant)
            self.assertIsNone(v['result']['error']);self.assertEqual(len(v['receives']),2)
            self.assertTrue(all(a['state']=='settled' for a in v['budget']['attempts']))
            self.assertEqual(v['budget']['meta']['config']['clock'],{'mode':'fixed','instant':'2026-10-09T00:00:00Z'})
            self.assertEqual(sum(e['kind']=='sending' for e in v['budget']['events']),2)
            self.assertEqual(v['budget']['totals']['cost_minor'],18024 if name=='no-cache' else 16848)
            body=json.loads(v['receives'][1]['raw']);payload=json.loads(body['messages'][1]['content'])
            self.assertEqual(set(payload),{'observations','memory','action_spec','op'})
            self.assertEqual(json.loads(payload['observations'][-1])['public_actions'],[{'seat':'A','action':'propose:morning'}])
            self.assertNotIn('scripted_actions',canonical(body));self.assertNotIn('judge',canonical(body))
            self.assertEqual(v['result']['export']['verification']['task_outcome'],'success' if name=='delayed' else 'task_failure')

    def test_02_faults_timeouts_length_and_usage_freeze(self):
        for case in ('400','401','429','500','no-first','stall','never-end','length','missing-usage','fractional','input-over','model-change'):
            with self.subTest(case=case):
                v=self.case(case,[{'text':'propose:morning'},{'text':'accept','case':case}])
                self.assertEqual(len(v['receives']),2)
                self.assertEqual(sum(e['kind']=='sending' for e in v['budget']['events']),2)
                b=next(a for a in v['budget']['attempts'] if a['scope']['seat']=='B')
                if case=='length':self.assertIn(b['state'],('settled','unknown'))
                else:self.assertEqual(b['state'],'unknown')
                self.assertGreaterEqual(next(iter(v['campaign']['report']['runs'].values()))['world_effects'],1)
                # Reopening cannot clear pending/unknown; a new database cannot spend the same authority.
                cfg=v['budget']['meta']['config'];root=Path(v['root'])
                with self.assertRaises(FileExistsError):Ledger(root/'bypass.sqlite',config=cfg)
                self.assertFalse((root/'bypass.sqlite').exists())
                l=Ledger(root/'budget.sqlite')
                try:
                    a=v['budget']['attempts'][0]
                    with self.assertRaises(ContractError):l.reserve(a['id'],a['request'])
                finally:l.close()

    def test_03_independent_controls_last_call_and_last_money(self):
        for constraint in ('calls','money'):
            folder=self.root/constraint;folder.mkdir()
            with ReadyStub(folder,[{'text':'propose:morning'}],self.secret) as service:
                cfg=rehearsal(service.endpoint,folder/'authority',uuid.uuid4().hex,1 if constraint=='calls' else 4)
                if constraint=='money':cfg['budget']['cost_minor']=reservation(cfg)['cost_minor']
                path=folder/'budget.sqlite';l=Ledger(path,config=cfg);l.close();write_json(folder/'config.json',cfg)
                code="""import json,pathlib,sys
sys.path.insert(0,sys.argv[1]);from support.priced_case import run
from actio.common import write_json
root=pathlib.Path(sys.argv[2]);secret=sys.stdin.readline().strip();cfg=json.loads((root.parent/'config.json').read_bytes())
r=run(root,cfg,root.parent/'budget.sqlite',secret);write_json(root/'child-result.json',r)
"""
                children=[];transcripts=[]
                for name in ('one','two'):
                    root=folder/name;root.mkdir();p=subprocess.Popen([sys.executable,'-X','utf8','-I','-B','-c',code,str(ROOT/'tests'),str(root)],cwd=root,env=clean_env(root),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    p.stdin.write((self.secret+'\n').encode());p.stdin.flush();children.append(p)
                try:
                    for p in children:
                        out,err=p.communicate(timeout=100);self.assertEqual(p.returncode,0,err.decode('utf8'))
                        transcripts.append({'exit':p.returncode,'stdout':out.decode('utf8'),'stderr':err.decode('utf8')})
                finally:
                    for p in children:
                        if p.poll() is None:p.kill();p.wait(10)
            l=Ledger(path,readonly=True)
            try:snap=l.snapshot();verify_snapshot(snap)
            finally:l.close()
            self.assertEqual(len(service.receives),1);self.assertEqual(sum(e['kind']=='sending' for e in snap['events']),1)
            report=export_campaign(path,[folder/n/'bundle' for n in ('one','two')],service.receives,folder/'campaign')
            self.evidence['cases'].append({'case':constraint,'root':str(folder),'budget':snap,'receives':service.receives,'report':report,'children':transcripts,'credential_scan':scan_secret(folder,self.secret)})

    def test_04_interruptions_helper_environment_and_pending_authority(self):
        for case,needle in [('reserved','const wireHash='),('sending',"log({kind:'sending'"),('before-settle',"a.response.chunks.push(chunk);yield chunk")]:
            class Interrupted(TransportPort):
                def prepare(port):
                    super().prepare();source=(PACKAGE/'adapters/transport/plugins/transport.mjs').read_text(encoding='utf8')
                    if case=='before-settle':change="if(chunk.type==='finish') process.exit(97)\n        "+needle
                    else:change='process.exit(97)\n    '+needle
                    source=source.replace(needle,change).replace("'./common.mjs'",repr((PACKAGE/'adapters/transport/plugins/common.mjs').as_uri()))
                    fault=port.root/'fault.mjs';fault.write_text(source,encoding='utf8')
                    patch=json.loads((port.root/'profile.patch.yml').read_bytes())
                    for item in patch:
                        for entry in item.get('insert',[]):
                            if entry['id']=='actio-transport':entry['name']=fault.as_uri()
                    write_json(port.root/'profile.patch.yml',patch)
            v=self.case(case,[{'text':'propose:morning'}],runtime_type=Interrupted)
            self.assertEqual(len(v['receives']),1 if case=='before-settle' else 0)
            self.assertEqual(v['budget']['attempts'][0]['state'],'unknown')
            self.assertEqual(v['budget']['totals']['cost_minor'],reservation(v['budget']['meta']['config'])['cost_minor'])
            cfg=v['budget']['meta']['config'];root=Path(v['root'])
            with self.assertRaises(FileExistsError):Ledger(root/'replacement.sqlite',config=cfg)
            l=Ledger(root/'budget.sqlite')
            try:self.assertEqual(l.snapshot()['attempts'][0]['state'],'unknown')
            finally:l.close()

    def test_06_runtime_stderr_credential_is_filtered_before_disk(self):
        class StderrExit(TransportPort):
            def prepare(port):
                super().prepare();source=(PACKAGE/'adapters/transport/plugins/transport.mjs').read_text(encoding='utf8')
                source=source.replace("'./common.mjs'",repr((PACKAGE/'adapters/transport/plugins/common.mjs').as_uri()))
                source=source.replace("  log({kind:'profile'", "  console.error(process.env[config.credential_env]);process.exit(97)\n  log({kind:'profile'")
                fault=port.root/'stderr-test.mjs';fault.write_text(source,encoding='utf8')
                patch=json.loads((port.root/'profile.patch.yml').read_bytes())
                for item in patch:
                    for entry in item.get('insert',[]):
                        if entry['id']=='actio-transport':entry['name']=fault.as_uri()
                write_json(port.root/'profile.patch.yml',patch)
        v=self.case('stderr-exit',[{'text':'propose:morning'}],runtime_type=StderrExit)
        self.assertIsNotNone(v['result']['error']);self.assertEqual(len(v['receives']),0)
        text=''.join(p.read_text(encoding='utf8',errors='replace') for p in Path(v['root']).glob('*/stderr.log'))
        self.assertNotIn(self.secret,text)
        self.evidence['diagnostic_stream_present']=bool(text)

    def test_05_rehashed_accounting_and_portable_reader(self):
        v=self.case('portable',[{'text':'propose:morning'},{'text':'accept'}])
        root=Path(v['root']);index=unseal(json.loads((root/'campaign/campaign.json').read_bytes()))
        objects={k:json.loads((root/'campaign'/n).read_bytes()) for k,n in index['paths'].items()}
        original=unseal(objects['ledger']);received=unseal(objects['receives'])
        for field in ('currency','quote','amount','owner','missing'):
            ledger=copy.deepcopy(original)
            if field=='currency':ledger['meta']['config']['quote']['currency']='SYNTHETIC'
            if field=='quote':ledger['meta']['config']['quote']['input_miss_minor']=1
            if field=='amount':ledger['attempts'][0]['usage']['cost_minor']=0
            if field=='owner':ledger['attempts'][0]['scope']['run']='another'
            if field=='missing':ledger['registrations'].pop()
            with self.assertRaises(ContractError):analyze(objects['dataset'],ledger,received)
        portable=self.root/'reader';portable.mkdir();shutil.copytree(PACKAGE,portable/'actio',ignore=shutil.ignore_patterns('__pycache__'))
        script=portable/'read.py';script.write_text("""import sys,pathlib,json
sys.path.insert(0,str(pathlib.Path(__file__).parent))
def audit(e,a):
 if e.startswith('socket.') or e=='subprocess.Popen':raise RuntimeError('network/process denied')
 if e=='import' and (a[0].split('.')[0] in ('deepseek_harness','concordia') or a[0] in ('actio.adapters.runtime.runtime','actio.adapters.transport.transport')):raise RuntimeError('runtime denied')
 if e=='open':
  p,m,f=a
  if isinstance(m,str) and any(c in m for c in 'wax+') or isinstance(f,int) and f&(1|2|64|512|1024):raise RuntimeError('writes denied')
sys.addaudithook(audit)
from actio.evidence.transport_campaign import verify_campaign
r=verify_campaign(sys.argv[1]);print(json.dumps(r));sys.exit(0 if r['valid'] else 2)
""",encoding='utf8')
        p=subprocess.run([sys.executable,'-X','utf8','-I','-S','-B',str(script),str(root/'campaign')],cwd=portable,env=clean_env(portable),capture_output=True,text=True,encoding='utf8',timeout=30)
        self.assertEqual(p.returncode,0,p.stderr+p.stdout);self.evidence['portable']=json.loads(p.stdout)


if __name__=='__main__':unittest.main()
