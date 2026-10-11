from actio.measurement.robustness_definitions import metric_definitions
"""Independent C2C4 metrics and three separately assigned comparison sets."""
import copy
import json
from actio.contracts.json import require
from actio.tasks.finite import observation
from actio.tasks.candidate import payload
from actio.evidence.candidate_measurement import source
from actio.tasks.diagnostic import visible
from actio.tasks.controls import cell
from actio.tasks.controls import aggregate
from actio.tasks.controls import diagnose_a
from actio.evidence.evaluation_measurement import metric_cells as previous_cells
from actio.evidence.evaluation_measurement import normalized_request
from actio.tasks.robustness import get


def metric_cells(c,actions,reasons):
    m,out=previous_cells(c,actions,reasons)
    d=diagnose_a(visible(c,'A'),actions.get('A'),missing_reason=reasons['A'])
    out.update({k:d[k] for k in ('conditional_offer_score','conditional_offer_gap','argmax_membership')})
    out['joint_feasible']=cell(m['joint_feasible'])
    out['omniscient_upper_bound']=cell(m['omniscient_upper_bound'])
    legal=m['format']['A'] is True
    public=own_a=own_b=None
    if legal:
        a=actions['A']
        if c['family']=='scheduling':
            slot=a[8:];public=slot in c['public']['open']
            own_a=slot in c['private']['A']['available'];own_b=slot in c['private']['B']['available']
        else:
            item,_,price,_=a.split();price=int(price)
            public=[item,price] in c['public']['allowed']
            own_a=price<=min(c['private']['A']['budget'],c['private']['A']['values'][item])
            own_b=price>=c['private']['B']['costs'][item]
    for seat in ('A','B'):
        applicable=m['format'][seat] is not False and (seat=='A' or m['format']['A'] is not False)
        defined=legal and (seat=='A' or m['format']['B'] is True)
        accept=actions.get('B')=='accept'
        out['public_hard_'+seat]=cell((public if seat=='A' else not accept or public) if defined else None,
            'invalid_action' if not applicable else reasons[seat],applicable)
        out['self_hard_'+seat]=cell((own_a if seat=='A' else not accept or own_b) if defined else None,
            'invalid_action' if not applicable else reasons[seat],applicable)
    return m,out


def coverage(cells,unit,name):
    return aggregate(cells,unit,boolean=metric_definitions()['metrics'][name]['type']=='boolean')


def strip_history(view):
    for item in view['observations']:
        obj=json.loads(item);obj['public_actions']=[]
        yield obj


def compare_metrics(left,right):
    result={}
    for name,a in left['metric_cells'].items():
        b=right['metric_cells'][name]
        applicable=a['state']!='not_applicable' and b['state']!='not_applicable'
        defined=applicable and a['state']==b['state']=='defined'
        result[name]={'left':a,'right':b,'delta':((int(b['value'])-int(a['value'])) if type(a['value']) is bool else b['value']-a['value']) if defined else None,
                      'coverage':cell(True if defined else None,'metric_not_applicable' if not applicable else 'metric_missing',applicable)}
    return result


