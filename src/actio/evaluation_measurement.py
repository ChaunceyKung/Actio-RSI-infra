"""v2 measurements: observed bad behavior does not imply missing infrastructure."""
import copy
import json
import uuid
from .common import digest
from .eval_contract import unseal
from .transport_contract import require
from .pilot_measurement import measure
from .suite_measurement import cell, aggregate
from .suite_tasks import get, observation
from .suite_oracle import evaluate
from .candidate_tasks import payload
from .candidate_measurement import source, facts
from .channel_audit import audit
from . import evaluation_campaign as contract


def metric_cells(c,actions,reasons):
    m=evaluate(c,actions);f=m['format'];invalid=f['A'] is False or f['B'] is False
    pair_reason='invalid_action' if invalid else next((reasons[s] for s in ('A','B') if actions.get(s) is None),None)
    # A lawful refusal (required by B's own/public rule) is true here. An
    # arbitrary refusal of a permitted proposal still violates the frozen
    # "accept exactly when" public rule; grammar alone is not rule compliance.
    m['local_hard']={'A':m['a_own'],'B':m['b_local']}
    out={}
    for s in ('A','B'):
        skip=s=='B' and f['A'] is False
        reason='task_predecessor_invalid' if skip else reasons[s]
        out['format_'+s]=cell(f[s],reason,not skip)
        out['local_hard_'+s]=cell(m['local_hard'][s],reason if f[s] is not False else 'syntax_invalid',not skip and f[s] is not False)
    out['b_response_rule']=cell(m['b_local'],pair_reason,not invalid)
    for key,value in [('joint',m['joint_achieved']),('utility_A',None if m['utilities'] is None else m['utilities']['A']),
                      ('utility_B',None if m['utilities'] is None else m['utilities']['B']),('pareto',m['pareto']),('regret',m['omniscient_regret'])]:
        out[key]=cell(value,pair_reason,not invalid)
    return m,out


def decision_state(static_valid,technical_complete,violations):
    return ('reject' if not static_valid else 'infrastructure_failure' if not technical_complete
            else 'reject' if violations else 'insufficient_evidence')


def normalized_request(attempt,m,seat,actions):
    request=attempt['request'];wire=json.loads(request['raw']);prepared=copy.deepcopy(request['prepared'])
    for message in prepared['messages']:
        mid=message.pop('id');require(uuid.UUID(mid).version==4 and mid not in request['raw'],'only non-wire UUID4 normalization')
    prior=[] if seat=='A' else [actions['A']]
    expected=payload(m,seat,[observation(m,seat,prior[:i]) for i in range(len(prior)+1)])
    require(json.loads(wire['messages'][1]['content'])==expected,'wire does not follow actual own-arm history')
    require(json.loads(prepared['messages'][1]['content'][0]['text'])==expected,'prepared actual history')
    other='B' if seat=='A' else 'A';altered=copy.deepcopy(m)
    altered['task']['body']['seats'][other]['private']={'counterfactual':'hidden'}
    hidden=payload(altered,seat,[observation(altered,seat,prior[:i]) for i in range(len(prior)+1)])
    require(hidden==expected,'hidden state leaked into own wire')
    wire['messages'][1]['content']='RENDERED_INPUT';prepared['messages'][1]['content']=[{'type':'text','text':'RENDERED_INPUT'}]
    return expected,wire,prepared


