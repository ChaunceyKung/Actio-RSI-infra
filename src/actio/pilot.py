"""Finite C2B2 controller. One immutable child ledger per preregistered episode."""
import argparse
import datetime
import json
from pathlib import Path
import time
from .common import canonical,write_json,uid,ContractError
from .eval_contract import seal,unseal
from .transport_contract import require
from .pilot_contract import preregistration,validate_preregistration,config,AUTH


def now():return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')


def create(path,value):
    import os
    with Path(path).open('x',encoding='utf8',newline='\n') as f:
        f.write(canonical(value));f.flush();os.fsync(f.fileno())


def run_unit(root,cfg,secret,*,receives=None,runtime_type=None):
    from .store import Store
    from .budget import Ledger
    from .transport import transport_spec,scheduling_transport
    from .task_v2 import card
    if cfg.get('schema')=='pilot-config.v7':
        from .suite_tasks import card
    from .evidence import export_bundle
    from .transport_campaign import export_campaign
    root=Path(root);root.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    create(root/'config.json',cfg)
    ledger=Ledger(root/'budget.sqlite',config=cfg);ledger.close()
    s=Store(root/'domain.sqlite',create=True);error=None
    try:
        for name in ('ACTOR_A','ACTOR_B'):s.agent(name,transport_spec(name,cfg))
        bindings={seat:{'agent':name,'spec_hash':s.agent(name)['spec_hash']} for seat,name in [('A','ACTOR_A'),('B','ACTOR_B')]}
        task=card(cfg['plan'][0],bindings,cfg['mode'])
        try:
            scheduling_transport(s,'episode',root,task=task,config=cfg,ledger_path=root/'budget.sqlite',credential=secret,
                                 **({'runtime_type':runtime_type} if runtime_type else {}))
        except Exception as e:error={'type':type(e).__name__,'reason':str(e).replace(secret,'[credential omitted]')[:1024]}
        bundle=export_bundle(s.path,'episode',root/'bundle')
        workers=s.rows('SELECT * FROM worker')
        require(all(w['state']=='reaped' and json.loads(w['report']).get('after',json.loads(w['report']))['active']==0 for w in workers),'Worker cleanup incomplete')
    finally:s.close()
    ledger=Ledger(root/'budget.sqlite',readonly=True)
    try:snapshot=ledger.snapshot()
    finally:ledger.close()
    # A shared local service can cover multiple children; bind only this ledger's receives.
    selected=None if receives is None else [r for r in receives if r['attempt'] in {a['id'] for a in snapshot['attempts']}]
    campaign=export_campaign(root/'budget.sqlite',[root/'bundle'],selected,root/'campaign')
    index=unseal(json.loads((root/'campaign/campaign.json').read_bytes()))
    dataset=json.loads((root/'campaign'/index['paths']['dataset']).read_bytes())
    result={'error':error,'bundle_verification':bundle['verification'],'campaign':campaign,'workers':workers}
    create(root/'result.json',result)
    entry={'unit':cfg['experiment']['unit'],'evidence':{'dataset':dataset,'ledger':snapshot,'receives':selected},
           'reason':canonical(error) if error else None,'episode_ms':round((time.monotonic()-started)*1000)}
    return entry,result


def frozen_publication(project,pre,contract=None):
    """Resolve publication from trusted Git, never artifact-selected executable source."""
    import subprocess
    project=Path(project).resolve();(contract.validate_preregistration if contract else validate_preregistration)(pre)
    def git(*args):return subprocess.check_output(['git',*args],cwd=project,text=True,encoding='utf8').strip()
    require(git('remote','get-url','origin')=='https://github.com/ChaunceyKung/Actio-RSI-infra','publication remote')
    require(not git('status','--porcelain'),'freeze requires clean checkout')
    head=git('rev-parse','HEAD');branch=contract.BRANCH if contract else 'phase1c2b2-measurement-integrity-and-pilot'
    refs={r.split()[1]:r.split()[0] for r in git('ls-remote','origin','refs/heads/main','refs/heads/'+branch).splitlines()}
    require(refs=={'refs/heads/main':head,'refs/heads/'+branch:head},'freeze must be published on both branches')
    require(json.loads(git('show',head+':docs/validation/'+(contract.PHASE if contract else 'phase1c2b2')+'/preregistration.json'))==pre,'published preregistration differs')
    return {'commit':head,'remote_main':head,'remote_branch':head,'preregistration_hash':pre['sha256'],'verified_utc':now()}


