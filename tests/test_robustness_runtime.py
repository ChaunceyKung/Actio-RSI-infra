import json
from pathlib import Path
import unittest
import uuid
from unittest.mock import patch
from actio.profiles import robustness_campaign as c
from actio.interfaces.robustness import verify
from actio.tasks.robustness import get
from actio.tasks.diagnostic import visible
from actio.tasks.controls import control
from actio.interfaces.pilot import execute
from actio.interfaces.pilot import run_unit
from actio.common import write_json
from actio.evidence.eval_contract import seal
from gateway_stub import GatewayStub
from test_robustness import empty


class RobustnessRuntime(unittest.TestCase):
    def setUp(self):
        self.root=Path('D:/actio-c2c4-tests')/uuid.uuid4().hex[:12];self.root.mkdir(parents=True)
        self.evidence={'root':str(self.root),'external_provider_requests':0}
        self.secret='ACTIO_FAKE_'+uuid.uuid4().hex;self.pre=c.preregistration()

    def test_01_behavior_errors_and_actual_own_arm_history(self):
        b=empty(self.pre)['body'];cases=[];plans=[]
        for i,u in enumerate(self.pre['body']['units'][:6]):
            card=get(u['card']);a=control(visible(card,'A'),'conditional_argmax_first')
            if i<2:a=visible(card,'A')['action_spec']['options'][i]
            if i==2:a='INVALID-A'
            ans=None if i==2 else control(visible(card,'B',[a]),'conditional_argmax_first')
            if i==3:ans='INVALID-B'
            if i==4:ans='accept' if ans!='accept' else ('decline' if card['family']=='scheduling' else 'reject')
            cases.append({'unit':u['id'],'A':a,'B':ans,'fixture_only':True})
            plans.extend({'pilot':True,'model':'gpt-5.6','text':text,'reasoning':'Synthetic channel marker.'} for text in (a,ans) if text is not None)
        write_json(self.root/'cases.json',cases)
        with GatewayStub(self.root,plans,self.secret) as service:
            for i,u in enumerate(self.pre['body']['units'][:6]):
                cfg=c.config(u['id'],mode=c.REHEARSAL,endpoint=service.endpoint,authority={'id':uuid.uuid4().hex,'root':str(self.root/'claims')})
                entry,result=run_unit(self.root/u['id'],cfg,self.secret,receives=service.receives)
                b['entries'][i]=entry
                self.assertIsNone(result['error'],result['error'])
        campaign=seal(b);write_json(self.root/'pilot.json',campaign);result=verify(campaign);write_json(self.root/'check.json',result)
        self.assertTrue(result['valid'],result)
        r=result['report'];self.assertEqual(r['counts']['sent'],11);self.assertEqual(r['counts']['task_predecessor_invalid'],1)
        self.assertEqual(r['counts']['execution_resolved_episodes'],6)
        self.assertTrue(any(w['different_A_history_checked'] for p in r['pairs'] for w in p['wire']))
        self.assertFalse(r['rows'][4]['metric_cells']['b_response_rule']['value'])
        self.evidence.update(counts=r['counts'],cases=cases,behavior_continued=True)

    def test_02_unknown_stops_suffix_duplicate_execute_denied(self):
        plans=c.fixture_plans()[:1];plans[0]['case']='missing-done'
        with GatewayStub(self.root,plans,self.secret) as service:
            r=execute(self.root/'matrix',self.pre,self.secret,endpoint=service.endpoint,receives=service.receives,
                      authority_root=self.root/'claims',operation_authorization=c.AUTH,contract=c)
            with self.assertRaises(FileExistsError):
                execute(self.root/'second-root',self.pre,self.secret,endpoint=service.endpoint,receives=service.receives,
                        authority_root=self.root/'claims',operation_authorization=c.AUTH,contract=c)
        self.assertEqual((r['counts']['sent'],r['counts']['unknown'],r['counts']['not_run']),(1,1,127))
        self.assertEqual(r['candidate_decision'],'infrastructure_failure')
        self.evidence.update(counts=r['counts'],duplicate_rejected=True)

    def test_03_headers_timeout_and_cleanup(self):
        plans=c.fixture_plans()[:1];plans[0]['case']='no-first'
        with GatewayStub(self.root,plans,self.secret) as service:
            r=execute(self.root/'matrix',self.pre,self.secret,endpoint=service.endpoint,receives=service.receives,
                      authority_root=self.root/'claims',operation_authorization=c.AUTH,contract=c)
        self.assertEqual((r['counts']['sent'],r['counts']['unknown'],r['counts']['not_run']),(1,1,127))
        self.assertEqual(r['candidate_decision'],'infrastructure_failure')
        self.evidence.update(counts=r['counts'],deadline='actual frozen headers60; no extended total',joined=not service.thread.is_alive())

    def test_04_controller_and_verifier_failure_preserve_inventory(self):
        with patch('actio.application.pilot.run_unit',side_effect=RuntimeError('controlled pre-send failure')),patch('actio.evidence.robustness_measurement.analyze_pilot',side_effect=ValueError('controlled verifier failure')):
            r=execute(self.root/'matrix',self.pre,self.secret,endpoint='http://127.0.0.1:18080/v1',authority_root=self.root/'claims',operation_authorization=c.AUTH,contract=c)
        self.assertFalse(r['valid'])
        for name in ('pilot.json','raw-attempt-inventory.json','controller-failure.json','verification-failure.json','credential-scan.json'):
            self.assertTrue((self.root/'matrix'/name).exists())
        self.assertEqual(len(json.loads((self.root/'matrix/raw-attempt-inventory.json').read_bytes())['full_unrun_suffix']),64)
        self.evidence.update(sent=0,retained_failure=True,complete_suffix=64)

    def test_05_equal_hidden_world_A_wire_allows_different_output(self):
        units=[u for u in self.pre['body']['units'] if u['structural_group']=='S-hidden' and u['presentation']=='normal' and u['arm']=='candidate']
        units.sort(key=lambda u:u['world']);b=empty(self.pre)['body'];plans=[]
        for u,action in zip(units,['propose:morning','propose:afternoon']):
            answer=control(visible(get(u['card']),'B',[action]),'conditional_argmax_first')
            plans.extend({'pilot':True,'model':'gpt-5.6','text':text,'reasoning':'Synthetic channel marker.'} for text in (action,answer))
        with GatewayStub(self.root,plans,self.secret) as service:
            for u in units:
                cfg=c.config(u['id'],mode=c.REHEARSAL,endpoint=service.endpoint,authority={'id':uuid.uuid4().hex,'root':str(self.root/'claims')})
                entry,result=run_unit(self.root/u['id'],cfg,self.secret,receives=service.receives)
                self.assertIsNone(result['error'],result['error']);b['entries'][u['order']]=entry
        campaign=seal(b);write_json(self.root/'pilot.json',campaign);result=verify(campaign);write_json(self.root/'check.json',result)
        self.assertTrue(result['valid'],result)
        row=next(r for r in result['report']['comparisons']['hidden_world']['rows'] if r['left']==units[0]['id'])
        self.assertFalse(row['actions_equal']['A']['value'])
        self.assertTrue(next(w for w in row['wire_checks'] if w['seat']=='A')['full_normalized_input_equal'])
        self.evidence.update(counts=result['report']['counts'],comparison=row,equal_input_different_output_accepted=True)
