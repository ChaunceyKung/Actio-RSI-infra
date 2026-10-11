from actio.domain.accounting import totals
"""Single-machine synthetic attempt ledger. SQLite commits precede provider sends."""
import hashlib
import json

from actio.contracts.json import canonical, digest, ContractError
from .transport_contract import validate_config, PROFILE, PROVIDER, MODEL, MAX_INPUT, MAX_OUTPUT
from actio.contracts.json import require


def sha(raw):return hashlib.sha256(raw.encode()).hexdigest()


def suite(c):return c is not None and c.get('schema') in ('pilot-config.v7','pilot-config.v8','pilot-config.v9','pilot-config.v10')

def pilot(c):return c is not None and c.get('schema') in ('pilot-config.v6','pilot-config.v7','pilot-config.v8','pilot-config.v9','pilot-config.v10')


def gateway(c):return c is not None and c.get('schema') in ('pilot-config.v5','pilot-config.v6','pilot-config.v7','pilot-config.v8','pilot-config.v9','pilot-config.v10')


def metered(c):return priced(c) or gateway(c)


def schema_for(c):return 4 if pilot(c) else 3 if gateway(c) else 2 if priced(c) else 1


def ledger_contract(c):return 'attempt-ledger.v'+str(schema_for(c))


def cap_allows(used,reserved,c):
    if gateway(c):return used['calls']+reserved['calls']<=2*len(c['plan'])
    return all(used[k]+v<=caps(c)[k] for k,v in reserved.items())


def priced(c):return c is not None and c.get('schema')=='pilot-config.v4'


def validate_budget_config(c):
    if c is not None and c.get('schema')=='pilot-config.v10':
        from .robustness_campaign import validate
        return validate(c)
    if c is not None and c.get('schema')=='pilot-config.v9':
        from .evaluation_campaign import validate
        return validate(c)
    if c is not None and c.get('schema')=='pilot-config.v8':
        from .candidate_campaign import validate
        return validate(c)
    if suite(c):
        from .suite_contract import validate
        return validate(c)
    if pilot(c):
        from .pilot_contract import validate
        return validate(c)
    if gateway(c):
        from .gateway_contract import validate
        return validate(c)
    if priced(c):
        from .readiness_contract import validate
        return validate(c)
    return validate_config(c)


def profile_for(c):
    if c is not None and c.get('schema')=='pilot-config.v10':
        from .robustness_campaign import PROFILE as selected
        return selected
    if c is not None and c.get('schema')=='pilot-config.v9':
        from .evaluation_campaign import PROFILE as selected
        return selected
    if c is not None and c.get('schema')=='pilot-config.v8':
        from .candidate_campaign import PROFILE as selected
        return selected
    if suite(c):
        from .suite_contract import PROFILE as selected
        return selected
    if pilot(c):
        from .pilot_contract import PROFILE as selected
        return selected
    if gateway(c):
        from .gateway_contract import PROFILE as p
        return p
    if priced(c):
        from .readiness_contract import PROFILE as p
        return p
    return PROFILE


def caps(c):
    if gateway(c):return {'calls':2*len(c['plan']),'input_tokens':None,'output_tokens':None,'cost_minor':None}
    return c['budget'] if priced(c) else c['roles']['solver']['budget']


def reserve_amount(c):
    if gateway(c):return {'calls':1,'input_tokens':None,'output_tokens':512,'cost_minor':None}
    if priced(c):
        from .readiness_contract import reservation
        return reservation(c)
    return {'calls':1,'input_tokens':MAX_INPUT,'output_tokens':MAX_OUTPUT,'cost_minor':MAX_INPUT+MAX_OUTPUT}


def endpoint_for(c):return c['endpoint'] if metered(c) else c['roles']['solver']['endpoint']


