"""Retain the failed rehearsal's facts and independently inspect OS cleanup."""
import ctypes as C
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import uuid
from actio.common import canonical,file_hash
from actio.pilot import create,now
from actio.pilot_contract import implementation
from actio.supervisor import Job,kernel

ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2c4'


def main():
    root=Path('D:/actio-c2c4-rehearsal-v1');matrix=root/'matrix'
    failure=DOC/'evidence/cli-1e6399a5e5e8.json'
    assert json.loads(failure.read_bytes())['status']=='FAIL'
    ledgers=[];jobs=[];preserved={}
    for folder in sorted(matrix.glob('ep-*')):
        for name in ('budget.sqlite','domain.sqlite'):
            path=folder/name;before=file_hash(path)
            db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
            try:
                if name=='budget.sqlite':
                    attempts=[json.loads(row[0]) for row in db.execute('SELECT body FROM attempt')]
                    ledgers.append({'unit':folder.name,'sent':db.execute("SELECT count(*) FROM event WHERE kind='sending'").fetchone()[0],
                        'unknown':sum(a['state']=='unknown' for a in attempts),
                        'active':sum(a['state'] in ('authorized','reserved','sending') for a in attempts)})
                else:
                    for row in db.execute('SELECT * FROM worker'):
                        k=kernel();handle=k.OpenJobObjectW(4,False,row['job'])
                        if not handle:assert C.get_last_error()==2;active=0
                        else:
                            job=object.__new__(Job);job.k=k;job.handle=handle
                            try:active=job.snapshot()['active']
                            finally:k.CloseHandle(handle)
                        jobs.append({'job':row['job'],'state':row['state'],'active':active})
            finally:db.close()
            assert file_hash(path)==before;preserved[str(path)]=before
    endpoint=json.loads((matrix/'ep-00/config.json').read_bytes())['endpoint'];port=int(endpoint.split(':')[-1].split('/')[0])
    command=("$c4Controllers=@(Get-CimInstance Win32_Process -Filter \"Name = 'python.exe'\" | "
             "Where-Object { $_.CommandLine -like '*actio-c2c4-rehearsal-v1*' } | Select-Object -ExpandProperty ProcessId); "
             f"$c4Listeners=@(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object {{ $_.LocalPort -eq {port} }} | Select-Object LocalPort,OwningProcess); "
             "@{controllers=$c4Controllers;listeners=$c4Listeners} | ConvertTo-Json -Compress")
    process=subprocess.run([shutil.which('pwsh') or shutil.which('powershell'),'-NoProfile','-NonInteractive','-Command',command],capture_output=True,text=True,encoding='utf8',timeout=45)
    assert process.returncode==0,process.stderr
    os_state=json.loads(process.stdout)
    db=sqlite3.connect((root/'candidates.sqlite').as_uri()+'?mode=ro',uri=True)
    try:lineage={table:db.execute('SELECT count(*) FROM '+table).fetchone()[0] for table in ('evaluation','evaluation_decision','decision')}
    finally:db.close()
    valid=not os_state['controllers'] and not os_state['listeners'] and all(j['state']=='reaped' and j['active']==0 for j in jobs) and not any(l['active'] for l in ledgers)
    record={'status':'PASS' if valid else 'FAIL','scope':'OS cleanup after failed development rehearsal; does not repair the failed CLI or complete its evaluation',
        'root':str(root),'actual_argv':sys.orig_argv,'script_sha256':file_hash(Path(__file__)),'implementation':implementation(),'checked_utc':now(),
        'failure_receipt':failure.relative_to(DOC).as_posix(),'failure_receipt_sha256':file_hash(failure),
        'checkpoint':json.loads((matrix/'checkpoint-ep-63.json').read_bytes()),'ledgers':ledgers,'jobs':jobs,'os_state':os_state,
        'database_hashes_unchanged':preserved,'lineage_counts':lineage,'service_endpoint':endpoint,'service_join_receipt':False,
        'credential_scan_completed':(matrix/'credential-scan.json').exists(),'delivery_created':(root/'delivery.json').exists(),
        'local_sent':sum(l['sent'] for l in ledgers),'local_unknown':sum(l['unknown'] for l in ledgers),
        'claims_deleted':0,'external_provider_requests':0,'full_controller_recovery':'unsupported'}
    dest=DOC/'evidence'/('interruption-'+uuid.uuid4().hex[:12]+'.json');create(dest,record)
    print(canonical({'status':record['status'],'receipt':str(dest),'local_sent':record['local_sent'],'jobs':len(jobs),'lineage':lineage,'join_receipt':False}))
    assert valid


if __name__=='__main__':main()