def intervention(entries,rows):
    validated={};refs=[]
    for e,r in zip(entries,rows):
        if not e['evidence']:continue
        data=source(e);m=json.loads(data['run']['input']);ledger=e['evidence']['ledger'];cfg=ledger['meta']['config']
        actions={s['seat']:s['action'] for s in r['seats']};requests={}
        for a in ledger['attempts']:
            if a['request']:
                seat=a['scope']['seat'];requests[seat]=normalized_request(a,m,seat,actions)
        validated[r['unit']['id']]=(m,requests,ledger)
        refs.append({'unit':r['unit'],'run':data['run']['id'],'request':data['run']['request_key'],
            'ledger_campaign':ledger['meta']['campaign'],'authority':cfg['authority']['id'],
            'dataset_hash':e['evidence']['dataset']['sha256'],'ledger_hash':digest(ledger),
            'scaffold_binding':m['transport']['scaffold_binding'],'initial_memory_hash':digest(m['memory']),
            'specs':m['agents'],'pins':m['pins'],'operations':[o['id'] for o in data['operations']],
            'actual_history_checked':list(requests),'hidden_counterfactual_checked':list(requests),
            'cleanup':[{'job':w['job'],'state':w['state'],'report':json.loads(w['report'])} for w in data['workers']]})
    for field in ('run','ledger_campaign','authority'):
        require(len({r[field] for r in refs})==len(refs),'execution identity reused')
    pairs=[]
    for block in range(12):
        group={r['unit']['arm']:r for r in rows if r['unit']['block']==block}
        require(set(group)=={'baseline','candidate'},'two assigned arms required')
        br,cr=group['baseline'],group['candidate'];require(br['unit']['pair']==cr['unit']['pair'],'pair identity')
        checks=[]
        if all(r['unit']['id'] in validated for r in (br,cr)):
            bm,breq,bl=validated[br['unit']['id']];cm,creq,cl=validated[cr['unit']['id']]
            require(bm['agents']==cm['agents'] and bm['memory']==cm['memory'],'cross-arm specs/initial memory')
            for seat in ('A','B'):
                if seat not in breq or seat not in creq:continue
                bt,bw,bp=copy.deepcopy(breq[seat]);ct,cw,cp=copy.deepcopy(creq[seat])
                same_a=br['seats'][0]['action']==cr['seats'][0]['action']
                if seat=='A':
                    require(bt.pop('subordinate_scaffold')==contract.baseline()['artifact']['scaffold'],'B0 scaffold')
                    require(ct.pop('subordinate_scaffold')==contract.candidate()['artifact']['scaffold'],'C1 scaffold')
                else:
                    if same_a:require(bt==ct,'same A requires identical B input')
                    for view in (bt,ct):
                        obs=[json.loads(x) for x in view['observations']]
                        for item in obs:item['public_actions']=[]
                        view['observations']=obs
                require(bt==ct and bw==cw and bp==cp,'intervention outside A scaffold or actual public history')
                checks.append({'seat':seat,'direct_A_checklist_only':seat=='A','actual_history_recomputed':True,
                    'B_nonhistory_equal':seat=='B','same_A_B_invariance_checked':seat=='B' and same_a,
                    'different_A_history_checked':seat=='B' and not same_a,
                    'wire_hashes':{arm:next(a['binding']['wire_hash'] for a in ledger['attempts'] if a['scope']['seat']==seat)
                        for arm,ledger in [('baseline',bl),('candidate',cl)]}})
        metric_pairs={}
        for name in br['metric_cells']:
            bc,cc=br['metric_cells'][name],cr['metric_cells'][name]
            applicable=bc['state']!='not_applicable' and cc['state']!='not_applicable'
            comparable=applicable and bc['state']==cc['state']=='defined'
            delta=(int(cc['value'])-int(bc['value']) if isinstance(bc['value'],bool) else cc['value']-bc['value']) if comparable else None
            metric_pairs[name]={'baseline':bc,'candidate':cc,'delta':delta,
                'coverage':cell(True if comparable else None,'arm_metric_not_applicable' if not applicable else 'arm_metric_missing',applicable)}
        resolved=all(r['execution_resolved'] and r['technical_evidence_complete'] for r in group.values())
        pairs.append({'block':block,'card':br['unit']['card'],'family':br['unit']['family'],'pair_hash':br['unit']['pair_hash'],
            'arm_pair_execution_resolved':resolved,'coverage':cell(True if resolved else None,'unresolved_arm'),
            'metrics':metric_pairs,'wire':checks})
    return pairs,refs


