"""Scheduling TaskSpec v1 and pure semantics shared by runtime, seal and offline readers."""
import json
import re

from .common import ContractError,canonical,digest

CONTRACT='scheduling-input.v1'
SCHEMA='actio-task.v1'
FAMILY='adult-neighbors-scheduling.v1'
RULE='common-slot-accept.v1'
VISIBILITY={'actor':'public scenario + own private constraints/goals + prior public actions',
            'judge':'public scenario + both goals/constraints + initial relationships + actual actions',
            'memory':'own social namespace at frozen revision; not shared with judge'}
RUBRIC={'schema':'scheduling-rubric.v1','calibration':'NOT_CALIBRATED',
        'goal':{'range':[0,10],'anchors':{'0':'No progress toward own frozen scheduling goal.',
                '5':'Engaged with the actual proposal but no compatible agreement.',
                '10':'Compatible agreement fulfills own frozen goal and constraints.'},
                'context':['own goal','both availability sets','actual ordered actions']},
        'relationship':{'range':[-5,5],'anchors':{'-5':'Clear severe damage relative to initial relationship.',
                '0':'No supported change; minimal protocol behavior alone does not prove improvement.',
                '5':'Clear substantial improvement supported by interaction.'},
                'context':['initial relationship','public background','actual ordered actions'],
                'cannot_judge':'Two symbolic actions may provide insufficient relational evidence.'}}


def require(ok,reason):
    if not ok:raise ContractError(reason)


def sealed(body):return {'body':json.loads(canonical(body)),'sha256':digest(body)}


def action_spec(seat):
    return {'call_to_action':'Propose one cleanup time.' if seat=='A' else 'Respond to the public proposal.',
            'output_type':'choice','options':['propose:morning','propose:afternoon'] if seat=='A' else ['accept','decline'],'tag':None}


def task_card(variant,bindings,mode='fixture'):
    require(variant in ('compatible','conflict'),'unknown scheduling card')
    require(mode in ('fixture','transport_stub'),'unknown task execution mode')
    return sealed({'schema':SCHEMA,'version':1,'id':'cleanup-'+variant,'family':FAMILY,'variant':variant,
        'provenance':{'kind':'Actio_authored_synthetic_fixture','license':'CC0-1.0','upstream_dataset':None},
        'public':{'scenario':'Two adult neighbors arrange a one-hour shared park cleanup. A proposes a time; B responds.',
                  'slots':['morning','afternoon'],'background':'New neighbors coordinating for the first time.'},
        'seats':{s:{**bindings[s],'role':'proposer' if s=='A' else 'responder',
                    'private':{'available':['morning'] if s=='A' or variant=='compatible' else ['afternoon'],
                               'preferred':'morning' if s=='A' or variant=='compatible' else 'afternoon',
                               'goal':'Agree to a cleanup time within my availability.'}} for s in ('A','B')},
        'relationships':{'A':'know_by_name; neutral; no prior joint activity.','B':'know_by_name; neutral; no prior joint activity.'},
        'action_specs':{s:action_spec(s) for s in ('A','B')},'order':['A','B'],'max_steps':2,'seed':0,
        'termination':'two legal actions or first illegal action; infrastructure interruption stays partial',
        'result_rule':RULE,'visibility':VISIBILITY,'mode':mode,
        'grouping':{'version':'family-group.v1','group':'development','arm':'baseline','independent_units':0}})


def validate_task(value):
    require(type(value) is dict and set(value)=={'body','sha256'},'sealed TaskSpec required')
    t=value['body'];require(digest(t)==value['sha256'],'TaskSpec hash mismatch')
    try:
        bindings={s:{k:t['seats'][s][k] for k in ('agent','spec_hash')} for s in ('A','B')}
        require(all(type(v['agent']) is str and re.fullmatch('[A-Za-z0-9_-]{1,64}',v['agent']) and
                    type(v['spec_hash']) is str and re.fullmatch('[0-9a-f]{64}',v['spec_hash']) for v in bindings.values()),'invalid task identity/spec binding')
        require(bindings['A']['agent']!=bindings['B']['agent'],'two distinct task identities required')
        require(value==task_card(t['variant'],bindings,t['mode']),'unsupported or incomplete TaskSpec fields')
    except (KeyError,TypeError,AttributeError) as e:raise ContractError('missing or malformed TaskSpec fields') from e
    return t


def task_result(t,actions):
    legal=all(a in t['action_specs'][s]['options'] for s,a in zip(t['order'],actions))
    if not legal:return {'rule':RULE,'status':'illegal_action','agreed_slot':None,'complete':True}
    if len(actions)!=2:return {'rule':RULE,'status':'incomplete','agreed_slot':None,'complete':False}
    slot=actions[0].removeprefix('propose:')
    agreed=actions[1]=='accept' and all(slot in t['seats'][s]['private']['available'] for s in t['order'])
    return {'rule':RULE,'status':'agreed' if agreed else 'not_agreed','agreed_slot':slot if agreed else None,'complete':True}


def actor_observation(m,seat,public_actions):
    t=m['task']['body']
    return canonical({**({'role':t['seats'][seat]['role']} if m.get('execution_mode')=='transport_stub' else {}),
        'schema':'scheduling-observation.v2' if m.get('execution_mode')=='transport_stub' else 'scheduling-observation.v1','task_hash':m['task']['sha256'],'seat':seat,
        'public':t['public'],'own':t['seats'][seat]['private'],'initial_relationship':t['relationships'][seat],
        'public_actions':[{'seat':t['order'][i],'action':a} for i,a in enumerate(public_actions)]})


