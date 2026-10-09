import json
from pathlib import Path
import unittest
import uuid
from unittest.mock import patch
from actio import evaluation_campaign as c
from actio.common import write_json
from actio.pilot import execute,run_unit
from actio.candidate_evaluation import prepare_store,finalize,verify
from actio.suite_tasks import get
from actio.suite_oracle import fixture_policy
from actio.eval_contract import seal
from gateway_stub import GatewayStub
from test_evaluation_candidate import SOURCE,empty


class EvaluationRuntime(unittest.TestCase):
    def setUp(self):
        self.root=Path('D:/actio-c2c2-tests')/uuid.uuid4().hex[:12];self.root.mkdir(parents=True)
        self.evidence={'root':str(self.root),'external_provider_requests':0}
        self.secret='ACTIO_FAKE_'+uuid.uuid4().hex;self.pre=c.preregistration()

    def test_01_new_mode_dual_channel_smoke_local_only(self):
        u=self.pre['body']['units'][0];actions=fixture_policy(get(u['card']),'own_rule')
        with GatewayStub(self.root,[{'pilot':True,'model':'gpt-5.6','text':actions[s],'reasoning':'Synthetic channel marker.'} for s in ('A','B')],self.secret) as service:
            cfg=c.config(u['id'],mode=c.REHEARSAL,endpoint=service.endpoint,authority={'id':uuid.uuid4().hex,'root':str(self.root/'claims')})
            e,result=run_unit(self.root/'run',cfg,self.secret,receives=service.receives)
        self.assertIsNone(result['error'],result['error'])
        b=empty(self.pre)['body'];b['entries'][0]=e;check=verify(seal(b));write_json(self.root/'check.json',check)
        self.assertTrue(check['valid'],check);self.assertTrue(check['report']['rows'][0]['execution_resolved'])
        self.evidence['counts']=check['report']['counts']

    def test_02_complete_rehearsal_behavior_and_dynamic_history(self):
        plans=[];fixtures=[]
        for u in self.pre['body']['units']:
            actions=fixture_policy(get(u['card']),'own_rule');case='own_rule'
            if u['card']=='S2':actions={'A':'propose:morning' if u['arm']=='baseline' else 'propose:evening','B':'accept'};case='different_A'
            if u['arm']=='candidate':
                overrides={'S1':({'A':'INVALID-A','B':None},'invalid_A'),
                    'H1':({'A':actions['A'],'B':'INVALID-B'},'invalid_B'),
                    'S3':({'A':'propose:morning','B':'decline'},'legal_refusal'),
                    'S4':({'A':'propose:morning','B':'accept'},'public_hard_violation'),
                    'H4':({'A':'apple for 3 coins','B':'accept'},'zero_utility'),
                    'H5':({'A':'apple for 1 coins','B':'reject'},'infeasible_refusal')}
                if u['card'] in overrides:actions,case=overrides[u['card']]
            fixtures.append({'unit':u['id'],'case':case,'actions':actions,'scope':'synthetic admission only'})
            plans.extend({'pilot':True,'model':'gpt-5.6','text':actions[s],'reasoning':'Synthetic channel marker.'} for s in ('A','B') if actions[s] is not None)
        write_json(self.root/'synthetic-cases.json',fixtures)
        eid=prepare_store(self.root,self.pre,SOURCE,'local_fixture')
        with GatewayStub(self.root,plans,self.secret) as service:
            report=execute(self.root/'matrix',self.pre,self.secret,endpoint=service.endpoint,authority_root=self.root/'claims',
                operation_authorization=c.AUTH,receives=service.receives,contract=c)
        self.assertEqual(report['engineering'],'PASS',report.get('reason'));self.assertEqual(report['candidate_decision'],'reject')
        self.assertEqual(report['counts']['execution_resolved_episodes'],24);self.assertEqual(report['counts']['sent'],47)
        self.assertEqual(report['counts']['unknown'],0);self.assertEqual(report['counts']['task_predecessor_invalid'],1)
        self.assertEqual(report['metric_pair_coverage']['joint']['not_applicable'],2)
        self.assertEqual(report['pair_coverage']['defined'],12)
        self.assertTrue(any(x['different_A_history_checked'] for p in report['pairs'] for x in p['wire']))
        self.assertTrue(any(x['same_A_B_invariance_checked'] for p in report['pairs'] for x in p['wire']))
        result=finalize(self.root,eid,report);self.evidence.update(result=result,counts=report['counts'],fixtures=fixtures)

    def test_03_unknown_stops_suffix_and_claim(self):
        u=self.pre['body']['units'][0];a=fixture_policy(get(u['card']),'own_rule')['A']
        with GatewayStub(self.root,[{'pilot':True,'model':'gpt-5.6','text':a,'reasoning':'Synthetic channel marker.','case':'missing-done'}],self.secret) as service:
            report=execute(self.root/'stopped',self.pre,self.secret,endpoint=service.endpoint,authority_root=self.root/'claims',operation_authorization=c.AUTH,receives=service.receives,contract=c)
            self.assertEqual(report['counts']['sent'],1);self.assertEqual(report['counts']['not_run'],47);self.assertEqual(report['counts']['unknown'],1)
            with self.assertRaises(FileExistsError):execute(self.root/'again',self.pre,self.secret,endpoint=service.endpoint,authority_root=self.root/'claims',operation_authorization=c.AUTH,receives=service.receives,contract=c)
        self.evidence.update(counts=report['counts'],state=report['candidate_decision'])

    def test_04_controller_failure_keeps_inventory_when_verifier_fails(self):
        with patch('actio.pilot.run_unit',side_effect=RuntimeError('controlled pre-send controller failure')),patch.object(c,'analyze',side_effect=ValueError('controlled verifier failure')):
            r=execute(self.root/'stopped',self.pre,self.secret,endpoint='http://127.0.0.1:1/v1',authority_root=self.root/'claims',operation_authorization=c.AUTH,contract=c)
        self.assertFalse(r['valid'])
        for name in ('pilot.json','raw-attempt-inventory.json','controller-failure.json','verification-failure.json','credential-scan.json'):self.assertTrue((self.root/'stopped'/name).is_file())
        self.assertEqual(len(json.loads((self.root/'stopped/raw-attempt-inventory.json').read_bytes())['full_unrun_suffix']),24)
        self.evidence.update(raw_preserved=True,verification_failure=True,sent=0)
