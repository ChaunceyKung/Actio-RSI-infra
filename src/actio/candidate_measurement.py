"""Independent, read-only arm comparison and structured observation semantics."""
import copy
import json
from actio.contracts.json import ContractError, digest
from actio.contracts.json import unseal
from actio.contracts.json import require
from .pilot_measurement import measure
from .suite_measurement import metrics, aggregate, cell
from actio.tasks.finite import get
from actio.measurement.oracle import evaluate
from . import candidate_campaign as contract
from actio.domain.candidate import decide
from .channel_audit import audit

FAILURE_VERSION='failure-latency-observation.v2'


def classify(attempt, operation=None, native_codes=(), *, syntax=None, hard=None):
    response=(attempt or {}).get('response') or {};integrity=(attempt or {}).get('text_integrity') or {}
    deadlines=response.get('deadlines') or {};timings=response.get('timings') or {}
    # Retain directly observed terminal fields even when the admission profile
    # rejects a different channel. These observations do not grant admission.
    from .stream_audit import strict_json
    finish_observations=[]
    for line in response.get('raw','').splitlines():
        if line.startswith('data:') and line[5:].strip()!='[DONE]':
            try:
                obj=strict_json(line[5:].strip())
                for choice in obj.get('choices',[]):
                    if choice.get('finish_reason') in ('stop','length'):finish_observations.append(choice['finish_reason'])
            except (ContractError,ValueError,TypeError,AttributeError):continue
    timeout=deadlines.get('trigger') in ('fetch_headers','fetch_total') or any(c in ('TIMEOUT','REQUEST_TIMEOUT','STREAM_IDLE_TIMEOUT') for c in native_codes)
    category='timeout' if timeout else integrity.get('category') if integrity.get('status')=='rejected' else 'accounting_unknown' if (attempt or {}).get('state')=='unknown' else 'syntax_invalid' if syntax is False else 'task_rule_violation' if hard is False else 'unknown' if operation and operation.get('terminal') not in ('completed',None) else None
    complete=bool(response.get('status')==200 and response.get('error') is None and response.get('raw','').rstrip().endswith('data: [DONE]'))
    clocks={}
    for name in ('headers_ms','first_token_ms','total_ms'):
        value=timings.get(name)
        observed=value is not None and (name!='total_ms' or complete)
        censored=not observed and timeout and value is not None
        # A missing first-token/header event has an observed elapsed lower bound
        # only if the total clock and an explicit deadline trigger were captured.
        lower=timings.get('total_ms') if timeout and not observed else None
        if lower is not None:censored=True
        clocks[name]={'state':'observed' if observed else 'right-censored' if censored else 'missing',
                      'value_ms':value if observed else None,'lower_bound_ms':lower if censored else None}
    return {'schema':FAILURE_VERSION,'category':category,'http_status':response.get('status') or None,
        'headers_observed':bool(response.get('status')),'native_codes':list(native_codes),'deadline_trigger':deadlines.get('trigger'),
        'finish':finish_observations[0] if len(finish_observations)==1 else None,'raw_finish_observations':finish_observations,
        'text_admission':integrity.get('status'),'accounting_state':(attempt or {}).get('state'),
        'domain_status':operation.get('state') if operation else None,'clocks':clocks,
        'supplier_received':None,'billed_cost':None}


def source(entry):
    return json.loads(next(iter(unseal(entry['evidence']['dataset'])['sources'].values()))['files']['evidence.json'])


def facts(entry,seat,syntax,hard):
    if entry['evidence'] is None:return classify(None,syntax=syntax,hard=hard)
    a=next((a for a in entry['evidence']['ledger']['attempts'] if a['scope']['seat']==seat),None)
    data=source(entry);op=next((o for o in data['operations'] if a and o['id']==a['id']),None);codes=[]
    for r in data['occurrences']:
        if op and r['stream']==op['stream']:
            event=json.loads(r['raw'])
            if event['type'] in ('error','run/failed'):
                d=event.get('data',{});error=d.get('error',{})
                code=d.get('code') or (error.get('code') if isinstance(error,dict) else None)
                if isinstance(code,str):codes.append(code)
    return classify(a,op,codes,syntax=syntax,hard=hard)


