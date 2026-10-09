"""C2C2 explicit-root census, owned Job cleanup and immutable local archives."""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import uuid
import zipfile
from actio.common import canonical,file_hash
from actio.pilot_contract import implementation
from actio.runtime import verify_runtime
from actio.supervisor import Job,kernel
from phase1c2c0_collect import files,scan,create
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2c2'


def main():
    p=argparse.ArgumentParser();p.add_argument('--main-root',type=Path);a=p.parse_args()
    roots=set();jobs={};services=[];ports=set();ledgers=[];dbhashes={};archives=[]
    for path in (DOC/'evidence').glob('*.json'):
        d=json.loads(path.read_bytes())
        for t in d.get('tests',[]):
            if t.get('evidence',{}).get('root'):roots.add(Path(t['evidence']['root']))
    if a.main_root:roots.add(a.main_root.resolve())
    allfiles=sorted({p for r in roots for p in files(r) if p.is_file()})
    verify_runtime();import actio
    assert {n:file_hash(Path(actio.__file__).parent/n) for n in implementation()}==implementation()
    secret=(ROOT/'.local/credentials/token_key.txt').read_text(encoding='utf-8-sig').strip() if a.main_root else None
    scanned=scan(allfiles,secret)
    for path in allfiles:
        if path.name=='service.json':
            d=json.loads(path.read_bytes());assert d['joined'];ports.add(int(d['endpoint'].split(':')[-1].split('/')[0]));services.append({'file':str(path),**d})
        if path.suffix!='.sqlite':continue
        h=file_hash(path);db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
        try:
            tables={r[0] for r in db.execute('SELECT name FROM sqlite_master')}
            if 'worker' in tables:
                for r in db.execute('SELECT * FROM worker'):jobs[r['job']]=dict(r)
            if {'meta','attempt','event','registration'}<=tables:
                meta=json.loads(db.execute('SELECT body FROM meta').fetchone()[0]);rows=[json.loads(r[0]) for r in db.execute('SELECT body FROM attempt')]
                assert meta['config']['mode'] in ('candidate_live','candidate_rehearsal')
                ledgers.append({'file':str(path),'mode':meta['config']['mode'],'scope':'live_matrix' if meta['config']['mode']=='candidate_live' else 'development_admission',
                    'sent':db.execute("SELECT count(*) FROM event WHERE kind='sending'").fetchone()[0],
                    'usage':sum(r['usage'] is not None for r in rows),'unknown':sum(r['state']=='unknown' for r in rows),
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
        assert active==0 and w['state']=='reaped'
        cleanup.append({'job':name,'active':active,'state':w['state'],'report':json.loads(w['report'])})
    shell=shutil.which('pwsh') or shutil.which('powershell')
    script='$candidatePorts=@('+','.join(map(str,sorted(ports)))+'); ConvertTo-Json -Compress -InputObject @(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -in $candidatePorts })'
    result=subprocess.run([shell,'-NoProfile','-NonInteractive','-Command',script],capture_output=True,text=True,encoding='utf8',timeout=45)
    assert result.returncode==0 and json.loads(result.stdout)==[],result.stderr
    archive_root=ROOT/'.local/phase1c2c2-raw';archive_root.mkdir(exist_ok=True)
    for root in sorted(roots):
        selected={p.relative_to(root).as_posix():file_hash(p) for p in files(root) if p.is_file()}
        dest=archive_root/(root.parent.name+'-'+root.name+'.zip')
        if not dest.exists():
            with zipfile.ZipFile(dest,'x',zipfile.ZIP_DEFLATED) as z:
                for n in sorted(selected):z.write(root/n,n)
        with zipfile.ZipFile(dest) as z:assert {n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}==selected
        archives.append({'root':str(root),'archive':str(dest),'sha256':file_hash(dest),'files':selected,'bytes':dest.stat().st_size})
    history=['docs/validation/'+s for s in ('phase1c0','phase1c1','phase1c2a1','phase1c2b0','phase1c2b1','phase1c2b2','phase1c2c0','phase1c2c1')]
    subprocess.run(['git','diff','--exit-code','5affb4785b537105c09cbcdaa4ef055061712ba6','--',*history],cwd=ROOT,check=True,capture_output=True)
    if a.main_root:
        from actio.candidate_evaluation import verify
        value=json.loads((a.main_root/'delivery.json').read_bytes());check=verify(value);assert check['valid'],check
        samples=DOC/'samples';samples.mkdir(exist_ok=True)
        for name in ('lineage.json','decision.json'):
            src=a.main_root/name;dst=samples/name
            if dst.exists():assert file_hash(dst)==file_hash(src)
            else:shutil.copyfile(src,dst)
        create(samples/'report.json',check['report'])
    census={scope:{k:sum(r[k] for r in ledgers if r['scope']==scope) for k in ('sent','usage','unknown','unresolved')} for scope in ('development_admission','live_matrix')}
    assert sum(r['unresolved'] for r in ledgers)==0
    log={'status':'PASS','actual_argv':sys.orig_argv,'implementation':implementation(),'roots':list(map(str,sorted(roots))),
        'ledgers':ledgers,'census':census,'jobs':cleanup,'services':services,'ports':sorted(ports),'remaining_listeners':0,
        'raw_archives':archives,'readonly_database_hashes':dbhashes,'scan':scanned,'history_unchanged':True,
        'external_provider_requests':census['live_matrix']['sent'],'historical_generation_attempts':91,'cumulative_real_generation_attempts':91+census['live_matrix']['sent'],'catalog_get':1,'raw_archive_access':'controlled local; reasoning bodies are not copied into public reports'}
    name='census-'+uuid.uuid4().hex[:12]+'.json';create(DOC/'evidence'/name,log)
    print(canonical({'status':'PASS','file':'evidence/'+name,'census':census,'jobs':len(jobs),'services':len(services)}))


if __name__=='__main__':main()
