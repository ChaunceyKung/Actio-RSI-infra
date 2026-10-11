"""Read-only C2C0 evaluation from full plan, native facts and trusted text."""
import json
from collections import Counter
from actio.contracts.json import ContractError
from actio.contracts.json import unseal
from actio.contracts.json import require
from actio.evidence.pilot_measurement import measure
from actio.profiles.suite_contract import validate_preregistration
from actio.profiles.suite_contract import config
from actio.profiles.suite_contract import LIVE
from actio.tasks.finite import get
from actio.measurement.oracle import evaluate
from actio.measurement.oracle import VERSION

def cell(value=None,reason='unobserved',applicable=True):
    return {'value':value,'state':'not_applicable' if not applicable else 'missing' if value is None else 'defined',
            'reason':reason if value is None or not applicable else None}

def aggregate(cells,unit):
    counts=Counter(c['state'] for c in cells);defined=[c['value'] for c in cells if c['state']=='defined']
    out={'unit':unit,'assigned':len(cells),'eligible':counts['defined']+counts['missing'],'not_applicable':counts['not_applicable'],
         'defined':counts['defined'],'missing':counts['missing'],'true':sum(v is True for v in defined),'false':sum(v is False for v in defined),
         'reasons':dict(Counter(c['reason'] for c in cells if c['reason']))}
    require(out['assigned']==out['eligible']+out['not_applicable'] and out['eligible']==out['defined']+out['missing'],'denominator invariant')
    return out

def metrics(c,actions,reasons):
    m=evaluate(c,actions);f=m['format'];pair_reason=next((reasons[s] for s in ('A','B') if actions.get(s) is None),None)
    if pair_reason is None and not all(f.values()):pair_reason='syntax_invalid'
    cs={'format':{s:cell(f[s],reasons[s]) for s in ('A','B')},
        'a_own':cell(m['a_own'],'syntax_invalid' if f['A'] is False else reasons['A'],f['A'] is not False),
        'b_local':cell(m['b_local'],'task_predecessor_invalid' if f['A'] is False else 'syntax_invalid' if f['B'] is False else pair_reason, f['A'] is not False and f['B'] is not False),
        'joint':cell(m['joint_achieved'],pair_reason),'utility':cell(m['utilities'],pair_reason),
        'pareto':cell(m['pareto'],pair_reason),'regret':cell(m['omniscient_regret'],pair_reason)}
    return m,cs

def failure_facts(entry,seat):
    if entry['evidence'] is None:return None
    ledger=entry['evidence']['ledger'];a=next((a for a in ledger['attempts'] if a['scope']['seat']==seat),None)
    if not a:return None
    data=json.loads(next(iter(unseal(entry['evidence']['dataset'])['sources'].values()))['files']['evidence.json'])
    op=next(o for o in data['operations'] if o['id']==a['id']);events=[json.loads(r['raw']) for r in data['occurrences'] if r['stream']==op['stream']]
    native=[e for e in events if e['type'] in ('run/failed','error') or 'error' in str(e.get('data',{})).lower() and e['type'] not in ('user/message','system/message')]
    response=a['response'] or {};evidence=json.dumps(native)+str(response.get('error'))+str(op.get('reason'))
    root='timeout' if 'TIMEOUT' in evidence or 'timeout' in evidence.lower() or 'deadline' in evidence.lower() else 'text_integrity' if (a.get('text_integrity') or {}).get('status')=='rejected' else 'accounting_unknown' if a['state']=='unknown' else None
    return {'root_cause':root,'native_failures':native,'operation_reason':op.get('reason'),
        'http_status':response.get('status') or None,'headers_observed':bool(response.get('status')),'partial_body_observed':bool(response.get('raw')),
        'response_error':response.get('error'),'deadline_observation':response.get('deadlines'),'accounting_state':a['state'],
        'supplier_received':None,'billed_cost':None,'censored':root is not None}

