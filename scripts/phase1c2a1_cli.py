"""Record clean-install public local-only CLI checks, including failed attempts."""
import datetime
import json
from pathlib import Path
import subprocess
import sys
import uuid

from actio.common import canonical,clean_env,file_hash

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/validation/phase1c2a1'


def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    root=Path('D:/actio-c2a1-cli')/stamp;root.mkdir(parents=True)
    result={'status':'FAIL','command':sys.argv,'root':str(root),'commands':[],
            'model_requests':0,'external_provider_requests':0,'real_cost':0,
            'product_hashes':{'src/actio/'+p.relative_to(ROOT/'src/actio').as_posix():file_hash(p)
                              for p in (ROOT/'src/actio').rglob('*') if p.is_file() and '__pycache__' not in p.parts}}

    def command(args,expected=0):
        args=list(map(str,args))
        p=subprocess.run(args,cwd=root,env=clean_env(root),capture_output=True,text=True,encoding='utf8',timeout=120)
        result['commands'].append({'command':args,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        assert p.returncode==expected,p.stdout+p.stderr
        return p.stdout

    try:
        cli=[sys.executable,'-X','utf8','-I','-B']
        caps=json.loads(command([*cli,'-m','actio','capabilities']))
        assert caps['live_provider'] is False
        for python in (ROOT/'.local/phase1c2a1-runtime-venv/Scripts/python.exe',Path(sys.executable)):
            command([python,'-X','utf8','-m','pip','--isolated','check'])
        for path in (DOC/'stub-config.json',ROOT/'docs/validation/phase1c2a/stub-config.json'):
            value=json.loads(command([*cli,'-m','actio.preflight',path],2))
            assert value['configuration_valid'] and value['status']=='BLOCKED'
            assert all(value[k] is False for k in ('transport_validated','live_authorized','live_ready'))
        duplicate=root/'duplicate.json';duplicate.write_text('{"schema":1,"schema":2}',encoding='utf8')
        value=json.loads(command([*cli,'-m','actio.preflight',duplicate],2))
        assert not value['configuration_valid'] and 'duplicate JSON key' in str(value['reasons'])
        smoke=json.loads(command([*cli,ROOT/'scripts/phase1c2a1_smoke.py']))
        assert smoke['error'] is None and smoke['states']==['settled','settled']
        assert smoke['local_http_requests']==2 and smoke['verification']['task_outcome']=='success'
        result.update(status='PASS',smoke=smoke,capabilities=caps)
    except Exception as e:
        result['error']={'type':type(e).__name__,'reason':str(e)}
        raise
    finally:
        target=DOC/'evidence'/('cli-'+stamp+'.json')
        with target.open('x',encoding='utf8',newline='\n') as f:f.write(canonical(result))
        print(canonical({'status':result['status'],'evidence':str(target),'smoke':result.get('smoke')}))


if __name__=='__main__':main()
