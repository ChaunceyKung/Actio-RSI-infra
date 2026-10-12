import base64
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
from actio.contracts.json import ContractError
from actio.contracts.json import canonical
from actio.contracts.json import digest
from actio.adapters.filesystem.common import clean_env
from actio.evidence.bundles.eval_contract import seal
from actio.profiles.pilot_contract import preregistration
from actio.profiles.pilot_contract import validate_preregistration
from actio.profiles.pilot_contract import config
from actio.profiles.pilot_contract import validate
from actio.evidence.campaigns.pilot_measurement import predicates
from actio.evidence.campaigns.pilot_measurement import verify
from actio.tasks.scheduling_v2 import cards
from actio.tasks.scheduling_v2 import card
from actio.tasks.scheduling_v2 import observation
from actio.tasks.scheduling_v2 import payload
from actio.evidence.audit.stream_audit import audit
from actio.evidence.audit.stream_audit import verdict

ROOT=Path(__file__).resolve().parents[1]
BINDINGS={s:{'agent':'ACTOR_'+s,'spec_hash':'0'*64} for s in ('A','B')}

def historic():
    for route in ('gpt56','claude'):
        root=ROOT/'docs/validation/phase1c2b1/samples'/route
        idx=json.loads((root/'campaign.json').read_bytes())['body']
        ledger=json.loads((root/idx['paths']['ledger']).read_bytes())['body']
        data=json.loads((root/idx['paths']['dataset']).read_bytes())['body']
        ops={o['id']:o for src in data['sources'].values() for o in json.loads(src['files']['evidence.json'])['operations']}
        for a in ledger['attempts']:yield a,ops[a['id']]['answer']


