"""Authored synthetic C5 fixtures. Never contains historical provider message text."""
import base64
import copy
import hashlib
from .common import canonical, digest
from .failure_observation import INPUT, bind

CASES=[
    {'id':'text-success','family':'scheduling','fault':None,'sends':2,'settled':2,'unknown':0,'admitted':2},
    {'id':'dual-success','family':'bargaining','fault':None,'sends':2,'settled':2,'unknown':0,'admitted':2},
    {'id':'c4-substitute','family':'scheduling','fault':'c4','sends':1,'settled':0,'unknown':1,'admitted':0},
    {'id':'data-error','family':'scheduling','fault':'data','sends':1,'settled':0,'unknown':1,'admitted':0},
    {'id':'prefix-error','family':'scheduling','fault':'prefix','sends':1,'settled':0,'unknown':1,'admitted':0},
    {'id':'b-error','family':'scheduling','fault':'data','sends':2,'settled':1,'unknown':1,'admitted':1},
    {'id':'http429','family':'scheduling','fault':'429','sends':1,'settled':0,'unknown':1,'admitted':0},
    {'id':'http503','family':'scheduling','fault':'503','sends':1,'settled':0,'unknown':1,'admitted':0},
    {'id':'truncated','family':'scheduling','fault':'truncated','sends':1,'settled':0,'unknown':1,'admitted':0}]


def frame(value,event=None):return ('event: '+event+'\n' if event else '')+'data: '+canonical(value)+'\n\n'


def chunk(delta,finish=None,usage=None):
    v={'id':'c5-synthetic','model':'gpt-5.6','object':'chat.completion.chunk','created':1791504000,
       'choices':[{'index':0,'delta':delta,**({'finish_reason':finish} if finish else {})}]}
    if usage is not None:v['usage']=usage
    return v


def error(type_='api_error',code=None):
    return {'error':{'type':type_,'message':'C5 synthetic fixture failure.',**({'code':code} if code else {})}}


def fault_response(kind):
    if kind in ('429','503'):
        return int(kind),canonical(error('rate_limit_error' if kind=='429' else 'server_error',
            'rate_limit_exceeded' if kind=='429' else 'service_unavailable')),'application/json'
    initial=frame(chunk({'role':'assistant'}))
    if kind=='c4':raw=initial+frame(error())+frame(error('upstream_error','upstream_stream_truncated'),'error')
    elif kind=='data':raw=frame(error())
    elif kind=='prefix':raw=frame(chunk({'role':'assistant','content':'propose:morning'}))+frame(error())
    elif kind=='truncated':raw=initial  # EOF at a frame boundary, no finish/DONE/usage.
    else:raise ValueError('unknown synthetic fault')
    return 200,raw,'text/event-stream'


def vector(kind='data',text='error is ordinary content',reasoning=None):
    """Hand-authored adapter/native ONLY for pure tests, never runtime evidence."""
    if kind=='success':
        raw='';chunks=[];blocks=[]
        for index,(typ,value) in enumerate([('reasoning',reasoning),('text',text)]):
            if value is None:continue
            raw+=frame(chunk({'role':'assistant', 'content' if typ=='text' else 'reasoning_content':value}))
            block={'type':typ,'text':value};blocks.append(block)
            chunks.extend([{'type':'block-start','index':index,'blockType':typ},
                {'type':typ+'-delta','index':index,'text':value},{'type':'block-end','index':index,'block':block}])
        usage={'prompt_tokens':12,'completion_tokens':5,'total_tokens':17,'prompt_cache_hit_tokens':4,'prompt_cache_miss_tokens':8}
        raw+=frame(chunk({},'stop',usage))+'data: [DONE]\n\n';status=200
        native_usage={'inputTokens':8,'outputTokens':5,'totalTokens':17,'cacheReadTokens':4}
        chunks.extend([{'type':'usage','usage':native_usage},{'type':'finish','reason':{'kind':'stop'}}])
    else:
        status,raw,_=fault_response(kind);blocks=None;native_usage=None;chunks=[]
        if kind=='prefix':
            chunks=[{'type':'block-start','index':0,'blockType':'text'},
                {'type':'text-delta','index':0,'text':'propose:morning'},
                {'type':'block-end','index':0,'block':{'type':'text','text':'propose:morning'}}]
        chunks.extend([{'type':'usage','usage':{'inputTokens':0,'outputTokens':0,'totalTokens':0}},
            {'type':'finish','reason':{'kind':'error','failure':{'code':'PI_AI_ERROR','message':'Synthetic adapter failure.'}}}])
    request={'raw':canonical({'model':'gpt-5.6','messages':[]})}
    return bind({'schema':INPUT,'origin':'synthetic_vector','source':{'fixture':'c5-authored-v1','kind':kind},
        'identity':{'attempt':'synthetic-attempt','run':'synthetic-run','stream':'synthetic-stream','seat':'A',
            'config_hash':digest('synthetic-config'),'request_hash':hashlib.sha256(request['raw'].encode()).hexdigest()},
        'request':request,'response':{'raw':raw,'raw_base64':base64.b64encode(raw.encode()).decode(),
            'status':status,'error':None,'chunks_json':canonical(chunks),'deadlines':{},'timings':{}},
        'native':{'stream':'synthetic-stream','chunks':chunks,'content':blocks,'usage':native_usage,
            'terminal':'completed' if kind=='success' else 'error','codes':[] if kind=='success' else ['PI_AI_ERROR']},
        'operation':{'id':'synthetic-attempt','run':'synthetic-run','stream':'synthetic-stream','answer':text if kind=='success' else None,'admitted':False,'domain_receipts':0},
        'accounting':{'state':'unknown','trusted_usage':None,'reason_code':'synthetic-only'},'transport':{'sending':True}})


def mutate(value,change,*,sync_bytes=True,sync_native=True):
    b=copy.deepcopy(value['body']);b.pop('hashes');change(b)
    if sync_bytes:b['response']['raw_base64']=base64.b64encode(b['response']['raw'].encode()).decode()
    if sync_native and b['native'] is not None:
        import json
        b['native']['chunks']=json.loads(b['response']['chunks_json'])
    return bind(b)


def portable_vectors():
    return [{'id':k,'input':vector(k),'expected':{'classification':
        'success_control' if k=='success' else 'http_error_observed' if k in ('429','503') else
        'incomplete_or_unclassified' if k=='truncated' else 'provider_error_observed',
        'admission':False,'original_state':'unknown'}} for k in ('success','c4','data','prefix','429','503','truncated')]
