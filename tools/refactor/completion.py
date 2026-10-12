"""0.2 installed/source/entrypoint audit; history uses Git blob bytes, not CRLF."""
import argparse
import ast
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile
import configparser

ROOT=Path(__file__).resolve().parents[2]
BASE='205cf8b1c2551e4075054131b5ff8baa0aaaadfa'
HISTORY='6ba6573dc2057b12624477c3b3a90cbf246f8f63'
def sha(data):return hashlib.sha256(data).hexdigest()
def methods(text):
 return {n.name+'.'+f.name for n in ast.parse(text).body if isinstance(n,ast.ClassDef)
         for f in n.body if isinstance(f,ast.FunctionDef) and f.name.startswith('test_')}
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def main():
 p=argparse.ArgumentParser();p.add_argument('--wheel',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(exist_ok=False)
 import actio
 installed=Path(actio.__file__).parent;assert ROOT not in installed.parents
 with zipfile.ZipFile(a.wheel) as wheel:
  files={n.removeprefix('actio/'):wheel.read(n) for n in wheel.namelist() if n.startswith('actio/') and not n.endswith('/')}
  ep=configparser.ConfigParser();ep.read_string(wheel.read('actio_rsi-0.2.0.dist-info/entry_points.txt').decode())
  assert dict(ep['console_scripts'])=={'actio':'actio.interfaces.cli.main:main'}
  assert 'Version: 0.2.0' in wheel.read('actio_rsi-0.2.0.dist-info/METADATA').decode().splitlines()
 assert actio.__version__=='0.2.0'
 assert all((installed/n).read_bytes()==b==(ROOT/'src/actio'/n).read_bytes() for n,b in files.items())
 roots=sorted(n for n in files if '/' not in n);assert roots==['README.md','__init__.py','__main__.py']
 source_py={p.relative_to(ROOT/'src/actio').as_posix() for p in (ROOT/'src/actio').rglob('*.py')}
 installed_py={p.relative_to(installed).as_posix() for p in installed.rglob('*.py')}
 assert source_py==installed_py=={n for n in files if n.endswith('.py')}
 with zipfile.ZipFile(io.BytesIO(git('archive','--format=zip',HISTORY))) as old:
  historical={n:sha(old.read(n)) for n in old.namelist() if n.startswith(('docs/validation/','scripts/')) and not n.endswith('/')}
 assert len(historical)==1048
 changed=set(git('-c','core.quotepath=false','diff','--name-only',HISTORY,'--','docs/validation','scripts').decode().splitlines())
 assert not changed.intersection(historical),sorted(changed.intersection(historical))
 test_rows=[]
 with zipfile.ZipFile(io.BytesIO(git('archive','--format=zip',BASE,'tests'))) as old:
  for n in old.namelist():
   if n.startswith('tests/test_') and n.endswith('.py'):
    before=methods(old.read(n).decode());after=methods((ROOT/n).read_text(encoding='utf8'));assert before<=after,(n,before-after)
    test_rows.append(dict(file=n,original=sorted(before),added=sorted(after-before)))
 assert len(test_rows)==34 and sum(len(r['original']) for r in test_rows)==165
 migration=json.loads((ROOT/'docs/validation/refactor_entrypoints/migration.json').read_bytes());resources={}
 for old,new in migration['resources'].items():resources[old]='resources/'+new
 for name in files:
  if name.endswith(('.sql','.mjs')) or 'LICENSE' in name or name=='_vendor/sotopia_provenance.json':resources[name]=name
 resource_rows=[]
 for old,new in resources.items():
  before=git('show',BASE+':src/actio/'+old);after=files[new]
  expected=before.replace(b'actio.budget',b'actio.interfaces.ipc.budget') if old.endswith('/transport.mjs') else before
  assert expected==after,(old,new)
  resource_rows.append(dict(old=old,new=new,old_sha256=sha(before),new_sha256=sha(after),mapping='budget module string only' if expected!=before else 'byte identical'))
 jobs=[]
 def run(name,cmd,expected=0,input=None):
  r=subprocess.run(cmd,input=input,cwd=a.output,capture_output=True,timeout=60)
  (a.output/(name+'.stdout')).write_bytes(r.stdout);(a.output/(name+'.stderr')).write_bytes(r.stderr)
  assert r.returncode==expected,(name,r.returncode,r.stderr.decode(errors='replace'))
  jobs.append(dict(name=name,exit=r.returncode,expected=expected,stdout_sha256=sha(r.stdout),stderr_sha256=sha(r.stderr)))
  return r
 py=[sys.executable,'-I','-B']
 run('pip-check',[sys.executable,'-m','pip','--isolated','check'])
 for command in ('run','verify','evaluate','candidate','candidate-evaluation','preflight','readiness','gateway','pilot','suite','robustness','diagnostics task','diagnostics transport','campaign verify'):
  run('help-'+command.replace(' ','-'),py+['-m','actio',*command.split(),'--help'])
 run('console-version',[str(Path(sys.executable).with_name('actio.exe')),'--version'])
 run('module-version',py+['-m','actio','--version'])
 code='import importlib.util; names='+repr(migration['removed_modules'])+'; assert all(importlib.util.find_spec(n) is None for n in names); print("removed APIs absent")'
 run('removed-imports',py+['-c',code])
 for name in migration['removed_modules']:
  run('removed-'+name,py+['-m',name],1)
 assert all(not Path(sys.executable).with_name(n+'.exe').exists() for n in ('actio-eval','actio-candidate','actio-candidate-evaluation'))
 run('unknown-command',py+['-m','actio','not-a-command'],2)
 run('database-success',py+['-m','actio','run','--db',str(a.output/'smoke.sqlite'),'init'])
 run('bundle-rejection',py+['-m','actio','verify',str(a.output/'missing')],2)
 result=dict(status='PASS',wheel_sha256=sha(a.wheel.read_bytes()),installed=str(installed),root_files=roots,
  wheel_source_installed_equal=True,product_files={n:sha(b) for n,b in files.items()},
  historical_files=1048,historical_basis='Git blob: git diff against fixed archive; no old tracked path changed',historical=historical,
  resources=resource_rows,original_test_methods=165,test_methods=test_rows,jobs=jobs,credential_reads=0,provider_requests=0,
  scope='packaging and preservation; runtime regression and formal matrix are separate receipts')
 (a.output/'receipt.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps({k:result[k] for k in ('status','wheel_sha256','historical_files','original_test_methods')}))
if __name__=='__main__':main()
