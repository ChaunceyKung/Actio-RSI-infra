"""Evaluation facts owned by the same SQLite Store; legacy candidate facts persist."""
import json
from actio.contracts.json import canonical, digest
from actio.contracts.json import seal, unseal
from actio.contracts.json import require
from . import candidate_store as legacy
from . import evaluation_campaign as contract

TABLES=('evaluation','evaluation_binding','evaluation_event','evaluation_decision','evaluation_migration')
LEGACY_ID='phase1c2c1-local-assessment'


def plan(pre,kind):
    from . import evaluation_history
    if pre.get('sha256')==evaluation_history.PLAN:
        return evaluation_history.plan(pre,kind)
    selected=contract
    if pre.get('body',{}).get('schema')=='robustness-execution-plan.v1':
        from . import robustness_campaign as selected
    p=selected.validate_preregistration(pre)
    require(kind in ('live_development_exploratory','local_fixture'),'evaluation evidence kind')
    return {'schema':'candidate-evaluation.v1','id':p['evaluation_namespace']+':'+kind,
        'evidence_kind':kind,'plan':pre,'policy':selected.POLICY,'policy_hash':digest(selected.POLICY),
        'dataset_hash':p['cards_hash'],'source_hash':digest(p['implementation']),
        'baseline':digest(contract.baseline()),'candidate':digest(contract.candidate()),
        'claim_namespace':p['evaluation_namespace']+':'+kind,'eligible_for_activation':False}


def event(s,eid,state,body):
    s.db.execute('INSERT INTO evaluation_event(evaluation,state,body) VALUES(?,?,?)',(eid,state,canonical(body)))


def register(s,body):
    require(s.version==4 and body==plan(body['plan'],body['evidence_kind']),'explicit frozen evaluation')
    with s.tx():
        old=s.row('SELECT body FROM evaluation WHERE id=?',(body['id'],))
        if old:
            require(old['body']==canonical(body),'evaluation identity conflict');return body['id']
        s.db.execute('INSERT INTO evaluation VALUES(?,?)',(body['id'],canonical(body)))
        for role in ('baseline','candidate'):
            c=s.row('SELECT * FROM candidate WHERE id=?',(body[role],))
            require(c and json.loads(c['validation'])['valid'],'statically validated immutable candidate required')
            binding={'schema':'evaluation-binding.v1','evaluation':body['id'],'candidate':body[role],'role':role,
                'plan_hash':body['plan']['sha256'],'policy_hash':body['policy_hash'],'scaffold_hash':c['scaffold_hash']}
            s.db.execute('INSERT INTO evaluation_binding VALUES(?,?,?,?)',(body['id'],body[role],role,canonical(binding)))
        event(s,body['id'],'registered',{'evaluation_hash':digest(body)})
    return body['id']


def claim(s,eid,claim_body):
    with s.tx():
        states=s.rows('SELECT state FROM evaluation_event WHERE evaluation=? ORDER BY seq',(eid,))
        require(states==[{'state':'registered'}],'evaluation once-only claim; no reclaim')
        require(set(claim_body)=={'root','namespace'} and all(type(v) is str and v for v in claim_body.values()),'claim fields')
        body=json.loads(s.row('SELECT body FROM evaluation WHERE id=?',(eid,))['body'])
        require(claim_body['namespace']==body['claim_namespace'],'claim namespace mismatch')
        event(s,eid,'claimed',claim_body)


def decision_for(body,campaign,report):
    require(body==plan(campaign['body']['preregistration'],report['evidence_kind']),'decision evaluation source')
    return {'schema':'evaluation-decision.v1','evaluation_id':body['id'],'candidate':body['candidate'],'baseline':body['baseline'],
        'policy_hash':body['policy_hash'],'dataset_hash':body['dataset_hash'],'plan_hash':body['plan']['sha256'],
        'report_hash':digest(report),'evidence_hash':campaign['sha256'],'state':report['candidate_decision'],
        'technical_evidence_complete':report['technical_evidence_complete'],'violations':report['violations']['candidate'],
        'counts':report['counts'],'metric_pair_coverage':report['metric_pair_coverage'],'evidence_kind':body['evidence_kind'],
        'reason':'technical evidence incomplete' if not report['technical_evidence_complete'] else 'zero-observed-violation development gate failed' if report['violations']['candidate'] else 'single repeated-use development dataset cannot admit capability',
        'scope':'C1 relative to B0, descriptive development only','eligible_for_activation':False}


def decide(s,eid,campaign,report):
    from .evaluation_measurement import analyze_pilot
    if campaign.get('body',{}).get('schema')=='robustness-campaign-evidence.v1':
        from .robustness_measurement import analyze_pilot
    require(report==analyze_pilot(campaign),'decision requires verified campaign')
    with s.tx():
        body=json.loads(s.row('SELECT body FROM evaluation WHERE id=?',(eid,))['body'])
        require(s.rows('SELECT state FROM evaluation_event WHERE evaluation=? ORDER BY seq',(eid,))==[{'state':'registered'},{'state':'claimed'}],'claimed evaluation required')
        d=decision_for(body,campaign,report)
        s.db.execute('INSERT INTO evaluation_decision VALUES(?,?,?)',(eid,body['candidate'],canonical(d)))
        event(s,eid,'decided',{'decision_hash':digest(d)})
    return d


