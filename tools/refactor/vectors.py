"""High-value deterministic vectors; old/new run in separate interpreters."""
import itertools
import json
import sys
from pathlib import Path
if len(sys.argv)>1:
    sys.path.insert(0,str(Path(sys.argv[1])/'src'))
from actio.common import canonical,digest,ContractError
from actio.verify import parse
from actio.eval_contract import seal,unseal
if len(sys.argv)>1:
    from actio.suite_tasks import cards,card,options,result,observation,payload
    from actio.suite_oracle import evaluate
    from actio.task_diagnostic_data import dataset,visible
    from actio.task_diagnostic_policy import control
    from actio.candidate_contract import baseline,candidate,validate_artifact
else:
    from actio.tasks.finite import cards,card,options,result,observation,payload
    from actio.measurement.oracle import evaluate
    from actio.tasks.diagnostic import dataset,visible
    from actio.tasks.controls import control
    from actio.domain.candidate import baseline,candidate,validate_artifact
from actio.failure_fixtures import portable_vectors,mutate
from actio.failure_observation import observe
from actio.budget import totals

rows=[]
for value in [None,False,True,0,-9007199254740991,9007199254740991,[],{},'中文',{'\U00010000':1,'\ue000':2},['x',{'b':1,'a':2}]]:
    rows.append(['canonical',canonical(value),digest(value),seal(value),unseal(seal(value))])
for value in [1.0,float('nan'),float('inf'),9007199254740992,{'x':(1,)},{1:'bad'},'\ud800']:
    try:canonical(value);raise AssertionError('bad canonical accepted')
    except (ContractError,UnicodeError) as e:rows.append(['rejection',type(e).__name__,str(e)])
for raw in ['{"x":1,"x":2}','{"x":NaN}','{"x":Infinity}']:
    try:parse(raw);raise AssertionError('bad JSON accepted')
    except ContractError as e:rows.append(['parse rejection',type(e).__name__,str(e)])
bindings={s:{'agent':'ACTOR_'+s,'spec_hash':'0'*64} for s in ('A','B')}
for c in cards():
    t=card(c['id'],bindings,'tokenkey_suite_rehearsal')
    m={'task':t,'entities':{s:'ACTOR_'+s for s in ('A','B')},'memory':{'ACTOR_'+s:{'items':[],'as_of':0} for s in ('A','B')}}
    for a,b in itertools.product(options(c,'A')+['INVALID',options(c,'A')[0]+' trailing',None],options(c,'B')+['INVALID',None]):
        acts=[] if a is None else [a] if b is None else [a,b]
        rows.append(['world',c['id'],a,b,result(t['body'],acts),evaluate(c,{'A':a,'B':b})])
    for seat,prior in [('A',[]),('B',[options(c,'A')[0]])]:
        obs=observation(m,seat,prior);rows.append(['view',c['id'],seat,obs,payload(m,seat,[obs])])
for c in dataset()['body']['cards']:
    a=control(visible(c,'A'),'conditional_argmax_first');b=control(visible(c,'B',[a]),'conditional_argmax_first')
    rows.append(['diagnostic',c,visible(c,'A'),visible(c,'B',[a]),a,b])
rows.append(['candidates',baseline(),candidate()])
for v in portable_vectors():
    rows.append(['failure',v['id'],observe(v['input'])])
    try:observe(mutate(v['input'],lambda b:b['identity'].update(attempt='forged')));raise AssertionError('tamper accepted')
    except ContractError as e:rows.append(['tamper',v['id'],type(e).__name__,str(e)])
for state in ('authorized','reserved','sending','settled','unknown','released','denied'):
    rows.append(['accounting',state,totals([{'state':state,'reservation':{'calls':1,'input_tokens':None,'output_tokens':512,'cost_minor':None},'usage':{'calls':1,'input_tokens':3,'output_tokens':4,'cost_minor':None}}])])
print(canonical({'count':len(rows),'sha256':digest(rows),'rows':rows}))
