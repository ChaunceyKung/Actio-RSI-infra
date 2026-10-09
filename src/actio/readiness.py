"""Public offline readiness CLI. Execute always stops before credential resolution."""
import argparse
import json
from pathlib import Path
from .common import ContractError
from .preflight import parse_config
from .readiness_contract import template,plan,execute


def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True)
    for name in ('plan','preflight','execute'):
        c=s.add_parser(name);c.add_argument('config',type=Path,nargs='?')
    c=s.add_parser('verify');c.add_argument('directory',type=Path)
    c=s.add_parser('export');c.add_argument('ledger',type=Path);c.add_argument('receives',type=Path);c.add_argument('destination',type=Path);c.add_argument('bundles',nargs='+',type=Path)
    a=p.parse_args()
    try:
        if a.command=='verify':
            from .transport_campaign import verify_campaign
            result=verify_campaign(a.directory);code=0 if result['valid'] else 2
        elif a.command=='export':
            from .transport_campaign import export_campaign
            result=export_campaign(a.ledger,a.bundles,parse_config(a.receives.read_bytes()),a.destination);code=0
        else:
            c=parse_config(a.config.read_bytes()) if a.config else template()
            if a.command=='execute':execute(c)
            result=plan(c);code=0 if a.command=='plan' else 2
    except (ContractError,OSError,ValueError,TypeError,KeyError) as e:
        result={'status':'BLOCKED','error':str(e),'credential_reads':0,'network_requests':0,'workers_started':0};code=2
    print(json.dumps(result,ensure_ascii=False));return code


if __name__=='__main__':raise SystemExit(main())
