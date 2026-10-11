"""Repo-external wheel smoke plus pure import guards, without optional runtimes."""
import argparse,hashlib,json,pathlib,subprocess,sys,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[2]
def main():
 p=argparse.ArgumentParser();p.add_argument('--python',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--wheel',type=pathlib.Path,required=True);a=p.parse_args();a.output.mkdir(exist_ok=False)
 sys.path.insert(0,str(ROOT/'tests'));from test_suite import GUARD
 probe=a.output/'guard.py';probe.write_text('import sys\nsys.dont_write_bytecode=True\n'+GUARD+'\nfrom actio.transport_diagnostics import main\nraise SystemExit(main())\n',encoding='utf8')
 jobs=[]
 def run(label,args,expected=0):
  r=subprocess.run([str(a.python),'-X','utf8','-I','-B',*args],cwd=a.output,capture_output=True,encoding='utf8',timeout=60)
  (a.output/(label+'.stdout')).write_text(r.stdout,encoding='utf8');(a.output/(label+'.stderr')).write_text(r.stderr,encoding='utf8')
  jobs.append({'name':label,'exit':r.returncode,'expected':expected,'stdout_sha256':hashlib.sha256(r.stdout.encode()).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr.encode()).hexdigest()})
  return r
 run('export',['-m','actio.transport_diagnostics','export',str(a.output/'export')]);run('repeat-export',['-m','actio.transport_diagnostics','export',str(a.output/'export')],2)
 for command in ('plan','verify','analyze'):run(command,[str(probe),command,*([str(a.output/'export/package.json')] if command!='plan' else [])])
 for mod in ('actio','actio.evaluation','actio.candidate','actio.candidate_evaluation'):run(mod.replace('.','-'),['-m',mod,'--help'])
 run('pure-import',['-c',"import sys; from actio.contracts.json import canonical,seal; from actio.tasks.diagnostic import dataset; from actio.measurement.oracle import evaluate; assert not any(n in sys.modules for n in ('sqlite3','actio.runtime','deepseek_harness','concordia','actio.eval_contract','actio.verify')); assert dataset()['body']['cards']; print('PASS')"])
 run('no-optional-runtime',['-c',"import importlib.util; assert importlib.util.find_spec('deepseek_harness') is None; assert importlib.util.find_spec('concordia') is None; print('PASS')"])
 with zipfile.ZipFile(a.wheel) as z:
  required=['actio/schema.sql','actio/evaluation_history.json','actio/plugins/transport.mjs','actio/_vendor/SOTOPIA_LICENSE','actio/adapters/transport/DSH_LICENSE.txt'];assert all(n in z.namelist() for n in required)
 result={'status':'PASS' if all(j['exit']==j['expected'] for j in jobs) else 'FAIL','jobs':jobs,'wheel_sha256':hashlib.sha256(a.wheel.read_bytes()).hexdigest(),'resources':required,'scope':'minimal wheel; no DSH/Concordia; -I external cwd; not full dependency pip-check'}
 (a.output/'receipt.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result));return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
