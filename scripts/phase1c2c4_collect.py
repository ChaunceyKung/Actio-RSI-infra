"""C2C4-only runtime/ledger census, explicit OS cleanup and historical preservation."""
import argparse
import ctypes as C
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import uuid
from actio.common import canonical,digest,file_hash
from actio.pilot_contract import implementation
from actio.runtime import verify_runtime
from actio.supervisor import Job,kernel
from phase1c2c0_collect import files,scan,create

ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2c4'
BASE='dbb0f815c5d1baae28e37ddaeb8f68b6b442f0dc'


def main():
    p=argparse.ArgumentParser();p.add_argument('--rehearsal-root',type=Path,required=True);p.add_argument('--live-root',type=Path);a=p.parse_args()
    roots={a.rehearsal_root.resolve()};jobs={};services=[];ledgers=[];raw=[];ports=set();receipts=[]
    if a.live_root:roots.add(a.live_root.resolve())
    for path in (DOC/'evidence').glob('*.json'):
        d=json.loads(path.read_bytes())
        if 'suite' in d or d.get('kind') in ('full_rehearsal','offline_cli'):
            receipts.append({'file':path.relative_to(DOC).as_posix(),'sha256':file_hash(path),'status':d.get('status',d.get('exit_code'))})
            for test in d.get('tests',[]):
                if test.get('evidence',{}).get('root'):roots.add(Path(test['evidence']['root']))
            if d.get('root'):roots.add(Path(d['root']))
    verify_runtime()
    assert all(file_hash(ROOT/'src/actio'/n)==h for n,h in implementation().items())
    selected=sorted({path for root in roots for path in files(root) if path.is_file()})
    for root in sorted(roots):
        # A killed development wrapper cannot leave a truthful join receipt.
        # Preserve that gap and independently check the actual bound port.
        if (root/'receives.json').is_file() and not (root/'service.json').exists():
            configs=list((root/'matrix').glob('ep-*/config.json'))
            endpoints={json.loads(p.read_bytes())['endpoint'] for p in configs}
            assert len(endpoints)==1
            endpoint=endpoints.pop();assert endpoint.startswith('http://127.0.0.1:')
            ports.add(int(endpoint.split(':')[-1].split('/')[0]))
            services.append({'file':None,'root':str(root),'endpoint':endpoint,'joined':False,
                'receives':len(json.loads((root/'receives.json').read_bytes())),
                'scope':'failed development rehearsal','cleanup':'controller terminated; no join receipt; bound port checked below',
                'external_provider_requests':0})
    # Rehearsal uses ephemeral fake keys; real-key exact scan is a separate publication operation.
    scanned=scan(selected)
    for path in selected:
        if path.name=='service.json':
            d=json.loads(path.read_bytes());assert d['joined'];ports.add(int(d['endpoint'].split(':')[-1].split('/')[0]));services.append({'file':str(path),**d})
        if path.suffix!='.sqlite':continue
        before=file_hash(path);db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
        try:
            tables={r[0] for r in db.execute('SELECT name FROM sqlite_master')}
            if 'worker' in tables:
                for row in db.execute('SELECT * FROM worker'):jobs[row['job']]=dict(row)
            if {'meta','attempt','event','registration'}<=tables:
                meta=json.loads(db.execute('SELECT body FROM meta').fetchone()[0]);attempts=[json.loads(r[0]) for r in db.execute('SELECT body FROM attempt')]
                assert meta['config']['schema']=='pilot-config.v10'
                scope='live' if meta['config']['mode']=='robustness_live' else 'full_rehearsal' if path.is_relative_to(a.rehearsal_root.resolve()) else 'development'
                ledgers.append({'file':str(path),'scope':scope,'mode':meta['config']['mode'],
                    'sent':db.execute("SELECT count(*) FROM event WHERE kind='sending'").fetchone()[0],
                    'attempts':len(attempts),'usage':sum(t['usage'] is not None for t in attempts),
                    'unknown':sum(t['state']=='unknown' for t in attempts),
                    'active':sum(t['state'] in ('authorized','reserved','sending') for t in attempts)})
        finally:db.close()
        assert file_hash(path)==before
    cleanup=[]
    for name,worker in jobs.items():
        k=kernel();handle=k.OpenJobObjectW(4,False,name)
        if not handle:assert C.get_last_error()==2;active=0
        else:
            job=object.__new__(Job);job.k=k;job.handle=handle
            try:active=job.snapshot()['active']
            finally:k.CloseHandle(handle)
        assert active==0 and worker['state']=='reaped'
        cleanup.append({'job':name,'root':worker['root'],'state':worker['state'],'active':active,'report':json.loads(worker['report'])})
    script='$robustnessPorts=@('+','.join(map(str,sorted(ports)))+'); ConvertTo-Json -Compress -InputObject @(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -in $robustnessPorts })'
    proc=subprocess.run([shutil.which('pwsh') or shutil.which('powershell'),'-NoProfile','-NonInteractive','-Command',script],capture_output=True,text=True,encoding='utf8',timeout=45)
    assert proc.returncode==0 and json.loads(proc.stdout)==[],proc.stderr
    inventory_root=ROOT/'.local/phase1c2c4-inventories';inventory_root.mkdir(exist_ok=True)
    for root in sorted(roots):
        inventory={p.relative_to(root).as_posix():file_hash(p) for p in files(root) if p.is_file()}
        dest=inventory_root/(root.parent.name+'-'+root.name+'-'+digest(inventory)[:12]+'.json')
        if not dest.exists():create(dest,inventory)
        raw.append({'root':str(root),'inventory':str(dest),'sha256':file_hash(dest),'files':len(inventory),
                    'scope':'controlled original files retained; no raw protocol/reasoning/database published'})
    oldclaims=json.loads((ROOT/'docs/validation/phase1c2c2/execution-claims.json').read_bytes())
    for name,entry in oldclaims['files'].items():assert file_hash(Path(oldclaims['namespace'])/name)==entry['sha256']
    oldmanifest=json.loads((ROOT/'docs/validation/phase1c2c2/evidence_manifest.json').read_bytes())
    oldcensus=json.loads((ROOT/'docs/validation/phase1c2c2'/oldmanifest['census']).read_bytes())
    preserved=0
    for name,h in oldcensus['readonly_database_hashes'].items():
        assert file_hash(Path(name))==h,name
        preserved+=1
    h=json.loads((DOC/'history.json').read_bytes())['readers'][0]['result']
    assert file_hash(Path('D:/actio-c2c2-live-v1/candidates.sqlite'))==h['database_sha256']
    assert file_hash(Path('D:/actio-c2c2-live-v1/delivery.json'))==h['delivery_file_sha256']
    historical=[str(p.relative_to(ROOT)) for p in (ROOT/'docs/validation').iterdir() if p.name!='phase1c2c4']
    subprocess.run(['git','diff','--exit-code',BASE,'--',*historical],cwd=ROOT,check=True,capture_output=True)
    census={scope:{k:sum(r[k] for r in ledgers if r['scope']==scope) for k in ('sent','attempts','usage','unknown','active')} for scope in ('development','full_rehearsal','live')}
    assert sum(r['active'] for r in ledgers)==0
    result={'status':'PASS','implementation':implementation(),'argv':sys.orig_argv,'roots':list(map(str,sorted(roots))),
        'receipts':receipts,'ledgers':ledgers,'census':census,'jobs':cleanup,'services':services,'ports':sorted(ports),
        'remaining_listeners':0,'raw_inventories':raw,'scan':scanned,'permanent_claims_deleted':0,
        'services_joined':sum(s['joined'] is True for s in services),
        'services_without_join_receipt':sum(s['joined'] is False for s in services),
        'historical_claims_preserved':len(oldclaims['files']),'historical_database_hashes_preserved':preserved,
        'historical_controlled_delivery_and_authority_preserved':True,'historical_public_artifacts_unchanged':True,
        'historical_generation_attempts':139,'catalog_get':1,'cumulative_real_generation_attempts':139+census['live']['sent'],
        'inactive_authority_basis':'all owned Jobs absent/inactive and ledger authorized/reserved/sending=0; permanent claim/active marker files retained, unknown accounting not released'}
    dest=DOC/'evidence'/('census-'+uuid.uuid4().hex[:12]+'.json');create(dest,result)
    print(canonical({'status':'PASS','file':str(dest),'census':census,'jobs':len(jobs),'services':len(services),'old_databases':preserved}))


if __name__=='__main__':main()
