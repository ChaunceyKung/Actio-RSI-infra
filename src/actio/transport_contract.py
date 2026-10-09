"""Pure, versioned loopback contract; no clients, credential lookup or runtime imports."""
import json
from .common import ContractError,canonical,digest

CONFIG='pilot-config.v3'
INPUT='scheduling-transport.v1'
PROFILE='sdk-minimal+actio-chat-budget.v1'
PROTOCOL='chat-completions.v1'
MODEL='actio-synthetic-chat-model'
PROVIDER='deepseek-official'
SOURCE='183f08e9c6dde7e36cd2318eaee70b0da08fb35e'
MAX_INPUT=65536
MAX_OUTPUT=64


def require(ok,reason):
    if not ok:raise ContractError(reason)


def config(endpoint,calls=2):
    from .preflight import template
    c=template('transport_stub');c['schema']=CONFIG
    s=c['roles']['solver'];s.update(provider=PROVIDER,model=MODEL,protocol=PROTOCOL,endpoint=endpoint,
        credential_ref='ACTIO_STUB_KEY',data_scope='synthetic-own-context.v1',parameters={'max_tokens':MAX_OUTPUT,'thinking':'disabled'})
    s['budget']={'calls':calls,'input_tokens':calls*MAX_INPUT,'output_tokens':calls*MAX_OUTPUT,
                 'cost_minor':calls*(MAX_INPUT+MAX_OUTPUT),'input_price_minor':1,'output_price_minor':1,
                 'currency':'SYNTHETIC','price_version':'synthetic-byte-upper.v1'}
    return c


def validate_config(c):
    from .preflight import validate,STUB_MODEL
    canonical(c)
    require(c['schema']==CONFIG,'Chat Completions requires pilot-config.v3')
    s=c['roles']['solver'];require(s['mode']=='transport_stub','v3 is loopback only; live blocked')
    require((s['provider'],s['model'],s['protocol'])==(PROVIDER,MODEL,PROTOCOL),'v3 provider/model/protocol')
    old=json.loads(canonical(c));old['schema']='pilot-config.v2';old['roles']['solver'].update(model=STUB_MODEL,protocol='messages.v1')
    validate(old)
    require(s['parameters']=={'max_tokens':MAX_OUTPUT,'thinking':'disabled'},'frozen text parameters')
    return c


def validate_pins(p):
    if p.get('profile')=='sdk-minimal+actio-tokenkey.v1':
        from .gateway_contract import PROFILE as profile,ROUTE,MODELS,PACKAGE
        require(p.get('provider')==ROUTE and p.get('model') in MODELS and p.get('protocol')=='openai-completions' and p.get('policy')=='sqlite-uncapped-attempt.v1' and p.get('adapter')==PACKAGE,'gateway identity pins')
        require(p.get('reviewed_dsh_source')==SOURCE and p.get('registry')==digest([]) and p.get('connection_mode') in ('tokenkey_live','tokenkey_rehearsal'),'gateway source/mode/tools')
        return
    if p.get('profile')=='sdk-minimal+actio-priced-memory.v1':
        from .readiness_contract import MODEL as model, PROFILE as profile
        require((p.get('profile'),p.get('provider'),p.get('model'),p.get('protocol'),p.get('policy'))==
                (profile,PROVIDER,model,PROTOCOL,'sqlite-priced-attempt.v1'),'priced identity pins mismatch')
        require(p.get('reviewed_dsh_source')==SOURCE and p.get('registry')==digest([]),'priced source/empty tools pins')
        return
    require((p.get('profile'),p.get('provider'),p.get('model'),p.get('protocol'),p.get('policy'))==
            (PROFILE,PROVIDER,MODEL,PROTOCOL,'sqlite-attempt.v1'),'transport identity pins mismatch')
    require(p.get('reviewed_dsh_source')==SOURCE and p.get('registry')==digest([]),'transport source/empty tools pins')


