import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
import uuid

from actio.contracts.json import canonical
from actio.adapters.filesystem.common import write_json
from actio.adapters.filesystem.common import clean_env
from actio.contracts.json import ContractError
from actio.adapters.persistence.ledger import Ledger
from actio.evidence.audit.accounting import verify_snapshot
from actio.profiles.transport import config
from actio.interfaces.transport_export import export_campaign
from actio.evidence.campaigns.transport_campaign import analyze
from actio.evidence.bundles.evaluation import read_json
from actio.evidence.bundles.evaluation import source_bundle
from actio.interfaces.cli.evaluation import evaluate
from actio.evidence.bundles.evaluation import prepare
from actio.evidence.bundles.eval_contract import unseal
from actio.evidence.bundles.eval_contract import seal
from actio.evidence.bundles.eval_contract import make_spec
from chat_stub import ChatStub

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from support.transport_case import run


class Transport(unittest.TestCase):
    def setUp(self):
        self.root=(Path(__file__).resolve().parents[2]/'t')/uuid.uuid4().hex[:12];self.root.mkdir(parents=True)
        self.evidence={'root':str(self.root),'cases':[],'model_requests':0}

    def case(self,name,plans,variant='compatible',calls=2):
        root=self.root/name;root.mkdir()
        with ChatStub(root,plans) as service:
            cfg=config(service.endpoint,calls);ledger=Ledger(root/'budget.sqlite',config=cfg);ledger.close()
            result=run(root,service.endpoint,root/'budget.sqlite',cfg,variant)
        ledger=Ledger(root/'budget.sqlite',readonly=True)
        try:snapshot=ledger.snapshot();verify_snapshot(snapshot)
        finally:ledger.close()
        campaign=export_campaign(root/'budget.sqlite',[root/'bundle'],service.receives,root/'campaign')
        value={'name':name,'error':result['error'],'verification':result['export']['verification'],
               'budget':snapshot,'receives':service.receives,'campaign':campaign}
        write_json(root/'result.json',value);self.evidence['cases'].append(value)
        self.assertTrue(campaign['valid'],campaign)
        self.assertTrue(all(w['state']=='reaped' for w in read_json(root/'bundle/evidence.json')['workers']))
        return value

    def test_01_official_success_visibility_and_domain_outcomes(self):
        for name,variant,answer,outcome,complete,receives in [
            ('attached-trailing','compatible','accept','success','complete',2),
            ('conflict','conflict','accept','task_failure','complete',2),
            ('declined','compatible','decline','task_failure','complete',2),
            ('illegal','compatible','INVALID','task_failure','complete',2),
        ]:
            with self.subTest(name=name):
                v=self.case(name,[{'text':'propose:morning','case':'attached'},{'text':answer,'case':'trailing'}],variant)
                self.assertIsNone(v['error']);self.assertEqual(v['verification']['task_outcome'],outcome)
                self.assertEqual(v['verification']['scenario_completeness'],complete);self.assertEqual(len(v['receives']),receives)
                for r in v['receives']:
                    body=json.loads(r['raw']);task=json.loads(body['messages'][1]['content'])
                    self.assertEqual(set(task),{'observations','memory','action_spec','op'})
                    obs=json.loads(task['observations'][-1]);self.assertNotIn('judge',canonical(task));self.assertNotIn('scripted_actions',canonical(task))
                    if obs['seat']=='B':self.assertEqual(obs['public_actions'],[{'seat':'A','action':'propose:morning'}])
                    if variant=='conflict':self.assertEqual(obs['own']['available'],['morning'] if obs['seat']=='A' else ['afternoon'])
                self.assertTrue(all(a['state']=='settled' for a in v['budget']['attempts']))
                self.assertEqual(v['budget']['totals']['input_tokens'],24)  # Includes each cache hit once.

    def test_02_real_faults_usage_unknown_no_retry_and_preserved_prefix(self):
        for case in ('429','500','missing-done','missing-usage','empty','malformed','deadline','negative','fractional','contradiction','cache-conflict','over-limit','redirect'):
            with self.subTest(case=case):
                v=self.case(case,[{'text':'propose:morning'},{'text':'accept','case':case}])
                self.assertEqual(len(v['receives']),2)
                states={a['scope']['seat']:a['state'] for a in v['budget']['attempts']}
                self.assertEqual(states,{'A':'settled','B':'unknown'})
                self.assertEqual(v['budget']['totals']['calls'],2)
                self.assertGreaterEqual(next(iter(v['campaign']['report']['runs'].values()))['world_effects'],1)
                if case in ('missing-usage','negative','fractional','contradiction','cache-conflict','over-limit'):
                    # SDK may have a complete action even when accounting must stay unknown.
                    self.assertEqual(v['verification']['scenario_completeness'],'complete')
                else:self.assertEqual(v['verification']['scenario_completeness'],'partial')

    def test_03_zero_exhausted_unknown_and_usage_override(self):
        zero=self.case('zero',[{'text':'propose:morning'},{'text':'accept'}],calls=0)
        self.assertEqual(len(zero['receives']),0);self.assertEqual(zero['budget']['attempts'][0]['state'],'denied')
        last=self.case('exhausted',[{'text':'propose:morning'},{'text':'accept'}],calls=1)
        self.assertEqual(len(last['receives']),1);self.assertEqual(last['campaign']['report']['counts']['denied'],1)
        unknown=self.case('unknown-blocks',[{'text':'propose:morning','case':'missing-usage'},{'text':'accept'}])
        self.assertEqual(len(unknown['receives']),1);self.assertEqual(unknown['campaign']['report']['counts']['unknown'],1)
        override=self.case('override',[{'text':'propose:morning','case':'override'},{'text':'accept','case':'trailing'}])
        self.assertEqual(override['budget']['totals']['input_tokens'],24)
        a=override['budget']['attempts'][0];ledger=Ledger(self.root/'override/budget.sqlite')
        try:
            with self.assertRaises(ContractError):ledger.reserve(a['id'],a['request'])
            with self.assertRaises(ContractError):ledger.sending(a['id'],a['binding']['wire_hash'])
        finally:ledger.close()

    def test_04_sealed_counterexamples_and_portable_readonly(self):
        v=self.case('readonly',[{'text':'propose:morning'},{'text':'accept','case':'trailing'}])
        source=source_bundle(self.root/'readonly/bundle')[0]
        record,_=evaluate(make_spec('deterministic','0'*64),source,self.root/'deterministic')
        self.assertEqual(record['body']['admission']['status'],'admitted')
        self.assertEqual(record['body']['measurement']['status'],'valid_measurement')
        _,admission,*_=prepare(make_spec('controlled_response','0'*64),source)
        self.assertEqual(admission['status'],'insufficient')  # No new judge path.
        self.evidence['transport_deterministic_evaluation']=record
        campaign=self.root/'readonly/campaign';index=unseal(read_json(campaign/'campaign.json'))
        d=read_json(campaign/index['paths']['dataset']);ledger=unseal(read_json(campaign/index['paths']['ledger']));receives=unseal(read_json(campaign/index['paths']['receives']))
        for name,change in {
            'amount':lambda l:l['totals'].update(cost_minor=0),
            'missing_failure':lambda l:l['registrations'].pop(),
            'wrong_run':lambda l:l['attempts'][0]['scope'].update(run='wrong'),
            'repeat_settlement':lambda l:l['events'].append({**l['events'][-1],'seq':len(l['events'])+1}),
            'wrong_wire':lambda l:l['attempts'][0]['binding'].update(wire_hash='0'*64),
        }.items():
            other=copy.deepcopy(ledger);change(other)
            with self.assertRaises((ContractError,KeyError),msg=name):analyze(d,other,receives)
        bad=copy.deepcopy(receives);bad[0]['attempt']=bad[1]['attempt']
        with self.assertRaises(ContractError):analyze(d,ledger,bad)
        # Standard-library portable reader, no optional dependencies, network, writes, Worker or evaluator.
        import shutil
        import actio
        portable=self.root/'portable';portable.mkdir();shutil.copytree(Path(actio.__file__).parent,portable/'actio',ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(campaign,portable/'campaign')
        script=portable/'read.py';script.write_text('''import sys,pathlib,json
base=pathlib.Path(__file__).parent;sys.path.insert(0,str(base))
def audit(e,a):
 if e.startswith('socket.') or e=='subprocess.Popen':raise RuntimeError('no network/worker')
 if e=='import' and (a[0].split('.')[0] in ('deepseek_harness','concordia') or a[0] in ('actio.adapters.runtime.runtime','actio.adapters.transport.transport')):raise RuntimeError('no runtime')
 if e=='open':
  path,mode,flags=a
  if isinstance(mode,str) and any(c in mode for c in 'wax+') or isinstance(flags,int) and flags&(1|2|64|512|1024):raise RuntimeError('no writes')
sys.addaudithook(audit)
from actio.evidence.campaigns.transport_campaign import verify_campaign
r=verify_campaign(base/'campaign');print(json.dumps(r));sys.exit(0 if r['valid'] else 2)
''',encoding='utf8')
        p=subprocess.run([sys.executable,'-I','-S','-B',str(script)],cwd=portable,env=clean_env(portable),capture_output=True,text=True,encoding='utf8',timeout=30)
        self.assertEqual(p.returncode,0,p.stderr+p.stdout);self.evidence['portable']=json.loads(p.stdout)


if __name__=='__main__':unittest.main()
