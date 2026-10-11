"""Scheduling TaskSpec v1 and pure semantics shared by runtime, seal and offline readers."""
import json
import re

from actio.contracts.json import ContractError, canonical, digest

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
    require(mode in ('fixture','transport_stub','priced_rehearsal','tokenkey_live','tokenkey_rehearsal'),'unknown task execution mode')
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
    t=value['body']
    if t.get('schema')=='actio-task.v6':
        from actio.tasks.robustness import validate
        return validate(value)
    if t.get('schema')=='actio-task.v5':
        from actio.tasks.evaluation import validate
        return validate(value)
    if t.get('schema')=='actio-task.v4':
        from actio.tasks.candidate import validate
        return validate(value)
    if t.get('schema')=='actio-task.v3':
        from actio.tasks.finite import validate
        return validate(value)
    if t.get('schema')=='actio-task.v2':
        from actio.tasks.scheduling_v2 import validate
        return validate(value)
    require(digest(t)==value['sha256'],'TaskSpec hash mismatch')
    try:
        bindings={s:{k:t['seats'][s][k] for k in ('agent','spec_hash')} for s in ('A','B')}
        require(all(type(v['agent']) is str and re.fullmatch('[A-Za-z0-9_-]{1,64}',v['agent']) and
                    type(v['spec_hash']) is str and re.fullmatch('[0-9a-f]{64}',v['spec_hash']) for v in bindings.values()),'invalid task identity/spec binding')
        require(bindings['A']['agent']!=bindings['B']['agent'],'two distinct task identities required')
        require(value==task_card(t['variant'],bindings,t['mode']),'unsupported or incomplete TaskSpec fields')
    except (KeyError,TypeError,AttributeError) as e:raise ContractError('missing or malformed TaskSpec fields') from e
    return t


def task_result(t,actions):
    if t.get('schema') in ('actio-task.v3','actio-task.v4','actio-task.v5','actio-task.v6'):
        from actio.tasks.finite import result
        return result(t,actions)
    legal=all(a in t['action_specs'][s]['options'] for s,a in zip(t['order'],actions))
    if not legal:return {'rule':RULE,'status':'illegal_action','agreed_slot':None,'complete':True}
    if len(actions)!=2:return {'rule':RULE,'status':'incomplete','agreed_slot':None,'complete':False}
    slot=actions[0].removeprefix('propose:')
    agreed=actions[1]=='accept' and all(slot in t['seats'][s]['private']['available'] for s in t['order'])
    return {'rule':RULE,'status':'agreed' if agreed else 'not_agreed','agreed_slot':slot if agreed else None,'complete':True}


def actor_observation(m,seat,public_actions):
    if m.get('input_contract') in ('finite-suite-tokenkey.v1','finite-candidate-loopback.v1','finite-candidate-tokenkey.v1','visible-robustness-tokenkey.v1'):
        from actio.tasks.finite import observation
        return observation(m,seat,public_actions)
    if m.get('input_contract') in ('scheduling-tokenkey.v2','finite-suite-tokenkey.v1','finite-candidate-loopback.v1','finite-candidate-tokenkey.v1','visible-robustness-tokenkey.v1'):
        from actio.tasks.scheduling_v2 import observation
        return observation(m,seat,public_actions)
    t=m['task']['body']
    return canonical({**({'role':t['seats'][seat]['role']} if m.get('execution_mode') in ('transport_stub','priced_rehearsal','tokenkey_live','tokenkey_rehearsal') else {}),
        'schema':'scheduling-observation.v2' if m.get('execution_mode') in ('transport_stub','priced_rehearsal','tokenkey_live','tokenkey_rehearsal') else 'scheduling-observation.v1','task_hash':m['task']['sha256'],'seat':seat,
        'public':t['public'],'own':t['seats'][seat]['private'],'initial_relationship':t['relationships'][seat],
        'public_actions':[{'seat':t['order'][i],'action':a} for i,a in enumerate(public_actions)]})






def resolved_text(t,actions):return canonical({'public_actions':actions,'task_result':task_result(t,actions)})
