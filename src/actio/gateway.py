"""Explicit, finite TokenKey execution. Pure plan/verify paths never resolve a key."""
import argparse
import json
from pathlib import Path
import sys
from actio.contracts.json import canonical, digest, ContractError
from actio.adapters.filesystem.common import file_hash, write_json, uid
from .gateway_contract import template,validate,plan,AUTH
from actio.contracts.json import require

def scan(root,secret):
    count=0;token=secret.encode()
    for p in Path(root).rglob('*'):
        if not p.is_file():continue
        with p.open('rb') as f:
            tail=b''
            while chunk:=f.read(1024*1024):
                data=tail+chunk;require(token not in data,'credential found in generated files; publication prohibited')
                tail=data[-len(token):]
        count+=1
    return {'files_scanned':count,'credential_found':False}

def run_episode(root,cfg,ledger_path,secret,variant,runtime_type=None):
    from .store import Store
    from .transport import transport_spec,scheduling_transport
    from actio.tasks.scheduling import task_card
    from .evidence import export_bundle
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    s=Store(root/'ledger.sqlite',create=True)
    try:
        for name in ('ACTOR_A','ACTOR_B'):s.agent(name,transport_spec(name,cfg))
        bindings={seat:{'agent':name,'spec_hash':s.agent(name)['spec_hash']} for seat,name in [('A','ACTOR_A'),('B','ACTOR_B')]}
        task=task_card(variant,bindings,cfg['mode']);error=None
        try:scheduling_transport(s,'episode',root,task=task,config=cfg,ledger_path=ledger_path,credential=secret,**({'runtime_type':runtime_type} if runtime_type else {}))
        except Exception as e:error={'type':type(e).__name__,'reason':str(e).replace(secret,'[credential omitted]')}
        run=s.run('episode');bundle=export_bundle(s.path,'episode',root/'bundle')
        return {'run':run,'error':error,'bundle':bundle,'workers':s.rows('SELECT * FROM worker')}
    finally:s.close()

def execute(c,root,secret,*,operation_authorization,runtime_type=None,receives=None):
    from actio.adapters.persistence.ledger import Ledger
    from .budget import verify_snapshot
    from .transport_campaign import export_campaign
    validate(c);require(operation_authorization==AUTH,'independent explicit C2B1 operator instruction required')
    require(c['authority'] is not None,'execution authority not allocated')
    root=Path(root);require(not root.exists(),'new batch only; cannot replay prior execution')
    root.mkdir(parents=True)
    write_json(root/'execution-plan.json',plan(c))
    l=Ledger(root/'budget.sqlite',config=c);l.close();results=[];bundles=[]
    for i,variant in enumerate(c['plan']):
        ep=root/('episode-'+str(i));r=run_episode(ep,c,root/'budget.sqlite',secret,variant,runtime_type)
        results.append(r);bundles.append(ep/'bundle')
        if r['error'] or r['bundle']['verification']['scenario_completeness']!='complete':break
    ledger=Ledger(root/'budget.sqlite',readonly=True)
    try:snap=ledger.snapshot();verify_snapshot(snap)
    finally:ledger.close()
    campaign=export_campaign(root/'budget.sqlite',bundles,receives,root/'campaign')
    result={'schema':'tokenkey-execution.v1','contract_hash':digest(c),'root':str(root),'episodes':results,
            'planned_episodes':len(c['plan']),'not_run_episodes':len(c['plan'])-len(results),'campaign':campaign,
            'source_hashes':c['implementation'],'credential_scan':scan(root,secret),'account_settings_changed':False}
    write_json(root/'result.json',result);return result

def resolve_credential(project):
    # Only the explicit execute branch calls this. The value and metadata never leave memory.
    import subprocess
    target=Path(project).resolve()/'.local/credentials/token_key.txt'
    require(subprocess.run(['git','check-ignore','--quiet',str(target)],cwd=project,capture_output=True).returncode==0,'credential path must be ignored')
    require(not subprocess.check_output(['git','ls-files','--',str(target)],cwd=project).strip(),'credential must not be tracked')
    if not target.exists():
        source=Path('D:/调研/CausalEngine/api_key/token_key.txt');target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(source.read_bytes())
    value=target.read_text(encoding='utf-8-sig').strip()
    require(bool(value) and '\n' not in value and '\r' not in value,'credential file format invalid')
    return value

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    for n in ('plan','preflight'):
        q=sub.add_parser(n);q.add_argument('--model',choices=('gpt-5.6','claude-sonnet-4-6'),default='gpt-5.6');q.add_argument('--config',type=Path)
    q=sub.add_parser('execute');q.add_argument('config',type=Path);q.add_argument('--root',required=True,type=Path);q.add_argument('--project',type=Path,default=Path.cwd());q.add_argument('--authorized-phase1c2b1',action='store_true')
    q=sub.add_parser('verify');q.add_argument('directory',type=Path)
    a=p.parse_args();secret=None
    try:
        if a.command=='verify':
            from .transport_campaign import verify_campaign
            r=verify_campaign(a.directory);code=0 if r['valid'] else 2
        elif a.command in ('plan','preflight'):
            from .preflight import parse_config
            r=plan(parse_config(a.config.read_bytes()) if a.config else template(a.model));code=0
        else:
            from .preflight import parse_config
            c=validate(parse_config(a.config.read_bytes()));require(a.authorized_phase1c2b1,'explicit execute acknowledgement required')
            require(c['mode']=='tokenkey_live','CLI execute requires explicit live config')
            require(not a.root.exists(),'prior batch path cannot execute again')
            # Previous immutable reports retain cumulative attempts; no silent unknown reset.
            for prior in c['predecessors']:
                path=Path(prior['path']);require(file_hash(path)==prior['sha256'],'predecessor report changed')
                previous=json.loads(path.read_bytes())
                require(all(w['state']=='reaped' and json.loads(w['report']).get('after',json.loads(w['report'])).get('active')==0 for ep in previous['episodes'] for w in ep['workers']),'previous workers not reaped')
            secret=resolve_credential(a.project)
            r=execute(c,a.root.resolve(),secret,operation_authorization=AUTH)
            code=0 if all(ep['error'] is None for ep in r['episodes']) and not r['not_run_episodes'] else 2
        print(canonical(r));return code
    except Exception as e:
        reason=str(e).replace(secret,'[credential omitted]') if secret else str(e)
        print(canonical({'status':'BLOCKED_OR_FAILED','type':type(e).__name__,'reason':reason}));return 2

if __name__=='__main__':raise SystemExit(main())