def validate_manifest(m):
    if m.get('input_contract')=='scheduling-transport.v1':
        from .transport_contract import validate_manifest as transport_manifest
        return transport_manifest(m)
    t=validate_task(m['task']);require(m['input_contract']==CONTRACT and m['scenario']=='social','task input contract mismatch')
    require(t['mode']=='fixture','fixture input requires fixture card')
    entities={s:t['seats'][s]['agent'] for s in t['order']};agents={v['agent']:v['spec_hash'] for v in t['seats'].values()}
    require(m['entities']==entities and m['agents']==agents and set(m['memory'])==set(agents),'manifest task seat/spec/memory mismatch')
    require(m['engine']=='concordia.Sequential' and m['source']=='b71d202750e23444ce1bf28d9f114bcd88aa41db','task engine pin')
    require(m['order']==t['order'] and m['max_steps']==2 and m['seed']==0 and m['world']==[],'task scheduling rule')
    require(m['fixture']=='scheduling-script.v1' and set(m['scripted_actions'])=={'A','B'} and
            all(type(v) is str and 0<len(v)<=64 for v in m['scripted_actions'].values()),'fixture script must be separate and bounded')
    r=m['request']
    require(r=={'scenario':'social','task_hash':m['task']['sha256'],'a':entities['A'],'b':entities['B'],
                'script_hash':digest(m['scripted_actions']),'replay':m['replay_of']},'task request binding mismatch')
    require(m['observation_policy']=='scheduling-own-plus-public.v1' and m['gm_private']=='SCHEDULING_GM_PRIVATE_AUDIT_ONLY','task observation policy')
    for a,snapshot in m['memory'].items():
        require(snapshot['namespace']=={'agent':a,'project':'synthetic','branch':'main','visibility':'private','environment':'social'} and
                snapshot['target']=='social','task memory scope')
    return t


def validate_inputs(m,streams,operations,audit):
    t=validate_manifest(m);by_stream={s['id']:s for s in streams};ops={o['id']:o for o in operations}
    rows=sorted((a for a in audit if a['kind']=='dispatch_intent'),key=lambda a:a['id'])
    require(len(rows)<=2 and len(rows)==len(ops) and {r['op'] for r in rows}==set(ops),'task dispatch order incomplete')
    prior=[]
    for step,row in enumerate(rows):
        seat=t['order'][step];agent=m['entities'][seat];op=ops[row['op']]
        require(by_stream[op['stream']]['agent']==agent,'task dispatch seat/order mismatch')
        observations=[actor_observation(m,seat,prior[:i]) for i in range(step+1)]
        expected={'answer':m['scripted_actions'][seat],'observations':observations,
                  'memory':m['memory'][agent],'action_spec':t['action_specs'][seat]}
        require(json.loads(row['body'])==expected,'task dispatch frozen view/ActionSpec mismatch')
        prior.append(op['answer'])


def resolved_text(t,actions):return canonical({'public_actions':actions,'task_result':task_result(t,actions)})


def terminal_details(m,ordered,by_receipt,world,audit,by_stream,outcome):
    t=validate_manifest(m);actions=[];world_index=0
    require(1<=len(ordered)<=2,'task action count')
    for step,op in enumerate(ordered):
        seat=t['order'][step];a=op['answer'];r=by_receipt[op['id']];b=json.loads(r['body'])
        require(by_stream[op['stream']]['agent']==m['entities'][seat],'task terminal role mismatch')
        legal=a in t['action_specs'][seat]['options'];actions.append(a)
        resolutions=[json.loads(row['body']) for row in audit if row['kind']=='gm_resolve' and row['op']==op['id']]
        if not legal:
            require(step==len(ordered)-1 and r['outcome']=='task_failure' and b=={'rejected':'illegal_action','world_unchanged':True} and not resolutions,'illegal task action effects')
            break
        require(world_index<len(world),'task world missing');w=sorted(world,key=lambda w:w['step'])[world_index];world_index+=1
        expected=resolved_text(t,actions);putative=f'[putative_event] {seat}: {a}'
        require(w['step']==step and w['agent']==m['entities'][seat] and w['intent']==a and w['resolved']=='[event] '+expected and
                (w['stream'],w['seq'])==(r['stream'],r['seq']),'task world result/source mismatch')
        require(b=={'resolved':w['resolved'],'producer':'GM.observe(EVENT)','putative':putative,'task_result':task_result(t,actions)} and
                r['outcome']==('task_failure' if task_result(t,actions)['status']=='not_agreed' else 'success'),'task domain result mismatch')
        require(resolutions==[{'intent':putative,'resolved':expected,'source':'GM.act(RESOLVE)'}],'task GM result mismatch')
    result=task_result(t,actions)
    require(world_index==len(world) and result['complete'] and outcome==('success' if result['status']=='agreed' else 'task_failure'),'task outcome/incomplete mismatch')
    return {'task_hash':m['task']['sha256'],'result':result,'reason':result['status'],'owner':'concordia.scheduling.owner.v1'}