def comparison(entries,rows):
    pairs=[]
    for block in range(12):
        group=[(e,r) for e,r in zip(entries,rows) if r['unit']['block']==block]
        require(len(group)==2 and {r['unit']['arm'] for _,r in group}=={'baseline','candidate'},'arm denominator')
        arms={r['unit']['arm']:(e,r) for e,r in group};be,br=arms['baseline'];ce,cr=arms['candidate']
        require(br['unit']['pair']==cr['unit']['pair'],'pair identity')
        complete=all(r['metric_cells']['joint']['state']=='defined' and not any(s['protocol_error'] for s in r['seats']) for _,r in group)
        wire=None
        if be['evidence'] is not None and ce['evidence'] is not None:
            bm=json.loads(source(be)['run']['input']);cm=json.loads(source(ce)['run']['input'])
            require(bm['agents']==cm['agents'],'base spec must remain identical across arms')
            require(source(be)['run']['id']!=source(ce)['run']['id'],'independent runs')
            wire=[]
            for seat in ('A','B'):
                ba=next((a for a in be['evidence']['ledger']['attempts'] if a['scope']['seat']==seat and a['request']),None)
                ca=next((a for a in ce['evidence']['ledger']['attempts'] if a['scope']['seat']==seat and a['request']),None)
                if ba is None or ca is None:continue
                bw=json.loads(ba['request']['raw']);cw=json.loads(ca['request']['raw'])
                bp=copy.deepcopy(ba['request']['prepared']);cp=copy.deepcopy(ca['request']['prepared'])
                # SDK UUID message IDs are execution identity, removed by the
                # official wire serializer. Validate them before normalization.
                import uuid
                for prepared in (bp,cp):
                    for message in prepared['messages']:
                        require(uuid.UUID(message.pop('id')).version==4,'SDK message identity')
                bt=json.loads(bw['messages'][1]['content']);ct=json.loads(cw['messages'][1]['content'])
                if seat=='A':
                    require(bt.pop('subordinate_scaffold')=={'checklist':[]},'baseline scaffold')
                    require(ct.pop('subordinate_scaffold')==contract.candidate()['artifact']['scaffold'],'candidate scaffold')
                same_a=br['seats'][0]['action']==cr['seats'][0]['action']
                if seat=='A' or same_a:
                    require(bt==ct,'wire intervention outside A checklist')
                    bw['messages'][1]['content']=cw['messages'][1]['content']='RENDERED_INPUT'
                    bp['messages'][1]['content']=cp['messages'][1]['content']=[{'type':'text','text':'RENDERED_INPUT'}]
                    require(bw==cw and bp==cp,'prepared/full-wire noninput difference')
                wire.append({'seat':seat,'baseline_wire_hash':ba['binding']['wire_hash'],'candidate_wire_hash':ca['binding']['wire_hash'],
                             'direct_intervention_checked':seat=='A','same_A_B_invariance_checked':seat=='B' and same_a,
                             'prepared_normalization':'only independent UUID4 message IDs removed; absent from full wire'})
        delta=None
        if complete:
            delta={k: int(cr['metrics'][k])-int(br['metrics'][k]) for k in ('a_own','b_local','joint_achieved')}
            delta['format']={s:int(cr['metrics']['format'][s])-int(br['metrics']['format'][s]) for s in ('A','B')}
            delta['utilities']={s:cr['metrics']['utilities'][s]-br['metrics']['utilities'][s] for s in ('A','B')}
        pairs.append({'block':block,'card':br['unit']['card'],'family':br['unit']['family'],'pair_hash':br['unit']['pair_hash'],
            'episodes':{k:r['unit']['id'] for k,(_,r) in arms.items()},'coverage':cell(True if complete else None,'incomplete_arm_pair'),
            'raw_metrics':{k:r['metrics'] for k,(_,r) in arms.items()},'delta':delta,'wire':wire})
    return pairs