class PilotPure(unittest.TestCase):
    def test_01_historical_raw_adapter_native_and_mutations(self):
        count=0
        for a,answer in historic():
            r=copy.deepcopy(a['response']);self.assertEqual(audit(r,answer)['text'],answer);count+=1
            lines=r['raw'].splitlines(keepends=True)
            for i,line in enumerate(lines):
                if not line.startswith('data: {'):continue
                row=json.loads(line[6:]);choices=row.get('choices',[])
                if choices and choices[0].get('delta',{}).get('content'):
                    choices[0]['delta']['content']='WRONG';lines[i]='data: '+json.dumps(row)+'\n';break
            r['raw']=''.join(lines)
            self.assertEqual(verdict(r,require_bytes=False)['status'],'rejected')
        self.assertEqual(count,8);self.evidence={'historical_records':count,'historical_writes':0}

    def test_02_strict_stream_branches_and_utf8(self):
        r=copy.deepcopy(next(historic())[0]['response'])
        rows=[json.loads(x[6:]) for x in r['raw'].splitlines() if x.startswith('data: ') and x!='data: [DONE]']
        base={k:v for k,v in rows[0].items() if k not in ('choices','usage')}
        usage=next(v['usage'] for v in rows if v.get('usage'))
        valid=[{**base,'choices':[{'index':0,'delta':{'role':'assistant','content':''}}]},
               *[{**base,'choices':[{'index':0,'delta':{'content':x}}]} for x in ('早','上','')],
               {**base,'choices':[{'index':0,'delta':{},'finish_reason':'stop'}]},
               {**base,'choices':[],'usage':usage}]
        def response(events):
            raw=''.join('data: '+json.dumps(x,ensure_ascii=False)+'\n\n' for x in events)+'data: [DONE]\n\n'
            chunks=[{'type':'block-start','index':0,'blockType':'text'},
                    {'type':'text-delta','index':0,'text':'早上'},
                    {'type':'block-end','index':0,'block':{'type':'text','text':'早上'}},
                    {'type':'usage','usage':{}},{'type':'finish','reason':{'kind':'stop'}}]
            return {'status':200,'error':None,'raw':raw,'raw_base64':base64.b64encode(raw.encode()).decode(),'chunks_json':json.dumps(chunks,ensure_ascii=False)}
        good=response(valid);self.assertEqual(audit(good,'早上',require_bytes=True)['text'],'早上')
        changes=[]
        def changed(fn):
            v=copy.deepcopy(valid);fn(v);changes.append(response(v))
        changed(lambda v:v[1]['choices'].append(copy.deepcopy(v[1]['choices'][0])))
        changed(lambda v:v[1]['choices'][0].update(index=1))
        for key,val in [('content',[]),('tool_calls',[]),('refusal','no'),('reasoning_content','hidden')]:
            changed(lambda v,k=key,x=val:v[1]['choices'][0]['delta'].update({k:x}))
        changed(lambda v:v.append(v[1]))
        changed(lambda v:v.append(v[-1]))
        changed(lambda v:v.pop(-2))
        changed(lambda v:v[1].update(model='other'))
        for f in (lambda s:s.replace('"index": 0','"index": 0, "index": 0',1),
                  lambda s:s.replace('data: [DONE]','data: [DONE]\n\ndata: [DONE]'),
                  lambda s:s.replace('data: [DONE]\n\n',''),
                  lambda s:s.replace('\n\n','\ndata: {}\n\n',1),
                  lambda s:s.replace('data: {','data: {bad',1)):
            v=copy.deepcopy(good);v['raw']=f(v['raw']);v['raw_base64']=base64.b64encode(v['raw'].encode()).decode();changes.append(v)
        v=copy.deepcopy(good);v['raw_base64']=base64.b64encode(b'\xff').decode();changes.append(v)
        for v in changes:self.assertEqual(verdict(v)['status'],'rejected')
        self.evidence={'rejected_stream_variants':len(changes),'utf8_fragmented_content':True}

    def test_03_independent_finite_oracle(self):
        n=0
        # Independently enumerate predicates over raw singleton sets and protocol symbols.
        with patch('actio.tasks.scheduling.task_result',side_effect=AssertionError('GM oracle forbidden')):
            for c in cards():
                t=card(c['id'],BINDINGS,'tokenkey_pilot_rehearsal')['body']
                for a in ('propose:morning','propose:afternoon','INVALID',None):
                    for b in ('accept','decline','INVALID',None):
                        m=predicates(t,{'A':a,'B':b});legal_a=a in ('propose:morning','propose:afternoon');legal_b=b in ('accept','decline')
                        slot=a.split(':')[1] if legal_a else None
                        self.assertEqual(m['a_own'],slot==c['available']['A'][0] if legal_a else None)
                        expected=(b=='accept' if slot==c['available']['B'][0] else b=='decline') if legal_a and legal_b else None
                        self.assertEqual(m['b_local'],expected)
                        self.assertEqual(m['joint_feasible'],c['available']['A']==c['available']['B'])
                        self.assertEqual(m['joint_achieved'],b=='accept' and c['available']['A']==c['available']['B']==[slot] if legal_a and legal_b else None);n+=1
        self.evidence={'truth_table_rows':n,'gm_calls':0}

    def test_04_counterfactual_visible_whitelist(self):
        def manifest():return {'input_contract':'scheduling-tokenkey.v2','task':card(cards()[0]['id'],BINDINGS,'tokenkey_pilot_rehearsal'),'entities':{'A':'ACTOR_A','B':'ACTOR_B'},'memory':{n:{'items':[],'as_of':0,'hidden_hash':'secret'} for n in ('ACTOR_A','ACTOR_B')}}
        def body(m,s,acts):return canonical(payload(m,s,[observation(m,s,acts)]))
        for seat,other,acts in [('A','B',[]),('B','A',['propose:morning'])]:
            m=manifest();expected=body(m,seat,acts);v=copy.deepcopy(m)
            v['task']['body']['seats'][other]['private'].update(available=['afternoon'],preferred='afternoon',hidden_metadata='counterfactual')
            v['task']['body']['seats'][other]['spec_hash']='f'*64;v['task']['body']['grouping']['instance']='secret_label';v['task']=seal(v['task']['body'])
            self.assertEqual(body(v,seat,acts),expected)
            v['task']['body']['seats'][seat]['private']['available']=['afternoon'];self.assertNotEqual(body(v,seat,acts),expected)
            self.assertNotIn('hash',expected);self.assertNotIn('ACTOR_',expected);self.assertNotIn('op',json.loads(expected))
        m=manifest();self.assertNotEqual(body(m,'B',['propose:morning']),body(m,'B',['propose:afternoon']))

    def test_05_complete_plan_tampering_and_missing_denominators(self):
        pre=preregistration();self.assertEqual(len(pre['body']['units']),32)
        evidence={'schema':'pilot-evidence.v1','preregistration':pre,'freeze':None,'phase_state':'local_validation',
                  'entries':[{'unit':u,'evidence':None,'reason':'prespecified local nonexecution','episode_ms':None} for u in pre['body']['units']]}
        v=verify(seal(evidence));self.assertTrue(v['valid'],v);self.assertEqual(v['report']['counts']['not_run'],64)
        self.assertEqual(v['report']['metrics_by_route']['gpt-5.6']['format']['missing'],32)
        for fn in (lambda b:b['entries'].pop(),lambda b:b['entries'].append(b['entries'][0]),
                   lambda b:b['entries'][0]['unit'].update(model='other'),lambda b:b['preregistration']['body']['parameters'].update(max_tokens=1),
                   lambda b:b['preregistration']['body'].update(task_version='actio-task.v1')):
            b=copy.deepcopy(evidence);fn(b);self.assertFalse(verify(seal(b))['valid'])
        for field,value in [('cost_limit_minor',0),('spending_policy','uncapped_for_phase1c2b1'),('model','other')]:
            c=config('ep-00');c[field]=value
            with self.assertRaises(ContractError):validate(c)

    def test_06_plan_and_verifier_side_effect_denial(self):
        # Imports and reads are allowed; no environment, credential, network, runtime or writes.
        code='''import sys,os
def audit(e,a):
 if e.startswith('socket.') or e=='subprocess.Popen':raise RuntimeError('network/process denied')
 if e=='import' and (a[0].split('.')[0] in ('deepseek_harness','concordia') or a[0] in ('actio.adapters.runtime.runtime','actio.adapters.transport.transport','actio.application.gateway')):raise RuntimeError('runtime denied')
 if e=='open':
  if 'token_key' in str(a[0]):raise RuntimeError('credential denied')
  if isinstance(a[1],str) and any(c in a[1] for c in 'wax+') or isinstance(a[2],int) and a[2]&(1|2|64|512|1024):raise RuntimeError('write denied')
sys.addaudithook(audit)
class NoEnv(dict):
 def get(self,*a):raise RuntimeError('env denied')
 def __getitem__(self,*a):raise RuntimeError('env denied')
os.environ=NoEnv()
from actio.profiles.pilot_contract import plan
from actio.evidence.campaigns.pilot_measurement import verify
from actio.evidence.bundles.eval_contract import seal
p=plan()['preregistration']
b={'schema':'pilot-evidence.v1','preregistration':p,'freeze':None,'phase_state':'local_validation','entries':[{'unit':u,'evidence':None,'reason':'local','episode_ms':None} for u in p['body']['units']]}
assert verify(seal(b))['valid']
print('PASS')
'''
        r=subprocess.run([sys.executable,'-I','-B','-c',code],capture_output=True,text=True,timeout=30)
        self.assertEqual(r.returncode,0,r.stderr)

if __name__=='__main__':unittest.main()
