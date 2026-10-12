from actio.adapters.filesystem.publication import frozen_publication
from actio.adapters.filesystem.publication import create
from actio.adapters.filesystem.publication import now
import argparse
import json
from pathlib import Path
import time
from actio.contracts.json import canonical
from actio.contracts.json import ContractError
from actio.adapters.filesystem.common import uid
from actio.contracts.json import seal
from actio.contracts.json import unseal
from actio.contracts.json import require
from actio.profiles.pilot_contract import validate_preregistration
from actio.profiles.pilot_contract import config
from actio.profiles.pilot_contract import AUTH
from actio.application import pilot as use_cases
from actio.interfaces.store import Store
from actio.adapters.persistence.ledger import Ledger
from actio.application.pilot import *

def execute(*args, **kwargs):
    return use_cases.execute(*args, store_factory=Store, ledger_factory=Ledger, **kwargs)

def run_unit(*args, **kwargs):
    return use_cases.run_unit(*args, store_factory=Store, ledger_factory=Ledger, **kwargs)

def main(argv=None):
    parser=argparse.ArgumentParser(description='C2B2 finite engineering pilot')
    sub=parser.add_subparsers(dest='command',required=True)
    for n in ('plan','preflight'):sub.add_parser(n)
    q=sub.add_parser('verify');q.add_argument('file',type=Path)
    q=sub.add_parser('execute');q.add_argument('--root',type=Path,required=True);q.add_argument('--project',type=Path,required=True)
    q.add_argument('--preregistration',type=Path,required=True);q.add_argument('--authorized-phase1c2b2',action='store_true',required=True)
    a=parser.parse_args(argv)
    try:
        if a.command in ('plan','preflight'):
            from actio.profiles.pilot_contract import plan
            result=plan()
        elif a.command=='verify':
            from actio.evidence.campaigns.pilot_measurement import verify
            result=verify(json.loads(a.file.read_bytes()))
        else:
            from actio.adapters.filesystem.credentials import resolve_credential
            pre=json.loads(a.preregistration.read_bytes());freeze=frozen_publication(a.project,pre)
            # Publication is checked before the only credential resolution branch.
            result=execute(a.root,pre,resolve_credential(a.project),freeze=freeze,authority_root=a.project/'.local/phase1c2b2-claims',operation_authorization=AUTH)
            result={'root':str(a.root),'counts':result['counts'],'usage':result['usage']}
        print(canonical(result));return 2 if result.get('valid') is False else 0
    except (ContractError,OSError,ValueError,KeyError) as e:
        print(canonical({'error':type(e).__name__,'reason':str(e)[:512]}));return 2

if __name__=='__main__':raise SystemExit(main())
