"""Public C2C0 entrypoint; reuse the existing bounded pilot controller."""
import argparse
import json
from pathlib import Path
from actio.contracts.json import canonical
from actio.contracts.json import ContractError
from actio.profiles import suite_contract as contract

def main(argv=None):
    p=argparse.ArgumentParser(description='C2C0 finite task-suite engineering pilot');sub=p.add_subparsers(dest='command',required=True)
    for n in ('plan','preflight'):sub.add_parser(n)
    sub.add_parser('verify').add_argument('file',type=Path)
    ex=sub.add_parser('execute');ex.add_argument('--project',type=Path,required=True);ex.add_argument('--root',type=Path,required=True)
    ex.add_argument('--preregistration',type=Path,required=True);ex.add_argument('--authorized-phase1c2c0',action='store_true',required=True)
    a=p.parse_args(argv)
    try:
        if a.command in ('plan','preflight'):r=contract.plan()
        elif a.command=='verify':
            from actio.evidence.campaigns.suite_measurement import verify
            r=verify(json.loads(a.file.read_bytes()))
        else:
            from actio.adapters.filesystem.publication import frozen_publication
            from actio.interfaces.cli.pilot import execute
            from actio.adapters.filesystem.credentials import resolve_credential
            pre=json.loads(a.preregistration.read_bytes());freeze=frozen_publication(a.project,pre,contract)
            r=execute(a.root,pre,resolve_credential(a.project),freeze=freeze,authority_root=a.project/'.local/phase1c2c0-claims',operation_authorization=contract.AUTH,contract=contract)
            r={'root':str(a.root),'counts':r['counts'],'usage':r['usage']}
        print(canonical(r));return 2 if r.get('valid') is False else 0
    except (ContractError,OSError,ValueError,KeyError) as e:
        print(canonical({'error':type(e).__name__,'reason':str(e)[:512]}));return 2

if __name__=='__main__':raise SystemExit(main())