def analyze_pilot(value):
    b=unseal(value);require(set(b)=={'schema','preregistration','freeze','entries','phase_state'} and b['schema']==contract.EVIDENCE,'evaluation evidence envelope')
    pre=b['preregistration'];p=contract.validate_preregistration(pre)
    require([e['unit'] for e in b['entries']]==p['units'],'complete ordered evaluation plan')
    require(all(set(e)=={'unit','evidence','reason','episode_ms'} for e in b['entries']),'evaluation entry fields')
    require(b['phase_state'] in ('completed','stopped','first-block','local_validation'),'evaluation phase state')
    rows=[]
    for e in b['entries']:
        r=measure(e,pre,configuration=contract.config,predicate=lambda t,a:evaluate(t['parameters'],a),reader=audit)
        actions={s['seat']:s['action'] if s['admitted'] else None for s in r['seats']}
        reasons={s['seat']:'protocol_rejected' if s['protocol_error'] else 'not_run' if s['not_run'] else 'unobserved' for s in r['seats']}
        m,cs=metric_cells(get(e['unit']['card']),actions,reasons)
        for s in r['seats']:
            seat=s['seat'];skip=seat=='B' and m['format']['A'] is False
            s.update(text_verified=s['admitted'],format_valid=m['format'][seat],domain_executable=s['admitted'] and m['format'][seat] is True,
                local_hard=m['local_hard'][seat],failure=facts(e,seat,m['format'][seat],m['local_hard'][seat]))
            if skip:
                require(s['not_run'],'invalid predecessor must skip B');s['not_run_reason']='task_predecessor_invalid'
            s['technical_evidence_complete']=bool(skip or s['admitted'] and s['response'] and s['usage'] is not None and s.get('accounting_state')=='settled' and s['receipt'])
            cs['text_verified_'+seat]=cell(True if s['admitted'] else False if s['operation'] else None,reasons[seat],not skip)
            cs['domain_executable_'+seat]=cell(m['format'][seat],reasons[seat],not skip)
        technical=e['evidence'] is not None and r['reason'] is None and all(s['technical_evidence_complete'] for s in r['seats'])
        resolved=technical and r['task_outcome'] in ('success','task_failure')
        r.update(metrics=m,metric_cells=cs,technical_evidence_complete=technical,execution_resolved=resolved);rows.append(r)
    cfgs=[e['evidence']['ledger']['meta']['config'] for e in b['entries'] if e['evidence']]
    require(len({c['mode'] for c in cfgs})<=1,'mixed live/rehearsal')
    live=b['freeze'] is not None or any(c['mode']==contract.LIVE for c in cfgs)
    if live:
        f=b['freeze'];require(type(f) is dict and set(f)=={'commit','remote_main','remote_branch','preregistration_hash','verified_utc','first_intent_utc'},'publication freeze fields')
        require(len(f['commit'])==40 and f['commit']==f['remote_main']==f['remote_branch'] and f['preregistration_hash']==pre['sha256'],'publication freeze mismatch')
        require(f['verified_utc']<=f['first_intent_utc'] and all(s.get('started_utc') is None or s['started_utc']>=f['first_intent_utc'] for r in rows for s in r['seats']),'publication timing')
        require(all(c['mode']==contract.LIVE for c in cfgs),'live mode mismatch')
    if b['phase_state']!='local_validation':
        seen=False
        for e in b['entries']:
            if e['evidence'] is None:seen=True
            else:require(not seen,'non-prefix execution')
        observed=[i for i,r in enumerate(rows) if r['status']=='observed']
        failed=[i for i in observed if not rows[i]['technical_evidence_complete'] or not rows[i]['execution_resolved']]
        require(not failed or failed==[observed[-1]] and b['phase_state']=='stopped','continued after technical failure')
        require(b['phase_state']!='completed' or not seen and not failed,'false completed state')
    pairs,refs=intervention(b['entries'],rows);seats=[s for r in rows for s in r['seats']];usage=[s['usage'] for s in seats if s['usage'] is not None]
    counts={'planned_episodes':24,'observed_episodes':len(refs),'not_run_episodes':24-len(refs),
        'technical_complete_episodes':sum(r['technical_evidence_complete'] for r in rows),'execution_resolved_episodes':sum(r['execution_resolved'] for r in rows),
        **{k:sum(s[k] for s in seats) for k in ('assigned','sent','response','terminal','admitted','not_run','protocol_error')},
        'attempted':sum(s['operation'] is not None for s in seats),'usage_responses':len(usage),'unknown':sum(s.get('accounting_state')=='unknown' for s in seats),
        'task_predecessor_invalid':sum(s.get('not_run_reason')=='task_predecessor_invalid' for s in seats)}
    pair_metrics={k:aggregate([p['metrics'][k]['coverage'] for p in pairs],'arm_pair') for k in rows[0]['metric_cells']}
    strata=[]
    for family in ('scheduling','bargaining'):
        for arm in ('baseline','candidate'):
            for feasible in (None,True,False):
                group=[r for r in rows if r['unit']['family']==family and r['unit']['arm']==arm and (feasible is None or r['unit']['joint_feasible']==feasible)]
                strata.append({'family':family,'arm':arm,'feasible':feasible,'metrics':{k:aggregate([r['metric_cells'][k] for r in group],'episode') for k in rows[0]['metric_cells']}})
    violations={arm:[{'unit':r['unit']['id'],'metric':k} for r in rows if r['unit']['arm']==arm for k,c in r['metric_cells'].items()
        if k in ('format_A','format_B','local_hard_A','local_hard_B') and c['state']=='defined' and c['value'] is False] for arm in ('baseline','candidate')}
    complete=all(r['technical_evidence_complete'] and r['execution_resolved'] for r in rows)
    return {'schema':'candidate-measurement.v2','preregistration_hash':pre['sha256'],'rows':rows,'counts':counts,'pairs':pairs,'strata':strata,
        'pair_coverage':aggregate([p['coverage'] for p in pairs],'arm_pair_execution'),'metric_pair_coverage':pair_metrics,'execution_refs':refs,
        'technical_evidence_complete':complete,'engineering':'PASS' if complete else 'INCOMPLETE','violations':violations,
        'candidate_decision':decision_state(True,complete,violations['candidate']),'baseline_role':'reference_only',
        'evidence_kind':'live_development_exploratory' if live else 'local_fixture','split':'development_exploratory',
        'external_provider_requests':counts['sent'] if live else 0,'loopback_sends':0 if live else counts['sent'],
        'historical_generation_attempts':91,'cumulative_real_generation_attempts':91+(counts['sent'] if live else 0),'catalog_get':1,
        'usage':{'responses':len(usage),'input_tokens':sum(u['input_tokens'] for u in usage),'output_tokens':sum(u['output_tokens'] for u in usage),
            'raw_costs':[u['gateway_reported_cost_raw'] for u in usage],'currency':None,'estimated_cost':None,'billed_cost':None,'billing_reconciled':False},
        'human_labels':0,'independent_research_units':0,'activation':False,'binary_source_mapping':'unproven','full_controller_recovery':'unsupported'}
