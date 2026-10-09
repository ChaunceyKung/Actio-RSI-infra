"""Read original C0/C1 artifacts with trusted hard-coded Git versions; no artifact-selected code."""
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

ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2b0'
VERSIONS={'phase1c0':'1e85d8c2fb4a756de81acb333905190df9e97592','phase1c1':'af0a88cfff23c22c396fd7c9ef9916f0df8cd21f'}


def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    root=Path('D:/actio-c2b0-legacy')/stamp;root.mkdir(parents=True)
    log={'status':'FAIL','root':str(root),'command':' '.join(sys.argv),'model_requests':0,'versions':{}}
    try:
        before={p.relative_to(ROOT).as_posix():file_hash(p) for phase in VERSIONS for p in (ROOT/'docs/validation'/phase).rglob('*') if p.is_file()}
        for phase,commit in VERSIONS.items():
            folder=root/phase;folder.mkdir()
            raw=subprocess.check_output(['git','-c','core.autocrlf=false','-c','core.eol=lf','archive','--format=zip',commit,'src'],cwd=ROOT)
            (folder/'fixed-source.zip').write_bytes(raw)
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                for name in z.namelist():
                    if name.endswith('/'):continue
                    assert name.startswith('src/') and '..' not in Path(name).parts
                    p=folder/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
            campaign=ROOT/'docs/validation'/phase/'campaign'
            if phase=='phase1c0':report=campaign/'reports/8f58df3b4b00d583130797981ec7c8c808446a1991b430f353d2324b1ed0b5e3.json'
            else:report=campaign/json.loads((campaign/'campaign.json').read_bytes())['body']['report']
            records=sorted({campaign/'records'/(r['record']+'.json') for r in json.loads(report.read_bytes())['body']['registrations']})
            expected=12 if phase=='phase1c0' else 22;assert len(records)==expected
            runner=folder/'reader.py'
            runner.write_text('''import sys,json,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).parent/'src'))
def audit(event,args):
    if event.startswith('socket.') or event=='subprocess.Popen':raise RuntimeError('offline only')
    if event=='import' and args[0].split('.')[0] in ('deepseek_harness','concordia','openai','redis','litellm'):raise RuntimeError('runtime denied')
sys.addaudithook(audit)
from actio.evaluation import verify_record
payload=json.loads(sys.stdin.read());result={'records':[verify_record(json.loads(pathlib.Path(p).read_bytes())) for p in payload['records']]}
if payload['campaign']:
    from actio.campaign import verify_campaign
    result['campaign']=verify_campaign(payload['campaign'])
print(json.dumps(result))
''',encoding='utf8')
            args=[sys.executable,'-X','utf8','-I','-S','-B',str(runner)]
            p=subprocess.run(args,input=canonical({'records':[str(p) for p in records],'campaign':str(campaign) if phase=='phase1c1' else None}),cwd=folder,env=clean_env(folder),capture_output=True,text=True,encoding='utf8',timeout=60)
            assert p.returncode==0,p.stderr;result=json.loads(p.stdout);assert all(r['valid'] for r in result['records']),result
            if phase=='phase1c1':assert result['campaign']['valid'] and result['campaign']['evaluator_calls']==0
            unsupported=[verify_record(json.loads(p.read_bytes())) for p in records]
            assert all(not r['valid'] and 'unsupported' in r['error'] for r in unsupported),unsupported
            log['versions'][phase]={'commit':commit,'command':args,'exit_code':p.returncode,'result':result,'current_pins_rejected':len(unsupported),
                    'source_archive':{'path':str(folder/'fixed-source.zip'),'sha256':file_hash(folder/'fixed-source.zip')},
                    'source_hashes':{p.relative_to(folder).as_posix():file_hash(p) for p in (folder/'src').rglob('*') if p.is_file()}}
        commit='b086cbae97fcebd5c818dce611a0c2a331380cb1';folder=root/'phase1c2a1';folder.mkdir()
        raw=subprocess.check_output(['git','-c','core.autocrlf=false','-c','core.eol=lf','archive','--format=zip',commit,'src'],cwd=ROOT)
        (folder/'fixed-source.zip').write_bytes(raw)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for name in z.namelist():
                if name.endswith('/'):continue
                assert name.startswith('src/') and '..' not in Path(name).parts
                p=folder/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
        runner=folder/'reader.py'
        runner.write_text("""import sys,json,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).parent/'src'))
def audit(e,a):
 if e.startswith('socket.') or e=='subprocess.Popen':raise RuntimeError('offline only')
 if e=='import' and (a[0].split('.')[0] in ('deepseek_harness','concordia') or a[0] in ('actio.runtime','actio.transport')):raise RuntimeError('runtime denied')
 if e=='open':
  p,m,f=a
  if isinstance(m,str) and any(c in m for c in 'wax+') or isinstance(f,int) and f&(1|2|64|512|1024):raise RuntimeError('writes denied')
sys.addaudithook(audit)
from actio.transport_campaign import verify_campaign
print(json.dumps({n:verify_campaign(pathlib.Path(sys.argv[1])/n) for n in ('success','missing-done','last-call')}))
""",encoding='utf8')
        args=[sys.executable,'-X','utf8','-I','-S','-B',str(runner),str(ROOT/'docs/validation/phase1c2a1/samples')]
        p=subprocess.run(args,cwd=folder,env=clean_env(folder),capture_output=True,text=True,encoding='utf8',timeout=60)
        assert p.returncode==0,p.stderr;result=json.loads(p.stdout);assert all(v['valid'] for v in result.values())
        log['versions']['phase1c2a1']={'commit':commit,'command':args,'exit_code':0,'samples':result,'source_archive':{'path':str(folder/'fixed-source.zip'),'sha256':file_hash(folder/'fixed-source.zip')}}
        assert before=={p:file_hash(ROOT/p) for p in before}
        log.update(status='PASS',history_unchanged=before)
    except Exception as e:log['error']={'type':type(e).__name__,'reason':str(e)};raise
    finally:
        (DOC/'evidence').mkdir(parents=True,exist_ok=True)
        with (DOC/'evidence'/('legacy-'+stamp+'.json')).open('x',encoding='utf8') as f:f.write(canonical(log))
    print(canonical({'status':'PASS','fixed_c0_records':12,'fixed_c1_records':22,'fixed_c2a1_samples':3,'model_requests':0}))


if __name__=='__main__':main()
