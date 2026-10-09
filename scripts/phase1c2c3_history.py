"""Explicit local source certification; never accepts reader code from an artifact."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PIN = '3bef7e15b0eb21beeb10888eb508056592b977b0'


def main():
    scratch = ROOT / '.local/phase1c2c3-history'
    scratch.mkdir(exist_ok=False)
    old = ROOT / 'docs/validation/phase1c2c2'
    raw = subprocess.check_output(['git', '-c', 'core.autocrlf=false', 'archive', '--format=zip', PIN, 'src'], cwd=ROOT)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for name in z.namelist():
            if name.endswith('/'):
                continue
            assert name.startswith('src/') and '..' not in Path(name).parts
            dest = scratch / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(z.read(name))
    sys.path.insert(0, str(ROOT / 'tests'))
    from test_suite import GUARD
    runner = scratch / 'reader.py'
    runner.write_text("import sys,pathlib\nsys.path.insert(0,str(pathlib.Path(__file__).parent/'src'))\n" + GUARD + '''
from actio.candidate_evaluation import verify
from actio.common import file_hash, digest
old=pathlib.Path(sys.argv[1]); raw=pathlib.Path(sys.argv[2])
ref=json.loads((old/'controlled-delivery.json').read_bytes())
assert file_hash(raw)==ref['file_sha256']
r=verify(json.loads(raw.read_bytes())); assert r['valid'],r
assert r['report']==json.loads((old/'samples/report.json').read_bytes())
print(json.dumps({'valid':True,'report_exact':True,'counts':r['report']['counts'],
 'lineage':r['lineage'],'report_hash':digest(r['report']),'delivery_file_sha256':file_hash(raw)}))
''', encoding='utf8')
    delivery = Path('D:/actio-c2c2-live-v1/delivery.json')
    args = [sys.executable, '-X', 'utf8', '-I', '-S', '-B', str(runner), str(old), str(delivery)]
    proc = subprocess.run(args, capture_output=True, text=True, encoding='utf8', timeout=90)
    record = {'schema': 'task-diagnostic-source-receipt.v1', 'reader_commit': PIN,
              'argv': args, 'exit_code': proc.returncode,
              'reader_archive_sha256': hashlib.sha256(raw).hexdigest(),
              'runner_sha256': hashlib.sha256(runner.read_bytes()).hexdigest(),
              'source_files': {p.relative_to(scratch / 'src').as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted((scratch / 'src').rglob('*')) if p.is_file()},
              'guard': ['key', 'env', 'network', 'process', 'runtime import', 'write'],
              'result': json.loads(proc.stdout) if proc.returncode == 0 else None,
              'stderr': proc.stderr, 'new_model_requests': 0,
              'scope': 'local fixed-reader attestation; portable diagnostics do not rerun raw authentication; not provider signature'}
    out = ROOT / 'docs/validation/phase1c2c3/historical-source.json'
    with out.open('x', encoding='utf8', newline='\n') as f:
        json.dump(record, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write('\n')
    print(json.dumps({'exit_code': proc.returncode, 'report_exact': proc.returncode == 0,
                      'record_sha256': hashlib.sha256(out.read_bytes()).hexdigest()}))
    raise SystemExit(proc.returncode)


if __name__ == '__main__':
    main()
