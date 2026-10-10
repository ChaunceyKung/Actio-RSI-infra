"""Bounded negative evidence observation. Never admits actions or settles usage."""
import base64
import codecs
import hashlib
import json
from pathlib import Path
from decimal import Decimal
from .common import canonical, digest, ContractError
from .eval_contract import seal, unseal
from .stream_audit import strict_json
from .transport_contract import require
from . import channel_audit

VERSION='transport-failure-observation.v1'
INPUT='transport-failure-evidence.v1'
C4_READER='3750954ea7cc8dff64115039e27bb671fa618d01'
C4_ENTRY='781eedab507df90f6a8b172fdf1918aec1866eed9e6594297ea8199aad03a549'
LIMITS={'raw_bytes':262144,'adapter_bytes':1048576,'frames':1024,'frame_bytes':65536,
        'data_lines':8,'depth':32,'fields':128,'items':4096,'string':1048576,'nodes':50000,'input_bytes':16777216}
ERROR_TYPES={'api_error','upstream_error','rate_limit_error','server_error'}
ERROR_CODES={'upstream_stream_truncated','rate_limit_exceeded','service_unavailable'}
NATIVE_CODES={'PI_AI_ERROR','RATE_LIMIT','TRANSPORT','AUTHENTICATION','SERVER_ERROR','TIMEOUT',
              'REQUEST_TIMEOUT','STREAM_IDLE_TIMEOUT','STREAM_CLOSED','EMPTY_RESPONSE','ABORTED','CONTEXT_WINDOW_EXCEEDED'}


def bounded(value):
    count=0
    def walk(v,depth):
        nonlocal count
        count+=1;require(count<=LIMITS['nodes'] and depth<=LIMITS['depth'],'diagnostic JSON resource limit')
        if isinstance(v,dict):
            require(len(v)<=LIMITS['fields'] and all(type(k) is str and len(k)<=256 for k in v),'diagnostic field bound')
            for x in v.values():walk(x,depth+1)
        elif isinstance(v,list):
            require(len(v)<=LIMITS['items'],'diagnostic list bound')
            for x in v:walk(x,depth+1)
        elif isinstance(v,str):require(len(v.encode('utf8'))<=LIMITS['string'],'diagnostic string bound')
        elif isinstance(v,Decimal):require(v.is_finite(),'nonfinite diagnostic value')
        else:require(v is None or type(v) in (bool,int,float) and (not isinstance(v,float) or __import__('math').isfinite(v)),'diagnostic value type')
    walk(value,0);return value


def parse(raw,limit):
    require(type(raw) is str and len(raw.encode('utf8'))<=limit,'diagnostic input byte bound')
    try:return bounded(strict_json(raw))
    except (ValueError,RecursionError,UnicodeError) as e:raise ContractError('invalid diagnostic JSON encoding') from e


def label(value,allowed):
    if value is None:return None
    require(type(value) is str and len(value.encode('utf8'))<=256,'error label shape/length')
    return value if value in allowed else 'unclassified'