def execute(root,pre,secret,*,freeze=None,endpoint=None,authority_root,operation_authorization,receives=None,runtime_type=None,contract=None):
    from .gateway import scan
    from .pilot_measurement import analyze_pilot
    if contract:
        from .suite_measurement import analyze_pilot
    p=(contract.validate_preregistration if contract else validate_preregistration)(pre);require(operation_authorization==AUTH,'explicit C2B2 operator instruction required')
    live=endpoint is None;root=Path(root).resolve();require(not root.exists(),'new experiment root required')
    require(not live or freeze and freeze['preregistration_hash']==pre['sha256'] and freeze['commit']==freeze['remote_main']==freeze['remote_branch'],'published preregistration required')
    authority=Path(authority_root).resolve();authority.mkdir(parents=True,exist_ok=True)
    # One persistent claim per preregistration across arbitrary output roots.
    create(authority/(pre['sha256']+'.json'),{'preregistration_hash':pre['sha256'],'root':str(root),'first_intent_utc':now()})
    root.mkdir(parents=True);create(root/'preregistration.json',pre)
    f={**freeze,'first_intent_utc':now()} if live else None
    if f:create(root/'freeze.json',f)
    entries=[{'unit':u,'evidence':None,'reason':'not_started','episode_ms':None} for u in p['units']]
    state='stopped';reason=None
    create(root/'intent.json',{'preregistration_hash':pre['sha256'],'freeze':f,'entries':entries})
    try:
        for i,u in enumerate(p['units']):
            cfg=(contract.config if contract else config)(u['id'],authority={'id':uid(),'root':str(authority)},**({'mode':contract.REHEARSAL if contract else 'tokenkey_pilot_rehearsal','endpoint':endpoint} if not live else {}))
            entry,result=run_unit(root/u['id'],cfg,secret,receives=receives,runtime_type=runtime_type);entries[i]=entry
            snapshot=seal({'schema':contract.EVIDENCE if contract else 'pilot-evidence.v1','preregistration':pre,'freeze':f,'entries':entries,'phase_state':'first-block' if i==1 else 'stopped'})
            report=analyze_pilot(snapshot)
            create(root/('checkpoint-'+u['id']+'.json'),{'observed_through':u['id'],'counts':report['counts'],'error':result['error']})
            if result['error'] or any(s['protocol_error'] for s in report['rows'][i]['seats']):
                reason='infrastructure stop at '+u['id'];break
            if i==1:create(root/'first-pair-check.json',{'basis':'integrity/cleanup only; behavioral scores not consulted','passed':True,'continues_same_preregistration':True})
        else:state='completed'
    except Exception as e:
        reason=type(e).__name__+': '+str(e).replace(secret,'[credential omitted]')[:1024]
        create(root/'controller-failure.json',{'reason':reason,'current_unit':u['id'],'raw_directory_retained':str(root/u['id'])})
        raise
    finally:
        for e in entries:
            if e['evidence'] is None:e['reason']=reason or 'not_started'
        evidence=seal({'schema':contract.EVIDENCE if contract else 'pilot-evidence.v1','preregistration':pre,'freeze':f,'entries':entries,'phase_state':state})
        create(root/'pilot.json',evidence)
        report=analyze_pilot(evidence);create(root/'report.json',report)
        create(root/'credential-scan.json',scan(root,secret))
    return report


def main():
    parser=argparse.ArgumentParser(description='C2B2 finite engineering pilot')
    sub=parser.add_subparsers(dest='command',required=True)
    for n in ('plan','preflight'):sub.add_parser(n)
    q=sub.add_parser('verify');q.add_argument('file',type=Path)
    q=sub.add_parser('execute');q.add_argument('--root',type=Path,required=True);q.add_argument('--project',type=Path,required=True)
    q.add_argument('--preregistration',type=Path,required=True);q.add_argument('--authorized-phase1c2b2',action='store_true',required=True)
    a=parser.parse_args()
    try:
        if a.command in ('plan','preflight'):
            from .pilot_contract import plan
            result=plan()
        elif a.command=='verify':
            from .pilot_measurement import verify
            result=verify(json.loads(a.file.read_bytes()))
        else:
            from .gateway import resolve_credential
            pre=json.loads(a.preregistration.read_bytes());freeze=frozen_publication(a.project,pre)
            # Publication is checked before the only credential resolution branch.
            result=execute(a.root,pre,resolve_credential(a.project),freeze=freeze,authority_root=a.project/'.local/phase1c2b2-claims',operation_authorization=AUTH)
            result={'root':str(a.root),'counts':result['counts'],'usage':result['usage']}
        print(canonical(result));return 2 if result.get('valid') is False else 0
    except (ContractError,OSError,ValueError,KeyError) as e:
        print(canonical({'error':type(e).__name__,'reason':str(e)[:512]}));return 2


if __name__=='__main__':raise SystemExit(main())
