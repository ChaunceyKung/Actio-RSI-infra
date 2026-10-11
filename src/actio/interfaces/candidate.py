from actio.evidence.lineage.candidate import binding_plan, decision_for, verify
"""Public offline candidate CLI. Never loads executable artifact references."""
import argparse
import json
from pathlib import Path
from actio.contracts.json import canonical
from actio.contracts.json import digest
from actio.contracts.json import ContractError
from actio.contracts.json import unseal
from actio.contracts.json import require
from actio.profiles import candidate_campaign as contract
from actio.domain.candidate import decide
from actio.domain.candidate import POLICY_HASH
from actio.evidence.lineage.candidate_lineage import verify as verify_lineage
from actio.evidence.campaigns.candidate_measurement import analyze_pilot











def main():
    p=argparse.ArgumentParser(description='C2C1 local candidate plan and read-only evidence verification')
    sub=p.add_subparsers(dest='command',required=True)
    for name in ('plan','preflight'):sub.add_parser(name)
    sub.add_parser('verify').add_argument('file',type=Path)
    sub.add_parser('lineage').add_argument('database',type=Path)
    a=p.parse_args()
    try:
        if a.command in ('plan','preflight'):result=contract.plan()
        elif a.command=='verify':result=verify(json.loads(a.file.read_bytes()))
        else:
            from actio.interfaces.store import Store
            s=Store(a.database,readonly=True)
            try:result={'lineage':s.candidate_lineage(),'credential_reads':0,'network_requests':0,'workers_started':0}
            finally:s.close()
        print(canonical(result));return 2 if result.get('valid') is False else 0
    except (ContractError,OSError,ValueError,KeyError) as e:
        print(canonical({'error':type(e).__name__,'reason':str(e)[:512]}));return 2


if __name__=='__main__':raise SystemExit(main())
