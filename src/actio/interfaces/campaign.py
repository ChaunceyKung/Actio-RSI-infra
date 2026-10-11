"""Offline task campaign CLI assembly."""
import argparse
import json
from pathlib import Path
from actio.contracts.json import ContractError, seal
from actio.evidence.evaluation import read_json
from actio.evidence.campaign import verify_campaign
from actio.interfaces.evaluation import execute_worker
from actio.application import campaign as use_cases

def run_campaign(*args, **kwargs):
    return use_cases.run_campaign(*args, worker=execute_worker, **kwargs)

def main(argv=None):
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True)
    c=s.add_parser('run');c.add_argument('dataset',type=Path);c.add_argument('--output',type=Path,required=True)
    c=s.add_parser('verify-campaign');c.add_argument('directory',type=Path)
    a=p.parse_args(argv)
    try:
        result=verify_campaign(a.directory) if a.command=='verify-campaign' else run_campaign(read_json(a.dataset),a.output)
        print(json.dumps(result));return 0 if result.get('valid',True) else 2
    except (ContractError,OSError,KeyError,TypeError,ValueError) as e:
        print(json.dumps({'error':type(e).__name__,'reason':str(e)[:512]}));return 2

if __name__=='__main__':raise SystemExit(main())
