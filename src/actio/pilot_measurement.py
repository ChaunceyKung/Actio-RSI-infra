"""Pure deterministic measurement of frozen constraints and observed actions."""
import json
from .common import digest,ContractError
from .eval_contract import seal,unseal
from .transport_contract import require
from .transport_campaign import analyze
from .pilot_contract import validate_preregistration,config
from .stream_audit import audit

VERSION='scheduling-measurement.v1'

def predicates(task,actions):
    """Independent set predicates: deliberately no GM task_result or outcome input."""
    av={s:set(task['seats'][s]['private']['available']) for s in ('A','B')}
    a,b=(actions.get(s) for s in ('A','B'))
    legal={s:None if actions.get(s) is None else actions[s] in task['action_specs'][s]['options'] for s in ('A','B')}
    slot=a[8:] if legal['A'] else None
    return {'format':legal,'a_own':None if slot is None else slot in av['A'],
            'b_local':None if slot is None or not legal['B'] else (b=='accept')==(slot in av['B']),
            'joint_feasible':bool(av['A']&av['B']),
            'joint_achieved':None if slot is None or not legal['B'] else b=='accept' and slot in av['A'] and slot in av['B'],
            'goal':'NOT_CALIBRATED','relationship':'NOT_CALIBRATED'}

def measure(entry,pre,configuration=None,predicate=None):
    unit=entry['unit'];bundle=entry['evidence']
    if bundle is None:
        require(type(entry['reason']) is str and bool(entry['reason']),'not_run reason required')
        return {'unit':unit,'status':'not_run','reason':entry['reason'],'seats':[{'seat':s,'assigned':True,'sent':False,'response':False,'terminal':False,'admitted':False,'not_run':True,'protocol_error':False,'action':None,'usage':None,'timings':None,'operation':None,'occurrences':[],'receipt':None} for s in ('A','B')],
                'metrics':None,'episode_ms':None,'world_effects':0,'task_outcome':None}
    require(set(bundle)=={'dataset','ledger','receives'},'unit evidence fields')
    ledger=bundle['ledger'];cfg=ledger['meta']['config'];require(cfg['experiment']=={'preregistration_hash':pre['sha256'],'unit':unit},'unit/prereg/config mismatch')
    require(cfg==(configuration or config)(unit['id'],mode=cfg['mode'],endpoint=cfg['endpoint'],authority=cfg['authority']),'unit config/model binding')
    report=analyze(bundle['dataset'],ledger,bundle['receives']);sources=unseal(bundle['dataset'])['sources']
    require(len(sources)==1,'one episode per child ledger')
    source=next(iter(sources.values()));data=json.loads(source['files']['evidence.json'])
    m=json.loads(data['run']['input']);task=m['task']['body'];require(task['id']==unit['card'],'unit task binding')
    streams={s['id']:s for s in data['streams']};ops=data['operations'];attempts={a['id']:a for a in ledger['attempts']};rows=[];actions={}
    for seat in ('A','B'):
        selected=[o for o in ops if streams[o['stream']]['agent']==m['entities'][seat]];require(len(selected)<=1,'multiple seat operations')
        op=selected[0] if selected else None;a=attempts.get(op['id']) if op else None
        sent=bool(a and any(e['kind']=='sending' and e['attempt']==a['id'] for e in ledger['events']))
        response=bool(a and a['response'] and a['response']['status']);terminal=bool(op and op['terminal']=='completed' and op['barrier'])
        integrity=bool(a and (a['text_integrity'] or {}).get('status')=='verified');admitted=bool(terminal and integrity and a['usage'] is not None and op['answer'] is not None)
        if admitted or configuration and terminal and integrity and op['answer'] is not None:
            audit(a['response'],op['answer'],require_bytes=True);actions[seat]=op['answer']
            if configuration:admitted=True
        receipt=next((r for r in data['domain_receipts'] if op and r['op']==op['id']),None)
        native=[{'stream':r['stream'],'seq':r['seq'],'raw_hash':r['raw_hash']} for r in data['occurrences'] if op and r['stream']==op['stream'] and json.loads(r['raw'])['type']=='assistant/message']
        rows.append({'seat':seat,'assigned':True,'sent':sent,'response':response,'terminal':terminal,'admitted':admitted,
                     'not_run':op is None,'protocol_error':bool(a and (a['state']=='unknown' or not integrity)),
                     'not_run_reason':('A has no admitted legal action or earlier infrastructure failure' if op is None else None),
                     'action':op['answer'] if op else None,'usage':a['usage'] if a else None,'accounting_state':a['state'] if a else None,
                     'text_integrity':a['text_integrity'] if a else None,'timings':a['response'].get('timings') if a and a['response'] else None,
                     'started_utc':a['response'].get('started_utc') if a and a['response'] else None,
                     'http_date':a['response'].get('http_date') if a and a['response'] else None,
                     'http_request_id':a['response'].get('http_request_id') if a and a['response'] else None,
                     'route_observation':a['usage']['provider_identity'] if a and a['usage'] else None,
                     'operation':op['id'] if op else None,'occurrences':native,'receipt':receipt})
    return {'unit':unit,'status':'observed','reason':entry['reason'],'seats':rows,'metrics':(predicate or predicates)(task,actions),
            'episode_ms':entry['episode_ms'],'world_effects':len(data['world']),'task_outcome':next(iter(report['runs'].values()))['task_outcome']}

