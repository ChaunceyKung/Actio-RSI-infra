from actio.evidence.candidate_evaluation import verify
import json
from actio.adapters.filesystem.common import file_hash
from actio.contracts.json import seal
from actio.contracts.json import require
from actio.profiles import evaluation_campaign as contract
from actio.evidence import evaluation_lineage as lineage

def prepare_store(root,pre,source,kind,*,store_factory,migrate):
    from actio.adapters.filesystem.publication import create
    migrate(source,root/'candidates.sqlite')
    s=store_factory(root/'candidates.sqlite');body=lineage.plan(pre,kind)
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
    try:require(s.evaluation_lineage()==history,'reopen differs')
    finally:s.close()
    delivery=seal({'schema':'candidate-delivery.v2','campaign':campaign,'lineage':history})
    create(root/'delivery.json',delivery);verified=verify(delivery);create(root/'verification.json',verified)
    require(verified['valid'],'delivery verification failed')
    return {'root':str(root),'counts':report['counts'],'candidate_decision':decision['state'],'lineage':verified['lineage'],'reopen_equal':True}


def execute_campaign(a,*,execute,prepare,finish,resolve_credential):
    from actio.adapters.filesystem.publication import frozen_publication
    from actio.adapters.filesystem.publication import create
    pre=json.loads((a.project/'docs/validation/phase1c2c2/preregistration.json').read_bytes())
    freeze=frozen_publication(a.project,pre,contract)
    admission=json.loads((a.project/'docs/validation/phase1c2c2/local-acceptance.json').read_bytes())
    require(admission['status']=='PASS' and admission['implementation']==contract.implementation(),'current-source local admission required')
    require(file_hash(a.source_database)==admission['legacy_source']['database_sha256'] and admission['legacy_source']['lineage_sha256']==contract.LEGACY_LINEAGE,'frozen C2C1 source database required')
    root=a.root.resolve();root.mkdir(parents=True,exist_ok=False)
    eid=prepare(root,pre,a.source_database,'live_development_exploratory')
    # This single global namespace prevents a changed output directory
    # or a future implementation hash from silently creating batch two.
    claims=a.project/'.local/phase1c2c2-claims';claims.mkdir(exist_ok=True)
    create(claims/'live-once.json',{'evaluation':eid,'root':str(root),'freeze':freeze})
    report=execute(root/'matrix',pre,resolve_credential(a.project),freeze=freeze,authority_root=claims,
        operation_authorization=contract.AUTH,contract=contract)
    require(report.get('valid') is not False,'controller/verification failure; raw inventory retained, no retry')
    return finish(root,eid,report)
