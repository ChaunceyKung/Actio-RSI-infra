import copy
import json
from pathlib import Path
import unittest
import uuid
from actio.profiles import candidate_campaign as contract
from actio.profiles.gateway_base import AUTH
from actio.common import write_json
from actio.evidence.eval_contract import seal
from actio.interfaces.pilot import run_unit
from actio.interfaces.pilot import execute
from actio.interfaces.candidate import verify
from actio.evidence.candidate_measurement import source
from actio.tasks.candidate import payload
from actio.tasks.finite import observation
from actio.tasks.finite import get
from actio.measurement.oracle import fixture_policy
from actio.adapters.filesystem.credentials import scan
from gateway_stub import GatewayStub


class CandidateRuntime(unittest.TestCase):
    def setUp(self):
        self.root=Path('D:/actio-c2c1-tests')/uuid.uuid4().hex[:12];self.root.mkdir(parents=True)
        self.secret='ACTIO_FAKE_'+uuid.uuid4().hex;self.pre=contract.preregistration();self.evidence={'root':str(self.root),'external_requests':0}

    def test_dual_channel_official_runtime_and_hidden_views(self):
        u=next(u for u in self.pre['body']['units'] if u['arm']=='candidate');actions=fixture_policy(get(u['card']),'own_rule')
        with GatewayStub(self.root,[{'pilot':True,'model':'gpt-5.6','text':actions[s],'reasoning':'Synthetic channel marker.','utf8':True} for s in ('A','B')],self.secret) as service:
            c=contract.config(u['id'],endpoint=service.endpoint,authority={'id':uuid.uuid4().hex,'root':str(self.root/'authority')})
            e,result=run_unit(self.root/'run',c,self.secret,receives=service.receives)
        self.evidence['error']=result['error'];self.assertIsNone(result['error'],result['error'])
        entries=[e if x==u else {'unit':x,'evidence':None,'reason':'local admission subset','episode_ms':None} for x in self.pre['body']['units']]
        value=seal({'schema':contract.EVIDENCE,'preregistration':self.pre,'freeze':None,'entries':entries,'phase_state':'local_validation'})
        report=verify(value);write_json(self.root/'pilot.json',value);write_json(self.root/'report.json',report);self.assertTrue(report['valid'],report)
        data=source(e);m=json.loads(data['run']['input']);checks=[]
        for at in e['evidence']['ledger']['attempts']:
            seat=at['scope']['seat'];other='B' if seat=='A' else 'A';prior=[] if seat=='A' else [actions['A']]
            expected=payload(m,seat,[observation(m,seat,prior[:i]) for i in range(len(prior)+1)])
            wire=json.loads(at['request']['raw']);self.assertEqual(json.loads(wire['messages'][1]['content']),expected)
            altered=copy.deepcopy(m);altered['task']['body']['seats'][other]['private']={'counterfactual':'unseen'}
            alt=payload(altered,seat,[observation(altered,seat,prior[:i]) for i in range(len(prior)+1)])
            self.assertEqual(alt,expected)
            self.assertNotIn('Synthetic channel marker.',at['request']['raw'])
            if seat=='B':self.assertNotIn('subordinate_scaffold',expected)
            checks.append({'seat':seat,'hidden_counterfactual_equal':True,'blocks':at['text_integrity']['blocks']})
        for r in data['world']:self.assertNotIn('Synthetic channel marker.',json.dumps(r))
        for r in data['memory_proofs']:self.assertNotIn('Synthetic channel marker.',r['memory']['content'])
        self.evidence.update(checks=checks,counts=report['report']['counts'],scan=scan(self.root,self.secret))

    def test_incomplete_stops_and_claim_is_not_reclaimed(self):
        u=self.pre['body']['units'][0];a=fixture_policy(get(u['card']),'own_rule')['A']
        with GatewayStub(self.root,[{'pilot':True,'model':'gpt-5.6','text':a,'reasoning':'Synthetic channel marker.','case':'missing-done'}],self.secret) as service:
            report=execute(self.root/'stopped',self.pre,self.secret,endpoint=service.endpoint,authority_root=self.root/'claims',operation_authorization=AUTH,receives=service.receives,contract=contract)
            self.assertEqual(report['counts']['sent'],1);self.assertEqual(report['counts']['not_run'],47);self.assertEqual(report['counts']['unknown'],1)
            with self.assertRaises(FileExistsError):execute(self.root/'repeat',self.pre,self.secret,endpoint=service.endpoint,authority_root=self.root/'claims',operation_authorization=AUTH,receives=service.receives,contract=contract)
        self.evidence.update(counts=report['counts'],decision=report['decision'],scan=scan(self.root,self.secret))

    def test_actual_arm_pair_prepared_full_wire_and_tamper(self):
        entries=[]
        for u in self.pre['body']['units'][:2]:
            folder=self.root/u['id'];folder.mkdir();actions=fixture_policy(get(u['card']),'own_rule')
            with GatewayStub(folder,[{'pilot':True,'model':'gpt-5.6','text':actions[s],'reasoning':'Synthetic channel marker.'} for s in ('A','B')],self.secret) as service:
                c=contract.config(u['id'],endpoint=service.endpoint,authority={'id':uuid.uuid4().hex,'root':str(folder/'authority')})
                e,result=run_unit(folder/'run',c,self.secret,receives=service.receives)
            self.assertIsNone(result['error'],result['error']);entries.append(e)
        body={'schema':contract.EVIDENCE,'preregistration':self.pre,'freeze':None,'phase_state':'local_validation',
            'entries':entries+[{'unit':u,'evidence':None,'reason':'local admission subset','episode_ms':None} for u in self.pre['body']['units'][2:]]}
        value=seal(body);report=verify(value);write_json(self.root/'pilot.json',value)
        self.assertTrue(report['valid'],report);self.assertEqual(report['report']['pair_coverage']['defined'],1)
        self.assertTrue(all(x['same_A_B_invariance_checked'] for x in report['report']['pairs'][0]['wire'] if x['seat']=='B'))
        bad=copy.deepcopy(body);bad['entries'].pop();self.assertFalse(verify(seal(bad))['valid'])
        bad=copy.deepcopy(body);bad['entries'][1]['evidence']=bad['entries'][0]['evidence'];self.assertFalse(verify(seal(bad))['valid'])
        self.evidence.update(counts=report['report']['counts'],pair=report['report']['pairs'][0],tampered_plan_and_copied_arm_rejected=True,scan=scan(self.root,self.secret))