def wire_binding(scope,request,config=None):
    if gateway(config):
        from .gateway_contract import wire_binding as bind
        return bind(scope,request,config)
    """Check the observed official transformation; IDs/source are not model content."""
    require(set(request)=={'method','url','raw','prepared'},'attempt request fields')
    require(request['method']=='POST' and request['url']==scope['endpoint']+'/chat/completions','attempt endpoint/method')
    require(type(request['raw']) is str and 0<len(request['raw'].encode())<=MAX_INPUT,'wire byte bound')
    raw=json.loads(request['raw']);prepared=request['prepared']
    require(prepared['provider']==PROVIDER and prepared['model']==(config['model'] if priced(config) else MODEL) and prepared.get('purpose') is None and prepared['tools']==[],'prepared call scope')
    messages=prepared['messages'];require(len(messages)==2 and [m['role'] for m in messages]==['system','user'],'pure text two-message scope')
    text=[]
    for m in messages:
        require(all(set(c)=={'type','text'} and c['type']=='text' for c in m['content']),'nontext input denied')
        text.append(''.join(c['text'] for c in m['content']))
    require(text[0]==scope['persona'] and json.loads(text[1])==scope['task'],'actor task/body binding')
    require(raw['messages']==[{'role':r,'content':v} for r,v in zip(('system','user'),text)],'official serialization message mapping')
    require(set(raw)=={'model','messages','stream','stream_options','thinking','max_tokens','dsh_plugin_packages'},'unexpected provider fields/tools')
    require(raw['model']==(config['model'] if priced(config) else MODEL) and raw['stream'] is True and raw['stream_options']=={'include_usage':True} and
            raw['thinking']=={'type':'disabled'} and raw['max_tokens']==MAX_OUTPUT,'official wire parameters')
    inventory=raw['dsh_plugin_packages'];require(inventory['version']==1,'inventory version')
    packages={p['name']:p['version'] for p in inventory['packages']}
    require(packages.get('@deepseek-ai/dsh-llm-deepseek')=='0.1.5-rc.1','official plugin version')
    require(not any(p in packages for p in ('@deepseek-ai/dsh-llm-retry','@deepseek-ai/dsh-session-title','@deepseek-ai/dsh-mcp-client')),'disabled producer present')
    return {'prepared_hash':digest(prepared),'wire_hash':sha(request['raw']),'actor_hash':digest(scope['task']),
            'mapping':'system/user text identical; source/id removed; pinned official fields/inventory added'}


def trusted_usage(response,native,config=None):
    if gateway(config):
        from .gateway_contract import trusted_usage as usage
        return usage(response,native,config)
    """Observe raw synthetic usage; official adapter still owns protocol/stream translation."""
    require(set(response)=={'status','raw','chunks_json','error'} and response['status']==200 and response['error'] is None,'response not complete')
    require(len(response['raw'].encode())<=65536,'response byte limit')
    values=[line[6:] for line in response['raw'].splitlines() if line.startswith('data: ')]
    require(0<len(values)<=128 and values[-1]=='[DONE]' and values.count('[DONE]')==1,'missing/extra DONE')
    rows=[json.loads(s) for s in values[:-1]]
    require(all(type(r) is dict for r in rows),'invalid raw stream row')
    usages=[r['usage'] for r in rows if r.get('usage') is not None];require(bool(usages),'usage missing')
    u=usages[-1];require(type(u) is dict,'usage shape');canonical(u)
    def number(n):require(type(n) is int and 0<=n<=9007199254740991,'invalid usage integer');return n
    prompt=number(u['prompt_tokens']);output=number(u['completion_tokens'])
    require(number(u.get('total_tokens',prompt+output))==prompt+output,'usage total contradiction')
    require(type(u.get('prompt_tokens_details',{})) is dict and type(u.get('completion_tokens_details',{})) is dict,'invalid usage detail shape')
    cache=u.get('prompt_tokens_details',{}).get('cached_tokens',u.get('prompt_cache_hit_tokens',0));number(cache)
    require(cache<=prompt,'cache exceeds prompt')
    if 'prompt_cache_hit_tokens' in u:require(number(u['prompt_cache_hit_tokens'])==cache,'cache sources disagree')
    if 'prompt_cache_miss_tokens' in u:require(number(u['prompt_cache_miss_tokens'])+cache==prompt,'cache sum contradiction')
    reasoning=u.get('completion_tokens_details',{}).get('reasoning_tokens');require(reasoning is None or number(reasoning)<=output,'reasoning exceeds output')
    expected={'inputTokens':prompt-cache,'outputTokens':output,'totalTokens':prompt+output}
    if 'prompt_cache_hit_tokens' in u or 'cached_tokens' in u.get('prompt_tokens_details',{}):expected['cacheReadTokens']=cache
    if reasoning is not None:expected['reasoningTokens']=reasoning
    mapped=[c['usage'] for c in json.loads(response['chunks_json']) if c['type']=='usage']
    require(mapped==[expected] and json.loads(native)==expected,'raw/translated/native usage mismatch')
    finish=[c.get('reason') for c in json.loads(response['chunks_json']) if c['type']=='finish']
    require(finish in ([{'kind':'stop'}],[{'kind':'max-tokens'}]) if priced(config) else finish==[{'kind':'stop'}],'unsupported official stream finish')
    limit=reserve_amount(config) if priced(config) else {'input_tokens':MAX_INPUT,'output_tokens':MAX_OUTPUT}
    require(prompt<=limit['input_tokens'] and output<=limit['output_tokens'],'usage exceeds reservation')
    if priced(config):
        from .readiness_contract import amount
        identities=[(r.get('id'),r.get('model')) for r in rows if r.get('choices')]
        require(bool(identities) and len(set(identities))==1,'response request ID/model missing or changed')
        request_id,model=identities[0]
        require(type(request_id) is str and 0<len(request_id)<=256 and model in config['model_policy']['response_models'],'response model/request ID rejected')
        cost=amount(cache,prompt-cache,output,config['quote'])
        require(cost<=limit['cost_minor'],'estimated cost exceeds reservation')
        return {'input_tokens':prompt,'output_tokens':output,'cost_minor':cost,'calls':1,
                'raw':u,'native':expected,'currency':'USD','minor_per_currency':1000000000,
                'quote_hash':digest(config['quote']),'basis':'frozen peak quote estimate; missing cache detail charged all miss',
                'provider_identity':{'id':request_id,'model':model,'system_fingerprints':[r.get('system_fingerprint') for r in rows]},
                'finish':finish[0]['kind'],'supplier_bill_minor':None,'billing_reconciled':False}

    return {'input_tokens':prompt,'output_tokens':output,'cost_minor':prompt+output,'calls':1,
            'raw':u,'native':expected,'basis':'synthetic provider usage; cache included once'}




