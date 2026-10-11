"""Public C2C4 CLI: pure readers; explicit rehearsal and once-only live execute."""
import json
import sys
from pathlib import Path
from actio.contracts.json import canonical, digest, ContractError
from actio.adapters.filesystem.common import file_hash
from actio.contracts.json import seal, unseal
from actio.contracts.json import require
from . import robustness_campaign as contract
from . import evaluation_store as lineage
from .robustness_measurement import analyze_pilot


def verify(value):
    try:
        b=unseal(value)
        if b['schema']==contract.EVIDENCE:result={'report':analyze_pilot(value)}
        elif b['schema']=='evaluation-lineage.v1':result={'lineage':lineage.verify(value),'scope':'structure and fixed historical binding only'}
        else:
            require(set(b)=={'schema','campaign','lineage'} and b['schema']=='robustness-delivery.v1','C2C4 delivery envelope')
            report=analyze_pilot(b['campaign']);ls=lineage.verify(b['lineage']);t=unseal(b['lineage'])['tables']
            expected=lineage.plan(b['campaign']['body']['preregistration'],report['evidence_kind'])
            require(next((json.loads(r['body']) for r in t['evaluation'] if r['id']==expected['id']),None)==expected,'delivery evaluation')
            require([json.loads(r['body']) for r in t['evaluation_decision'] if r['evaluation']==expected['id']]==
                    [lineage.decision_for(expected,b['campaign'],report)],'delivery evidence/decision binding')
            result={'report':report,'lineage':ls}
        return {'valid':True,**result,'credential_reads':0,'network_requests':0,'workers_started':0}
    except (ContractError,KeyError,TypeError,ValueError,OSError,AttributeError,IndexError,StopIteration) as e:
        return {'valid':False,'error':str(e)[:512],'credential_reads':0,'network_requests':0,'workers_started':0}


def prepare_store(root,pre,source,kind):
    from .database import snapshot_evaluation_copy
    from .store import Store
    from .pilot import create
    body=lineage.plan(pre,kind)  # Reject malformed plans before mutating any copy.
    snapshot_evaluation_copy(source,root/'candidates.sqlite')
    s=Store(root/'candidates.sqlite')
    try:
        eid=s.evaluation(body)
        s.claim_evaluation(eid,{'root':str(root),'namespace':body['claim_namespace']})
        create(root/'lineage-before.json',s.evaluation_lineage())
    finally:s.close()
    return eid


def finalize(root,eid,report):
    from .store import Store
    from .pilot import create
    campaign=json.loads((root/'matrix/pilot.json').read_bytes());s=Store(root/'candidates.sqlite')
    try:
        decision=s.decide_evaluation(eid,campaign,report);history=s.evaluation_lineage()
        create(root/'lineage.json',history);create(root/'decision.json',decision)
    finally:s.close()
    s=Store(root/'candidates.sqlite',readonly=True)
    try:require(s.evaluation_lineage()==history,'reopened lineage changed')
    finally:s.close()
    delivery=seal({'schema':'robustness-delivery.v1','campaign':campaign,'lineage':history})
    create(root/'delivery.json',delivery);verified=verify(delivery);create(root/'verification.json',verified)
    require(verified['valid'],'delivery verification failed')
    return {'root':str(root),'counts':report['counts'],'candidate_decision':decision['state'],'lineage':verified['lineage'],'reopen_equal':True}


def reserve_live(project,root,eid,freeze):
    from .pilot import create
    claims=Path(project)/'.local/phase1c2c4-claims';claims.mkdir(exist_ok=True)
    create(claims/'live-once.json',{'evaluation':eid,'root':str(root),'freeze':freeze})
    return claims


def offline(args):
    require(len(args)==(2 if args[0] in ('verify','analyze','lineage') else 1),'offline command arguments')
    if args[0] in ('plan','preflight'):return contract.plan()
    if args[0]=='analyze':return analyze_pilot(json.loads(Path(args[1]).read_bytes()))
    if args[0]=='verify':return verify(json.loads(Path(args[1]).read_bytes()))
    from .store import Store
    s=Store(Path(args[1]),readonly=True)
    try:return {'lineage':s.evaluation_lineage(),'credential_reads':0,'network_requests':0,'workers_started':0}
    finally:s.close()


def main():
    args=sys.argv[1:]
    try:
        if args and args[0] in ('plan','preflight','analyze','verify','lineage'):
            result=offline(args)
        else:
            import argparse
            p=argparse.ArgumentParser(description='C2C4 finite robustness execution')
            p.add_argument('command',choices=['execute']);p.add_argument('--root',type=Path,required=True)
            p.add_argument('--project',type=Path,required=True);p.add_argument('--source-database',type=Path,required=True)
            mode=p.add_mutually_exclusive_group(required=True)
            mode.add_argument('--rehearsal',action='store_true');mode.add_argument('--authorized-phase1c2c4',action='store_true')
            a=p.parse_args();project=a.project.resolve();root=a.root.resolve()
            from .pilot import frozen_publication,execute,create
            if a.rehearsal:
                # Test-only server is explicit, project-owned, never selected by artifacts.
                sys.path.insert(0,str(project/'tests'))
                from gateway_stub import GatewayStub
                import uuid
                pre=contract.preregistration();root.mkdir(parents=True,exist_ok=False)
                eid=prepare_store(root,pre,a.source_database,'local_fixture')
                secret='ACTIO_FAKE_'+uuid.uuid4().hex
                with GatewayStub(root,contract.fixture_plans(),secret) as service:
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
                eid=prepare_store(root,pre,a.source_database,'live_development_exploratory')
                claims=reserve_live(project,root,eid,freeze)
                from .gateway import resolve_credential
                report=execute(root/'matrix',pre,resolve_credential(project),freeze=freeze,authority_root=claims,
                    operation_authorization=contract.AUTH,contract=contract)
            require(report.get('valid') is not False,'controller/verifier failure; raw inventory retained; no retry')
            result=finalize(root,eid,report)
        print(canonical(result));return 2 if result.get('valid') is False else 0
    except (ContractError,OSError,ValueError,KeyError) as e:
        print(canonical({'error':type(e).__name__,'reason':str(e)[:512]}));return 2


if __name__=='__main__':raise SystemExit(main())
