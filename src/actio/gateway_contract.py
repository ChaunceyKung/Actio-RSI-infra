"""TokenKey C2B1 contract. Pure validation; no environment, credential or network reads."""
import json
from decimal import Decimal
from pathlib import Path
from .common import canonical,digest,file_hash
from .transport_contract import require,SOURCE
from .preflight import loopback_endpoint

CONFIG='pilot-config.v5'
INPUT='scheduling-tokenkey.v1'
PROFILE='sdk-minimal+actio-tokenkey.v1'
ROUTE='actio-tokenkey'
PACKAGE='@deepseek-ai/dsh-llm-pi-ai'
MODELS=('gpt-5.6','claude-sonnet-4-6')
ENDPOINT='https://api.tokenkey.dev/v1'
AUTH='explicit_user_instruction_2026_10_09'
TIMEOUTS={'ready':30,'rpc':5,'first_response':45,'idle':30,'request':90,'result':115,'drained':5,'closed':5,'worker':165}
PERSONA='You are one actor in a synthetic scheduling task. Respect your own availability and goal. Return exactly one action_spec option as plain text, without quotes, JSON, explanation or private details. Use only your own context and observed public actions.'

def template(model=MODELS[0],mode='tokenkey_live',endpoint=ENDPOINT):
    return {'schema':CONFIG,'mode':mode,'gateway':'TokenKey','adapter':PACKAGE,'adapter_version':'0.1.5-rc.1',
            'provider':ROUTE,'model':model,'endpoint':endpoint,'path':'/chat/completions','protocol':'openai-completions',
            'profile':PROFILE,'source':SOURCE,'credential_ref':'file:.local/credentials/token_key.txt',
            'credential_env':'ACTIO_SOLVER_KEY','spending_policy':'uncapped_for_phase1c2b1','cost_limit_minor':None,
            'authorization_basis':AUTH,'plan':['compatible','conflict'],'timeouts':dict(TIMEOUTS),
            'parameters':{'max_tokens':512,'reasoning':'not_requested','temperature':None,'seed':None},
            'bounds':{'input_bytes':65536,'response_bytes':262144,'chunks':1024},
            'identity_policy':'response_model must equal requested label; upstream identity unverified',
            'pricing':'TokenKey usage.cost preserved as decimal text; currency/unit unverified; no USD estimate',
            'stop':'first unknown/protocol/identity/timeout stops batch; no retries; new diagnostics must reference predecessor',
            'implementation':{p.relative_to(Path(__file__).parent).as_posix():file_hash(p) for p in sorted(Path(__file__).parent.rglob('*')) if p.suffix in ('.py','.mjs','.sql','.json')},
            'predecessors':[],'authority':None}

def validate(c):
    canonical(c);require(type(c) is dict and set(c)==set(template()),'v5 exact fields')
    require(c['model'] in MODELS and c['mode'] in ('tokenkey_live','tokenkey_rehearsal'),'explicit gateway model/mode')
    base=template(c['model'],c['mode'],c['endpoint'])
    require(all(c[k]==base[k] for k in base if k not in ('plan','authority','predecessors')),'gateway frozen contract or implementation mismatch')
    require(type(c['plan']) is list and c['plan'] in (['compatible'],['compatible','conflict']), 'finite ordered authored episode plan')
    if c['mode']=='tokenkey_live':require(c['endpoint']==ENDPOINT,'key destination must be exact TokenKey HTTPS base URL')
    else:require(c['endpoint'].endswith('/v1') and loopback_endpoint(c['endpoint'][:-3]),'literal loopback rehearsal /v1')
    require(type(c['predecessors']) is list and all(type(v) is dict and set(v)=={'path','sha256','reason'} and all(type(x) is str and x for x in v.values()) for v in c['predecessors']),'diagnostic predecessor references')
    a=c['authority']
    require(a is None or type(a) is dict and set(a)=={'id','root'} and type(a['id']) is str and len(a['id'])==32 and all(x in '0123456789abcdef' for x in a['id']) and Path(a['root']).is_absolute(),'authority binding')
    return c

def plan(c):
    from .task_contract import task_card
    validate(c)
    return {'schema':'tokenkey-plan.v1','status':'AUTHORIZED_SCOPE_READY_FOR_EXPLICIT_EXECUTE','contract_hash':digest(c),
            'candidate':c,'tasks':[task_card(v,{s:{'agent':'PROPOSED_'+s,'spec_hash':'0'*64} for s in ('A','B')},c['mode']) for v in c['plan']],
            'maximum_planned_calls':2*len(c['plan']),'cost_limit_minor':None,'estimated_cost':None,'supplier_bill':None,
            'authorization_basis':AUTH,'credential_reads':0,'network_requests':0,'workers_started':0,
            'actual_wire_hash':None,'binding':'proposal; B wire frozen after actual A action; implementation/task/config and real wire bound before sending',
            'upstream_identity_verified':False,'research_promotion':'BLOCKED'}