def segmented_utf8(segments):
    """Synthetic segmentation check; captured runtime bytes do not prove segmentation."""
    require(type(segments) is list and len(segments)<=4096,'segment count')
    decoder=codecs.getincrementaldecoder('utf8')('strict');parts=[];size=0
    try:
        for encoded in segments:
            require(type(encoded) is str and len(encoded)<=4*((LIMITS['raw_bytes']+2)//3),'segment bound')
            blob=base64.b64decode(encoded,validate=True);size+=len(blob)
            require(size<=LIMITS['raw_bytes'],'segmented byte bound');parts.append(decoder.decode(blob))
        parts.append(decoder.decode(b'',final=True))
    except (ValueError,UnicodeError) as e:raise ContractError('invalid segmented UTF8') from e
    return ''.join(parts)


def usage_mapping(value):
    def n(v):
        require(type(v) is int and 0<=v<=9007199254740991,'invalid diagnostic token count');return v
    p=n(value['prompt_tokens']);o=n(value['completion_tokens']);t=n(value['total_tokens'])
    require(t==p+o,'raw usage total conflict')
    cache=n((value.get('prompt_tokens_details') or {}).get('cached_tokens',value.get('prompt_cache_hit_tokens',0)))
    require(cache<=p,'raw cache exceeds input')
    if 'prompt_cache_hit_tokens' in value:require(n(value['prompt_cache_hit_tokens'])==cache,'raw cache conflict')
    if 'prompt_cache_miss_tokens' in value:require(n(value['prompt_cache_miss_tokens'])==p-cache,'raw cache miss conflict')
    return {'inputTokens':p-cache,'outputTokens':o,'totalTokens':t,**({'cacheReadTokens':cache} if cache else {})}


def native_chunks(stream):
    """Expand recorded official delta compaction without dropping any record."""
    require(type(stream) is list and len(stream)<=1024,'native stream bound')
    chunks=[]
    for item in stream:
        require(type(item) is dict,'native stream record')
        if item.get('type')=='chunk':
            require(set(item)=={'type','time','chunk'} and type(item['time']) is int,'native chunk fields')
            chunks.append(item['chunk'])
        else:
            require(item.get('type') in ('text-chunks','reasoning-chunks') and set(item)=={'type','time0','index','dt','texts'},'unsupported native stream record')
            require(type(item['index']) is int and 0<=item['index']<=1023 and type(item['time0']) is int,'native delta identity')
            texts=item['texts'];dt=item['dt']
            require(type(texts) is list and 0<len(texts)<=1024 and all(type(t) is str for t in texts),'native delta texts')
            require(type(dt) is list and len(dt)==len(texts)-1 and all(type(t) is int and t>=0 for t in dt),'native delta times')
            chunks.extend({'type':item['type'].removesuffix('-chunks')+'-delta','index':item['index'],'text':t} for t in texts)
        require(len(chunks)<=1024,'expanded native chunk bound')
    return chunks


def protocol(response):
    require(type(response['status']) is int and 0<=response['status']<=599,'HTTP status shape')
    raw=response['raw'];require(type(raw) is str and len(raw.encode('utf8'))<=LIMITS['raw_bytes'],'raw bound')
    encoded=response['raw_base64'];require(type(encoded) is str and len(encoded)<=4*((LIMITS['raw_bytes']+2)//3),'base64 bound')
    try:blob=base64.b64decode(encoded,validate=True);require(blob.decode('utf8',errors='strict')==raw,'UTF8 byte/text mismatch')
    except (ValueError,UnicodeError) as e:raise ContractError('invalid diagnostic raw bytes') from e
    text=raw.replace('\r\n','\n');require('\r' not in text,'bare CR unsupported')
    frames=[];current=[];comments=empty=0
    for line in text.split('\n'):
        if line:
            current.append(line);require(len('\n'.join(current).encode())<=LIMITS['frame_bytes'],'frame byte bound')
        elif current:frames.append((current,True));current=[]
        else:empty+=1
        require(len(frames)<=LIMITS['frames'],'frame count bound')
    if current:frames.append((current,False))
    require(len(frames)<=LIMITS['frames'],'frame count bound')
    # Non-200 bodies are HTTP evidence, not implicitly SSE.
    http_body=response['status']!=200 and not any(raw.startswith(p) for p in ('data:',':','event:'))
    if http_body:frames=[(['data: '+raw],True)] if raw else []
    errors=[];events=[];signals=[];identities=[];finishes=[];usages=[];done=[];parts={'text':[],'reasoning':[]}
    for index,(lines,terminated) in enumerate(frames):
        names=[];data=[];unsupported=0
        for line in lines:
            if line.startswith(':'):comments+=1
            elif line.startswith('event:'):names.append(label(line[6:].lstrip(' '),{'error','message','ping'}))
            elif line.startswith('data:'):data.append(line[5:].removeprefix(' '))
            else:unsupported+=1
        require(len(data)<=LIMITS['data_lines'],'multiline data bound')
        if unsupported:signals.append('unsupported_sse_field')
        if len(names)>1:signals.append('duplicate_event_field')
        payload='\n'.join(data);kind='empty';has_error=False
        if data:
            if payload=='[DONE]':done.append(index);kind='done'
            else:
                obj=parse(payload,LIMITS['frame_bytes']);kind=type(obj).__name__
                if type(obj) is not dict:signals.append('unsupported_data_type')
                else:
                    if 'error' in obj:
                        error=obj['error'];require(type(error) is dict,'structured error object required')
                        require(error.get('message') is None or type(error['message']) is str,'error message shape')
                        errors.append({'frame':index,'source':'http_body' if http_body else 'data.error',
                            'type':label(error.get('type'),ERROR_TYPES),'code':label(error.get('code'),ERROR_CODES),
                            'message_present':error.get('message') is not None,'unknown_fields_present':bool(set(error)-{'message','type','code','param'})})
                        has_error=True
                    if 'choices' in obj:
                        require(obj.get('object')=='chat.completion.chunk','chunk object type')
                        pair=(obj.get('id'),obj.get('model'));require(all(type(x) is str and 0<len(x)<=256 for x in pair),'stream identity shape');identities.append(pair)
                        choices=obj['choices'];require(type(choices) is list and len(choices)<=1,'single-choice shape')
                        for choice in choices:
                            require(type(choice) is dict and choice.get('index')==0,'choice identity')
                            delta=choice.get('delta');require(type(delta) is dict,'delta shape')
                            if set(delta)-{'role','content','reasoning_content'}:signals.append('unsupported_delta_channel')
                            for field,target in (('content','text'),('reasoning_content','reasoning')):
                                value=delta.get(field);require(value is None or type(value) is str,'content channel type')
                                if value:parts[target].append(value)
                            if choice.get('finish_reason') is not None:finishes.append({'frame':index,'kind':label(choice['finish_reason'],{'stop','length'})})
                    if obj.get('usage') is not None:require(type(obj['usage']) is dict,'usage object shape');usages.append((index,obj['usage']))
        if 'error' in names and not has_error:signals.append('event_error_without_structured_error')
        if not terminated:signals.append('unterminated_frame')
        events.append({'index':index,'event_names':names,'data_lines':len(data),'data_kind':kind,'error_object':has_error,'terminated':terminated,'unsupported_fields':unsupported})
    require(len(set(identities))<=1,'raw response identity conflict')
    if len(done)>1:signals.append('duplicate_DONE')
    if done and done[-1]!=len(frames)-1:signals.append('data_after_DONE')
    if len(finishes)>1:signals.append('duplicate_finish')
    if len(usages)>1:signals.append('duplicate_usage')
    if errors and done:signals.append('error_with_DONE')
    if errors and finishes:signals.append('error_with_success_finish')
    if len(errors)>1:signals.append('multiple_provider_errors')
    if not done and not http_body:signals.append('missing_DONE')
    if not usages:signals.append('missing_raw_usage')
    return {'bytes_verified':True,'kind':'http_error_body' if http_body else 'sse','frames':events,'comments':comments,'empty_frames':empty,
            'errors':errors,'done_positions':done,'finishes':finishes,'usage_positions':[i for i,u in usages],'identity_consistent':True,
            'response_model_hash':digest(identities[0][1]) if identities else None,'signals':signals},parts,[u for _,u in usages]


def bind(body):
    """Explicit data-only envelope. Content hashes are not external attestation."""
    body=dict(body);body['hashes']={k:digest(body[k]) for k in ('identity','request','response','native','operation','accounting','transport')}
    return seal(body)


def observe(value):
    require(value.get('body',{}).get('origin')=='synthetic_vector','non-synthetic input requires authenticated full entry')
    return _observe(value)


def _observe(value):
    bounded(value);require(len(canonical(value).encode())<=LIMITS['input_bytes'],'observation input bound')
    b=unseal(value);require(set(b)=={'schema','origin','source','identity','request','response','native','operation','accounting','transport','hashes'} and b['schema']==INPUT,'diagnostic input schema')
    require(b['origin'] in ('synthetic_vector','local_official_runtime','historical_c4'),'diagnostic origin')
    require(b['hashes']=={k:digest(b[k]) for k in ('identity','request','response','native','operation','accounting','transport')},'diagnostic evidence hash mismatch')
    ident=b['identity'];op=b['operation'];native=b['native'];response=b['response'];account=b['accounting']
    require(set(ident)=={'attempt','run','stream','seat','config_hash','request_hash'},'identity fields')
    require(ident['attempt']==op['id'] and ident['run']==op['run'] and ident['stream']==op['stream'] and ident['seat'] in ('A','B'),'cross-attempt operation binding')
    require(ident['request_hash']==hashlib.sha256(b['request']['raw'].encode()).hexdigest(),'request binding')
    if native is not None:require(native['stream']==ident['stream'],'cross-attempt native binding')
    if b['origin']=='historical_c4':require(b['source']['reader']==C4_READER and b['source']['entry_sha256']==C4_ENTRY,'unknown historical source')
    p,parts,raw_usage=protocol(response);chunks=parse(response['chunks_json'],LIMITS['adapter_bytes'])
    request=parse(b['request']['raw'],65536)
    require(p['response_model_hash'] in (None,digest(request['model'])),'response/request model mismatch')
    require(type(chunks) is list and len(chunks)<=1024,'adapter chunk count')
    finish=[];usage=[];adapter_parts={'text':[],'reasoning':[]};signals=list(p['signals'])
    for chunk in chunks:
        require(type(chunk) is dict and type(chunk.get('type')) is str,'adapter event shape')
        kind=chunk['type']
        if finish:signals.append('adapter_event_after_finish')
        if kind in ('text-delta','reasoning-delta'):
            require(type(chunk.get('text')) is str,'adapter text shape');adapter_parts[kind.removesuffix('-delta')].append(chunk['text'])
        elif kind=='usage':require(type(chunk.get('usage')) is dict,'adapter usage shape');usage.append(chunk['usage'])
        elif kind=='finish':
            reason=chunk.get('reason');require(type(reason) is dict,'adapter finish shape')
            finish.append({'kind':label(reason.get('kind'),{'error','aborted','stop','max-tokens'}),
                           'failure_code':label((reason.get('failure') or {}).get('code'),NATIVE_CODES)})
        elif kind not in ('block-start','block-end'):signals.append('unsupported_adapter_event')
    if len(finish)!=1:signals.append('adapter_terminal_count')
    if len(usage)>1:signals.append('adapter_usage_count')
    adapter_error=any(x['kind'] in ('error','aborted') for x in finish)
    if p['errors'] and not adapter_error:signals.append('raw_error_adapter_success_conflict')
    if adapter_error and not p['errors']:signals.append('adapter_error_without_raw_error')
    for kind in parts:
        if ''.join(parts[kind])!=''.join(adapter_parts[kind]):signals.append('raw_adapter_'+kind+'_conflict')
    native_equal=None;native_codes=[]
    if native is None:signals.append('native_missing')
    else:
        native_equal=native['chunks']==chunks
        if not native_equal:signals.append('adapter_native_conflict')
        native_codes=[label(x,NATIVE_CODES) for x in native['codes']]
        if (native['terminal']=='error')!=adapter_error:signals.append('native_terminal_conflict')
        if native['content'] is not None and not adapter_error:
            for kind in parts:
                seen=''.join(x.get('text','') for x in native['content'] if x.get('type')==kind)
                if seen!=''.join(parts[kind]):signals.append('native_content_conflict')
    mapped_usage=None;usage_consistent=None
    if raw_usage:
        try:mapped_usage=[usage_mapping(u) for u in raw_usage]
        except (ContractError,KeyError,TypeError):signals.append('raw_usage_integrity_conflict')
        if mapped_usage is not None:
            usage_consistent=mapped_usage==usage
            if not usage_consistent:signals.append('raw_adapter_usage_conflict')
            if native is not None and native['usage'] is not None and mapped_usage!=[native['usage']]:signals.append('raw_native_usage_conflict')
    if not raw_usage and usage:signals.append('adapter_usage_without_raw_source')
    if p['finishes'] and finish:
        expected={'stop':'stop','length':'max-tokens'}.get(p['finishes'][0]['kind'])
        if finish[0]['kind']!=expected:signals.append('raw_adapter_finish_conflict')
    deadlines=response.get('deadlines') or {};trigger=deadlines.get('trigger')
    require(trigger in (None,'fetch_headers','fetch_total'),'unknown deadline trigger')
    if trigger:
        limit=60000 if trigger=='fetch_headers' else 90000
        require(deadlines.get('headers_ms')==60000 and deadlines.get('total_ms')==90000 and
                (response.get('timings') or {}).get('total_ms',0)>=limit-250,'unsupported/forged deadline evidence')
    original=channel_audit.verdict(response)
    if original['status']=='verified':
        if op['answer'] is not None:require(op['answer']==original['text'],'native action/text mismatch')
    else:require(op['domain_receipts']==0 and not op['admitted'],'rejected content reached domain')
    require(account['state'] in ('settled','unknown','released','denied'),'unresolved accounting')
    require(account['state']=='settled' or account['trusted_usage'] is None,'untrusted accounting usage fabricated')
    if not raw_usage and account['trusted_usage'] is not None:raise ContractError('trusted usage without raw source')
    conflict=any('conflict' in s or s in ('error_with_DONE','error_with_success_finish','duplicate_DONE','duplicate_finish','duplicate_usage','data_after_DONE','duplicate_event_field','adapter_event_after_finish','adapter_terminal_count','adapter_usage_count') for s in signals)
    unsupported=any(s.startswith('unsupported_') or s in ('native_missing','event_error_without_structured_error') for s in signals)
    category=('contradictory_evidence' if conflict else 'unclassified_evidence' if unsupported else
              'http_error_observed' if response['status']>=400 else 'deadline_observed' if trigger else
              'provider_error_observed' if p['errors'] and adapter_error else
              'success_control' if original['status']=='verified' else 'incomplete_or_unclassified')
    numeric_usage=[{k:v for k,v in u.items() if k in ('inputTokens','outputTokens','totalTokens','cacheReadTokens') and type(v) is int} for u in usage]
    return {'schema':VERSION,'origin':b['origin'],'source':b['source'],'identity':ident,'bindings':b['hashes'],
        'classification':category,'signals':sorted(set(signals)),
        'transport':{'sending_recorded':b['transport']['sending'],'http_status':response['status'],
            'capture_exception_present':response.get('error') is not None,'deadline_trigger':trigger,
            'native_codes':native_codes,'native_code_source':'recorded official runtime; may derive from adapter message classification',
            'supplier_received_independently_verified':False},
        'protocol':p,'provider_declared_errors':p['errors'],
        'adapter_native':{'adapter_finish':finish,'adapter_usage_observations':numeric_usage,'native_present':native is not None,
            'native_chunks_equal':native_equal,'native_terminal':label(native['terminal'],{'completed','stop','error','aborted','max-tokens'}) if native else None,
            'content_prefix_present':bool(parts['text']),'reasoning_present':bool(parts['reasoning']),
            'raw_content_adapter_equal':''.join(parts['text'])==''.join(adapter_parts['text'])},
        'admission':{'original_audit':{k:original[k] for k in ('schema','status','category','reason') if k in original},
            'trusted_complete_text':original['status']=='verified','actually_admitted':op['admitted'],'domain_receipts':op['domain_receipts'],
            'diagnosis_grants_admission':False},
        'accounting':{'original_state':account['state'],'raw_usage_frames':len(raw_usage),'adapter_usage_present':bool(usage),
            'native_usage_present':native is not None and native['usage'] is not None,
            'raw_usage_numeric_mapping':mapped_usage,'raw_adapter_usage_consistent':usage_consistent,
            'verified_usage_preserved':account['trusted_usage'],'adapter_zero_is_trusted_usage':False,
            'ledger_reason_code':account['reason_code'],'bill':'UNVERIFIED','diagnosis_settles':False},
        'limits':LIMITS,'upstream_identity':'UNVERIFIED','retry_authorized':False,'activation':False}


def from_entry(entry,origin):
    """Authenticate controlled source before extracting a data-only observation."""
    bounded(entry)
    require(origin in ('historical_c4','local_official_runtime'),'entry origin')
    source_reader=C4_READER if origin=='historical_c4' else 'current-code-owned-runtime-verifier'
    if origin=='historical_c4':require(digest(entry)==C4_ENTRY,'C4 archived entry differs')
    else:
        cfg=entry['evidence']['ledger']['meta']['config']
        require(cfg['mode']=='robustness_rehearsal','diagnostic live input denied')
        pin=json.loads((Path(__file__).parent/'pins/c5_runtime.json').read_bytes())
        if digest(entry) in pin['entries'].values():source_reader=pin['reader_commit']
        else:
            from .transport_campaign import analyze
            analyze(entry['evidence']['dataset'],entry['evidence']['ledger'],entry['evidence']['receives'])
    evidence=entry['evidence'];ledger=evidence['ledger'];dataset=unseal(evidence['dataset'])
    source=next(iter(dataset['sources'].values()));data=parse(source['files']['evidence.json'],LIMITS['input_bytes'])
    observations=[]
    for attempt in ledger['attempts']:
        scope=attempt['scope'];op=next(o for o in data['operations'] if o['id']==attempt['id'])
        require(scope['op']==op['id'] and scope['run']==op['run'] and scope['stream']==op['stream'],'attempt/source identity')
        if origin=='local_official_runtime':
            receives=[r for r in evidence['receives'] if r['attempt']==attempt['id']]
            require(len(receives)==1 and receives[0]['raw']==attempt['request']['raw'],'local request/service binding')
            captured=receives[0]['response'];actual=attempt['response']
            require(captured['status']==actual['status'] and captured['raw']==actual['raw'] and captured['sha256']==hashlib.sha256(actual['raw'].encode()).hexdigest(),'local error response/service binding')
        occurrences=[parse(x['raw'],LIMITS['input_bytes']) for x in data['occurrences'] if x['stream']==scope['stream']]
        messages=[x for x in occurrences if x['type'] in ('assistant/message','assistant/attempt')]
        native=None
        if messages:
            event=messages[-1]['data'];stream=event.get('stream',[])
            codes=[]
            for x in occurrences:
                if x['type']=='turn/end':
                    code=(x['data'].get('reason',{}).get('error') or {}).get('code')
                    if code is not None:codes.append(code)
            native={'stream':scope['stream'],'chunks':native_chunks(stream),
                'content':event.get('message',{}).get('content'),'terminal':op['terminal'],'codes':codes,
                'usage':event.get('usage')}
        receipts=[r for r in data['domain_receipts'] if r['op']==op['id']]
        state=attempt['state'];reason=attempt.get('reason')
        # Known ledger descriptions are code-owned. Unknown free text is suppressed.
        reason_code=reason if reason in ('gateway missing/extra DONE','gateway response incomplete','gateway usage missing/ambiguous','unsupported gateway terminal') else 'other_recorded_reason' if reason else None
        body={'schema':INPUT,'origin':origin,
            'source':{'entry_sha256':digest(entry),'dataset_sha256':evidence['dataset']['sha256'],'ledger_sha256':digest(ledger),
                'reader':source_reader,
                'config_schema':ledger['meta']['config']['schema'],'native_occurrences_sha256':digest(occurrences)},
            'identity':{'attempt':attempt['id'],'run':scope['run'],'stream':scope['stream'],'seat':scope['seat'],
                'config_hash':scope['config_hash'],'request_hash':attempt['binding']['wire_hash']},
            'request':attempt['request'],'response':attempt['response'],'native':native,
            'operation':{'id':op['id'],'run':op['run'],'stream':op['stream'],'answer':op['answer'],
                'admitted':op['state']=='execution_complete' and bool(receipts),'domain_receipts':len(receipts)},
            'accounting':{'state':state,'trusted_usage':attempt['usage'],'reason_code':reason_code},
            'transport':{'sending':any(e['attempt']==attempt['id'] and e['kind']=='sending' for e in ledger['events'])}}
        observations.append(_observe(bind(body)))
    return observations
