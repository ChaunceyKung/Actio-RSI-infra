"""Store-owned immutable candidate facts. JSON is a read-only projection."""
import json
from actio.contracts.json import canonical, digest
from actio.contracts.json import require
from actio.domain.candidate import validate_proposal, validate_decision, POLICY_HASH
from actio.contracts.json import seal, unseal

TABLES=('candidate','candidate_event','lineage_edge','campaign_binding','decision')


def event(s, cid, state, body):
    s.db.execute('INSERT INTO candidate_event(candidate,state,policy_hash,body) VALUES(?,?,?,?)',(cid,state,POLICY_HASH,canonical(body)))


def register(s, proposal):
    require(s.version in (3,4),'explicit candidate Store schema required')
    cid=digest(proposal)
    with s.tx():
        old=s.row('SELECT * FROM candidate WHERE id=?',(cid,))
        if old:
            require(old['proposal']==canonical(proposal),'immutable proposal conflict');return cid
        parent=s.row('SELECT * FROM candidate WHERE id=?',(proposal.get('parent'),)) if isinstance(proposal.get('parent'),str) else None
        eligible=parent and json.loads(parent['validation'])['valid']
        validation=validate_proposal(proposal,json.loads(parent['proposal']) if eligible else None)
        s.db.execute('INSERT INTO candidate VALUES(?,?,?,?)',(cid,canonical(proposal),canonical(validation),digest(proposal.get('artifact'))))
        event(s,cid,'proposed',{'proposal_hash':cid})
        if validation['valid'] and parent:
            s.db.execute('INSERT INTO lineage_edge VALUES(?,?)',(cid,parent['id']))
        event(s,cid,'validated' if validation['valid'] else 'rejected',validation)
    return cid


def state(s,cid):
    r=s.row('SELECT state FROM candidate_event WHERE candidate=? ORDER BY seq DESC LIMIT 1',(cid,))
    require(r is not None,'unknown candidate');return r['state']


def bind(s,cid,plan):
    with s.tx():
        require(state(s,cid)=='validated','validated candidate required; evaluating cannot be reclaimed')
        require(plan['policy_hash']==POLICY_HASH and cid in plan['candidate_hashes'],'campaign candidate/policy binding')
        s.db.execute('INSERT INTO campaign_binding VALUES(?,?,?)',(cid,digest(plan),canonical(plan)))
        event(s,cid,'evaluating',{'plan_hash':digest(plan)})


def record_decision(s,cid,decision):
    validate_decision(decision)
    with s.tx():
        current=state(s,cid)
        require(current in ('evaluating','rejected'),'decision transition')
        valid=json.loads(s.row('SELECT validation FROM candidate WHERE id=?',(cid,))['validation'])['valid']
        require(valid==decision['inputs']['static_valid'] and decision['evidence_kind']!='policy_fixture','registered candidate decision validity/scope')
        s.db.execute('INSERT INTO decision VALUES(?,?,?)',(cid,digest(decision),canonical(decision)))
        event(s,cid,'decided',{'decision_hash':digest(decision)})


def export(s):
    s.db.execute('BEGIN')
    try:
        require(s.version in (3,4) and not s.db.execute('PRAGMA foreign_key_check').fetchall(),'candidate Store integrity')
        body={'schema':'candidate-lineage.v1','store':s.row("SELECT value FROM meta WHERE key='store'")['value'],
              'tables':{t:s.rows('SELECT * FROM '+t+' ORDER BY '+('seq' if t=='candidate_event' else 'child' if t=='lineage_edge' else 'candidate' if t in ('campaign_binding','decision') else 'id')) for t in TABLES},
              'full_controller_recovery':'unsupported','active_pointer':None}
        verify(seal(body));return seal(body)
    finally:s.db.rollback()


def verify(value):
    b=unseal(value);require(set(b)=={'schema','store','tables','full_controller_recovery','active_pointer'} and b['schema']=='candidate-lineage.v1','lineage schema')
    require(b['full_controller_recovery']=='unsupported' and b['active_pointer'] is None and set(b['tables'])==set(TABLES),'lineage scope')
    t=b['tables'];candidates={c['id']:c for c in t['candidate']}
    require(len(candidates)==len(t['candidate']),'duplicate candidate')
    events=t['candidate_event'];require([e['seq'] for e in events]==list(range(1,len(events)+1)),'event sequence')
    require(all(e['candidate'] in candidates and e['policy_hash']==POLICY_HASH for e in events),'event ownership')
    edges={r['child']:r['parent'] for r in t['lineage_edge']};bindings={r['candidate']:r for r in t['campaign_binding']};decisions={r['candidate']:r for r in t['decision']}
    require(len(edges)==len(t['lineage_edge']) and len(bindings)==len(t['campaign_binding']) and len(decisions)==len(t['decision']),'duplicate facts')
    require(set(edges)<=set(candidates) and set(bindings)<=set(candidates) and set(decisions)<=set(candidates),'orphan facts')
    for cid,c in candidates.items():
        p=json.loads(c['proposal']);par=candidates.get(p.get('parent'));parent=json.loads(par['proposal']) if par and json.loads(par['validation'])['valid'] else None
        v=validate_proposal(p,parent)
        require(digest(p)==cid and digest(p.get('artifact'))==c['scaffold_hash'] and json.loads(c['validation'])==v,'proposal/hash/validation')
        require(edges.get(cid)==(p['parent'] if v['valid'] else None),'canonical parent edge')
        ev=[e for e in events if e['candidate']==cid];expected=[('proposed',{'proposal_hash':cid}),('validated' if v['valid'] else 'rejected',v)]
        if cid in bindings:
            r=bindings[cid];plan=json.loads(r['body'])
            require(v['valid'] and digest(plan)==r['plan_hash'] and plan['policy_hash']==POLICY_HASH and cid in plan['candidate_hashes'],'campaign binding')
            expected.append(('evaluating',{'plan_hash':r['plan_hash']}))
        if cid in decisions:
            r=decisions[cid];d=validate_decision(json.loads(r['body']))
            require((cid in bindings or not v['valid']) and digest(d)==r['decision_hash'] and d['inputs']['static_valid']==v['valid'] and d['evidence_kind']!='policy_fixture','decision binding')
            expected.append(('decided',{'decision_hash':r['decision_hash']}))
        require([(e['state'],json.loads(e['body'])) for e in ev]==expected,'transition/event facts')
    return {'valid':True,'candidates':len(candidates),'rejected':sum(not json.loads(c['validation'])['valid'] for c in candidates.values()),'decisions':len(decisions),'activation':False}
