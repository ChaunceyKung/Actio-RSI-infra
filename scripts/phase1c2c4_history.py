"""Authenticate fixed historical readers and the authoritative C2C2 database."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/validation/phase1c2c4'
PINS = {'c2c2': '3bef7e15b0eb21beeb10888eb508056592b977b0',
        'c2c3': '0a66334d61a0de302bbf8f5e15ee1db1b9d2e8fb'}


def main():
    sys.path.insert(0, str(ROOT / 'tests'))
    from test_suite import GUARD
    records = []
    for name, pin in PINS.items():
        scratch = ROOT / '.local/phase1c2c4-history' / name
        scratch.mkdir(parents=True, exist_ok=False)
        raw = subprocess.check_output(['git', 'archive', '--format=zip', pin, 'src'], cwd=ROOT)
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            for entry in archive.namelist():
                assert entry.startswith('src/') and '..' not in Path(entry).parts
                if entry.endswith('/'): continue
                dest = scratch / entry
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(archive.read(entry))
        code = ("import sys,pathlib\nsys.path.insert(0,str(pathlib.Path(__file__).parent/'src'))\n" + GUARD +
                "\nfrom actio.common import digest,file_hash\nroot=pathlib.Path(sys.argv[1])\n")
        if name == 'c2c2':
            code += '''
from actio.candidate_evaluation import verify
from actio.store import Store
delivery=pathlib.Path('D:/actio-c2c2-live-v1/delivery.json')
database=delivery.with_name('candidates.sqlite')
before=file_hash(database)
d=json.loads(delivery.read_bytes());r=verify(d);assert r['valid'],r
s=Store(database,readonly=True)
try:
 assert s.version==4
 lineage=s.evaluation_lineage()
 assert lineage==d['body']['lineage']
finally:s.close()
assert file_hash(database)==before
assert r['report']==json.loads((root/'docs/validation/phase1c2c2/samples/report.json').read_bytes())
print(json.dumps({'valid':True,'delivery_file_sha256':file_hash(delivery),'database_sha256':before,
 'database_unchanged':True,'lineage_sha256':lineage['sha256'],'report_hash':digest(r['report']),
 'lineage':r['lineage'],'counts':r['report']['counts']}))
'''
        else:
            code += '''
from actio.task_diagnostics import verify
package=root/'docs/validation/phase1c2c3/package'
r=verify(package);assert r['valid'],r
print(json.dumps({'valid':True,'result':r}))
'''
        runner = scratch / 'reader.py'
        runner.write_text(code, encoding='utf8')
        argv = [sys.executable, '-X', 'utf8', '-I', '-S', '-B', str(runner), str(ROOT)]
        run = subprocess.run(argv, capture_output=True, text=True, encoding='utf8', timeout=180)
        records.append({'reader': pin, 'argv': argv, 'archive_sha256': hashlib.sha256(raw).hexdigest(),
                        'runner_sha256': hashlib.sha256(runner.read_bytes()).hexdigest(),
                        'sources': {p.relative_to(scratch/'src').as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in sorted((scratch/'src').rglob('*')) if p.is_file()},
                        'exit_code': run.returncode, 'stderr': run.stderr,
                        'result': json.loads(run.stdout) if run.returncode == 0 else None})
    DOC.mkdir(parents=True, exist_ok=True)
    result = {'status': 'PASS' if all(r['exit_code']==0 for r in records) else 'FAIL', 'readers': records,
              'guard': ['key','env','network','process','runtime import','write'], 'new_provider_requests':0}
    with (DOC/'history.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({'status':result['status'],'readers':[{'reader':r['reader'],'exit':r['exit_code'],'stderr':r['stderr']} for r in records]}))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
