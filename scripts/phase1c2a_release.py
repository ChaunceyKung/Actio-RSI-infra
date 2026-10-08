"""Seal the bounded NO_GO delivery, without new DSH/provider execution or history rewrites."""
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

from actio.common import canonical,clean_env,file_hash
from actio.eval_contract import DEPENDENCIES,pins
from actio.runtime import verify_runtime
from actio.supervisor import Job,kernel

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/validation/phase1c2a'
HANDOFF='a06729e01526def46195c0f3fdd157ebb7e780a8'
BASELINE='af0a88cfff23c22c396fd7c9ef9916f0df8cd21f'
BRANCH='phase1c2a-solver-transport-and-budget'
SUITES={'preflight':5,'task':7,'runtime':2,'reliability':7,'evidence':7,'schema':5,
        'input_binding':3,'sotopia':3,'evaluation':8}


def read(path):
    return json.loads(Path(path).read_bytes())


def create(path,value):
    with path.open('x',encoding='utf8',newline='\n') as f:f.write(canonical(value))


def tree_hashes(root):
    return {p.relative_to(root).as_posix():file_hash(p) for p in sorted(root.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts}


def main():
    if (DOC/'evidence_manifest.json').exists():raise SystemExit('immutable manifest already exists; do not overwrite this batch')
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    local=Path('D:/actio-c2a-release')/stamp;local.mkdir(parents=True)
    delivery=DOC/'evidence'/('delivery-'+stamp+'.json')
    log={'status':'FAIL','transport_gate':'NO_GO','command':' '.join(sys.argv),'root':str(local),
         'python':sys.version,'platform':platform.platform(),'commands':[],'model_requests':0}

    def command(args,expected=0,cwd=local):
        args=list(map(str,args));env=clean_env(local)
        env['PATH']=str(Path(shutil.which('git')).parent)+';'+env['PATH']
        p=subprocess.run(args,cwd=cwd,env=env,capture_output=True,text=True,encoding='utf8',timeout=120)
        log['commands'].append({'command':args,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        assert p.returncode==expected,p.stderr+p.stdout
        return p.stdout

    try:
        assert command(['git','branch','--show-current'],cwd=ROOT).strip()==BRANCH
        command(['git','merge-base','--is-ancestor',BASELINE,HANDOFF],cwd=ROOT)
        product={'src/actio/'+n:h for n,h in tree_hashes(ROOT/'src/actio').items()}
        source=tree_hashes(ROOT/'src/actio');installations={}
        for name in ('runtime','eval','delivery'):
            site=ROOT/f'.local/phase1c2a-{name}-venv/Lib/site-packages/actio'
            assert tree_hashes(site)==source,(name,'installed source set/bytes mismatch')
            installations[name]={'path':str(site),'source_files':len(source),'all_match':True}
        verify_runtime()
        versions={n:metadata.version(n) for n in DEPENDENCIES};assert versions==DEPENDENCIES
        for name in ('runtime','delivery'):
            python=ROOT/f'.local/phase1c2a-{name}-venv/Scripts/python.exe'
            installations[name]['pip_check']=command([python,'-X','utf8','-m','pip','--isolated','check']).strip()
        caps=json.loads(command([sys.executable,'-X','utf8','-I','-B','-m','actio','capabilities']))
        assert caps['live_provider'] is False
        cli={}
        for name,valid in (('stub-config.json',True),('future-live-config.json',False)):
            value=json.loads(command([sys.executable,'-X','utf8','-I','-B','-m','actio.preflight',DOC/name],2))
            assert value['configuration_valid']==valid and value['status']=='BLOCKED'
            assert all(value[k] is False for k in ('transport_validated','live_authorized','live_ready'))
            cli[name]=value
        duplicate=local/'duplicate.json';duplicate.write_text('{"schema":1,"schema":2}',encoding='utf8')
        cli['duplicate_key']=json.loads(command([sys.executable,'-X','utf8','-I','-B','-m','actio.preflight',duplicate],2))
        assert cli['duplicate_key']['configuration_valid'] is False
        assert 'duplicate JSON key' in str(cli['duplicate_key']['reasons'])

        current={};attempts=[];roots=set()
        for path in sorted((DOC/'evidence').glob('*.json')):
            d=read(path)
            if 'suite' not in d:continue
            current[d['suite']]=(path,d)
            attempts.append({'file':path.relative_to(DOC).as_posix(),'sha256':file_hash(path),
                             'suite':d['suite'],'tests_run':d['tests_run'],'exit_code':d['exit_code']})
            roots.update(Path(t['evidence']['root']) for t in d['tests'] if t.get('evidence',{}).get('root'))
        assert set(current)==set(SUITES)
        suites=[]
        for name,(path,d) in sorted(current.items()):
            assert d['exit_code']==0 and d['tests_run']==SUITES[name] and all(t['status']=='PASS' for t in d['tests']),name
            assert all(d['source_hashes'].get(n)==h for n,h in product.items() if Path(n).suffix in ('.py','.mjs','.sql','.json')),(name,'product pins')
            test='tests/test_'+name+'.py';assert d['source_hashes'][test]==file_hash(ROOT/test)
            suites.append({'suite':name,'tests_run':d['tests_run'],'file':path.relative_to(DOC).as_posix(),
                           'sha256':file_hash(path),'command':d['command'],'exit_code':0,'mode':d['mode']})

        probes=[];findings=[];ports=set()
        for path in sorted((DOC/'evidence').glob('probe-*.json')):
            d=read(path);root=Path(d['root']);roots.add(root)
            assert d['server_thread_alive'] is False and d['model_requests']==0
            assert d['local_http_requests']==len(d['wire'])
            # Only preflight changed after these diagnostic attempts; runtime path stayed fixed.
            assert all(source[n]==h for n,h in d['runtime_pins']['code'].items() if n!='preflight.py')
            for n,h in d['files'].items():assert file_hash(root/n)==h,(path.name,n)
            workers=[]
            for w in d['workers']:
                assert w['state']=='reaped' and read_report(w)['after']['active']==0
                wr=Path(w['root']);patch=read(wr/'profile.patch.yml')
                for entry in patch:
                    if entry.get('config',{}).get('baseURL'):
                        ports.add(int(entry['config']['baseURL'].rsplit(':',1)[1]))
                    for inserted in entry.get('insert',[]):
                        if inserted.get('config',{}).get('baseURL'):
                            ports.add(int(inserted['config']['baseURL'].rsplit(':',1)[1]))
                inventory=[]
                packages=wr/'home/profiles/node_modules/@deepseek-ai'
                for name in ('dsh-llm-deepseek','dsh-llm','dsh-llm-retry','dsh-llm-deepseek-api-key'):
                    package=packages/name/'package.json'
                    inventory.append({'package':name,'present_in_extracted_profile':package.exists(),
                                      'metadata':read(package) if package.exists() else None,
                                      'sha256':file_hash(package) if package.exists() else None})
                capture=wr/'probe.jsonl'
                workers.append({'job':w['job'],'report':read_report(w),'host_config':read(wr/'host-config.json'),
                                'profile_patch':patch,'inventory':inventory,
                                'llm_capture':[json.loads(line) for line in capture.read_text(encoding='utf8').splitlines()] if capture.exists() else []})
            probes.append({'file':path.relative_to(DOC).as_posix(),'sha256':file_hash(path),'status':d['status'],
                           'case':d['case'],'local_http_requests':d['local_http_requests'],'root':d['root']})
            findings.append({'evidence':path.relative_to(DOC).as_posix(),'workers':workers})
        assert len(probes)==4 and sum(p['local_http_requests'] for p in probes)==2
        last=read(DOC/probes[-1]['file'])
        assert 'ERR_MODULE_NOT_FOUND' in last['error']['reason'] and 'explicit-messages' in last['error']['reason']
        assert len(ports)==4
        ps=shutil.which('pwsh') or shutil.which('powershell');assert ps
        check='$ports=@('+','.join(map(str,sorted(ports)))+'); $listeners=@(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -in $ports }); ConvertTo-Json -Compress -InputObject $listeners'
        listeners=json.loads(command([ps,'-NoProfile','-NonInteractive','-Command',check]))
        assert listeners==[],listeners
        findings_value={'scope':'diagnostic snapshots, not a transport campaign','transport_gate':'NO_GO','model_requests':0,
                        'local_http_requests':2,'probes':findings,
                        'inventory_caveat':'absence from extracted profile alone is not proof; actual loader failure and wire behavior are decisive'}
        findings_path=DOC/'probe_findings.json'
        if findings_path.exists():assert read(findings_path)==findings_value
        else:create(findings_path,findings_value)

        jobs={};db_hashes={}
        for root in sorted(roots):
            assert root.exists(),root
            for path in root.rglob('*.sqlite'):
                before=file_hash(path);db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
                try:
                    if db.execute("SELECT name FROM sqlite_master WHERE name='worker'").fetchone():
                        for row in db.execute('SELECT * FROM worker'):
                            w=dict(row);jobs.setdefault(w['job'],w)
                finally:db.close()
                assert file_hash(path)==before
                db_hashes[str(path)]=before
        cleanup=[]
        for name,w in sorted(jobs.items()):
            k=kernel();handle=k.OpenJobObjectW(4,False,name)
            if not handle:assert C.get_last_error()==2;active=0;state='object_absent'
            else:
                job=object.__new__(Job);job.k=k;job.handle=handle
                try:active=job.snapshot()['active'];state='queried'
                finally:k.CloseHandle(handle)
            assert active==0 and w['state']=='reaped'
            cleanup.append({'job':name,'active':active,'query':state,'recorded_pid':w['pid'],
                            'stored_worker_state':w['state'],'report':read_report(w)})
        archives=[];archive_root=ROOT/'.local/phase1c2a-raw';archive_root.mkdir(exist_ok=True)
        for root in sorted(roots):
            files={p.relative_to(root).as_posix():file_hash(p) for p in root.rglob('*')
                   if p.is_file() and not {'node_modules','.cache','__pycache__'} & set(p.parts)
                   and (p.suffix in ('.sqlite','.json','.jsonl','.log','.yml','.yaml','.txt') or '.sqlite-' in p.name)}
            archive=archive_root/(root.parent.name+'-'+root.name+'.zip')
            if not archive.exists():
                with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
                    for n in sorted(files):z.write(root/n,n)
            with zipfile.ZipFile(archive) as z:
                import hashlib
                assert {n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}==files
            archives.append({'root':str(root),'file':archive.relative_to(ROOT).as_posix(),
                             'sha256':file_hash(archive),'files':files,'bytes':archive.stat().st_size})

        legacy_path=sorted((DOC/'evidence').glob('legacy-*.json'))[-1];legacy=read(legacy_path)
        assert legacy['status']=='PASS'
        for phase,count in (('phase1c0',12),('phase1c1',22)):
            v=legacy['versions'][phase];assert len(v['result']['records'])==count and v['current_pins_rejected']==count
            assert v['source_archive']['sha256']==file_hash(Path(v['source_archive']['path']))
        assert legacy['versions']['phase1c1']['result']['campaign']['valid']
        assert legacy['versions']['phase1c1']['result']['campaign']['evaluator_calls']==0
        assert all(file_hash(ROOT/n)==h for n,h in legacy['history_unchanged'].items())
        history=['docs/validation/phase1a','docs/validation/phase1b','docs/validation/phase1b1','docs/validation/phase1c0',
                 'docs/validation/phase1c1','docs/reviews','probes/phase1a','requirements.lock','requirements-eval.lock',
                 'requirements-eval-test.lock','src/actio/pins','src/actio/_vendor']
        command(['git','diff','--exit-code',HANDOFF,'--',*history],cwd=ROOT)
        ref=(ROOT/'../../codebase/01_deepseek-harness/repo').resolve();reuse=read(DOC/'evidence/reuse.json')
        assert command(['git','rev-parse','HEAD'],cwd=ref).strip()==reuse['commit']
        assert not command(['git','status','--porcelain'],cwd=ref).strip()
        assert all(file_hash(ref/r['path'])==r['local_sha256'] for r in reuse['files'])
        assert file_hash(DOC/'DSH_LICENSE.txt')==file_hash(ref/'LICENSE')
        links=0
        for doc in (ROOT/'README.md',*DOC.glob('*.md')):
            for link in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf8')):
                if re.match(r'\w+://',link) or link.startswith('#'):continue
                target=(doc.parent/link.split('#')[0].strip('<>')).resolve()
                assert target.exists() or target==DOC/'evidence_manifest.json',(doc,link)
                links+=1
        log.update(status='PASS',meaning='NO_GO delivery checks passed; not transport admission',installations=installations,
                   installed_dependencies=versions,eval_pins=pins(),public_cli=cli,capabilities=caps,
                   jobs=cleanup,listeners={'ports':sorted(ports),'remaining':listeners},readonly_database_hashes=db_hashes,
                   history_unchanged=history,links_checked=links)
        create(delivery,log)
        manifest={'phase':'1C2A','branch':BRANCH,'handoff':HANDOFF,'product_baseline':BASELINE,
                  'publish':'normal push task branch only; no main merge/push','gate':'NO_GO',
                  'gates':{'configuration_fix':'PASS','transport_stub':'NO_GO','live_provider':'BLOCKED',
                           'human_calibration':'BLOCKED','research_evolution':'BLOCKED'},
                  'model_requests':0,'external_provider_requests':0,'real_cost':0,'local_provider_http_requests':2,
                  'human_labels':0,'independent_research_units':0,'product_hashes':product,
                  'current_suites':suites,'aggregate_tests':sum(SUITES.values()),'suite_attempts':attempts,
                  'delivery':delivery.relative_to(DOC).as_posix(),'legacy_verification':legacy_path.relative_to(DOC).as_posix(),
                  'probes':probes,'probe_findings':'probe_findings.json','raw_archives':archives,
                  'jobs_inactive':len(cleanup),'jobs_with_recorded_pid':sum(w['recorded_pid'] is not None for w in cleanup),
                  'job_count_scope':'all current worker-table names, including two controlled/no-launch rows; not historical 59',
                  'server_threads_joined':4,'probe_listeners_remaining':0,
                  'artifact_hashes':{p.relative_to(DOC).as_posix():file_hash(p) for p in sorted(DOC.rglob('*')) if p.is_file() and p.name!='evidence_manifest.json'},
                  'lock_hashes':{n:file_hash(ROOT/n) for n in ('requirements.lock','requirements-eval.lock','requirements-eval-test.lock','pyproject.toml')},
                  'test_hashes':{p.relative_to(ROOT).as_posix():file_hash(p) for p in (ROOT/'tests').glob('*.py')},
                  'tooling_hashes':{p.relative_to(ROOT).as_posix():file_hash(p) for p in (ROOT/'scripts').glob('*') if p.suffix in ('.py','.mjs')},
                  'entry_hashes':{n:file_hash(ROOT/n) for n in ('README.md','.gitattributes')},
                  'preparation_logs':{p.relative_to(ROOT).as_posix():file_hash(p) for p in (ROOT/'.local').glob('phase1c2a*.log') if not p.name.startswith('phase1c2a-release-attempt')},
                  'intermediate_source_archives':{p.relative_to(ROOT).as_posix():file_hash(p) for p in (ROOT/'.local').glob('phase1c2a-*.zip')},
                  'failure_accounting':'all four adapter probes, failed preflight suite, failed concurrent build and sequential retry retained; final source selected explicitly',
                  'not_implemented':['answer-free two-seat transport contract','per-attempt persistent budget and final TS gate',
                                     'transport negative matrix','new transport campaign/verifier admission','live execution'],
                  'limits':['source/binary build mapping unproven','regressions use preset fixture provider',
                            'one observed 429 receive is not a general retry guarantee','no Messages SSE success or usage',
                            'synthetic budget fields are not enforced runtime caps','hashes are not signatures',
                            'raw archives retained locally; public extracts and hashes do not include binary caches']}
        create(DOC/'evidence_manifest.json',manifest)
        print(canonical({'status':'PASS','transport_gate':'NO_GO','tests':manifest['aggregate_tests'],
                         'jobs_inactive':len(cleanup),'jobs_with_recorded_pid':manifest['jobs_with_recorded_pid'],
                         'local_provider_http_requests':2,'model_requests':0,'delivery':str(delivery)}))
    except Exception as e:
        log['error']={'type':type(e).__name__,'reason':str(e)}
        if not delivery.exists():create(delivery,log)
        raise


def read_report(worker):
    return json.loads(worker['report']) if worker.get('report') else None


if __name__=='__main__':main()
