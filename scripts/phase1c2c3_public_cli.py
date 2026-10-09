"""Documented literal -m commands, separate from guarded runpy CLI evidence."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from actio.common import canonical
from actio.task_diagnostics import source_pins


def main():
    dest = ROOT / '.local/phase1c2c3-public-env'
    folder = ROOT / 'docs/validation/phase1c2c3'
    records = []
    commands = [[sys.executable, '-X', 'utf8', '-I', '-B', 'scripts/install_task_diagnostics.py', str(dest)]]
    python = str(dest / 'Scripts/python.exe')
    commands += [[python, '-X', 'utf8', '-I', '-B', '-m', 'actio.task_diagnostics', *args] for args in [
        ['plan'], ['analyze', '--source', 'docs/validation/phase1c2c2', '--output', '.local/phase1c2c3-public-analysis',
                   '--source-receipt', 'docs/validation/phase1c2c3/historical-source.json', '--dataset', 'docs/validation/phase1c2c3/frozen-design/dataset.json'],
        ['verify', '.local/phase1c2c3-public-analysis'], ['verify', 'docs/validation/phase1c2c3/package']]]
    for argv in commands:
        proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, encoding='utf8', timeout=60)
        records.append({'argv': argv, 'exit_code': proc.returncode, 'stdout_hash': hashlib.sha256(proc.stdout.encode()).hexdigest(),
                        'result': json.loads(proc.stdout) if proc.returncode == 0 else None, 'stderr': proc.stderr})
        if proc.returncode:
            break
    record = {'schema': 'task-diagnostic-literal-cli.v1', 'status': 'PASS' if len(records) == len(commands) and all(r['exit_code'] == 0 for r in records) else 'FAIL',
              'source': source_pins(), 'argv': [sys.executable, *sys.orig_argv[1:]], 'commands': records,
              'tooling': {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in ('scripts/install_task_diagnostics.py', 'scripts/phase1c2c3_public_cli.py')},
              'new_model_requests': 0, 'new_workers': 0}
    name = 'literal-cli-' + hashlib.sha256(canonical(record).encode()).hexdigest()[:12] + '.json'
    with (folder / 'evidence' / name).open('x', encoding='utf8', newline='\n') as f:
        f.write(canonical(record))
    print(canonical({'status': record['status'], 'commands': len(records), 'record': name}))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
