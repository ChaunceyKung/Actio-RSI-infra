from actio.evidence.lineage.candidate_evaluation import verify
"""Public C2C2 CLI. Credentials/network are reachable only from execute."""
import argparse
import json
import sys
from pathlib import Path
from actio.contracts.json import canonical
from actio.contracts.json import ContractError
from actio.adapters.filesystem.common import file_hash
from actio.contracts.json import seal
from actio.contracts.json import unseal
from actio.contracts.json import require
from actio.profiles import evaluation_campaign as contract
from actio.evidence.lineage import evaluation_lineage as lineage
from actio.evidence.campaigns.evaluation_measurement import analyze_pilot


def main(argv=None):
    # argparse consults locale/terminal environment even for a valid command.
    # Offline entrypoints avoid that ambient state as well as execution imports.
    args=list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ('plan','preflight','verify','lineage'):
        try:
            require(len(args)==(2 if args[0] in ('verify','lineage') else 1),'offline command arguments')
            if args[0] in ('plan','preflight'):result=contract.plan()
            elif args[0]=='verify':result=verify(json.loads(Path(args[1]).read_bytes()))
            else:
                from actio.interfaces.store import Store
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
    a=p.parse_args(argv)
    try:
        if a.command in ('plan','preflight'):result=contract.plan()
        elif a.command=='verify':result=verify(json.loads(a.file.read_bytes()))
        elif a.command=='lineage':
            from actio.interfaces.store import Store
            s=Store(a.database,readonly=True)
            try:result={'lineage':s.evaluation_lineage(),'credential_reads':0,'network_requests':0,'workers_started':0}
            finally:s.close()
        else:
            from actio.application.candidate_evaluation import execute_campaign
            from actio.interfaces.cli.pilot import execute
            from actio.adapters.filesystem.credentials import resolve_credential
            result=execute_campaign(a,execute=execute,prepare=prepare_store,finish=finalize,resolve_credential=resolve_credential)
        print(canonical(result));return 2 if result.get('valid') is False else 0
    except (ContractError,OSError,ValueError,KeyError) as e:
        print(canonical({'error':type(e).__name__,'reason':str(e)[:512]}));return 2


def prepare_store(root,pre,source,kind):
    from actio.application.candidate_evaluation import prepare_store as prepare
    from actio.interfaces.store import Store
    from actio.interfaces.migration import migrate_evaluation_copy
    return prepare(root,pre,source,kind,store_factory=Store,migrate=migrate_evaluation_copy)


def finalize(root,eid,report):
    from actio.application.candidate_evaluation import finalize as finish
    from actio.interfaces.store import Store
    return finish(root,eid,report,store_factory=Store)

if __name__=='__main__':raise SystemExit(main())