def terminal_keys(c):
    return ('response','native_usage','usage','reason')+(('text_integrity',) if pilot(c) else ())




def verify_snapshot(s):
    m=s['meta'];validate_budget_config(m['config']);require(m['schema']==ledger_contract(m['config']) and m['config_hash']==digest(m['config']) and m['profile']==profile_for(m['config']),'ledger metadata')
    require(s['totals']==totals(s['attempts']),'budget totals mismatch')
    require(cap_allows(s['totals'],dict.fromkeys(s['totals'],0),m['config']),'budget cap exceeded')
    regs={r['id']:r for r in s['registrations']};require(len(regs)==len(s['registrations']),'duplicate registration')
    attempts={a['id']:a for a in s['attempts']};require(len(attempts)==len(s['attempts']),'duplicate attempt')
    events=s['events'];require([e['seq'] for e in events]==list(range(1,len(events)+1)),'budget event sequence')
    require(all(e['attempt'] in attempts for e in events),'unreferenced budget event')
    registered=[]
    for a in attempts.values():
        scope=a['scope'];registered.append(scope['registration'])
        require(scope['registration'] in regs and scope['campaign']==m['campaign'] and scope['config_hash']==m['config_hash'] and scope['profile']==profile_for(m['config']),'attempt ownership')
        require(scope['run']==regs[scope['registration']]['run'] and scope['op']==a['id'] and scope['endpoint']==endpoint_for(m['config']),'attempt endpoint/run')
        ev=[e for e in events if e['attempt']==a['id']];kinds=[e['kind'] for e in ev]
        require(ev[0]['kind']=='authorized' and ev[0]['body']==scope,'attempt authorization')
        allowed=[['authorized'],['authorized','denied'],['authorized','released'],['authorized','reserved'],
                 ['authorized','reserved','released'],['authorized','reserved','unknown'],['authorized','reserved','sending'],
                 ['authorized','reserved','sending','unknown'],['authorized','reserved','sending','settled']]
        require(kinds in allowed and kinds[-1]==a['state'],'invalid/duplicate transition')
        if a['request'] is not None:
            require(a['binding']==wire_binding(scope,a['request'],m['config']),'wire/prepared binding')
            require(a['reservation']==reserve_amount(m['config']),'reserve amounts')
            require(ev[1]['body']=={k:a[k] for k in ('request','binding','reservation')},'reserve event mismatch')
        else:require(a['binding'] is None and a['reservation'] is None,'unreserved amount')
        if 'sending' in kinds:require(ev[kinds.index('sending')]['body']=={'wire_hash':a['binding']['wire_hash']},'sending event')
        if a['state']=='settled':require(a['usage']==trusted_usage(a['response'],a['native_usage'],m['config']),'settled usage mismatch')
        else:require(a['usage'] is None,'nonsettled cannot charge zero/usage')
        if a['state'] in ('settled','unknown'):
            require(ev[-1]['body']=={k:a[k] for k in terminal_keys(m['config'])},'terminal budget event')
        if pilot(m['config']) and a['state'] in ('settled','unknown'):
            from .channel_audit import for_config
            require(a['text_integrity']==for_config(m['config']).verdict(a['response']),'text audit recomputation mismatch')
        if a['state']=='denied':require(ev[-1]['body']=={'reason':a['reason']},'denial reason mismatch')
    require(len(registered)==len(set(registered)),'multiple attempts per registration')
    replay={};cap=caps(m['config'])
    for e in events:
        aid=e['attempt'];kind=e['kind'];body=e['body']
        if kind=='authorized':replay[aid]={'state':'authorized','reservation':None,'usage':None}
        else:
            a=replay[aid]
            if kind=='reserved':
                used=totals(list(replay.values()))
                require(not any(v['state'] in ('reserved','sending','unknown') for v in replay.values()),'reserve after unresolved reservation')
                require(cap_allows(used,body['reservation'],m['config']),'reservation exceeded concurrent cap')
                a['reservation']=body['reservation']
            if kind=='settled':a['usage']=body['usage']
            a['state']=kind
    return True


