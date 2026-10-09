"""Public CLI and installation validation in the clean release environment."""
import argparse
import datetime
import json
from pathlib import Path
import subprocess
import sys
import uuid
from actio.common import canonical,clean_env,file_hash
from actio.suite_contract import implementation
from actio.runtime import verify_runtime
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2c0'

def main():
    p=argparse.ArgumentParser();p.add_argument('sample',type=Path);a=p.parse_args()
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    root=Path('D:/actio-c2c0-cli')/stamp;root.mkdir(parents=True)
    log={'status':'FAIL','root':str(root),'actual_argv':sys.orig_argv,'commands':[],'source_hashes':implementation()}
    try:
        verify_runtime()
        import actio
        assert {n:file_hash(Path(actio.__file__).parent/n) for n in implementation()}==implementation()
        for args in (['-m','pip','--isolated','check'],['-m','actio.suite','plan'],['-m','actio.suite','preflight'],['-m','actio.suite','verify',str(a.sample.resolve())]):
            cmd=[sys.executable,'-X','utf8','-I','-B',*args]
            result=subprocess.run(cmd,cwd=root,env=clean_env(root),capture_output=True,text=True,encoding='utf8',timeout=60)
            log['commands'].append({'argv':cmd,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr});assert result.returncode==0,result.stderr
            if 'actio.suite' in args:
                v=json.loads(result.stdout);assert v['credential_reads']==v['network_requests']==v['workers_started']==0
                if 'verify' in args:assert v['valid']
        log['status']='PASS'
    except Exception as e:log['error']={'type':type(e).__name__,'reason':str(e)};raise
    finally:
        target=DOC/'evidence'/('cli-'+stamp+'.json')
        with target.open('x',encoding='utf8',newline='\n') as f:f.write(canonical(log))
        print(canonical({'status':log['status'],'file':str(target)}))

if __name__=='__main__':main()
