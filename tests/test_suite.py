import copy
import itertools
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
from actio.common import canonical, ContractError, file_hash
from actio.eval_contract import seal
from actio import suite_contract as contract
from actio.tasks.finite import cards,card,options,result,observation,payload
from actio.measurement.oracle import evaluate,fixture_policy
from actio.suite_measurement import metrics,aggregate,verify,correct_c2b2

ROOT=Path(__file__).resolve().parents[1]
BINDINGS={s:{'agent':'ACTOR_'+s,'spec_hash':'0'*64} for s in ('A','B')}

def empty():
    pre=contract.preregistration()
    return {'schema':contract.EVIDENCE,'preregistration':pre,'freeze':None,'phase_state':'local_validation',
        'entries':[{'unit':u,'evidence':None,'reason':'offline nonexecution','episode_ms':None} for u in pre['body']['units']]}

GUARD="""import sys,os,json
def audit(e,a):
 if e.startswith('socket.') or e=='subprocess.Popen':raise RuntimeError('network/process denied')
 if e=='import' and (a[0].split('.')[0] in ('deepseek_harness','concordia') or a[0] in ('actio.runtime','actio.transport','actio.gateway','actio.eval_worker')):raise RuntimeError('runtime denied')
 if e=='open':
  if 'token_key' in str(a[0]):raise RuntimeError('credential denied')
  if isinstance(a[1],str) and any(c in a[1] for c in 'wax+') or isinstance(a[2],int) and a[2]&(1|2|64|512|1024):raise RuntimeError('write denied')
sys.addaudithook(audit)
class NoEnv(dict):
 def get(self,*a):raise RuntimeError('env denied')
 def __getitem__(self,*a):raise RuntimeError('env denied')
os.environ=NoEnv()
"""

