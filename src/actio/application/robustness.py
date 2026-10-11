from actio.evidence.robustness import verify
import json
from pathlib import Path
from actio.adapters.filesystem.common import file_hash
from actio.contracts.json import seal
from actio.contracts.json import require
from actio.profiles import robustness_campaign as contract
from actio.evidence import evaluation_lineage as lineage

def prepare_store(root,pre,source,kind,*,store_factory,migrate):
    from actio.adapters.filesystem.publication import create
    body=lineage.plan(pre,kind)  # Reject malformed plans before mutating any copy.
    migrate(source,root/'candidates.sqlite')
    s=store_factory(root/'candidates.sqlite')
    try:
        eid=s.evaluation(body)
        s.claim_evaluation(eid,{'root':str(root),'namespace':body['claim_namespace']})
        create(root/'lineage-before.json',s.evaluation_lineage())
    finally:s.close()
    return eid

def finalize(root,eid,report,*,store_factory):
    from actio.adapters.filesystem.publication import create
    campaign=json.loads((root/'matrix/pilot.json').read_bytes());s=store_factory(root/'candidates.sqlite')
    try:
        decision=s.decide_evaluation(eid,campaign,report);history=s.evaluation_lineage()
        create(root/'lineage.json',history);create(root/'decision.json',decision)
    finally:s.close()
    s=store_factory(root/'candidates.sqlite',readonly=True)
    try:require(s.evaluation_lineage()==history,'reopened lineage changed')
    finally:s.close()
    delivery=seal({'schema':'robustness-delivery.v1','campaign':campaign,'lineage':history})
    create(root/'delivery.json',delivery);verified=verify(delivery);create(root/'verification.json',verified)
    require(verified['valid'],'delivery verification failed')
    return {'root':str(root),'counts':report['counts'],'candidate_decision':decision['state'],'lineage':verified['lineage'],'reopen_equal':True}


def reserve_live(project,root,eid,freeze):
    from actio.adapters.filesystem.publication import create
    claims=Path(project)/'.local/phase1c2c4-claims';claims.mkdir(exist_ok=True)
    create(claims/'live-once.json',{'evaluation':eid,'root':str(root),'freeze':freeze})
    return claims


def execute_campaign(a,*,execute,prepare,finish,fixture_factory,resolve_credential):
    project=a.project.resolve();root=a.root.resolve()
    from actio.adapters.filesystem.publication import frozen_publication
    from actio.adapters.filesystem.publication import create
    if a.rehearsal:
        # Installed local fixture, never selected by artifacts.
        import uuid
        pre=contract.preregistration();root.mkdir(parents=True,exist_ok=False)
        eid=prepare(root,pre,a.source_database,'local_fixture')
        secret='ACTIO_FAKE_'+uuid.uuid4().hex
        with fixture_factory(root,contract.fixture_plans(),secret) as service:
            report=execute(root/'matrix',pre,secret,endpoint=service.endpoint,receives=service.receives,
                authority_root=root/'claims',operation_authorization=contract.AUTH,contract=contract)
        require(not service.thread.is_alive(),'loopback service did not join')
    else:
        pre=json.loads((project/'docs/validation/phase1c2c4/preregistration.json').read_bytes())
        freeze=frozen_publication(project,pre,contract)
        admission=json.loads((project/'docs/validation/phase1c2c4/local-acceptance.json').read_bytes())
        require(admission['status']=='PASS' and admission['implementation']==contract.implementation(),'current-source local admission required')
        require({k:file_hash(project/'src/actio'/k) for k in contract.implementation()}==contract.implementation(),'installed source mismatch')
        require(file_hash(a.source_database)==admission['source_database_sha256'],'frozen C2C2 source database')
        root.mkdir(parents=True,exist_ok=False)
        eid=prepare(root,pre,a.source_database,'live_development_exploratory')
        claims=reserve_live(project,root,eid,freeze)
        report=execute(root/'matrix',pre,resolve_credential(project),freeze=freeze,authority_root=claims,
            operation_authorization=contract.AUTH,contract=contract)
    require(report.get('valid') is not False,'controller/verifier failure; raw inventory retained; no retry')
    return finish(root,eid,report)