def analyze_pilot(value):
    b=unseal(value);require(set(b)=={'schema','preregistration','freeze','entries','phase_state'} and b['schema']=='pilot-evidence.v1','pilot evidence schema')
    pre=b['preregistration'];p=validate_preregistration(pre)
    require([r['unit'] for r in b['entries']]==p['units'],'complete ordered plan missing/duplicated/changed')
    require(all(set(e)=={'unit','evidence','reason','episode_ms'} for e in b['entries']),'pilot entry fields')
    require(b['phase_state'] in ('completed','stopped','first-block','local_validation'),'pilot status')
    rows=[measure(e,pre) for e in b['entries']];seats=[s for r in rows for s in r['seats']]
    cfgs=[e['evidence']['ledger']['meta']['config'] for e in b['entries'] if e['evidence']]
    require(len({c['authority']['id'] for c in cfgs})==len(cfgs),'child authority reused')
    require(len({e['evidence']['ledger']['meta']['campaign'] for e in b['entries'] if e['evidence']})==len(cfgs),'child campaign reused')
    live=b['freeze'] is not None or any(c['mode']=='tokenkey_pilot_live' for c in cfgs)
    if live:
        f=b['freeze'];require(set(f)=={'commit','preregistration_hash','remote_main','remote_branch','verified_utc','first_intent_utc'},'publication freeze fields')
        require(len(f['commit'])==40 and f['commit']==f['remote_main']==f['remote_branch'] and f['preregistration_hash']==pre['sha256'],'published freeze mismatch')
        require(f['verified_utc']<=f['first_intent_utc'],'intent predates remote verification')
        require(all(s['started_utc'] is None or f['first_intent_utc']<=s['started_utc'] for s in seats if 'started_utc' in s),'send predates intent')
        require(all(c['mode']=='tokenkey_pilot_live' for c in cfgs),'mixed live/rehearsal')
        seen_missing=False
        for e in b['entries']:
            if e['evidence'] is None:seen_missing=True
            else:require(not seen_missing,'non-prefix pilot execution')
        require(b['phase_state']!='completed' or not seen_missing,'completed pilot has unrun episodes')
        failed=[i for i,r in enumerate(rows) if r['status']=='observed' and (r['reason'] is not None or any(s['protocol_error'] for s in r['seats']))]
        require(not failed or failed==[sum(r['status']=='observed' for r in rows)-1] and b['phase_state']=='stopped','continued after infrastructure stop')
    metrics={}
    for model in ('gpt-5.6','claude-sonnet-4-6'):
        group=[r for r in rows if r['unit']['model']==model];available=[r['metrics'] for r in group if r['metrics'] is not None]
        def ratio(values):return {'true':sum(v is True for v in values),'denominator':sum(v is not None for v in values),'missing':sum(v is None for v in values)}
        missing=len(group)-len(available)
        metrics[model]={'assigned_episodes':len(group),'observed_episodes':len(available),
            'format':ratio([v for m in available for v in m['format'].values()]+[None]*2*missing),
            **{k:ratio([m[k] for m in available]+[None]*missing) for k in ('a_own','b_local')},
            'joint_by_feasibility':{str(feasible):ratio([m['joint_achieved'] for m in available if m['joint_feasible']==feasible]) for feasible in (True,False)}}
    usage=[s['usage'] for s in seats if s['usage'] is not None]
    return {'schema':VERSION,'preregistration_hash':pre['sha256'],'rows':rows,'metrics_by_route':metrics,
            'counts':{'planned_episodes':32,'observed_episodes':sum(r['status']=='observed' for r in rows),
                'not_run_episodes':sum(r['status']=='not_run' for r in rows),
                **{k:sum(s[k] for s in seats) for k in ('assigned','sent','response','terminal','admitted','not_run','protocol_error')},
                'attempted':sum(s['operation'] is not None for s in seats),
                'usage_responses':len(usage),'unknown':sum(s.get('accounting_state')=='unknown' for s in seats)},
            'usage':{'input_tokens':sum(u['input_tokens'] for u in usage),'output_tokens':sum(u['output_tokens'] for u in usage),
                     'cost_fields':sum(u['gateway_reported_cost_raw'] is not None for u in usage),'estimated_cost':None,'billed_cost':None},
            'supplier_received':None,'independent_research_units':0,'model_requests_during_measurement':0,
            'limits':'one family, four instances/two symmetries, paired routes, joint presentation factor, repeated correlated observations; no ranking/CI/promotion'}

def verify(value):
    try:return {'valid':True,'report':analyze_pilot(value),'credential_reads':0,'network_requests':0,'workers_started':0}
    except (ContractError,KeyError,TypeError,ValueError,OSError,AttributeError,IndexError,StopIteration) as e:
        return {'valid':False,'error':str(e)[:512],'credential_reads':0,'network_requests':0,'workers_started':0}
