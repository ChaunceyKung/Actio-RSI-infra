"""Read-only incremental census of explicit C2B2 runs, including failed validations."""
import argparse
import ctypes as C
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import uuid
import zipfile
from actio.common import canonical,file_hash,clean_env
from actio.pilot_contract import implementation
from actio.pilot_measurement import verify
from actio.supervisor import Job,kernel
from actio.runtime import verify_runtime
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2b2'
START='6436fc7bc4d25570ee93fb44ab2428635bf6b218'

def read(p):return json.loads(Path(p).read_bytes())
def create(p,v):
    with Path(p).open('x',encoding='utf8',newline='\n') as f:f.write(canonical(v))
def files(root):
    for base,dirs,names in os.walk(root):
        dirs[:]=[d for d in dirs if d not in ('__pycache__','node_modules')]
        for name in names:yield Path(base)/name
def scan(paths,secret=None):
    forbidden=secret.encode() if secret else None;count=0
    fake=re.compile(rb'ACTIO_FAKE_[0-9a-f]{32}')
    for p in paths:
        with p.open('rb') as f:
            tail=b''
            while chunk:=f.read(1024*1024):
                data=tail+chunk
                assert forbidden is None or forbidden not in data,'credential persisted; publication blocked'
                assert not fake.search(data),'fake credential persisted'
                tail=data[-max(len(forbidden) if forbidden else 0,128):]
        count+=1
    return {'files_scanned':count,'credential_found':False,'scope':'all generated files; unchanged node_modules and bytecode omitted; locked installation/runtime hashes separately checked'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--live-root',type=Path);a=p.parse_args()
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    roots=set();attempts=[];jobs={};services=[];ports=set();ledgers=[];archives=[];dbhashes={}
    log={'status':'FAIL','actual_argv':sys.orig_argv,'source_hashes':implementation(),'live_root':str(a.live_root) if a.live_root else None}
    try:
        verify_runtime()
        import actio
        assert {n:file_hash(Path(actio.__file__).parent/n) for n in implementation()}==implementation()
        for path in sorted((DOC/'evidence').glob('*.json')):
            d=read(path)
            if 'suite' in d:
                attempts.append({'file':path.relative_to(DOC).as_posix(),'sha256':file_hash(path),'suite':d['suite'],'tests':d['tests_run'],'exit_code':d['exit_code'],'argv':d['actual_argv']})
                for t in d['tests']:
                    if t.get('evidence',{}).get('root'):roots.add(Path(t['evidence']['root']))
        if a.live_root:roots.add(a.live_root.resolve())
        allfiles=sorted({p for root in roots for p in files(root) if p.is_file()})
        secret=(ROOT/'.local/credentials/token_key.txt').read_text(encoding='utf-8-sig').strip() if a.live_root else None
        scans=scan(allfiles,secret)
        for path in allfiles:
            if path.name=='service.json':
                d=read(path);assert d['joined'];ports.add(int(d['endpoint'].split(':')[-1].split('/')[0]));services.append({'file':str(path),**d})
            if path.suffix!='.sqlite':continue
            h=file_hash(path);db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
            try:
                tables={r[0] for r in db.execute('SELECT name FROM sqlite_master')}
                if 'worker' in tables:
                    for r in db.execute('SELECT * FROM worker'):jobs[r['job']]=dict(r)
                if {'meta','attempt','event','registration'}<=tables:
                    c=json.loads(db.execute('SELECT body FROM meta').fetchone()[0])['config'];rows=[json.loads(r[0]) for r in db.execute('SELECT body FROM attempt')]
                    ledgers.append({'file':str(path),'mode':c['mode'],'model':c['model'],
                        'sent':db.execute("SELECT count(*) FROM event WHERE kind='sending'").fetchone()[0],
                        'registered':db.execute('SELECT count(*) FROM registration').fetchone()[0],
                        'usage_responses':sum(r['usage'] is not None for r in rows),'unknown':sum(r['state']=='unknown' for r in rows),
                        'unresolved':sum(r['state'] in ('authorized','reserved','sending') for r in rows)})
            finally:db.close()
            assert h==file_hash(path);dbhashes[str(path)]=h
        cleanup=[]
        for name,w in jobs.items():
            k=kernel();handle=k.OpenJobObjectW(4,False,name)
            if not handle:assert C.get_last_error()==2;active=0
            else:
                job=object.__new__(Job);job.k=k;job.handle=handle
                try:active=job.snapshot()['active']
                finally:k.CloseHandle(handle)
            assert active==0 and w['state']=='reaped',(name,w['state'])
            cleanup.append({'job':name,'active':active,'state':w['state'],'report':json.loads(w['report'])})
        ps=shutil.which('pwsh') or shutil.which('powershell')
        script='$pilotPorts=@('+','.join(map(str,sorted(ports)))+'); ConvertTo-Json -Compress -InputObject @(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -in $pilotPorts })'
        cmd=[ps,'-NoProfile','-NonInteractive','-Command',script]
        result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',timeout=45);assert result.returncode==0,result.stderr
        assert json.loads(result.stdout)==[]
        archive_root=ROOT/'.local/phase1c2b2-raw';archive_root.mkdir(exist_ok=True)
        for root in sorted(roots):
            selected={p.relative_to(root).as_posix():file_hash(p) for p in files(root) if p.is_file()}
            dest=archive_root/(root.parent.name+'-'+root.name+'.zip')
            if not dest.exists():
                with zipfile.ZipFile(dest,'x',zipfile.ZIP_DEFLATED) as z:
                    for n in sorted(selected):z.write(root/n,n)
            with zipfile.ZipFile(dest) as z:assert {n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}==selected
            archives.append({'root':str(root),'archive':str(dest),'sha256':file_hash(dest),'files':selected,'bytes':dest.stat().st_size})
        history=['docs/validation/'+x for x in ('phase1c0','phase1c1','phase1c2a1','phase1c2b0','phase1c2b1')]
        subprocess.run(['git','diff','--exit-code',START,'--',*history],cwd=ROOT,check=True,capture_output=True)
        if a.live_root:
            value=read(a.live_root/'pilot.json');report=verify(value);assert report['valid'],report
            assert sum(l['sent'] for l in ledgers if l['mode']=='tokenkey_pilot_live')==report['report']['counts']['sent']
            target=DOC/'samples';target.mkdir(exist_ok=True)
            for name in ('pilot.json','report.json','freeze.json','intent.json','first-pair-check.json','controller-failure.json'):
                src=a.live_root/name
                if not src.exists():continue
                if (target/name).exists():assert file_hash(target/name)==file_hash(src)
                else:shutil.copyfile(src,target/name)
            log['pilot_verification']=report
        log.update(status='PASS',validation_attempts=attempts,roots=list(map(str,sorted(roots))),ledgers=ledgers,
            jobs=cleanup,services=services,ports=sorted(ports),remaining_listeners=0,unresolved=sum(l['unresolved'] for l in ledgers),
            credential_scan=scans,raw_archives=archives,readonly_database_hashes=dbhashes,historical_diff='unchanged',
            historical_generation_attempts_excluded=22,historical_catalog_get_excluded=1,
            census={mode:{k:sum(l[k] for l in ledgers if l['mode']==mode) for k in ('sent','registered','usage_responses','unknown')} for mode in sorted({l['mode'] for l in ledgers})})
        scan(list(files(DOC)),secret)
    except Exception as e:log['error']={'type':type(e).__name__,'reason':str(e)};raise
    finally:
        target=DOC/'evidence'/('census-'+stamp+'.json');create(target,log)
        print(canonical({'status':log['status'],'file':str(target),'census':log.get('census'),'jobs':len(jobs),'services':len(services)}))

if __name__=='__main__':main()
