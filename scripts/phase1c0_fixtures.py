"""New synthetic identities, public runtime CLI smoke and actual replay for C0 cluster evidence."""
import datetime
import json
from pathlib import Path
import subprocess
import sys
import uuid

from actio.common import clean_env,file_hash,write_json
from actio.store import Store

ROOT=Path(__file__).resolve().parents[1]
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
base=Path('D:/actio-p1c0-tests')/stamp;base.mkdir(parents=True)
db=base/'ledger.sqlite';env=clean_env(base);calls=[]
evidence={'mode':'REAL_DSH_CONCORDIA_SYNTHETIC_START_REPLAY','model_requests':0,'root':str(base),'commands':calls,'status':'FAIL'}
target=ROOT/'docs/validation/phase1c0/evidence'/('runtime-smoke-'+stamp+'.json')
target.parent.mkdir(parents=True,exist_ok=True)


def cli(args):
    cmd=[sys.executable,'-I','-m','actio','--db',str(db),'--short-root',str(base),*args]
    p=subprocess.run(cmd,cwd=base,env=env,capture_output=True,text=True,timeout=100)
    calls.append({'command':cmd,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    if p.returncode:raise RuntimeError('fixture CLI failed: '+str(args)+': '+p.stderr)
    return json.loads(p.stdout)


try:
    cli(['init'])
    for agent in ('C0_NORTH','C0_SOUTH'):cli(['agent',agent,'--create'])
    cli(['assistant','--agent','C0_NORTH','--key','c0-assistant'])
    cli(['social','--a','C0_NORTH','--b','C0_SOUTH','--key','c0-social','--memory-revision','1'])
    cli(['social','--a','C0_NORTH','--b','C0_SOUTH','--key','c0-replay','--replay','c0-social'])
    bundles={}
    for key in ('c0-assistant','c0-social','c0-replay'):
        dest=base/key;cli(['export',key,'--output',str(dest)]);v=cli(['verify',str(dest)])
        assert v['scenario_completeness']=='complete' and v['task_outcome']=='success',v
        bundles[key]=str(dest)
    s=Store(db,readonly=True)
    try:
        workers=s.rows('SELECT id,report FROM worker');assert all(json.loads(w['report'])['after']['active']==0 for w in workers)
    finally:s.close()
    evidence.update(status='PASS',bundles=bundles,workers=workers,
                    artifact_hashes={p.relative_to(base).as_posix():file_hash(p) for p in base.rglob('*') if p.is_file() and p.suffix in ('.sqlite','.json','.jsonl')})
except Exception as e:
    evidence['error']={'type':type(e).__name__,'reason':str(e)}
    raise
finally:
    write_json(target,evidence);print('Evidence:',target)
