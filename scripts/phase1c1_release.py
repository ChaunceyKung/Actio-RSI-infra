"""Final independent release evidence: installed bytes, readonly portability, Jobs and retained attempts."""
import ctypes as C
import datetime
import importlib.metadata as metadata
import json
from pathlib import Path
import platform
import re
import shutil
import sqlite3
import subprocess
import sys
import uuid
import zipfile

from actio.common import canonical,file_hash,clean_env
from actio.campaign import verify_campaign
from actio.evaluation import read_json
from actio.supervisor import Job,kernel
from actio.eval_contract import DEPENDENCIES,pins

ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c1'
HANDOFF='4f942fd77fbaf382de2b93a6016a384206fb249e'


def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    local=Path('D:/actio-p1c1-release')/stamp;local.mkdir(parents=True)
    log={'status':'FAIL','command':' '.join(sys.argv),'python':sys.version,'platform':platform.platform(),
         'root':str(local),'commands':[],'model_requests':0}
    delivery=DOC/'evidence'/('delivery-'+stamp+'.json')
    def command(args,expected=0,cwd=local):
        env=clean_env(local)
        # Extraction's nested git process needs the explicitly discovered binary directory.
        env['PATH']=str(Path(shutil.which('git')).parent)+';'+env['PATH']
        p=subprocess.run(list(map(str,args)),cwd=cwd,env=env,capture_output=True,text=True,encoding='utf8',timeout=120)
        log['commands'].append({'command':list(map(str,args)),'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        assert p.returncode==expected,p.stderr+p.stdout
        return p.stdout
    try:
        import actio
        installed=Path(actio.__file__).parent
        product={p.relative_to(ROOT).as_posix():file_hash(p) for p in (ROOT/'src/actio').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        assert all(file_hash(installed/Path(n).relative_to('src/actio'))==h for n,h in product.items())
        assert {p.relative_to(installed).as_posix() for p in installed.rglob('*') if p.is_file() and '__pycache__' not in p.parts}=={str(Path(n).relative_to('src/actio')).replace('\\','/') for n in product}
        installed_versions={n:metadata.version(n) for n in DEPENDENCIES};assert installed_versions==DEPENDENCIES
        pip_check=command([sys.executable,'-X','utf8','-m','pip','--isolated','check'])
        command([sys.executable,'-X','utf8','-I','-B','-m','actio','capabilities'])
        before={p.relative_to(DOC).as_posix():file_hash(p) for p in (DOC/'campaign').rglob('*') if p.is_file()}
        result=json.loads(command([sys.executable,'-X','utf8','-I','-B','-m','actio.campaign','verify-campaign',DOC/'campaign']))
        assert result['valid'] and result['evaluator_calls']==0,result
        command([sys.executable,'-X','utf8','-I','-B','-m','actio.preflight',DOC/'pilot-config.json'],2)
        assert before=={p.relative_to(DOC).as_posix():file_hash(p) for p in (DOC/'campaign').rglob('*') if p.is_file()}
        # Truly portable standard-library reader. Runtime/source roots unavailable,
        # all writes, socket, subprocess and runtime imports denied in this child.
        portable=local/'portable';portable.mkdir();shutil.copytree(installed,portable/'actio',ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(DOC/'campaign',portable/'campaign')
        runner=portable/'reader.py'
        runner.write_text('''import sys,pathlib,json
base=pathlib.Path(__file__).parent.resolve();sys.path.insert(0,str(base))
def audit(event,args):
    if event.startswith('socket.') or event=='subprocess.Popen':raise RuntimeError('network/process denied')
    if event=='import' and args[0].split('.')[0] in ('deepseek_harness','concordia','openai','litellm','redis'):raise RuntimeError('runtime denied')
    if event=='open':
        path,mode,flags=args
        if isinstance(mode,str) and any(c in mode for c in 'wax+') or isinstance(flags,int) and flags & (1|2|64|512|1024):raise RuntimeError('write denied')
        if isinstance(path,str):
            p=pathlib.Path(path).resolve()
            if not p.is_relative_to(base) and not p.is_relative_to(pathlib.Path(sys.base_prefix)):raise RuntimeError('original root read denied')
sys.addaudithook(audit)
import actio.campaign as c
import actio.evaluation as e
def denied(*a,**kw):raise RuntimeError('evaluator execution denied')
c.evaluate=denied;e.execute_worker=denied
result=c.verify_campaign(base/'campaign');print(json.dumps(result));sys.exit(0 if result['valid'] else 2)
''',encoding='utf8')
        portable_result=json.loads(command([sys.executable,'-X','utf8','-I','-S','-B',runner],cwd=portable));assert portable_result['valid']
        current={};attempts=[];roots=set();archives=[]
        archive_root=ROOT/'.local/phase1c1-raw';archive_root.mkdir(exist_ok=True)
        for path in sorted((DOC/'evidence').glob('*.json')):
            d=read_json(path)
            if d.get('root'):roots.add(Path(d['root']))
            if 'suite' not in d:continue
            current[d['suite']]=(path,d)
            attempts.append({'file':str(path.relative_to(DOC)),'sha256':file_hash(path),'suite':d['suite'],'exit_code':d['exit_code'],'tests_run':d['tests_run']})
            roots|={Path(t['evidence']['root']) for t in d['tests'] if t.get('evidence',{}).get('root')}
        assert set(current)=={'task','input_binding','sotopia','evaluation','runtime','reliability','evidence','schema'}
        suites=[]
        relevant={n:h for n,h in product.items() if Path(n).suffix in ('.py','.mjs','.sql','.json')}
        for name,(path,d) in sorted(current.items()):
            assert d['exit_code']==0 and all(t['status']=='PASS' for t in d['tests']),name
            assert all(d['source_hashes'].get(n)==h for n,h in relevant.items()),(name,'product source mismatch')
            test='tests/test_'+name+'.py';assert d['source_hashes'][test]==file_hash(ROOT/test)
            suites.append({'suite':name,'file':str(path.relative_to(DOC)),'sha256':file_hash(path),'tests_run':d['tests_run'],'command':d['command'],'exit_code':0})
        for root in sorted(roots):
            archive=archive_root/(root.parent.name+'-'+root.name+'.zip')
            if not archive.exists():
                with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
                    for p in sorted(root.rglob('*')):
                        if p.is_file() and 'node_modules' not in p.parts and p.suffix in ('.sqlite','.json','.jsonl','.log','.yml'):
                            z.write(p,p.relative_to(root).as_posix())
            archives.append({'root':str(root),'file':str(archive.relative_to(ROOT)),'sha256':file_hash(archive)})
        jobs=set()
        for root in roots:
            for path in root.rglob('ledger.sqlite'):
                db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
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
        history=['docs/validation/phase1a','docs/validation/phase1b','docs/validation/phase1b1','docs/validation/phase1c0',
                 'probes/phase1a','requirements.lock','requirements-eval.lock','requirements-eval-test.lock','src/actio/pins/concordia.json','src/actio/_vendor']
        command(['git','diff','--exit-code',HANDOFF,'--',*history],cwd=ROOT)
        extraction=json.loads(command([sys.executable,'-X','utf8',ROOT/'scripts/extract_sotopia.py',ROOT/'../../codebase/18_sotopia/repo','--check'],cwd=ROOT))
        legacy=[(p,read_json(p)) for p in sorted((DOC/'evidence').glob('legacy-*.json'))]
        assert legacy[-1][1]['status']=='PASS' and legacy[-1][1]['original_records']==12
        artifacts=[(p,read_json(p)) for p in sorted((DOC/'evidence').glob('artifacts-*.json'))]
        assert artifacts[-1][1]['status']=='PASS'
        links=0
        for doc in [ROOT/'README.md',*DOC.glob('*.md')]:
            for link in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf8')):
                if re.match(r'\w+://',link) or link.startswith('#'):continue
                target=(doc.parent/link.split('#')[0].strip('<>')).resolve()
                assert target.exists() or target==DOC/'evidence_manifest.json',(doc,link)
                links+=1
        log.update(status='PASS',product_hashes=product,eval_pins=pins(),installed_dependencies=installed_versions,
                   core_plus_eval_pip_check=pip_check.strip(),portable_readonly=portable_result,source_readonly_hashes=before,
                   jobs=cleanup,history_unchanged=history,sotopia_extraction=extraction,links_checked=links)
        with delivery.open('x',encoding='utf8') as f:f.write(canonical(log))
        artifact_hashes={p.relative_to(DOC).as_posix():file_hash(p) for p in DOC.rglob('*') if p.is_file() and p.name!='evidence_manifest.json'}
        manifest={'phase':'1C1','handoff':HANDOFF,'baseline':'1e85d8c2fb4a756de81acb333905190df9e97592',
                  'branch':'phase1c1-task-contract-and-calibration','publish_main':'explicitly authorized by user; normal fast-forward only',
                  'gates':{'engineering':'CONDITIONAL_GO','human_calibration':'BLOCKED','live_provider':'BLOCKED','research_evolution':'BLOCKED'},
                  'model_requests':0,'live_budget':0,'independent_research_units':0,'product_hashes':product,
                  'current_suites':suites,'aggregate_tests':sum(d['tests_run'] for _,d in current.values()),'suite_attempts':attempts,
                  'delivery':delivery.relative_to(DOC).as_posix(),'legacy_verification':legacy[-1][0].relative_to(DOC).as_posix(),
                  'public_cli':artifacts[-1][0].relative_to(DOC).as_posix(),'current_campaign':'campaign/campaign.json','campaign':result,
                  'raw_archives':archives,'jobs_inactive':len(cleanup),'artifact_hashes':artifact_hashes,
                  'lock_hashes':{n:file_hash(ROOT/n) for n in ('requirements.lock','requirements-eval.lock','requirements-eval-test.lock','pyproject.toml')},
                  'tooling_hashes':{p.relative_to(ROOT).as_posix():file_hash(p) for p in (ROOT/'scripts').glob('*.py')},
                  # Release stdout is still being written when this manifest is built.
                  # Its command transcripts are sealed in delivery JSON instead.
                  'preparation_logs':{p.relative_to(ROOT).as_posix():file_hash(p) for p in (ROOT/'.local').glob('phase1c1*.log') if not p.name.startswith('phase1c1-release-attempt')},
                  'intermediate_source_archives':{p.relative_to(ROOT).as_posix():file_hash(p) for p in (ROOT/'.local').glob('phase1c1-*.zip')},
                  'failure_accounting':'all failed suite/script/staging attempts retained; current sets explicitly selected; expected BLOCKED exits are not tests passed as live',
                  'limits':['hashes are not signatures or authorship proof','two authored cards in one observed family; no holdout',
                            'controlled preset response is parser/dataflow evidence, not model judgment',
                            'synthetic labels only; no human calibration','short Windows paths required for staging/publication',
                            'C0 pinned implementation verifies original 12 records; current implementation rejects old pins',
                            'raw native/database archives retained locally and hashed, not uploaded binary caches',
                            'no transport, provider compatibility, training, candidate or deployment implemented']}
        with (DOC/'evidence_manifest.json').open('x',encoding='utf8') as f:f.write(canonical(manifest))
        print(canonical({'status':'PASS','tests':manifest['aggregate_tests'],'jobs_inactive':len(cleanup),'campaign':result['counts'],'delivery':str(delivery)}))
    except Exception as e:
        log['error']={'type':type(e).__name__,'reason':str(e)}
        if not delivery.exists():
            with delivery.open('x',encoding='utf8') as f:f.write(canonical(log))
        raise


if __name__=='__main__':main()
