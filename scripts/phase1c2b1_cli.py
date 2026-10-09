"""Record clean-install public CLI behavior; all calls here are local/offline."""
import datetime
import json
from pathlib import Path
import subprocess
import sys
import uuid
from actio.common import canonical,clean_env,file_hash
from actio.gateway_contract import template

ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2b1'

def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    root=Path('D:/actio-c2b1-cli')/stamp;root.mkdir(parents=True)
    log={'status':'FAIL','root':str(root),'actual_argv':sys.orig_argv,'commands':[],'external_requests':0,
         'product_hashes':{'src/actio/'+p.relative_to(ROOT/'src/actio').as_posix():file_hash(p) for p in (ROOT/'src/actio').rglob('*') if p.is_file() and '__pycache__' not in p.parts}}
    def command(args,expected=0):
        args=list(map(str,args));p=subprocess.run(args,cwd=root,env=clean_env(root),capture_output=True,text=True,encoding='utf8',timeout=180)
        log['commands'].append({'argv':args,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr});assert p.returncode==expected,p.stderr+p.stdout
        return p.stdout
    try:
        cli=[sys.executable,'-X','utf8','-I','-B'];config=root/'config.json';config.write_text(canonical(template()),encoding='utf8')
        for env in ('runtime','release'):command([ROOT/f'.local/phase1c2b1-{env}-venv/Scripts/python.exe','-m','pip','--isolated','check'])
        for sub in ('plan','preflight'):
            r=json.loads(command([*cli,'-m','actio.gateway',sub,'--config',config]));assert r['credential_reads']==0 and r['network_requests']==0
        missing=json.loads(command([*cli,'-m','actio.gateway','execute',config,'--root',root/'never-created','--project',root],2))
        assert missing['reason']=='explicit execute acknowledgement required' and not (root/'never-created').exists()
        blocked=json.loads(command([*cli,'-m','actio.readiness','execute'],2));assert blocked['credential_reads']==0
        smoke=json.loads(command([*cli,ROOT/'scripts/phase1c2b1_rehearsal.py']));assert smoke['counts']['received']==2 and smoke['valid']
        verified=json.loads(command([*cli,'-m','actio.gateway','verify',Path(smoke['root'])/'run/campaign']));assert verified['valid']
        log.update(status='PASS',smoke=smoke,verification=verified)
    finally:
        with (DOC/'evidence'/('cli-'+stamp+'.json')).open('x',encoding='utf8',newline='\n') as f:f.write(canonical(log))
        print(canonical({'status':log['status'],'root':str(root),'smoke':log.get('smoke')}))

if __name__=='__main__':main()