def validate_manifest(m):
    from .task_contract import validate_task
    v4=m.get('input_contract')=='scheduling-priced.v1'
    v5=m.get('input_contract')=='scheduling-tokenkey.v1'
    mode=m.get('execution_mode') if v5 else 'priced_rehearsal' if v4 else 'transport_stub'
    if v5:require(mode in ('tokenkey_live','tokenkey_rehearsal'),'gateway mode')
    from .readiness_contract import PROFILE as priced_profile,validate as validate_priced
    from .gateway_contract import PROFILE as gateway_profile,validate as validate_gateway
    profile=gateway_profile if v5 else priced_profile if v4 else PROFILE
    t=validate_task(m['task']);require(t['mode']==mode,'transport task mode')
    require(set(m)=={'input_contract','execution_mode','scenario','task','entities','agents','memory','pins','engine','source',
                    'order','max_steps','seed','world','observation_policy','gm_private','request','replay_of','transport'},'transport manifest fields')
    require(m['input_contract']==('scheduling-tokenkey.v1' if v5 else 'scheduling-priced.v1' if v4 else INPUT) and m['execution_mode']==mode and m['scenario']=='social','transport input mode')
    require(m['entities']=={s:t['seats'][s]['agent'] for s in t['order']} and
            m['agents']=={s['agent']:s['spec_hash'] for s in t['seats'].values()},'transport seats/specs')
    require(m['engine']=='concordia.Sequential' and m['source']=='b71d202750e23444ce1bf28d9f114bcd88aa41db','transport Engine pin')
    require(m['order']==['A','B'] and m['max_steps']==2 and m['seed']==0 and m['world']==[] and m['replay_of'] is None,'transport fixed schedule')
    require(m['observation_policy']=='scheduling-own-plus-public.v2' and m['gm_private']=='SCHEDULING_GM_PRIVATE_AUDIT_ONLY','transport visibility policy')
    tr=m['transport'];require(set(tr)=={'config','config_hash','campaign','profile'},'transport binding fields')
    (validate_gateway if v5 else validate_priced if v4 else validate_config)(tr['config']);require(tr['config_hash']==digest(tr['config']) and tr['profile']==profile and type(tr['campaign']) is str,'transport config binding')
    validate_pins(m['pins']);require(m['pins']['profile']==profile,'mode/profile mismatch')
    if v4 or v5:require(m['pins'].get('connection_mode')==mode and tr['config']['mode']==mode,'connection mode pin mismatch')
    require(m['request']=={'scenario':'social','task_hash':m['task']['sha256'],'a':m['entities']['A'],'b':m['entities']['B'],
                           'config_hash':tr['config_hash'],'campaign':tr['campaign'],'mode':mode},'transport request binding')
    require(set(m['memory'])==set(m['agents']),'transport memory identities')
    for a,s in m['memory'].items():
        require(s['namespace']=={'agent':a,'project':'synthetic','branch':'main','visibility':'private','environment':'social'} and s['target']=='social','transport memory ACL')
    return t


def payload(m,seat,observations):
    t=m['task']['body']
    return {'observations':observations,'memory':m['memory'][m['entities'][seat]],'action_spec':t['action_specs'][seat]}


def validate_inputs(m,streams,operations,audit):
    from .task_contract import actor_observation
    t=validate_manifest(m);by_stream={s['id']:s for s in streams};ops={o['id']:o for o in operations}
    rows=sorted((a for a in audit if a['kind']=='dispatch_intent'),key=lambda a:a['id']);prior=[]
    require(len(rows)<=2 and len(rows)==len(ops) and {r['op'] for r in rows}==set(ops),'transport dispatch completeness')
    for step,row in enumerate(rows):
        seat=t['order'][step];op=ops[row['op']]
        require(by_stream[op['stream']]['agent']==m['entities'][seat],'transport dispatch seat')
        expected=payload(m,seat,[actor_observation(m,seat,prior[:i]) for i in range(step+1)])
        require(json.loads(row['body'])==expected,'transport frozen actor view mismatch')
        if step:require(prior[-1] in t['action_specs']['A']['options'],'second actor without legal first action')
        prior.append(op['answer'])