def verify_run_attempts(data,m):
    streams={s['id']:s for s in data['streams']};agents={a['id']:json.loads(a['spec']) for a in data['agents']}
    attempts=[json.loads(row['body']) for row in data['audit'] if row['kind']=='transport_attempt']
    ops={o['id']:o for o in data['operations']};require(len(attempts)==len(ops) and {a['id'] for a in attempts}==set(ops),'missing/duplicate run budget attempt')
    for a in attempts:
        op=ops[a['id']];stream=streams[op['stream']];scope=a['scope']
        intent=next(json.loads(r['body']) for r in data['audit'] if r['kind']=='dispatch_intent' and r['op']==op['id'])
        seat=next(s for s,v in m['entities'].items() if v==stream['agent'])
        require(scope=={'campaign':m['transport']['campaign'],'run':data['run']['id'],'op':op['id'],
                'registration':data['run']['id']+':'+seat,'seat':seat,'stream':op['stream'],'epoch':op['epoch'],
                'worker':stream['worker'],'config_hash':m['transport']['config_hash'],'profile':profile_for(m['transport']['config']),
                'endpoint':endpoint_for(m['transport']['config']),'persona':agents[stream['agent']]['persona'],'task':intent if pilot(m['transport']['config']) else {**intent,'op':op['id']}},'run/actor/attempt ownership mismatch')
        if a['request'] is not None:require(a['binding']==wire_binding(scope,a['request'],m['transport']['config']),'run wire mapping')
        if pilot(m['transport']['config']):
            from .channel_audit import for_config, native_content
            reader=for_config(m['transport']['config'])
            expected=reader.verdict(a['response'])
            require(a['text_integrity']==expected or a['text_integrity'] is None and a['response'] is None and a['state'] in ('denied','released'),'run text audit mismatch')
            integrity=(a['text_integrity'] or {}).get('status')=='verified'
            if integrity and op['answer'] is not None:
                reader.audit(a['response'],op['answer'],require_bytes=True,**({'native_blocks':native_content(data,op['stream'])} if m['transport']['config']['schema'] in ('pilot-config.v8','pilot-config.v9','pilot-config.v10') else {}))
            if not integrity:require(not any(r['op']==op['id'] for r in data['domain_receipts']),'rejected text cannot mutate world')
        require(a['state'] in ('denied','released','unknown','settled'),'unresolved active budget state')
        if a['state']=='settled':
            require((op['terminal']=='completed' and op['barrier']) or (metered(m['transport']['config']) and a['usage']['finish']=='max-tokens'),'settlement without native terminal')
            events=[json.loads(e['raw']) for e in data['occurrences'] if e['stream']==op['stream']]
            finals=[e for e in events if e['type']=='assistant/message']
            require(finals and finals[-1]['data'].get('usage')==json.loads(a['native_usage']),'native usage not bound')
            require(a['usage']==trusted_usage(a['response'],a['native_usage'],m['transport']['config']),'run settlement usage')
        else:require(a['usage'] is None,'unknown/denied usage cannot be zero charge')
    return {'attempts':len(attempts),'settled':sum(a['state']=='settled' for a in attempts),
            'unknown':sum(a['state']=='unknown' for a in attempts),'mode':'gateway_usage_cost_unverified' if gateway(m['transport']['config']) else 'simulated_provider_usage_usd_estimate' if priced(m['transport']['config']) else 'synthetic_only'}






def __getattr__(name):
    if name == 'Ledger':
        from .adapters.persistence.ledger import Ledger
        return Ledger
    if name == 'main':
        from .interfaces.budget import main
        return main
    raise AttributeError(name)


if __name__ == '__main__':
    from .interfaces.budget import main
    raise SystemExit(main())
