"""Read-only completion audit: one installed wheel, original methods and history bytes."""
import argparse
import ast
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
BASE = '6ba6573dc2057b12624477c3b3a90cbf246f8f63'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def methods(text):
    return {n.name + '.' + f.name for n in ast.parse(text).body if isinstance(n, ast.ClassDef)
            for f in n.body if isinstance(f, ast.FunctionDef) and f.name.startswith('test_')}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--wheel', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(exist_ok=False)
    import actio
    installed = Path(actio.__file__).parent
    assert ROOT not in installed.parents
    with zipfile.ZipFile(a.wheel) as wheel:
        files = {n.removeprefix('actio/'): wheel.read(n) for n in wheel.namelist()
                 if n.startswith('actio/') and not n.endswith('/')}
    assert all((installed / n).read_bytes() == b == (ROOT / 'src/actio' / n).read_bytes()
               for n, b in files.items())
    archive = subprocess.check_output(['git', 'archive', '--format=zip', BASE], cwd=ROOT)
    with zipfile.ZipFile(io.BytesIO(archive)) as old:
        historical = [n for n in old.namelist() if n.startswith(('docs/validation/', 'scripts/'))
                      and not n.endswith('/')]
        assert len(historical) == 1048
        assert all((ROOT / n).read_bytes() == old.read(n) for n in historical)
    previous = subprocess.check_output(['git', 'archive', '--format=zip', '8ab5b5a', 'tests'], cwd=ROOT)
    test_rows = []
    with zipfile.ZipFile(io.BytesIO(previous)) as old:
        for n in old.namelist():
            if not n.startswith('tests/test_') or not n.endswith('.py'):
                continue
            before = methods(old.read(n).decode('utf8'))
            after = methods((ROOT / n).read_text(encoding='utf8'))
            assert before <= after, (n, before - after)
            test_rows.append({'file': n, 'original': sorted(before), 'added': sorted(after - before)})
    assert sum(len(r['original']) for r in test_rows) == 163
    resources = {}
    for name in ('schema.sql', 'candidate_schema.sql', 'evaluation_schema.sql', 'legacy_schema.sql'):
        resources[name] = 'adapters/persistence/' + name
    for name in ('plugins/common.mjs', 'plugins/guard.mjs', 'plugins/transport.mjs', 'fixtures/provider.mjs'):
        resources[name] = 'adapters/transport/' + name
    for name in ('readiness_quote.json', 'evaluation_history.json', 'task_diagnostic_trust.json',
                 'pins/c5_runtime.json', 'pins/concordia.json', '_vendor/sotopia_provenance.json'):
        resources[name] = name
    for before, after in resources.items():
        data = subprocess.check_output(['git', 'show', '8ab5b5a:src/actio/' + before], cwd=ROOT)
        assert data == files[after], (before, after)
    jobs = []
    commands = [('pip-check', [sys.executable, '-m', 'pip', '--isolated', 'check'])]
    for exe, mod in [('actio', 'actio'), ('actio-eval', 'actio.evaluation'),
                     ('actio-candidate', 'actio.candidate'), ('actio-candidate-evaluation', 'actio.candidate_evaluation')]:
        commands += [(exe, [str(Path(sys.executable).with_name(exe + '.exe')), '--help']),
                     (mod, [sys.executable, '-I', '-B', '-m', mod, '--help'])]
    for name, cmd in commands:
        result = subprocess.run(cmd, cwd=a.output, capture_output=True, timeout=60)
        assert result.returncode == 0, (name, result.stderr.decode(errors='replace'))
        jobs.append({'name': name, 'exit': result.returncode, 'stdout_sha256': sha(result.stdout),
                     'stderr_sha256': sha(result.stderr)})
    result = {'status': 'PASS', 'wheel_sha256': sha(a.wheel.read_bytes()), 'installed': str(installed),
              'wheel_source_installed_equal': True, 'product_files': {n: sha(b) for n, b in files.items()},
              'historical_files': len(historical), 'historical_bytes_unchanged': True,
              'resource_moves_bytes_unchanged': resources, 'original_test_methods': 163,
              'test_methods': test_rows, 'jobs': jobs, 'credential_reads': 0, 'provider_requests': 0,
              'scope': 'packaging and preservation; full regression and runtime receipts are separate'}
    (a.output / 'receipt.json').write_text(json.dumps(result, indent=2), encoding='utf8')
    print(json.dumps({'status': 'PASS', 'wheel_sha256': result['wheel_sha256'], 'historical_files': 1048,
                      'original_methods': 163, 'jobs': len(jobs)}))


if __name__ == '__main__':
    main()
