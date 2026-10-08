"""Public CLI, installed-source/dependency, immutable history and managed Job delivery audit."""
import argparse
import ctypes as C
import datetime
import importlib.metadata as metadata
import json
from pathlib import Path
import platform
import re
import sqlite3
import subprocess
import sys
import uuid
import zipfile

from actio.common import clean_env,file_hash,write_json
from actio.eval_contract import DEPENDENCIES
from actio.evaluation import read_json,verify_record
from actio.supervisor import Job,kernel
from actio.verify import verify_bundle

ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c0'
BASE='449691e3685a96eecb1134ebb139d0de39dd6c35'


def ref(path):return {'file':path.relative_to(DOC).as_posix(),'sha256':file_hash(path)}


def main():
    p=argparse.ArgumentParser();p.add_argument('--eval-python',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();report=read_json(a.report)['body'];eval_python=a.eval_python.resolve()
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    local=ROOT/'.local'/('phase1c0-delivery-'+stamp);local.mkdir();env=clean_env(local)
    log={'status':'FAIL','command':' '.join(sys.argv),'platform':platform.platform(),'python':sys.version,'commands':[],'model_requests':0}
    delivery=DOC/'evidence'/('delivery-'+stamp+'.json')
    def command(args,expected=0):
        result=subprocess.run([str(eval_python),'-I','-B',*args],cwd=local,env=env,capture_output=True,text=True,timeout=30)
        log['commands'].append({'command':[str(eval_python),'-I','-B',*map(str,args)],'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        assert result.returncode==expected,result.stderr+result.stdout
        return json.loads(result.stdout)
    try:
        product={p.relative_to(ROOT).as_posix():file_hash(p) for p in (ROOT/'src/actio').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        import actio
        installed=Path(actio.__file__).parent
        for name,h in product.items():assert file_hash(installed/Path(name).relative_to('src/actio'))==h,name
        current={};attempts=[]
        for path in sorted((DOC/'evidence').glob('20*.json')):
            d=read_json(path)
            if 'suite' not in d:continue
            current[d['suite']]=(path,d);attempts.append({**ref(path),'suite':d['suite'],'exit_code':d['exit_code'],'tests_run':d['tests_run']})
        assert set(current)=={'input_binding','sotopia','evaluation','runtime','reliability','evidence','schema'}
        suites=[];roots=set();total=0
        core={n:h for n,h in product.items() if not any(x in n for x in ('/_vendor/','/eval_contract.py','/evaluation.py','/eval_worker.py'))}
        archive_root=ROOT/'.local/phase1c0-raw';archive_root.mkdir(exist_ok=True)
        for name,(path,d) in sorted(current.items()):
            assert d['exit_code']==0 and all(t['status']=='PASS' for t in d['tests']),name
            relevant=product if name in ('input_binding','sotopia','evaluation') else core
            relevant={n:h for n,h in relevant.items() if Path(n).suffix in ('.py','.mjs','.sql','.json')}
            assert all(d['source_hashes'].get(n)==h for n,h in relevant.items()),(name,'relevant source changed')
            testnames=['tests/test_'+name+'.py']
            if name in ('evaluation','sotopia'):testnames+=['tests/test_input_binding.py'] if name=='evaluation' else ['tests/fixtures/sotopia_episode.py']
            assert all(d['source_hashes'].get(n)==file_hash(ROOT/n) for n in testnames),name
            suite_roots={Path(t['evidence']['root']) for t in d['tests'] if t.get('evidence',{}).get('root')}
            roots|=suite_roots;total+=d['tests_run']
            archive=archive_root/(d['id']+'.zip')
            if not archive.exists():
                with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
                    for root in sorted(suite_roots):
                        for f in sorted(root.rglob('*')):
                            if f.is_file() and 'node_modules' not in f.parts and f.suffix in ('.sqlite','.json','.jsonl','.log','.yml'):
                                z.write(f,root.name+'/'+f.relative_to(root).as_posix())
            suites.append({'suite':name,**ref(path),'command':d['command'],'exit_code':0,'tests_run':d['tests_run'],
                           'relevant_product_hashes':relevant,'relevant_test_hashes':{n:file_hash(ROOT/n) for n in testnames},
                           'raw_archive':archive.relative_to(ROOT).as_posix(),'raw_archive_sha256':file_hash(archive)})
        smoke_path=sorted((DOC/'evidence').glob('runtime-smoke-*.json'))[-1];smoke=read_json(smoke_path)
        assert smoke['status']=='PASS';roots.add(Path(smoke['root']))
        source_files=[p for p in (ROOT/'docs/validation/phase1b1/samples').rglob('*') if p.is_file()]
        source_files+=[Path(smoke['root'])/'ledger.sqlite']
        before={str(p):file_hash(p) for p in source_files}
        records={r['record']:read_json(DOC/'campaign/records'/(r['record']+'.json')) for r in report['registrations']}
        for record in records.values():assert verify_record(record)['valid']
        # Reproduce the public interfaces in the eval-only environment with no runtime packages.
        env_info=command(['-c',"import json,importlib.metadata as m,importlib.util as u; print(json.dumps({'deps':{n:m.version(n) for n in ['pydantic','pydantic_core','annotated-types','typing_extensions','typing-inspection','json-repair']},'absent':{n:u.find_spec(n) is None for n in ['deepseek_harness','concordia','redis','litellm','openai']}}))"])
        assert env_info['deps']==DEPENDENCIES and all(env_info['absent'].values())
        spec_result=command(['-m','actio.evaluation','spec','--mode','deterministic','--dataset-hash',report['dataset_hash'],'--output',str(local/'specs')])
        det_path=Path(spec_result['spec']);assert det_path.stem==report['specs']['deterministic']
        run_args=['-m','actio.evaluation','run','--spec',str(det_path),'--bundle',str(ROOT/'docs/validation/phase1b1/samples/assistant'),'--output',str(local/'records')]
        first=command(run_args);repeat=command(run_args);assert not first['reused'] and repeat['reused']
        command(['-m','actio.evaluation','verify-record',first['record']])
        synthetic_file=next(p for p in (DOC/'examples').glob('*.json') if p.name!='controlled-response.json')
        control=['-m','actio.evaluation','run','--spec',str(DOC/'campaign/specs'/(report['specs']['controlled_response']+'.json')),
                 '--synthetic',str(synthetic_file),'--response',str(DOC/'examples/controlled-response.json'),'--output',str(local/'records')]
        actual=command(control);assert actual['measurement']=='valid_measurement'
        command(['-m','actio.evaluation','verify-record',actual['record']])
        invalid=local/'invalid-response.json';invalid.write_text('{"scores":null}',encoding='utf8')
        control[control.index('--response')+1]=str(invalid);actual=command(control,2);assert actual['measurement']=='invalid_measurement'
        command(['-m','actio.evaluation','verify-record',actual['record']])
        assert before=={str(p):file_hash(p) for p in source_files},'source evidence or runtime DB mutated by evaluation'
        jobs=set()
        for root in roots:
            for dbpath in root.rglob('ledger.sqlite'):
                db=sqlite3.connect(dbpath.as_uri()+'?mode=ro',uri=True)
                try:jobs.update(row[0] for row in db.execute('SELECT job FROM worker'))
                finally:db.close()
        cleanup=[]
        for name in sorted(jobs):
            k=kernel();handle=k.OpenJobObjectW(4,False,name)
            if not handle:assert C.get_last_error()==2;active=0
            else:
                job=object.__new__(Job);job.k=k;job.handle=handle
                try:active=job.snapshot()['active']
                finally:k.CloseHandle(handle)
            assert active==0;cleanup.append({'job':name,'active':active})
        history=['docs/validation/phase1a','docs/validation/phase1b','docs/validation/phase1b1','probes/phase1a','requirements.lock','src/actio/pins/concordia.json']
        check=subprocess.run(['git','diff','--exit-code',BASE,'--',*history],cwd=ROOT,capture_output=True,text=True);assert check.returncode==0
        extraction=subprocess.run([str(eval_python),str(ROOT/'scripts/extract_sotopia.py'),str(ROOT/'../../codebase/18_sotopia/repo'),'--check'],cwd=ROOT,capture_output=True,text=True);assert extraction.returncode==0,extraction.stderr
        check=subprocess.run([sys.executable,'-m','pip','--isolated','check'],capture_output=True,text=True);assert check.returncode==0,check.stdout
        documents=[ROOT/'README.md',*DOC.glob('*.md')];links=0
        for document in documents:
            for link in re.findall(r'\]\(([^)]+)\)',document.read_text(encoding='utf8')):
                if re.match(r'\w+://',link) or link.startswith('#'):continue
                target=(document.parent/link.split('#')[0].strip('<>')).resolve()
                assert target.exists() or target==DOC/'evidence_manifest.json',(document,link)
                links+=1
        metric_denominators={}
        for mode in ('deterministic','controlled_response'):
            rows=[r['body'] for r in records.values() if r['body']['mode']==mode]
            metric_denominators[mode]={'unique_requests':len(rows),'admitted':sum(r['admission']['status']=='admitted' for r in rows),
                                       'valid':sum(r['measurement']['status']=='valid_measurement' for r in rows)}
        log.update(status='PASS',exit_code=0,installed_product_hashes=product,eval_environment=env_info,jobs=cleanup,
                   source_readonly_hashes=before,history_unchanged=history,extraction=json.loads(extraction.stdout),
                   core_and_eval_pip_check=check.stdout.strip(),links_checked=links,current_records_verified=len(records))
        write_json(delivery,log)
        attempts_files={p.relative_to(DOC).as_posix():file_hash(p) for p in DOC.rglob('*') if p.is_file() and p.name!='evidence_manifest.json'}
        bootstrap_logs=[p for p in (ROOT/'.local').glob('phase1c0*.log')]
        manifest={'phase':'1C0','gate':'CONDITIONAL_GO','handoff':BASE,'branch':'phase1c0-offline-measurement','live_budget':0,
                  'product_hashes':product,'current_suites':suites,'aggregate_tests':total,'history':attempts,'delivery':ref(delivery),
                  'current_campaign':ref(a.report.resolve()),'campaign_counts':report['counts'],'measurement_denominators':metric_denominators,
                  'runtime_smoke':ref(smoke_path),'artifact_hashes':attempts_files,
                  'source_readonly':'Git history unchanged; sample bytes and runtime DB before/after evaluation identical',
                  'regression_scope':'Runtime/reliability/evidence/schema bind all unchanged core files. Later changes only enriched offline alias metadata and isolated spec builders; final eval suites bind all product code.',
                  'optional_lock_hashes':{p:file_hash(ROOT/p) for p in ('requirements-eval.lock','requirements-eval-test.lock','pyproject.toml')},
                  'tooling_hashes':{p.relative_to(ROOT).as_posix():file_hash(p) for p in (ROOT/'scripts').glob('*.py')},
                  'preparation_commands':[
                      {'command':'.local/phase1b1-delivery-venv/Scripts/python.exe -X utf8 scripts/bootstrap.py --venv .local/phase1c0-runtime-venv --offline-wheels --concordia-source ../../codebase/15_concordia/repo','exit_code':0,'log':'.local/phase1c0-runtime-bootstrap.log'},
                      {'command':'.local/phase1b1-delivery-venv/Scripts/python.exe -X utf8 scripts/bootstrap_eval.py --venv .local/phase1c0-release-venv --offline --characterization','exit_code':0,'log':'.local/phase1c0-release-bootstrap.log'},
                      {'command':'.local/phase1c0-runtime-venv/Scripts/python.exe -m pip --isolated install --no-index --require-hashes --only-binary=:all: -r requirements-eval.lock --find-links .local/wheels --find-links .local/eval-wheels','exit_code':0,'log':'.local/phase1c0-eval-overlay.log'},
                      {'command':'.local/phase1c0-runtime-venv/Scripts/python.exe -m pip --isolated install --no-cache-dir --no-deps --no-build-isolation .','exit_code':0,'log':'.local/phase1c0-runtime-release-install.log'}],
                  'preparation_logs':{p.relative_to(ROOT).as_posix():file_hash(p) for p in bootstrap_logs},
                  'preserved_intermediate_source_archives':{p.relative_to(ROOT).as_posix():file_hash(p) for p in (ROOT/'.local').glob('phase1c0-*-source.zip')},
                  'upstream_episode':'COMPATIBILITY_FAIL_NOT_ADOPTED; actual parser/schema PASS',
                  'not_run':['live/model/provider requests (budget 0)','Redis or full SOTOPIA platform','human calibration/pilot/holdout/statistical admission',
                             'Raven evolution/training/version activation','new database migration','main merge/deployment'],
                  'limits':['synthetic scores are preset structure fixtures','hashes do not authenticate authors or binary-source provenance',
                            'observation count inferred by pinned Engine rule and checked against actual dispatch/native inputs; no independent delivery timestamps',
                            'measurement failures are recorded local diagnostics, not external execution attestations',
                            'earlier campaign reports are historical pins; current report is explicitly selected above']}
        write_json(DOC/'evidence_manifest.json',manifest)
        print(json.dumps({'status':'PASS','tests':total,'jobs_inactive':len(cleanup),'current_campaign_records':len(records),'delivery':str(delivery)}))
    except Exception as e:
        log['error']={'type':type(e).__name__,'reason':str(e)};write_json(delivery,log);raise


if __name__=='__main__':main()