def analyze_pilot(value):
    b=unseal(value);require(set(b)=={'schema','preregistration','freeze','entries','phase_state'} and b['schema']==contract.EVIDENCE,'candidate campaign envelope')
    pre=b['preregistration'];p=contract.validate_preregistration(pre)
    require([e['unit'] for e in b['entries']]==p['units'],'complete ordered arm plan')
    require(all(set(e)=={'unit','evidence','reason','episode_ms'} for e in b['entries']),'entry fields')
    require(b['phase_state'] in ('completed','stopped','first-block','local_validation'),'phase state')
    rows=[];refs=[]
    for e in b['entries']:
        r=measure(e,pre,configuration=contract.config,predicate=lambda t,a:evaluate(t['parameters'],a),reader=audit)
        actions={s['seat']:s['action'] if s['admitted'] else None for s in r['seats']}
        reasons={s['seat']:'protocol_rejected' if s['protocol_error'] else 'not_run' if s['not_run'] else 'unobserved' for s in r['seats']}
        m,cs=metrics(get(e['unit']['card']),actions,reasons)
        for s in r['seats']:
            s['failure']=facts(e,s['seat'],m['format'][s['seat']],m['a_own' if s['seat']=='A' else 'b_local'])
            if s['seat']=='B' and s['not_run'] and m['format']['A'] is False:s['not_run_reason']='task_predecessor_invalid'
        r.update(metrics=m,metric_cells=cs);rows.append(r)
        if e['evidence']:
            d=source(e);manifest=json.loads(d['run']['input']);ledger=e['evidence']['ledger']
            refs.append({'unit':e['unit'],'run':d['run']['id'],'request':d['run']['request_key'],'ledger_campaign':ledger['meta']['campaign'],
                'authority':ledger['meta']['config']['authority']['id'],'dataset_hash':e['evidence']['dataset']['sha256'],
                'ledger_hash':digest(ledger),'scaffold_binding':manifest['transport']['scaffold_binding'],
                'initial_memory_hash':digest(manifest['memory']),'specs':manifest['agents'],'pins':manifest['pins'],
                'operations':[o['id'] for o in d['operations']],'cleanup':[{'job':w['job'],'state':w['state'],'report':json.loads(w['report'])} for w in d['workers']]})
    for field in ('run','ledger_campaign','authority'):require(len({r[field] for r in refs})==len(refs),'execution identity reused')
    if b['phase_state']!='local_validation':
        seen_missing=False
        for e in b['entries']:
            if e['evidence'] is None:seen_missing=True
            else:require(not seen_missing,'non-prefix execution')
        require(b['phase_state']!='completed' or not seen_missing,'completed with unrun')
        failed=[i for i,r in enumerate(rows) if r['status']=='observed' and (r['reason'] or any(s['protocol_error'] for s in r['seats']))]
        require(not failed or failed==[len(refs)-1] and b['phase_state']=='stopped','continued after infrastructure failure')
    if b['freeze']:
        f=b['freeze'];require(f['commit']==f['remote_main']==f['remote_branch'] and len(f['commit'])==40 and f['preregistration_hash']==pre['sha256'],'publication freeze')
        require(f['verified_utc']<=f['first_intent_utc'] and all(s.get('started_utc') is None or f['first_intent_utc']<=s['started_utc'] for r in rows for s in r['seats']),'publication timing')
    seats=[s for r in rows for s in r['seats']];usage=[s['usage'] for s in seats if s['usage'] is not None]
    counts={'planned_episodes':24,'observed_episodes':len(refs),'complete_episodes':sum(r['metric_cells']['joint']['state']=='defined' for r in rows),
        'not_run_episodes':24-len(refs),**{k:sum(s[k] for s in seats) for k in ('assigned','sent','response','terminal','admitted','not_run','protocol_error')},
        'usage_responses':len(usage),'unknown':sum(s.get('accounting_state')=='unknown' for s in seats)}
    pairs=comparison(b['entries'],rows);coverage=aggregate([p['coverage'] for p in pairs],'arm_pair')
    strata=[]
    for family in ('scheduling','bargaining'):
        for arm in ('baseline','candidate'):
            group=[r for r in rows if r['unit']['family']==family and r['unit']['arm']==arm]
            strata.append({'family':family,'arm':arm,'format':aggregate([r['metric_cells']['format'][s] for r in group for s in ('A','B')],'seat'),
                **{k:aggregate([r['metric_cells'][k] for r in group],'episode' if k in ('joint','utility') else 'seat') for k in ('a_own','b_local','joint','utility')}})
    complete=counts['complete_episodes']==24 and coverage['defined']==12 and counts['protocol_error']==0 and not any(r['reason'] for r in rows)
    decision=decide(static_valid=True,complete=complete,evidence_kind='local_fixture',diagnostics={'counts':counts,'arm_pair_coverage':coverage,'report_scope':'engineering fixture only'})
    return {'schema':'candidate-measurement.v1','preregistration_hash':pre['sha256'],'counts':counts,'rows':rows,'pairs':pairs,'strata':strata,'pair_coverage':coverage,
        'execution_refs':refs,'decision':decision,'engineering':'PASS' if complete else 'INCOMPLETE','human_labels':0,'independent_research_units':0,
        'external_provider_requests':0,'historical_generation_attempts':91,'catalog_get':1,'usage':{'responses':len(usage),'billed_cost':None},
        'binary_source_mapping':'unproven','full_controller_recovery':'unsupported','activation':False}


def verify(value):
    try:return {'valid':True,'report':analyze_pilot(value),'credential_reads':0,'network_requests':0,'workers_started':0}
    except (ContractError,KeyError,TypeError,ValueError,OSError,AttributeError,IndexError,StopIteration) as e:
        return {'valid':False,'error':str(e)[:512],'credential_reads':0,'network_requests':0,'workers_started':0}
