"""Install a minimal stdlib reader and exercise actual public CLI under guards."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import venv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from actio.common import canonical
from actio.task_diagnostics import SOURCE_FILES, source_pins

GUARD = r'''
import sys,os,json,pathlib,runpy
output = None if sys.argv[1]=='-' else pathlib.Path(sys.argv[1]).resolve()
args=sys.argv[2:]
blocked=('deepseek_harness','concordia','mcp','actio.runtime','actio.transport','actio.gateway','actio.eval_worker','actio.host','actio.supervisor')
def deny_write(path):
 p=pathlib.Path(path).resolve()
 if output is None or not (p==output or p.is_relative_to(output)):
  raise RuntimeError('write outside explicit output denied')
def audit(event,args):
 if event.startswith('socket.') or event in ('subprocess.Popen','os.system','os.posix_spawn','os.spawn'):
  raise RuntimeError('network/process denied')
 if event=='import' and any(args[0]==n or args[0].startswith(n+'.') for n in blocked):
  raise RuntimeError('runtime import denied')
 if event=='open':
  if any(x in str(args[0]).lower() for x in ('token_key','credentials','.sqlite')) or pathlib.Path(str(args[0])).name=='delivery.json':
   raise RuntimeError('credential/raw/database access denied')
  if isinstance(args[1],str) and any(x in args[1] for x in 'wax+') or isinstance(args[2],int) and args[2]&(1|2|64|512|1024):
   deny_write(args[0])
 if event in ('os.mkdir','os.remove','os.rmdir','os.rename','os.link','os.symlink'):
  deny_write(args[0])
  if event in ('os.rename','os.link','os.symlink'):deny_write(args[1])
sys.addaudithook(audit)
class NoEnv(dict):
 def denied(self,*a,**kw):raise RuntimeError('environment access denied')
 get=__getitem__=__iter__=__contains__=keys=items=values=copy=denied
os.environ=NoEnv()
os.getenv=os.environ.denied
sys.argv=['actio.task_diagnostics',*args]
try:
 runpy.run_module('actio.task_diagnostics',run_name='__main__')
except SystemExit as exit:
 assert not any(any(n==b or n.startswith(b+'.') for b in blocked) for n in sys.modules)
 raise
'''


def main():
    stage = ROOT / 'docs/validation/phase1c2c3'
    root = ROOT / '.local/phase1c2c3-offline-env'
    if root.exists():
        # A previous failed attempt is retained; use an additional environment.
        root = root.with_name(root.name + '-' + str(time.time_ns()))
    venv.EnvBuilder(with_pip=False).create(root)
    package = root / 'Lib/site-packages/actio'; package.mkdir(parents=True)
    for name in SOURCE_FILES:
        shutil.copyfile(ROOT / 'src/actio' / name, package / name)
    python = root / 'Scripts/python.exe'
    assert {n: hashlib.sha256((package / n).read_bytes().replace(b'\r\n', b'\n')).hexdigest() for n in SOURCE_FILES} == source_pins()
    output = stage / 'package'
    if output.exists():
        output = ROOT / '.local' / ('phase1c2c3-package-' + str(time.time_ns()))
    moved = ROOT / '.local' / ('phase1c2c3-relocated-' + str(time.time_ns()))
    fallback = ROOT / '.local' / ('phase1c2c3-public-' + str(time.time_ns()))
    old = ROOT / 'docs/validation/phase1c2c2'
    records = []
    record = {'schema': 'task-diagnostic-cli-acceptance.v1', 'source': source_pins(), 'source_install_equal': True,
              'environment': 'clean Python 3.12 venv, no pip/third-party packages; explicit pure import closure only',
              'python': str(python), 'argv': [sys.executable, *sys.orig_argv[1:]], 'commands': records,
              'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'guard': GUARD, 'new_model_requests': 0, 'new_workers': 0}
    def run(args, write=None, expected=0):
        argv = [str(python), '-X', 'utf8', '-I', '-B', '-c', GUARD, str(write) if write else '-', *args]
        result = subprocess.run(argv, cwd=root, capture_output=True, text=True, encoding='utf8', timeout=60)
        body = json.loads(result.stdout) if result.stdout.startswith('{') else None
        records.append({'argv': argv, 'exit_code': result.returncode, 'expected_exit': expected,
                        'stdout_sha256': hashlib.sha256(result.stdout.encode()).hexdigest(), 'result': body, 'stderr': result.stderr})
        assert result.returncode == expected, result.stderr or result.stdout
        return body
    try:
        run(['plan'])
        run(['analyze', '--source', str(old), '--output', str(output), '--source-receipt', str(stage / 'historical-source.json'),
             '--dataset', str(stage / 'frozen-design/dataset.json')], output)
        original = run(['verify', str(output)])
        shutil.copytree(output, moved)
        relocated = run(['verify', str(moved)])
        assert original == relocated
        run(['analyze', '--source', str(old), '--output', str(output)], output, expected=1)
        run(['analyze', '--source', str(old), '--output', str(fallback)], fallback)
        result = run(['verify', str(fallback)])
        assert result['source_assurance']['source_assurance'] == 'public_projection_only'
        run(['analyze', '--source', str(old), '--output', str(fallback), '--source', str(old)], expected=1)
        record.update(status='PASS', actual_commands=len(records), relocation_equal=True, package_manifest_hash=original['manifest_hash'])
    except Exception as exc:
        record.update(status='FAIL', failure=type(exc).__name__ + ': ' + str(exc))
    folder = stage / 'evidence'; folder.mkdir(exist_ok=True)
    name = 'cli-' + hashlib.sha256(canonical(record).encode()).hexdigest()[:12] + '.json'
    with (folder / name).open('x', encoding='utf8', newline='\n') as f:
        f.write(canonical(record))
    print(canonical({'status': record['status'], 'commands': len(records), 'record': name, 'failure': record.get('failure')}))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