class SuitePure(unittest.TestCase):
    def test_01_exhaustive_independent_truth_and_sensitivity(self):
        truth=[];sensitivity={}
        for c in cards():
            t=card(c['id'],BINDINGS,contract.REHEARSAL)['body'];valid=[]
            for a,b in itertools.product(options(c,'A')+['INVALID',options(c,'A')[0]+' trailing',None],options(c,'B')+['INVALID',None]):
                with patch('actio.tasks.finite.result',side_effect=AssertionError('production oracle forbidden')):
                    m=evaluate(c,{'A':a,'B':b})
                acts=[] if a is None else [a] if b is None else [a,b]
                prod=result(t,acts)
                self.assertEqual(prod['utilities'],m['utilities'])
                if all(m['format'].values()):
                    self.assertEqual(prod['status']=='agreed',m['joint_achieved'])
                    self.assertEqual(prod['hard'],{'A':m['a_own'],'B':m['b_local']});valid.append(m)
                truth.append({'card':c['id'],'A':a,'B':b,'oracle':m,'production':prod})
            sensitivity[c['id']]={'hard_violation':any(v['a_own'] is False or v['b_local'] is False for v in valid),
                'correct_accept':any(v['b_local'] and v['joint_achieved'] for v in valid),
                'correct_response_cases':sum(v['b_local'] for v in valid),
                'feasible':evaluate(c,{})['joint_feasible']}
        for family in ('scheduling','bargaining'):
            fc=[c for c in cards() if c['family']==family];rows=[t for t in truth if t['card'] in {c['id'] for c in fc}]
            self.assertTrue(any(x['oracle']['a_own'] is False for x in rows))
            self.assertTrue(any(x['B']=='accept' and x['oracle']['b_local'] is True for x in rows))
            self.assertTrue(any(x['B'] in ('decline','reject') and x['oracle']['b_local'] is True for x in rows))
            self.assertTrue(any(len({canonical(x['oracle']['utilities']) for x in rows if x['card']==c['id'] and x['oracle']['a_own'] and x['oracle']['b_local'] and x['oracle']['joint_achieved']})>1 for c in fc))
        controls=[{'card':c['id'],'policy':p,'actions':fixture_policy(c,p),'metrics':evaluate(c,fixture_policy(c,p))} for c in cards() for p in ('first_option','always_accept','always_reject','own_rule')]
        self.evidence={'truth_table':truth,'sensitivity':sensitivity,'controls':controls,'human_labels':0,'oracle_independence':'distinct formulas and code path; not human calibration'}

    def test_02_hand_computable_boundary_vectors(self):
        lookup={c['id']:c for c in cards()}
        vectors=[('H4','apple for 3 coins','accept',True,{'A':0,'B':0}),
          ('H1','apple for 3 coins','accept',True,{'A':2,'B':1}),
          ('H1','banana for 3 coins','reject',False,{'A':0,'B':0}),
          ('H6','apple for 5 coins','accept',False,{'A':0,'B':0}),
          ('S4','propose:morning','accept',False,{'A':0,'B':0}),
          ('S6','propose:morning','accept',True,{'A':5,'B':1}),
          ('S6','propose:afternoon','accept',True,{'A':4,'B':5})]
        for cid,a,b,j,u in vectors:
            m=evaluate(lookup[cid],{'A':a,'B':b});self.assertEqual((m['joint_achieved'],m['utilities']),(j,u))
        for a in ('pear for 2 coins','apple for 0 coins','apple for 6 coins','apple for 2 coins extra'):
            m=evaluate(lookup['H1'],{'A':a,'B':'accept'});self.assertFalse(m['format']['A']);self.assertIsNone(m['utilities'])
        self.evidence={'hand_vectors':vectors,'labels':'authored test oracle, no human behavioral labels'}

    def test_03_full_plan_and_tamper_rejection(self):
        b=empty();r=verify(seal(b));self.assertTrue(r['valid'],r);rep=r['report'];self.assertEqual(rep['counts']['not_run'],48)
        for s in rep['strata']:
            self.assertEqual(s['joint']['assigned'],6);self.assertEqual(s['joint']['missing'],6)
            self.assertEqual(sum(x['assigned'] for x in s['joint_by_feasibility']),6)
        self.assertEqual(rep['pair_coverage']['missing'],12)
        for fn in (lambda v:v['entries'].pop(),lambda v:v['entries'].append(v['entries'][0]),
          lambda v:v['entries'][0]['unit'].update(model='other'),lambda v:v['preregistration']['body'].update(task_version='actio-task.v2')):
            bad=copy.deepcopy(b);fn(bad);self.assertFalse(verify(seal(bad))['valid'])
        for field,value in [('spending_policy','uncapped_for_phase1c2b2'),('timeouts',{'idle':300}),('cost_limit_minor',0)]:
            c=contract.config('ep-00');c[field]=value
            with self.assertRaises(ContractError):contract.validate(c)

    def test_04_layered_missing_invalid_and_task_failure(self):
        c=cards()[0]
        cases=[({},'not_started'),({'A':'propose:afternoon'},'infrastructure_unknown'),({'A':'INVALID'},'not_run'),
               ({'A':'propose:morning','B':'decline'},'none'),({'A':'propose:afternoon','B':'bad'},'none')]
        for actions,reason in cases:
            m,cs=metrics(c,actions,{'A':reason,'B':reason})
            for k in ('a_own','b_local','joint'):
                r=aggregate([cs[k]],'episode');self.assertEqual(r['assigned'],r['eligible']+r['not_applicable']);self.assertEqual(r['defined'],r['true']+r['false'])
            if actions.get('A')=='INVALID':self.assertEqual(cs['format']['A']['value'],False);self.assertEqual(cs['b_local']['state'],'not_applicable')
            if actions.get('B')=='decline':self.assertEqual(cs['joint']['value'],False);self.assertTrue(cs['b_local']['value']);self.assertEqual(m['utilities'],{'A':0,'B':0})
            if not actions:self.assertEqual(cs['joint']['state'],'missing')

    def test_05_counterfactual_all_visible_fields(self):
        for c in cards():
            m={'task':card(c['id'],BINDINGS,contract.REHEARSAL),'entities':{'A':'ACTOR_A','B':'ACTOR_B'},'memory':{n:{'items':[],'as_of':0} for n in ('ACTOR_A','ACTOR_B')}}
            def visible(v,s,acts):return canonical(payload(v,s,[observation(v,s,acts)]))
            for seat,other,acts in [('A','B',[]),('B','A',[options(c,'A')[0]])]:
                baseline=visible(m,seat,acts);v=copy.deepcopy(m);t=v['task']['body'];t['seats'][other]['private']={'changed':True};t['seats'][other]['spec_hash']='f'*64;t['grouping']={'secret':'hidden'};v['task']=seal(t)
                self.assertEqual(visible(v,seat,acts),baseline)
                v['task']['body']['seats'][seat]['private']={'changed':True};self.assertNotEqual(visible(v,seat,acts),baseline)
                self.assertNotIn('hash',baseline);self.assertNotIn('ACTOR_',baseline)
            self.assertNotEqual(visible(m,'B',[options(c,'A')[0]]),visible(m,'B',[options(c,'A')[1]]))

    def test_06_historical_correction_from_full_plan(self):
        folder=ROOT/'docs/validation/phase1c2b2';pre=json.loads((folder/'preregistration.json').read_bytes());report=json.loads((folder/'samples/report.json').read_bytes())
        rows=correct_c2b2(pre,report)
        self.assertEqual([(r['assigned'],r['defined'],r['missing']) for r in rows],[(8,7,1),(8,6,2),(8,7,1),(8,6,2)])
        for row in report['rows']:row['metrics']=None
        self.assertEqual([r['missing'] for r in correct_c2b2(pre,report)],[8]*4)
        self.evidence={'correction':rows,'source_hashes':{str(p.relative_to(ROOT)):file_hash(p) for p in (folder/'preregistration.json',folder/'samples/report.json')}}

    def test_07_readonly_plan_no_environment(self):
        code=GUARD+"\nfrom actio.suite_contract import plan\nfrom actio.suite_measurement import verify\nfrom actio.eval_contract import seal\np=plan()['preregistration']\nr=verify(seal({'schema':'suite-evidence.v1','preregistration':p,'freeze':None,'phase_state':'local_validation','entries':[{'unit':u,'evidence':None,'reason':'local','episode_ms':None} for u in p['body']['units']]}))\nassert r['valid'],r\nprint('PASS')"
        r=subprocess.run([sys.executable,'-I','-B','-c',code],capture_output=True,text=True,timeout=30);self.assertEqual(r.returncode,0,r.stderr)

if __name__=='__main__':unittest.main()