def contrasts(rows,requests,kind):
    groups={}
    keys=('structural_group','presentation','arm') if kind=='hidden_world' else ('world','arm')
    for row in rows:groups.setdefault(tuple(row['unit'][k] for k in keys),[]).append(row)
    output=[]
    for key,members in sorted(groups.items()):
        require(len(members)==2,'complete contrast assignment')
        left,right=sorted(members,key=lambda r:r['unit']['world'] if kind=='hidden_world' else 0 if r['unit']['presentation']=='normal' else 1)
        checks=[];actions={};same_a=None
        for seat in ('A','B'):
            ls,rs=(next(s for s in row['seats'] if s['seat']==seat) for row in (left,right))
            applicable=all(s.get('not_run_reason')!='task_predecessor_invalid' for s in (ls,rs))
            observed=all(s['admitted'] for s in (ls,rs))
            equal=ls['action']==rs['action'] if observed else None
            if seat=='A':same_a=equal
            actions[seat]=cell(equal,'task_predecessor_invalid' if not applicable else 'unobserved',applicable)
            a=requests.get(left['unit']['id'],{}).get(seat);b=requests.get(right['unit']['id'],{}).get(seat)
            if a is None or b is None:continue
            av,aw,ap=copy.deepcopy(a);bv,bw,bp=copy.deepcopy(b)
            exact=a==b
            if kind=='hidden_world' and seat=='A':require(exact,'A input differs across hidden worlds')
            else:
                if kind=='presentation':
                    require(av['action_spec']['options']==bv['action_spec']['options'][::-1],'both actor options reverse exactly')
                    bv['action_spec']['options'].reverse()
                if seat=='B':
                    av['observations']=list(strip_history(av));bv['observations']=list(strip_history(bv))
                    if kind=='hidden_world':
                        for v in (av,bv):
                            for obs in v['observations']:obs['own']='AUTHENTICATED_WORLD_OWN'
                require(av==bv and aw==bw and ap==bp,'contrast changed nonpermitted input')
            checks.append({'seat':seat,'verified':True,'full_normalized_input_equal':exact,'permitted_difference':
                           'none' if kind=='hidden_world' and seat=='A' else 'B own and actual A history' if kind=='hidden_world' else 'options order and B actual A history'})
        resolved=all(r['execution_resolved'] and r['technical_evidence_complete'] for r in (left,right))
        conditional=cell(actions['B']['value'] if same_a is True else None,
                         'A_changed_post_observation' if same_a is False else 'A_unobserved' if same_a is None else actions['B']['reason'],
                         same_a is not False and actions['B']['state']!='not_applicable')
        output.append({'key':dict(zip(keys,key)),'left':left['unit']['id'],'right':right['unit']['id'],
            'execution_coverage':cell(True if resolved else None,'unresolved_episode'),'actions_equal':actions,
            'B_same_actual_A_conditional':conditional,'metrics':compare_metrics(left,right),'wire_checks':checks})
    require(len(output)==32,'32 contrasts retained')
    return {'assigned':32,'rows':output,
        'execution_coverage':aggregate([r['execution_coverage'] for r in output],kind,boolean=True),
        'action_equality':{s:aggregate([r['actions_equal'][s] for r in output],kind,boolean=True) for s in ('A','B')},
        'metric_coverage':{k:aggregate([r['metrics'][k]['coverage'] for r in output],kind,boolean=True) for k in rows[0]['metric_cells']},
        'B_same_actual_A_conditional':aggregate([r['B_same_actual_A_conditional'] for r in output],kind,boolean=True),
        'scope':'single-run descriptive; outputs may differ for equal inputs; conditional B subset is post-observation, not causal option effect'}


def analyze_pilot(value):
    from actio.profiles import robustness_campaign as contract
    from actio.evidence.evaluation_measurement import analyze_pilot as measure
    report=measure(value,contract=contract,card_get=get,metrics=metric_cells)
    rows=report['rows'];requests={}
    for entry,row in zip(value['body']['entries'],rows):
        if not entry['evidence']:continue
        data=source(entry);m=json.loads(data['run']['input']);acts={s['seat']:s['action'] for s in row['seats']}
        requests[row['unit']['id']]={}
        for attempt in entry['evidence']['ledger']['attempts']:
            if not attempt['request']:continue
            seat=attempt['scope']['seat'];req=normalized_request(attempt,m,seat,acts)
            requests[row['unit']['id']][seat]=req
            # Provenance, card identity and private state are external bindings.
            altered=copy.deepcopy(m);t=altered['task']['body']
            for k in ('id','variant','parameters','provenance','grouping'):t[k]={'counterfactual':'external'}
            other='B' if seat=='A' else 'A';t['seats'][other]['private']={'hidden':'changed'}
            altered['memory'][m['entities'][other]]={'hidden':'changed'}
            prior=[] if seat=='A' else [acts['A']]
            require(payload(altered,seat,[observation(altered,seat,prior[:i]) for i in range(len(prior)+1)])==req[0],
                    'external labels/private memory leaked into request')
        row['visible_diagnostic']=diagnose_a(visible(get(row['unit']['card']),'A'),acts.get('A'),trusted=row['seats'][0]['admitted'])
    # Type-aware denominators: integer metrics never have boolean true/false counts.
    strata=[]
    for field in ('family','structural_group','world','presentation','arm','model'):
        for key in sorted({r['unit'][field] for r in rows}):
            group=[r for r in rows if r['unit'][field]==key]
            strata.append({'field':field,'value':key,'metrics':{k:coverage([r['metric_cells'][k] for r in group],'episode',k) for k in rows[0]['metric_cells']}})
    report.update(schema='robustness-measurement.v1',split='diagnostic_development',strata=strata,
        metric_definitions=metric_definitions(),metrics={k:coverage([r['metric_cells'][k] for r in rows],'episode',k) for k in rows[0]['metric_cells']},
        comparisons={kind:contrasts(rows,requests,kind) for kind in ('hidden_world','presentation')},
        comparison_denominators={'candidate':32,'hidden_world':32,'presentation':32},eligible_for_activation=False,
        distinct_A_visible_views=16,A_input_conditions=32,independent_research_units=0,
        inference='single development observation; correlated repeats; no equivalence, ranking, causal gain or stable position preference')
    return report
