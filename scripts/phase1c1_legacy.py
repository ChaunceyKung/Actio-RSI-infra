"""Read original C0 records with an explicit, trusted fixed Git commit; never record-selected code."""
import datetime
import io
import json
from pathlib import Path
import subprocess
import sys
import uuid
import zipfile

from actio.common import canonical,file_hash,clean_env
from actio.evaluation import verify_record

ROOT=Path(__file__).resolve().parents[1]
COMMIT='1e85d8c2fb4a756de81acb333905190df9e97592'
REPORT=ROOT/'docs/validation/phase1c0/campaign/reports/8f58df3b4b00d583130797981ec7c8c808446a1991b430f353d2324b1ed0b5e3.json'


def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    root=ROOT/'.local'/('phase1c1-legacy-'+stamp);root.mkdir()
    log={'status':'FAIL','fixed_commit':COMMIT,'command':' '.join(sys.argv),'model_requests':0}
    target=ROOT/'docs/validation/phase1c1/evidence'/('legacy-'+stamp+'.json')
    try:
        raw=subprocess.check_output(['git','-c','core.autocrlf=false','-c','core.eol=lf','archive','--format=zip',COMMIT,'src'],cwd=ROOT)
        (root/'fixed-c0-source.zip').write_bytes(raw)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for name in z.namelist():
                if name.endswith('/'):continue
                assert name.startswith('src/') and '..' not in Path(name).parts
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
        report=json.loads(REPORT.read_bytes());paths=sorted({REPORT.parent.parent/'records'/(r['record']+'.json') for r in report['body']['registrations']})
        assert len(paths)==12
        before={str(p):file_hash(p) for p in (ROOT/'docs/validation/phase1c0').rglob('*') if p.is_file()}
        runner=root/'verify_fixed.py'
        runner.write_text('''import sys,json,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).parent/'src'))
def audit(event,args):
    if event.startswith('socket.') or event=='subprocess.Popen':raise RuntimeError('offline verification boundary')
    if event=='import' and args[0].split('.')[0] in ('deepseek_harness','concordia','openai','litellm','redis'):raise RuntimeError('runtime import denied')
sys.addaudithook(audit)
from actio.evaluation import verify_record
print(json.dumps([verify_record(json.loads(pathlib.Path(p).read_bytes())) for p in json.loads(sys.stdin.read())]))
''',encoding='utf8')
        command=[sys.executable,'-X','utf8','-I','-S','-B',str(runner)]
        p=subprocess.run(command,input=canonical([str(x) for x in paths]),cwd=root,env=clean_env(root),capture_output=True,text=True,encoding='utf8',timeout=30)
        log['fixed_verifier']={'command':command,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
        assert p.returncode==0,p.stderr
        old=json.loads(p.stdout);assert len(old)==12 and all(r['valid'] for r in old),old
        unsupported=[verify_record(json.loads(p.read_bytes())) for p in paths]
        assert all(not r['valid'] and 'unsupported' in r['error'] for r in unsupported),unsupported
        assert before=={p:file_hash(Path(p)) for p in before}
        log.update(status='PASS',original_records=12,current_verifier_rejects_old_pins=unsupported,
                   fixed_source_hashes={p.relative_to(root).as_posix():file_hash(p) for p in (root/'src').rglob('*') if p.is_file()},
                   fixed_source_archive={'path':str(root/'fixed-c0-source.zip'),'sha256':file_hash(root/'fixed-c0-source.zip')},
                   unchanged_c0_files={str(Path(p).relative_to(ROOT)):h for p,h in before.items()})
    except Exception as e:
        log['error']={'type':type(e).__name__,'reason':str(e)};raise
    finally:
        with target.open('x',encoding='utf8') as f:f.write(canonical(log))
    print(canonical({'status':'PASS','records':12,'evidence':str(target)}))


if __name__=='__main__':main()
