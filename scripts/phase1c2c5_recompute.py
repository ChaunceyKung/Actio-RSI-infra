"""Authenticate the one fixed C5 matrix with its original reader; recompute diagnostics only."""
import argparse
import io
import json
from pathlib import Path
import subprocess
import sys
import uuid
import zipfile

ROOT=Path(__file__).resolve().parents[1]
PIN='196e8a6f3327b9d17ee0c0ba3bc45c93c38334e0'
sys.path.insert(0,str(ROOT/'tests'))
from test_suite import GUARD
from actio.common import canonical,file_hash,digest
from actio.diagnostic_runtime import review_entry,cleanup
from actio.failure_fixtures import CASES
from actio.transport_diagnostics import sources


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('D:/actio-c2c5-formal-v1'));a=p.parse_args()
    scratch=ROOT/'.local/phase1c2c5-recomputed'/uuid.uuid4().hex;scratch.mkdir(parents=True)
    archive=subprocess.check_output(['git','archive','--format=zip',PIN,'src'],cwd=ROOT)
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        for name in z.namelist():
            assert name.startswith('src/') and '..' not in Path(name).parts
            if name.endswith('/'):continue
            path=scratch/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.read(name))
    runner=scratch/'fixed-reader.py'
    code="import sys,pathlib\nsys.path.insert(0,str(pathlib.Path(__file__).parent/'src'))\n"+GUARD+'''
from actio.transport_campaign import analyze
from actio.common import digest,file_hash
from actio.budget import Ledger
root=pathlib.Path(sys.argv[1]);rows=[]
for path in sorted(root.glob('*/entry.json')):
 e=json.loads(path.read_bytes())['body']['entry'];db=path.parent/'episode/budget.sqlite';before=file_hash(db)
 ledger=Ledger(db,readonly=True)
 try:assert ledger.snapshot()==e['evidence']['ledger']
 finally:ledger.close()
 assert file_hash(db)==before
 r=analyze(e['evidence']['dataset'],e['evidence']['ledger'],e['evidence']['receives'])
 for a in e['evidence']['ledger']['attempts']:
  receives=[x for x in e['evidence']['receives'] if x['attempt']==a['id']];assert len(receives)==1
  assert receives[0]['response']['raw']==a['response']['raw'] and receives[0]['response']['status']==a['response']['status']
 rows.append({'case':path.parent.name,'entry_hash':digest(e),'database_sha256':before,'source_integrity':'PASS'})
assert len(rows)==9
print(json.dumps(rows))
'''
    runner.write_text(code,encoding='utf8',newline='\n')
    argv=[sys.executable,'-X','utf8','-I','-S','-B',str(runner),str(a.root)]
    proc=subprocess.run(argv,capture_output=True,encoding='utf8',timeout=240)
    (scratch/'fixed-reader.stdout').write_text(proc.stdout,encoding='utf8')
    (scratch/'fixed-reader.stderr').write_text(proc.stderr,encoding='utf8')
    assert proc.returncode==0,'fixed local source reader failed; controlled logs retained'
    auth=json.loads(proc.stdout);pin=json.loads((ROOT/'src/actio/pins/c5_runtime.json').read_bytes())
    assert {r['case']:r['entry_hash'] for r in auth}==pin['entries']
    original=json.loads((a.root/'report.json').read_bytes());rows=[]
    for case in CASES:
        path=a.root/case['id']/'entry.json';before=file_hash(path);entry=json.loads(path.read_bytes())['body']['entry']
        rows.append(review_entry(entry,case));assert file_hash(path)==before
    stop=json.loads((a.root/'suite-stop.json').read_bytes());clean=cleanup(stop['workers'],stop['endpoints'])
    report={**original,'status':'PASS' if all(r['status']=='PASS' for r in rows) else 'FAIL','sources':sources(),'rows':rows,
        'scope':'final diagnostic offline recomputation of fixed original runtime; no runtime replay',
        'original_report_sha256':file_hash(a.root/'report.json'),'original_status':original['status'],
        'runtime_commit':PIN,'runtime_sources':original['sources'],'cleanup':clean,
        'authentication':{'fixed_reader':PIN,'argv':argv,'exit':proc.returncode,'rows':auth,'runner_sha256':file_hash(runner)},
        'tool_sha256':file_hash(Path(__file__)),'argv':sys.orig_argv,'additional_loopback_sends':0}
    dest=ROOT/'docs/validation/phase1c2c5'/('runtime-recomputed-'+scratch.name[:12]+'.json')
    dest.write_text(canonical(report),encoding='utf8',newline='\n')
    print(canonical({'status':report['status'],'receipt':str(dest),'totals':report['totals'],'failed':[{r['case']:[k for k,v in r['checks'].items() if not v]} for r in rows if r['status']!='PASS']}))
    return 0 if report['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
