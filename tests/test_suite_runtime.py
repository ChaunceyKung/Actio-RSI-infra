from support.paths import runtime_root
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
import uuid
from actio.contracts.json import canonical
from actio.adapters.filesystem.common import write_json
from actio.contracts.json import ContractError
from actio.adapters.filesystem.common import clean_env
from actio.evidence.bundles.eval_contract import seal
from actio.profiles import suite_contract as contract
from actio.tasks.finite import get
from actio.tasks.finite import observation
from actio.tasks.finite import payload
from actio.measurement.oracle import fixture_policy
from actio.evidence.campaigns.suite_measurement import verify
from actio.interfaces.cli.pilot import run_unit
from actio.interfaces.cli.pilot import execute
from actio.adapters.transport.transport import TransportPort
from actio.adapters.persistence.ledger import Ledger
from actio.adapters.filesystem.credentials import scan
from gateway_stub import GatewayStub
from test_suite import GUARD

class SuiteRuntime(unittest.TestCase):
    def setUp(self):
        self.root=runtime_root()/uuid.uuid4().hex[:12];self.root.mkdir(parents=True)
        self.secret='ACTIO_FAKE_'+uuid.uuid4().hex;self.pre=contract.preregistration();self.evidence={'root':str(self.root),'cases':[],'external_requests':0}

    def case(self,name,u,plans,runtime_type=None):
        folder=self.root/name;folder.mkdir()
        with GatewayStub(folder,[{**p,'pilot':True,'model':u['model']} for p in plans],self.secret) as service:
            cfg=contract.config(u['id'],mode=contract.REHEARSAL,endpoint=service.endpoint,authority={'id':uuid.uuid4().hex,'root':str(folder/'authority')})
            entry,r=run_unit(folder/'run',cfg,self.secret,receives=service.receives,runtime_type=runtime_type)
        self.evidence['cases'].append({'root':str(folder),'error':r['error'],'counts':r['campaign']['report']['counts'],'scan':scan(folder,self.secret)})
        return entry,r

    def snapshot(self,entries):
        lookup={e['unit']['id']:e for e in entries}
        return seal({'schema':contract.EVIDENCE,'preregistration':self.pre,'freeze':None,'phase_state':'local_validation','entries':[
            lookup.get(u['id'],{'unit':u,'evidence':None,'reason':'local not_run','episode_ms':None}) for u in self.pre['body']['units']]})

    def test_01_matrix_full_wire_and_portable_reader(self):
        entries=[];comparisons=0
        for u in self.pre['body']['units']:
            acts=fixture_policy(get(u['card']),'own_rule');e,r=self.case(u['id'],u,[{'text':acts[s]} for s in ('A','B')]);entries.append(e)
            self.assertIsNone(r['error'],r['error']);self.assertEqual(len(e['evidence']['receives']),2)
            source=next(iter(e['evidence']['dataset']['body']['sources'].values()));m=json.loads(json.loads(source['files']['evidence.json'])['run']['input'])
            for at in e['evidence']['ledger']['attempts']:
                seat=at['scope']['seat'];other='B' if seat=='A' else 'A';prior=[] if seat=='A' else [acts['A']]
                expected=payload(m,seat,[observation(m,seat,prior[:i]) for i in range(len(prior)+1)])
                wire=json.loads(at['request']['raw']);prepared=copy.deepcopy(at['request']['prepared'])
                self.assertEqual(json.loads(wire['messages'][1]['content']),expected)
                # Compare every prepared/wire field after fixed external random IDs.
                for msg in prepared['messages']:
                    self.assertNotIn(msg['id'],at['request']['raw']);msg['id']='FIXED_AUDIT_ID'
                altered=copy.deepcopy(m);altered['task']['body']['seats'][other]['private']={'hidden':'counterfactual'};altered['task']['body']['grouping']={'private':'different'};altered['task']=seal(altered['task']['body'])
                projected=payload(altered,seat,[observation(altered,seat,prior[:i]) for i in range(len(prior)+1)])
                changed_wire=copy.deepcopy(wire);changed_wire['messages'][1]['content']=json.dumps(projected,sort_keys=True)
                changed_prepared=copy.deepcopy(prepared);changed_prepared['messages'][1]['content'][0]['text']=json.dumps(projected,sort_keys=True)
                self.assertEqual(changed_wire,wire);self.assertEqual(changed_prepared,prepared);comparisons+=1
                self.assertNotIn('hash',at['request']['raw']);self.assertNotIn('ACTOR_',at['request']['raw'])
                rec=next(x for x in e['evidence']['receives'] if x['attempt']==at['id'])
                self.assertEqual(uuid.UUID(rec['headers']['X-Actio-Attempt']).version,4)
                self.assertFalse(any('hash' in k.lower() for k in rec['headers']))
        value=self.snapshot(entries);r=verify(value);self.assertTrue(r['valid'],r);self.assertEqual(r['report']['counts']['sent'],48)
        self.assertEqual(r['report']['counts']['complete_episodes'],24);write_json(self.root/'pilot.json',value);write_json(self.root/'report.json',r)
        code=GUARD+"\nfrom actio.evidence.campaigns.suite_measurement import verify\nr=verify(json.load(open(sys.argv[1],encoding='utf8')));assert r['valid'],r;print(json.dumps(r['report']['counts']))"
        p=subprocess.run([sys.executable,'-I','-B','-c',code,str(self.root/'pilot.json')],capture_output=True,text=True,env=clean_env(self.root),timeout=60)
        self.assertEqual(p.returncode,0,p.stderr);self.evidence.update(portable_counts=json.loads(p.stdout),full_wire_counterfactuals=comparisons,projection='actual official serialization plus hidden-counterfactual substitution; independent UUID fixed, all headers inspected')

    def test_02_format_false_partial_unknown_claim_and_rehash(self):
        u=self.pre['body']['units'][0];acts=fixture_policy(get(u['card']),'own_rule')
        for name,plans in [('illegal-A',[{'text':'INVALID'}]),('illegal-B',[{'text':acts['A']},{'text':'INVALID'}]),
            ('unknown-B',[{'text':acts['A']},{'text':acts['B'],'case':'missing-done'}]),('raw-untrusted',[{'text':acts['A'],'pilot_multichoice':True}])]:
            e,r=self.case(name,u,plans);v=verify(self.snapshot([e]));self.assertTrue(v['valid'],v);row=v['report']['rows'][0]
            if name=='illegal-A':
                self.assertIsNone(r['error']);self.assertFalse(row['metric_cells']['format']['A']['value']);self.assertEqual(row['metric_cells']['b_local']['state'],'not_applicable');self.assertEqual(row['seats'][1]['not_run_reason'],'task_predecessor_invalid')
            if name=='illegal-B':self.assertFalse(row['metric_cells']['format']['B']['value']);self.assertEqual(row['metric_cells']['joint']['state'],'missing')
            if name in ('unknown-B','raw-untrusted'):self.assertIsNotNone(r['error']);self.assertEqual(row['metric_cells']['joint']['state'],'missing')
            if name=='raw-untrusted':self.assertEqual(v['report']['counts']['usage_responses'],1);self.assertEqual(v['report']['counts']['admitted'],0)
            cfg=e['evidence']['ledger']['meta']['config']
            with self.assertRaises(FileExistsError):Ledger(self.root/(name+'-reuse.sqlite'),config=cfg)
            l=Ledger(self.root/name/'run/budget.sqlite');at=e['evidence']['ledger']['attempts'][0]
            try:
                with self.assertRaises(ContractError):l.sending(at['id'],at['binding']['wire_hash'])
            finally:l.close()
            bad=copy.deepcopy(self.snapshot([e])['body']);bad['entries'].pop();self.assertFalse(verify(seal(bad))['valid'])

    def test_03_first_unknown_stops_complete_plan_and_atomic_claim(self):
        u=self.pre['body']['units'][0]
        with GatewayStub(self.root,[{'pilot':True,'text':'INVALID','model':u['model'],'case':'missing-done'}],self.secret) as service:
            r=execute(self.root/'experiment',self.pre,self.secret,endpoint=service.endpoint,authority_root=self.root/'authority',operation_authorization=contract.AUTH,receives=service.receives,contract=contract)
            self.assertEqual(r['counts']['sent'],1);self.assertEqual(r['counts']['unknown'],1);self.assertEqual(r['counts']['not_run'],47)
            with self.assertRaises(FileExistsError):execute(self.root/'different-root',self.pre,self.secret,endpoint=service.endpoint,authority_root=self.root/'authority',operation_authorization=contract.AUTH,receives=service.receives,contract=contract)
        code="from actio.application.pilot import create\nimport sys\ntry:create(sys.argv[1],{'claim':True});print('claimed')\nexcept FileExistsError:print('denied')"
        ps=[subprocess.Popen([sys.executable,'-I','-B','-c',code,str(self.root/'claim.json')],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=clean_env(self.root)) for _ in range(2)]
        out=[p.communicate(timeout=30) for p in ps];self.assertEqual(sorted(o[0].decode().strip() for o in out),['claimed','denied'])
        self.evidence['counts']=r['counts']

    def test_04_deadlines_production_31s_and_short_failure_boundaries(self):
        u=self.pre['body']['units'][0];acts=fixture_policy(get(u['card']),'own_rule')
        e,r=self.case('production-31s',u,[{'text':acts['A'],'headers_delay':31},{'text':acts['B']}]);self.assertIsNone(r['error'],r['error'])
        at=next(a for a in e['evidence']['ledger']['attempts'] if a['scope']['seat']=='A')
        self.assertGreater(at['response']['timings']['headers_ms'],30000);self.assertEqual(at['response']['deadlines']['headers_ms'],60000)
        for name,case,first,idle,total in [('preheaders','no-first',800,1800,3000),('idle-after-text','stall',2000,800,3000),('heartbeat-total','never-end',2000,60000,2500),('near-terminal','attached',2000,60000,2500)]:
            class ShortPort(TransportPort):
                def prepare_gateway(self):
                    super().prepare_gateway();p=self.root/'profile.patch.yml';v=json.loads(p.read_bytes())
                    for x in v:
                        for plugin in x.get('insert',[]):
                            if plugin['id']=='actio-transport':plugin['config'].update(first_ms=first,total_ms=total)
                            if plugin['id']=='llm-pi-ai':plugin['config']['providers']['actio-tokenkey'].update(streamIdleTimeoutMs=idle,timeoutMs=total)
                    write_json(p,v)
            plans=[{'text':acts['A'],'case':case,**({'terminal_delay':3} if name=='near-terminal' else {})}]
            e,r=self.case(name,u,plans,runtime_type=ShortPort);self.assertIsNotNone(r['error'],name)
            v=verify(self.snapshot([e]));self.assertTrue(v['valid'],v);self.assertEqual(v['report']['counts']['sent'],1);self.assertEqual(v['report']['counts']['unknown'],1)
            self.evidence['cases'][-1]['failure']=v['report']['rows'][0]['seats'][0]['failure']
        self.evidence['production_timeout_contract']=contract.TIMEOUTS

if __name__=='__main__':unittest.main()