def wire_binding(scope,request,c):
    from .budget import sha
    require(set(request)=={'method','url','raw','prepared'} and request['method']=='POST' and request['url']==c['endpoint']+c['path'],'TokenKey exact wire origin/path/method')
    require(type(request['raw']) is str and len(request['raw'].encode())<=c['bounds']['input_bytes'],'gateway wire byte limit')
    raw=json.loads(request['raw']);p=request['prepared']
    require(p['provider']==ROUTE and p['model']==c['model'] and p['purpose'] is None and p['tools']==[],'gateway route/model/tools')
    messages=p['messages'];require(len(messages)==2 and [m['role'] for m in messages]==['system','user'],'two messages only')
    text=[]
    for m in messages:
        require(len(m['content'])==1 and m['content'][0]['type']=='text','pure text messages')
        text.append(m['content'][0]['text'])
    persona=PERSONA
    if c.get('schema') in ('pilot-config.v7','pilot-config.v8','pilot-config.v9','pilot-config.v10'):
        from .suite_contract import PERSONA as persona
    require(text[0]==scope['persona']==persona and json.loads(text[1])==scope['task'],'actor visible context binding')
    require(raw=={'model':c['model'],'messages':[{'role':r,'content':t} for r,t in zip(('system','user'),text)],
                 'stream':True,'stream_options':{'include_usage':True},'max_tokens':512},'official pi-ai wire differs from frozen parameters')
    return {'wire_hash':sha(request['raw']),'prepared_hash':digest(p),'mapping':'official pi-ai pure text system/user; exact versioned fields'}

def trusted_usage(response,native,c):
    require(type(response) is dict and response['status']==200 and response['error'] is None,'gateway response incomplete')
    require(len(response['raw'].encode())<=c['bounds']['response_bytes'],'gateway response byte bound')
    values=[s[6:] for s in response['raw'].splitlines() if s.startswith('data: ')]
    require(values and values[-1]=='[DONE]' and values.count('[DONE]')==1,'gateway missing/extra DONE')
    if c.get('schema') in ('pilot-config.v6','pilot-config.v7','pilot-config.v8','pilot-config.v9','pilot-config.v10'):
        from .stream_audit import strict_json
        rows=[strict_json(s) for s in values[:-1]]
    else:rows=[json.loads(s,parse_float=Decimal) for s in values[:-1]]
    usage=[r['usage'] for r in rows if r.get('usage') is not None]
    require(len(usage)==1,'gateway usage missing/ambiguous')
    u=usage[0]
    def n(v):require(type(v) is int and 0<=v<=9007199254740991,'invalid gateway token count');return v
    prompt=n(u['prompt_tokens']);output=n(u['completion_tokens']);require(n(u['total_tokens'])==prompt+output,'gateway total mismatch')
    details=u.get('prompt_tokens_details') or {};cache=n(details.get('cached_tokens',u.get('prompt_cache_hit_tokens',0)))
    require(cache<=prompt,'gateway cache exceeds prompt')
    if 'prompt_cache_miss_tokens' in u:require(n(u['prompt_cache_miss_tokens'])==prompt-cache,'cache miss mismatch')
    if 'prompt_cache_hit_tokens' in u:require(n(u['prompt_cache_hit_tokens'])==cache,'cache hit mismatch')
    reasoning=(u.get('completion_tokens_details') or {}).get('reasoning_tokens')
    require(reasoning is None or n(reasoning)<=output,'reasoning already part of output')
    require(output<=512,'output exceeds explicit cap')
    expected={'inputTokens':prompt-cache,'outputTokens':output,'totalTokens':prompt+output,**({'cacheReadTokens':cache} if cache else {})}
    chunks=json.loads(response['chunks_json']);require([x['usage'] for x in chunks if x['type']=='usage']==[expected] and json.loads(native)==expected,'gateway raw/adapter/native usage mismatch')
    finish=[x['reason']['kind'] for x in chunks if x['type']=='finish'];require(finish in (['stop'],['max-tokens']),'unsupported gateway terminal')
    raw_finish=[x['finish_reason'] for r in rows for x in r.get('choices',[]) if x.get('finish_reason') is not None]
    require(raw_finish==['stop' if finish==['stop'] else 'length'],'gateway raw/native finish mismatch')
    identities={(r.get('id'),r.get('model')) for r in rows};require(len(identities)==1,'response identity changed within stream')
    rid,model=next(iter(identities));require(type(rid) is str and bool(rid) and model==c['model'],'gateway response model/id mismatch')
    cost=u.get('cost');require(cost is None or type(cost) in (int,Decimal) and cost>=0 and Decimal(cost).is_finite(),'invalid gateway cost')
    def safe(v):
        if isinstance(v,Decimal):return str(v)
        if isinstance(v,dict):return {k:safe(x) for k,x in v.items()}
        if isinstance(v,list):return [safe(x) for x in v]
        return v
    return {'calls':1,'input_tokens':prompt,'output_tokens':output,'cost_minor':None,'raw':safe(u),'native':expected,'finish':finish[0],
            'gateway_reported_cost_raw':None if cost is None else str(cost),'cost_source':'SSE usage.cost; numeric spelling preserved via Decimal',
            'currency':None,'cost_unit':None,'estimated_cost':None,'supplier_bill_minor':None,'billing_reconciled':False,
            'provider_identity':{'gateway':'TokenKey','adapter':PACKAGE,'requested_model':c['model'],'response_model':model,'response_id':rid,
                                 'http_request_id':response['http_request_id'],'system_fingerprints':[r.get('system_fingerprint') for r in rows],'upstream_identity_verified':False}}