def export(s):
    require(s.version==4,'evaluation Store schema required')
    s.db.execute('BEGIN')
    try:
        require(not s.db.execute('PRAGMA foreign_key_check').fetchall(),'evaluation FK integrity')
        old={'schema':'candidate-lineage.v1','store':s.row("SELECT value FROM meta WHERE key='store'")['value'],
            'tables':{t:s.rows('SELECT * FROM '+t+' ORDER BY '+('seq' if t=='candidate_event' else 'child' if t=='lineage_edge' else 'candidate' if t in ('campaign_binding','decision') else 'id')) for t in legacy.TABLES},
            'full_controller_recovery':'unsupported','active_pointer':None}
        body={'schema':'evaluation-lineage.v1','legacy':seal(old),'tables':{t:s.rows('SELECT * FROM '+t+' ORDER BY '+('seq' if t=='evaluation_event' else 'evaluation,candidate' if t in ('evaluation_binding','evaluation_decision') else 'id')) for t in TABLES},'active_pointer':None}
        result=seal(body);verify(result);return result
    finally:s.db.rollback()


def verify(value):
    b=unseal(value);require(set(b)=={'schema','legacy','tables','active_pointer'} and b['schema']=='evaluation-lineage.v1' and b['active_pointer'] is None,'evaluation lineage envelope')
    old=legacy.verify(b['legacy']);lt=unseal(b['legacy'])['tables'];t=b['tables'];require(set(t)==set(TABLES),'evaluation tables')
    require(b['legacy']['sha256']==contract.LEGACY_LINEAGE,'must retain the published C2C1 lineage exactly')
    candidates={c['id']:c for c in lt['candidate']};ev={r['id']:json.loads(r['body']) for r in t['evaluation']}
    require(len(ev)==len(t['evaluation']),'duplicate evaluation')
    events=t['evaluation_event'];require([e['seq'] for e in events]==list(range(1,len(events)+1)) and all(e['evaluation'] in ev for e in events),'evaluation event ordering/ownership')
    require(len(t['evaluation_migration'])==1 and t['evaluation_migration'][0]['id']==1,'migration fact required')
    migration=json.loads(t['evaluation_migration'][0]['body'])
    require(migration['from']==3 and migration['to']==4 and migration['legacy_lineage_hash']==b['legacy']['sha256'] and migration['reader']==contract.LEGACY_READER,'immutable migrated lineage source')
    require(all(r['evaluation'] in ev and r['candidate'] in candidates for table in ('evaluation_binding','evaluation_decision') for r in t[table]),'orphan evaluation fact')
    for eid,body in ev.items():
        bindings=[r for r in t['evaluation_binding'] if r['evaluation']==eid];decs=[r for r in t['evaluation_decision'] if r['evaluation']==eid]
        require(len(bindings)==2 and {r['role'] for r in bindings}=={'baseline','candidate'},'one baseline and one candidate binding')
        es=[(r['state'],json.loads(r['body'])) for r in events if r['evaluation']==eid]
        if eid==LEGACY_ID:
            require(body=={'schema':'historical-evaluation-reference.v1','id':LEGACY_ID,'evidence_kind':'local_fixture','reader':contract.LEGACY_READER,'lineage_hash':b['legacy']['sha256']} and not decs,'historical evaluation reference')
            require(es==[('imported',{'legacy_lineage_hash':b['legacy']['sha256']})],'historical import event')
            for r in bindings:
                cid=digest(contract.baseline() if r['role']=='baseline' else contract.candidate())
                expected={'legacy_binding':next(x for x in lt['campaign_binding'] if x['candidate']==cid),'legacy_decision':next(x for x in lt['decision'] if x['candidate']==cid)}
                require(r['candidate']==cid and json.loads(r['body'])==expected,'historical binding/decision changed')
        else:
            require(body==plan(body['plan'],body['evidence_kind']) and eid==body['id'],'evaluation plan')
            for r in bindings:
                require(r['candidate']==body[r['role']] and json.loads(r['body'])=={'schema':'evaluation-binding.v1','evaluation':eid,'candidate':r['candidate'],'role':r['role'],'plan_hash':body['plan']['sha256'],'policy_hash':body['policy_hash'],'scaffold_hash':candidates[r['candidate']]['scaffold_hash']},'evaluation binding')
            require(es and es[0]==('registered',{'evaluation_hash':digest(body)}) and len(es)<=3,'evaluation register event')
            if len(es)>1:require(es[1][0]=='claimed' and set(es[1][1])=={'root','namespace'} and es[1][1]['namespace']==body['claim_namespace'],'evaluation claim event')
            require(len(decs)==(1 if len(es)==3 else 0),'decision cardinality')
            for r in decs:
                d=json.loads(r['body']);require(r['candidate']==body['candidate'] and d['evaluation_id']==eid and d['candidate']==body['candidate'] and d['baseline']==body['baseline'] and d['policy_hash']==body['policy_hash'] and d['dataset_hash']==body['dataset_hash'] and d['plan_hash']==body['plan']['sha256'] and d['state'] in ('reject','infrastructure_failure','insufficient_evidence') and d['eligible_for_activation'] is False and es[2]==('decided',{'decision_hash':digest(d)}),'evaluation decision binding')
    require(LEGACY_ID in ev,'old assessment missing')
    if any(body.get('plan',{}).get('body',{}).get('schema')=='robustness-execution-plan.v1' for body in ev.values()):
        from .evaluation_history import preserve
        preserve(value)
    return {'valid':True,'legacy':old,'evaluations':len(ev),'evaluation_decisions':len(t['evaluation_decision']),'activation':False}