def analyze_pilot(value):
    b=unseal(value);require(set(b)=={'schema','preregistration','freeze','entries','phase_state'} and b['schema']=='suite-evidence.v1','suite envelope')
    pre=b['preregistration'];p=validate_preregistration(pre)
    require([e['unit'] for e in b['entries']]==p['units'],'complete suite plan missing/duplicated/changed')
    require(all(set(e)=={'unit','evidence','reason','episode_ms'} for e in b['entries']),'suite entry fields')
    require(b['phase_state'] in ('completed','stopped','first-block','local_validation'),'suite state')
    rows=[]
    for e in b['entries']:
        r=measure(e,pre,configuration=config,predicate=lambda t,a:evaluate(t['parameters'],a));c=get(e['unit']['card'])
        actions={s['seat']:s['action'] if s['admitted'] else None for s in r['seats']}
        reasons={s['seat']:('infrastructure_unknown' if s.get('accounting_state')=='unknown' else 'raw_text_untrusted' if s['protocol_error'] else 'not_started' if r['status']=='not_run' else 'not_run' if s['not_run'] else 'unobserved') for s in r['seats']}
        m,cs=metrics(c,actions,reasons)
        require(m['joint_feasible']==e['unit']['joint_feasible'],'frozen feasibility differs')
        for s in r['seats']:
            s['text_verified']=s['admitted'];s['format']=m['format'][s['seat']];s['domain_executable']=s['admitted'] and s['format'] is True
            s['failure']=failure_facts(e,s['seat'])
            if s['seat']=='B' and s['not_run'] and m['format']['A'] is False:s['not_run_reason']='task_predecessor_invalid'
        r.update(metrics=m,metric_cells=cs);rows.append(r)
    cfgs=[e['evidence']['ledger']['meta']['config'] for e in b['entries'] if e['evidence']]
    require(len({c['authority']['id'] for c in cfgs})==len(cfgs),'reused authority')
    require(len({e['evidence']['ledger']['meta']['campaign'] for e in b['entries'] if e['evidence']})==len(cfgs),'reused ledger')
    require(len({c['mode'] for c in cfgs})<=1,'mixed execution modes')
    seats=[s for r in rows for s in r['seats']]
    live=b['freeze'] is not None or any(c['mode']==LIVE for c in cfgs)
    if live:
        f=b['freeze'];require(type(f) is dict and set(f)=={'commit','preregistration_hash','remote_main','remote_branch','verified_utc','first_intent_utc'},'suite publication fields')
        require(len(f['commit'])==40 and f['commit']==f['remote_main']==f['remote_branch'] and f['preregistration_hash']==pre['sha256'],'suite publication mismatch')
        require(f['verified_utc']<=f['first_intent_utc'] and all(s.get('started_utc') is None or s['started_utc']>=f['first_intent_utc'] for s in seats),'publication/intent/send order')
        require(all(c['mode']==LIVE for c in cfgs),'live mode')
    if b['phase_state']!='local_validation':
        seen_missing=False
        for e in b['entries']:
            if e['evidence'] is None:seen_missing=True
            else:require(not seen_missing,'non-prefix execution')
        require(b['phase_state']!='completed' or not seen_missing,'completed with unrun episodes')
        failures=[i for i,r in enumerate(rows) if r['status']=='observed' and (r['reason'] is not None or any(s['protocol_error'] for s in r['seats']))]
        require(not failures or failures==[sum(r['status']=='observed' for r in rows)-1] and b['phase_state']=='stopped','continued after infrastructure failure')
    strata=[]
    for family in ('scheduling','bargaining'):
        for model in ('gpt-5.6','claude-sonnet-4-6'):
            group=[r for r in rows if r['unit']['family']==family and r['unit']['model']==model]
            strata.append({'family':family,'route':model,'format':aggregate([r['metric_cells']['format'][s] for r in group for s in ('A','B')],'seat'),
                **{k:aggregate([r['metric_cells'][k] for r in group],'seat' if k in ('a_own','b_local') else 'episode') for k in ('a_own','b_local','joint','utility','pareto','regret')},
                'joint_by_feasibility':[{'feasible':f,**aggregate([r['metric_cells']['joint'] for r in group if r['unit']['joint_feasible']==f],'episode')} for f in (True,False)]})
    pairs=[{'block':block,'episodes':[r['unit']['id'] for r in rows if r['unit']['block']==block],
            'coverage':cell(True if all(r['metric_cells']['joint']['state']=='defined' for r in rows if r['unit']['block']==block) else None,'incomplete_route_pair')} for block in range(12)]
    usage=[s['usage'] for s in seats if s['usage'] is not None]
    counts={'planned_episodes':len(rows),'observed_episodes':sum(r['status']=='observed' for r in rows),'complete_episodes':sum(r['metric_cells']['joint']['state']=='defined' for r in rows),
        'not_run_episodes':sum(r['status']=='not_run' for r in rows),**{k:sum(s[k] for s in seats) for k in ('assigned','sent','response','terminal','admitted','not_run','protocol_error')},
        'attempted':sum(s['operation'] is not None for s in seats),'usage_responses':len(usage),'unknown':sum(s.get('accounting_state')=='unknown' for s in seats)}
    return {'schema':VERSION,'preregistration_hash':pre['sha256'],'rows':rows,'strata':strata,'pairs':pairs,'pair_coverage':aggregate([p['coverage'] for p in pairs],'pair'),
        'counts':counts,'usage':{'input_tokens':sum(u['input_tokens'] for u in usage),'output_tokens':sum(u['output_tokens'] for u in usage),
        'cost_fields':sum(u['gateway_reported_cost_raw'] is not None for u in usage),'estimated_cost':None,'billed_cost':None},
        'human_labels':0,'independent_research_units':0,'model_requests_during_measurement':0,'supplier_received':None,
        'cumulative_real_generation_attempts':76+(counts['sent'] if live else 0),'loopback_sends':0 if live else counts['sent'],
        'limits':'two task families; authored correlated cases, fixed presentations, paired gateway routes; no ranking/CI/human validity/promotion'}

def correct_c2b2(pre,report):
    """Append-only correction, after a trusted fixed historical reader reproduces report."""
    p=unseal(pre);require([r['unit'] for r in report['rows']]==p['units'],'historical full plan')
    cards={c['id']:c for c in p['cards']};out=[]
    for route in ('gpt-5.6','claude-sonnet-4-6'):
        for feasible in (True,False):
            group=[r for r in report['rows'] if r['unit']['model']==route and bool(set(cards[r['unit']['card']]['available']['A'])&set(cards[r['unit']['card']]['available']['B']))==feasible]
            out.append({'route':route,'feasible':feasible,**aggregate([cell(r['metrics']['joint_achieved'] if r['metrics'] else None,'not_started' if not r['metrics'] else 'incomplete_pair') for r in group],'episode')})
    return out

def verify(value):
    try:return {'valid':True,'report':analyze_pilot(value),'credential_reads':0,'network_requests':0,'workers_started':0}
    except (ContractError,KeyError,TypeError,ValueError,OSError,AttributeError,IndexError,StopIteration) as e:
        return {'valid':False,'error':str(e)[:512],'credential_reads':0,'network_requests':0,'workers_started':0}
