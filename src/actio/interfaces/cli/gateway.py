from actio.adapters.filesystem.credentials import resolve_credential
from actio.adapters.filesystem.credentials import scan
import argparse
import json
from pathlib import Path
from actio.contracts.json import canonical
from actio.contracts.json import digest
from actio.adapters.filesystem.common import file_hash
from actio.adapters.filesystem.common import write_json
from actio.profiles.gateway_base import template
from actio.profiles.gateway_contract import validate
from actio.profiles.gateway_contract import plan
from actio.profiles.gateway_base import AUTH
from actio.contracts.json import require
from actio.application import gateway as use_cases
from actio.interfaces.store import Store
from actio.adapters.persistence.ledger import Ledger
from actio.application.gateway import *

def execute(*args, **kwargs):
    return use_cases.execute(*args, store_factory=Store, ledger_factory=Ledger, **kwargs)

def run_episode(*args, **kwargs):
    return use_cases.run_episode(*args, store_factory=Store, ledger_factory=Ledger, **kwargs)

def main(argv=None):
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    for n in ('plan','preflight'):
        q=sub.add_parser(n);q.add_argument('--model',choices=('gpt-5.6','claude-sonnet-4-6'),default='gpt-5.6');q.add_argument('--config',type=Path)
    q=sub.add_parser('execute');q.add_argument('config',type=Path);q.add_argument('--root',required=True,type=Path);q.add_argument('--project',type=Path,default=Path.cwd());q.add_argument('--authorized-phase1c2b1',action='store_true')
    q.add_argument('--settings',type=Path)
    q=sub.add_parser('run',help='run DSH + Concordia using project TOML settings')
    q.add_argument('--settings',type=Path);q.add_argument('--root',type=Path)
    q.add_argument('--rehearsal',action='store_true',help='real local runtime and environment with a synthetic provider')
    q.add_argument('--predecessor',type=Path,action='append',default=[])
    q=sub.add_parser('verify');q.add_argument('directory',type=Path)
    a=p.parse_args(argv);secret=None
    try:
        if a.command=='run':
            from actio.interfaces.gateway_settings import run
            r=run(a.settings,root=a.root,rehearsal=a.rehearsal,previous=a.predecessor)
            code=0 if r['status']=='complete' else 2
        elif a.command=='verify':
            from actio.evidence.campaigns.transport_campaign import verify_campaign
            r=verify_campaign(a.directory);code=0 if r['valid'] else 2
        elif a.command in ('plan','preflight'):
            from actio.domain.roles import parse_config
            r=plan(parse_config(a.config.read_bytes()) if a.config else template(a.model));code=0
        else:
            from actio.domain.roles import parse_config
            c=validate(parse_config(a.config.read_bytes()));require(a.authorized_phase1c2b1,'explicit execute acknowledgement required')
            require(c['mode']=='tokenkey_live','CLI execute requires explicit live config')
            require(not a.root.exists(),'prior batch path cannot execute again')
            # Previous immutable reports retain cumulative attempts; no silent unknown reset.
            for prior in c['predecessors']:
                path=Path(prior['path']);require(file_hash(path)==prior['sha256'],'predecessor report changed')
                previous=json.loads(path.read_bytes())
                require(all(w['state']=='reaped' and json.loads(w['report']).get('after',json.loads(w['report'])).get('active')==0 for ep in previous['episodes'] for w in ep['workers']),'previous workers not reaped')
            secret=resolve_credential(a.project,settings_path=a.settings)
            r=execute(c,a.root.resolve(),secret,operation_authorization=AUTH)
            code=0 if all(ep['error'] is None for ep in r['episodes']) and not r['not_run_episodes'] else 2
        print(canonical(r));return code
    except Exception as e:
        reason=str(e).replace(secret,'[credential omitted]') if secret else str(e)
        print(canonical({'status':'BLOCKED_OR_FAILED','type':type(e).__name__,'reason':reason}));return 2

if __name__=='__main__':raise SystemExit(main())
