"""Public C2C2 CLI. Credentials/network are reachable only from execute."""
import argparse
import json
import sys
from pathlib import Path
from actio.contracts.json import canonical, digest, ContractError
from actio.adapters.filesystem.common import file_hash
from actio.contracts.json import seal, unseal
from actio.contracts.json import require
from . import evaluation_campaign as contract
from . import evaluation_store as lineage
from .evaluation_measurement import analyze_pilot


def verify(value):
    try:
        b=unseal(value)
        if b['schema']==contract.EVIDENCE:result={'report':analyze_pilot(value)}
        elif b['schema']=='evaluation-lineage.v1':result={'lineage':lineage.verify(value),'scope':'structure only'}
        else:
            require(set(b)=={'schema','campaign','lineage'} and b['schema']=='candidate-delivery.v2','evaluation delivery envelope')
            report=analyze_pilot(b['campaign']);ls=lineage.verify(b['lineage']);t=unseal(b['lineage'])['tables']
            expected=lineage.plan(b['campaign']['body']['preregistration'],report['evidence_kind'])
            require(next((json.loads(r['body']) for r in t['evaluation'] if r['id']==expected['id']),None)==expected,'delivery evaluation')
            ds=[json.loads(r['body']) for r in t['evaluation_decision'] if r['evaluation']==expected['id']]
            require(ds==[lineage.decision_for(expected,b['campaign'],report)],'delivery evidence/decision binding')
            result={'report':report,'lineage':ls}
        return {'valid':True,**result,'credential_reads':0,'network_requests':0,'workers_started':0}
    except (ContractError,KeyError,TypeError,ValueError,OSError,AttributeError,IndexError,StopIteration) as e:
        return {'valid':False,'error':str(e)[:512],'credential_reads':0,'network_requests':0,'workers_started':0}


def prepare_store(root,pre,source,kind):
    from .database import migrate_evaluation_copy
    from .store import Store
    from .pilot import create
    migrate_evaluation_copy(source,root/'candidates.sqlite')
    s=Store(root/'candidates.sqlite');body=lineage.plan(pre,kind)
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
    try:require(s.evaluation_lineage()==history,'reopen differs')
    finally:s.close()
    delivery=seal({'schema':'candidate-delivery.v2','campaign':campaign,'lineage':history})
    create(root/'delivery.json',delivery);verified=verify(delivery);create(root/'verification.json',verified)
    require(verified['valid'],'delivery verification failed')
    return {'root':str(root),'counts':report['counts'],'candidate_decision':decision['state'],'lineage':verified['lineage'],'reopen_equal':True}


def main():
    # argparse consults locale/terminal environment even for a valid command.
    # Offline entrypoints avoid that ambient state as well as execution imports.
    args=sys.argv[1:]
    if args and args[0] in ('plan','preflight','verify','lineage'):
        try:
            require(len(args)==(2 if args[0] in ('verify','lineage') else 1),'offline command arguments')
            if args[0] in ('plan','preflight'):result=contract.plan()
            elif args[0]=='verify':result=verify(json.loads(Path(args[1]).read_bytes()))
            else:
                from .store import Store
                s=Store(Path(args[1]),readonly=True)
                try:result={'lineage':s.evaluation_lineage(),'credential_reads':0,'network_requests':0,'workers_started':0}
                finally:s.close()
            print(canonical(result));return 2 if result.get('valid') is False else 0
        except (ContractError,OSError,ValueError,KeyError) as e:
            print(canonical({'error':type(e).__name__,'reason':str(e)[:512]}));return 2
    p=argparse.ArgumentParser(description='C2C2 finite candidate evaluation and offline evidence reader')
    sub=p.add_subparsers(dest='command',required=True)
    for n in ('plan','preflight'):sub.add_parser(n)
    sub.add_parser('verify').add_argument('file',type=Path)
    sub.add_parser('lineage').add_argument('database',type=Path)
    q=sub.add_parser('execute');q.add_argument('--root',type=Path,required=True);q.add_argument('--project',type=Path,required=True)
    q.add_argument('--source-database',type=Path,required=True);q.add_argument('--authorized-phase1c2c2',action='store_true',required=True)
    a=p.parse_args()
    try:
        if a.command in ('plan','preflight'):result=contract.plan()
        elif a.command=='verify':result=verify(json.loads(a.file.read_bytes()))
        elif a.command=='lineage':
            from .store import Store
            s=Store(a.database,readonly=True)
            try:result={'lineage':s.evaluation_lineage(),'credential_reads':0,'network_requests':0,'workers_started':0}
            finally:s.close()
        else:
            from .pilot import frozen_publication,execute,create
            pre=json.loads((a.project/'docs/validation/phase1c2c2/preregistration.json').read_bytes())
            freeze=frozen_publication(a.project,pre,contract)
            admission=json.loads((a.project/'docs/validation/phase1c2c2/local-acceptance.json').read_bytes())
            require(admission['status']=='PASS' and admission['implementation']==contract.implementation(),'current-source local admission required')
            require(file_hash(a.source_database)==admission['legacy_source']['database_sha256'] and admission['legacy_source']['lineage_sha256']==contract.LEGACY_LINEAGE,'frozen C2C1 source database required')
            root=a.root.resolve();root.mkdir(parents=True,exist_ok=False)
            eid=prepare_store(root,pre,a.source_database,'live_development_exploratory')
            # This single global namespace prevents a changed output directory
            # or a future implementation hash from silently creating batch two.
            claims=a.project/'.local/phase1c2c2-claims';claims.mkdir(exist_ok=True)
            create(claims/'live-once.json',{'evaluation':eid,'root':str(root),'freeze':freeze})
            from .gateway import resolve_credential
            report=execute(root/'matrix',pre,resolve_credential(a.project),freeze=freeze,authority_root=claims,
                operation_authorization=contract.AUTH,contract=contract)
            require(report.get('valid') is not False,'controller/verification failure; raw inventory retained, no retry')
            result=finalize(root,eid,report)
        print(canonical(result));return 2 if result.get('valid') is False else 0
    except (ContractError,OSError,ValueError,KeyError) as e:
        print(canonical({'error':type(e).__name__,'reason':str(e)[:512]}));return 2


if __name__=='__main__':raise SystemExit(main())
