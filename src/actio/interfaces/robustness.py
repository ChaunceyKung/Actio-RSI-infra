from actio.evidence.robustness import verify
"""Public C2C4 CLI: pure readers; explicit rehearsal and once-only live execute."""
import json
import sys
from pathlib import Path
from actio.contracts.json import canonical
from actio.contracts.json import ContractError
from actio.adapters.filesystem.common import file_hash
from actio.contracts.json import seal
from actio.contracts.json import unseal
from actio.contracts.json import require
from actio.profiles import robustness_campaign as contract
from actio.evidence import evaluation_lineage as lineage
from actio.evidence.robustness_measurement import analyze_pilot


def offline(args):
    require(len(args)==(2 if args[0] in ('verify','analyze','lineage') else 1),'offline command arguments')
    if args[0] in ('plan','preflight'):return contract.plan()
    if args[0]=='analyze':return analyze_pilot(json.loads(Path(args[1]).read_bytes()))
    if args[0]=='verify':return verify(json.loads(Path(args[1]).read_bytes()))
    from actio.interfaces.store import Store
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
            from actio.application.robustness import execute_campaign
            from actio.interfaces.pilot import execute
            from actio.adapters.transport.fixture import GatewayStub
            from actio.adapters.filesystem.credentials import resolve_credential
            result=execute_campaign(a,execute=execute,prepare=prepare_store,finish=finalize,fixture_factory=GatewayStub,resolve_credential=resolve_credential)
        print(canonical(result));return 2 if result.get('valid') is False else 0
    except (ContractError,OSError,ValueError,KeyError) as e:
        print(canonical({'error':type(e).__name__,'reason':str(e)[:512]}));return 2


def prepare_store(root,pre,source,kind):
    from actio.application.robustness import prepare_store as prepare
    from actio.interfaces.store import Store
    from actio.interfaces.migration import snapshot_evaluation_copy
    return prepare(root,pre,source,kind,store_factory=Store,migrate=snapshot_evaluation_copy)


def finalize(root,eid,report):
    from actio.application.robustness import finalize as finish
    from actio.interfaces.store import Store
    return finish(root,eid,report,store_factory=Store)

if __name__=='__main__':raise SystemExit(main())
