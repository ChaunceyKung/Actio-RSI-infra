"""Finite authorized C2B1 baseline runner; genuine DSH execution, no direct API fallback.

Every invocation creates and records a new batch. No retries or model discovery.
"""
import argparse
import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
from actio.common import canonical,write_json,clean_env,file_hash
from actio.gateway_contract import template,plan
from actio.gateway import scan,resolve_credential

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/validation/phase1c2b1'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--model',choices=['gpt-5.6','claude-sonnet-4-6'],required=True)
    parser.add_argument('--predecessor',type=Path);parser.add_argument('--reason');args=parser.parse_args()
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    base=Path('D:/actio-c2b1-live')/stamp;base.mkdir(parents=True);root=base/'run'
    cfg=template(args.model);cfg['authority']={'id':uuid.uuid4().hex,'root':str(base/'authority')}
    if args.predecessor:
        assert args.reason,'new diagnostic must explain predecessor and changed hypothesis'
        cfg['predecessors']=[{'path':str(args.predecessor.resolve()),'sha256':file_hash(args.predecessor),'reason':args.reason}]
    path=base/'config.json';write_json(path,cfg)
    value={'status':'FAIL','root':str(base),'model':args.model,'proposal':plan(cfg),'actual_argv':sys.orig_argv,
           'prior_direct_diagnostics':'docs/reviews/phase1c2b1_tokenkey_evidence.json','prior_diagnostic_generation_attempts':14,
           'commands':[],'automatic_retries':0,'supplier_bill':None,'upstream_identity_verified':False}
    target=DOC/'evidence'/('live-'+stamp+'.json')
    # Persist the batch pointer before any secret resolution or network action.
    with (DOC/'evidence'/('live-intent-'+stamp+'.json')).open('x',encoding='utf8',newline='\n') as f:
        f.write(canonical({'root':str(base),'config_hash':value['proposal']['contract_hash'],'model':args.model,'scope':'two ordered baseline episodes, max four formal seats','authorization_basis':cfg['authorization_basis']}))
    try:
        command=[sys.executable,'-X','utf8','-I','-B','-m','actio.gateway','execute',str(path),'--root',str(root),'--project',str(ROOT),'--authorized-phase1c2b1']
        env=clean_env(base);git=shutil.which('git');assert git,'Git required for ignored/untracked credential check'
        # Only the control CLI needs Git; Worker/helper environments are rebuilt separately.
        env['PATH']=str(Path(git).parent)+';'+env['PATH']
        p=subprocess.run(command,cwd=base,env=env,capture_output=True,text=True,encoding='utf8',timeout=720)
        # Resolve only within this explicit live operation; scan buffers before disk publication.
        secret=resolve_credential(ROOT)
        assert secret not in p.stdout and secret not in p.stderr,'credential in subprocess output; preserve in memory, do not publish'
        value['commands'].append({'argv':command,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        value['credential_scan']=scan(base,secret)
        result=json.loads((root/'result.json').read_bytes()) if (root/'result.json').exists() else None
        value['result']=result
        value['status']='PASS' if p.returncode==0 and result is not None else 'OBSERVED_FAILURE'
        write_json(base/'execution.json',value)
    except Exception as e:
        value['error']={'type':type(e).__name__,'reason':str(e)}
        raise
    finally:
        with target.open('x',encoding='utf8',newline='\n') as f:f.write(canonical(value))
        print(canonical({'status':value['status'],'evidence':str(target),'root':str(base),
                         'report':value.get('result',{}).get('campaign',{}).get('report') if value.get('result') else None}))
    return 0 if value['status']=='PASS' else 2

if __name__=='__main__':raise SystemExit(main())
