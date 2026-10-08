"""Collect bounded offline delivery evidence; seal only after human-readable docs exist.

Does not start a Worker, HTTP server or evaluator. Raw archives remain local.
"""
import argparse
import ctypes as C
import datetime
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
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
DOC=ROOT/'docs/validation/phase1c2a1'
HANDOFF='2b43ea306bfeaca4b4200b69be65d65a5dc1fee9'
BASELINE='7fb2f682b2726ce3bba9b38bc71ebbf893c5de22'
BRANCH='phase1c2a1-chat-completions-budget'
SUITES={'preflight':5,'transport_config':3,'task':7,'runtime':2,'reliability':8,
        'evidence':7,'schema':5,'input_binding':3,'sotopia':3,'evaluation':8,'transport':4,'budget':4}
HISTORY=['docs/validation/'+p for p in ('phase1a','phase1b','phase1b1','phase1c0','phase1c1','phase1c2a')]+[
    'docs/reviews','docs/prompts','probes/phase1a','requirements.lock','requirements-eval.lock',
    'requirements-eval-test.lock','src/actio/pins','src/actio/_vendor']


def read(p):return json.loads(Path(p).read_bytes())


def create(p,value):
    with Path(p).open('x',encoding='utf8',newline='\n') as f:f.write(canonical(value))


def files(root):
    for parent,dirs,names in os.walk(root):
        dirs[:]=[d for d in dirs if d not in ('__pycache__','node_modules','.cache')]
        for n in names:yield Path(parent)/n


def hashes(root):return {p.relative_to(root).as_posix():file_hash(p) for p in sorted(files(root))}


def collect():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    local=Path('D:/actio-c2a1-release')/stamp;local.mkdir(parents=True)
    delivery=DOC/'evidence'/('delivery-'+stamp+'.json')
    log={'status':'FAIL','root':str(local),'command':sys.argv,'commands':[],
         'model_requests':0,'external_provider_requests':0,'real_cost':0}

    def command(args,expected=0,cwd=local):
        args=list(map(str,args));env=clean_env(local)
        env['PATH']=str(Path(shutil.which('git')).parent)+';'+env['PATH']
        p=subprocess.run(args,cwd=cwd,env=env,capture_output=True,text=True,encoding='utf8',timeout=120)
        log['commands'].append({'command':args,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        assert p.returncode==expected,p.stdout+p.stderr
        return p.stdout

    try:
        assert command(['git','branch','--show-current'],cwd=ROOT).strip()==BRANCH
        command(['git','merge-base','--is-ancestor',BASELINE,HANDOFF],cwd=ROOT)
        source=hashes(ROOT/'src/actio');product={'src/actio/'+n:h for n,h in source.items()}
        installs={}
        for name in ('runtime','eval','release2'):
            site=ROOT/f'.local/phase1c2a1-{name}-venv/Lib/site-packages/actio'
            assert hashes(site)==source,(name,'installed source file set/bytes mismatch')
            installs[name]={'path':str(site),'source_files':len(source),'all_match':True}
        verify_runtime();versions={n:metadata.version(n) for n in DEPENDENCIES};assert versions==DEPENDENCIES
        current={};attempts=[];roots=set();final_roots=set()
        for p in sorted((DOC/'evidence').glob('*.json')):
            d=read(p)
            if 'suite' not in d:continue
            current[d['suite']]=(p,d)
            attempts.append({'file':p.relative_to(DOC).as_posix(),'sha256':file_hash(p),
                             'suite':d['suite'],'tests_run':d['tests_run'],'exit_code':d['exit_code']})
            roots.update(Path(t['evidence']['root']) for t in d['tests'] if t.get('evidence',{}).get('root'))
        assert set(current)==set(SUITES)
        suites=[]
        for name,(p,d) in sorted(current.items()):
            assert d['exit_code']==0 and d['tests_run']==SUITES[name] and all(t['status']=='PASS' for t in d['tests']),name
            assert all(d['source_hashes'].get(n)==h for n,h in product.items() if Path(n).suffix in ('.py','.mjs','.sql','.json')),(name,'product pins')
            for n in ['tests/test_'+name+'.py']+(['tests/chat_stub.py','scripts/phase1c2a1_smoke.py'] if name in ('transport','budget') else []):
                assert d['source_hashes'][n]==file_hash(ROOT/n),(name,n)
            final_roots.update(Path(t['evidence']['root']) for t in d['tests'] if t.get('evidence',{}).get('root'))
            suites.append({'suite':name,'tests_run':d['tests_run'],'file':p.relative_to(DOC).as_posix(),
                           'sha256':file_hash(p),'command':d['command'],'exit_code':0,'mode':d['mode']})
        roots.add(Path(read(DOC/'evidence/failure-task-start.json')['root']))
        roots.update(Path('D:/actio-c2a1-smoke')/n for n in ('146642ba00cc','cfb373cfe690'))
        clis=[]
        for p in sorted((DOC/'evidence').glob('cli-*.json')):
            d=read(p);roots.add(Path(d['root']))
            for c in d['commands']:
                if any(str(a).endswith('phase1c2a1_smoke.py') for a in c['command']):
                    s=json.loads(c['stdout']);roots.add(Path(s['root']))
            clis.append({'file':p.relative_to(DOC).as_posix(),'sha256':file_hash(p),'status':d['status']})
        cli=read(DOC/clis[-1]['file']);assert cli['status']=='PASS' and cli['product_hashes']==product
        final_roots.add(Path(cli['smoke']['root']))

        probes=[];ports=set()
        for p in sorted((DOC/'evidence').glob('probe-*.json')):
            d=read(p);root=Path(d['root']);roots.add(root)
            assert d['diagnostic'] and d['max_receives']==1 and d['local_http_requests']==len(d['wire'])==1
            assert not d['server_thread_alive'] and d['model_requests']==0
            for n,h in d['files'].items():assert file_hash(root/n)==h,(p.name,n)
            for w in d['workers']:
                patch=read(Path(w['root'])/'profile.patch.yml')
                for entry in patch:
                    for x in [entry,*entry.get('insert',[])]:
                        endpoint=x.get('config',{}).get('baseURL')
                        if endpoint:ports.add(int(endpoint.rsplit(':',1)[1]))
            probes.append({'file':p.relative_to(DOC).as_posix(),'sha256':file_hash(p),'case':d['case'],
                           'status':d['status'],'local_http_requests':1,'root':str(root)})
        assert len(probes)==3

        # Copy only final-source synthetic immutable objects; no native databases/logs.
        transport=current['transport'][1]['tests'];budget=current['budget'][1]['tests']
        samples={'success':Path(transport[3]['evidence']['root'])/'readonly/campaign',
                 'missing-done':Path(transport[1]['evidence']['root'])/'missing-done/campaign',
                 'last-call':Path(budget[0]['evidence']['root'])/'campaign'}
        sample_records={}
        for name,source_dir in samples.items():
            dest=DOC/'samples'/name
            if dest.exists():assert hashes(dest)==hashes(source_dir),'immutable sample already differs'
            else:shutil.copytree(source_dir,dest)
            result=json.loads(command([sys.executable,'-X','utf8','-I','-B','-m','actio.transport_campaign',dest]))
            assert result['valid'] and result['evaluator_calls']==0
            sample_records[name]={'source':str(source_dir),'hashes':hashes(dest),'verification':result}

        services=[];ledgers=[];jobs={};db_hashes={};all_files=set()
        for root in sorted(roots):
            assert root.exists(),root
            all_files.update(files(root))
        for p in sorted(all_files):
            final=any(p.is_relative_to(root) for root in final_roots)
            if p.name=='service.json':
                d=read(p);capture=p.with_name('receives.json')
                # The service writes its receive list on first receipt; zero leaves no file.
                if not capture.exists():assert d['receives']==0
                receives=read(capture) if capture.exists() else []
                assert d['joined'] and d['receives']==len(receives)<=d['max_receives'] and d['model_requests']==0
                ports.add(int(d['endpoint'].rsplit(':',1)[1]))
                services.append({'file':str(p),'sha256':file_hash(p),'receives_file_sha256':file_hash(capture) if capture.exists() else None,
                                 'receives':len(receives),'joined':True,'final_source':final})
            if p.suffix!='.sqlite':continue
            before=file_hash(p);db=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
            try:
                tables={r[0] for r in db.execute('SELECT name FROM sqlite_master')}
                if 'worker' in tables:
                    for row in db.execute('SELECT * FROM worker'):
                        w=dict(row);jobs.setdefault(w['job'],w)
                if {'attempt','event','registration','meta'}<=tables and p.name in ('budget.sqlite','original.sqlite'):
                    rows=[json.loads(r[0]) for r in db.execute('SELECT body FROM attempt')]
                    totals={k:0 for k in ('calls','input_tokens','output_tokens','cost_minor')}
                    settled={k:0 for k in totals}
                    for a in rows:
                        amount=a['usage'] if a['state']=='settled' else a['reservation'] if a['state'] in ('reserved','sending','unknown') else None
                        if amount:
                            for k in totals:totals[k]+=amount[k]
                        if a['state']=='settled':
                            for k in settled:settled[k]+=a['usage'][k]
                    ledgers.append({'file':str(p),'sha256':before,'final_source':final,
                                    'sending':db.execute("SELECT count(*) FROM event WHERE kind='sending'").fetchone()[0],
                                    'registered':db.execute('SELECT count(*) FROM registration').fetchone()[0],
                                    'states':{s:sum(a['state']==s for a in rows) for s in ('authorized','reserved','sending','settled','unknown','denied','released')},
                                    'retained_totals':totals,'settled_synthetic_usage':settled})
            finally:db.close()
            assert file_hash(p)==before;db_hashes[str(p)]=before
        cleanup=[]
        for name,w in sorted(jobs.items()):
            k=kernel();handle=k.OpenJobObjectW(4,False,name)
            if not handle:assert C.get_last_error()==2;active=0;state='object_absent'
            else:
                job=object.__new__(Job);job.k=k;job.handle=handle
                try:active=job.snapshot()['active'];state='queried'
                finally:k.CloseHandle(handle)
            assert active==0 and w['state']=='reaped',(name,w['state'])
            cleanup.append({'job':name,'active':active,'query':state,'recorded_pid':w['pid'],
                            'stored_worker_state':w['state'],'report':json.loads(w['report']) if w.get('report') else None})
        ps=shutil.which('pwsh') or shutil.which('powershell');assert ps
        check='$ports=@('+','.join(map(str,sorted(ports)))+'); $listeners=@(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -in $ports }); ConvertTo-Json -Compress -InputObject $listeners'
        listeners=json.loads(command([ps,'-NoProfile','-NonInteractive','-Command',check]));assert listeners==[],listeners

        archives=[];archive_root=ROOT/'.local/phase1c2a1-raw';archive_root.mkdir(exist_ok=True)
        for root in sorted(roots):
            selected={p.relative_to(root).as_posix():file_hash(p) for p in files(root)
                      if p.suffix in ('.sqlite','.json','.jsonl','.log','.yml','.yaml','.txt','.mjs','.py') or '.sqlite-' in p.name}
            archive=archive_root/(root.parent.name+'-'+root.name+'.zip')
            if not archive.exists():
                with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
                    for n in sorted(selected):z.write(root/n,n)
            with zipfile.ZipFile(archive) as z:assert {n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}==selected
            archives.append({'root':str(root),'file':archive.relative_to(ROOT).as_posix(),
                             'sha256':file_hash(archive),'files':selected,'bytes':archive.stat().st_size})

        legacy_path=sorted((DOC/'evidence').glob('legacy-*.json'))[-1];legacy=read(legacy_path);assert legacy['status']=='PASS'
        for phase,count in (('phase1c0',12),('phase1c1',22)):
            v=legacy['versions'][phase];assert len(v['result']['records'])==count and v['current_pins_rejected']==count
            assert v['source_archive']['sha256']==file_hash(Path(v['source_archive']['path']))
        assert legacy['versions']['phase1c1']['result']['campaign']['valid'] and legacy['versions']['phase1c1']['result']['campaign']['evaluator_calls']==0
        assert all(file_hash(ROOT/n)==h for n,h in legacy['history_unchanged'].items())
        command(['git','diff','--exit-code',HANDOFF,'--',*HISTORY],cwd=ROOT)
        historical=command(['git','ls-tree','-r','--name-only',HANDOFF,'--',*HISTORY],cwd=ROOT).splitlines()
        historical_hashes={n:file_hash(ROOT/n) for n in historical}
        ref=(ROOT/'../../codebase/01_deepseek-harness/repo').resolve();old_reuse=read(ROOT/'docs/validation/phase1c2a/evidence/reuse.json')
        assert command(['git','rev-parse','HEAD'],cwd=ref).strip()==old_reuse['commit']
        assert not command(['git','status','--porcelain'],cwd=ref).strip()
        assert all(file_hash(ref/r['path'])==r['local_sha256'] for r in old_reuse['files'])
        upstream=read(DOC/'reuse.json')
        for f in upstream['files']:assert file_hash(ROOT/'.local/phase1c2a-review-upstream'/f['path'])==f['sha256']
        assert file_hash(DOC/'DSH_LICENSE.txt')==next(f['sha256'] for f in upstream['files'] if f['path']=='LICENSE')

        def amount(rows,key):return {k:sum(r[key][k] for r in rows) for k in ('calls','input_tokens','output_tokens','cost_minor')}
        census={'diagnostic_http':3,'all_budget_path_http':sum(s['receives'] for s in services),
                'all_phase_http':3+sum(s['receives'] for s in services),
                'all_budget_sending':sum(l['sending'] for l in ledgers),
                'final_formal_http':sum(s['receives'] for s in services if s['final_source']),
                'final_formal_sending':sum(l['sending'] for l in ledgers if l['final_source']),
                'final_formal_settled_synthetic_usage':amount([l for l in ledgers if l['final_source']],'settled_synthetic_usage'),
                'all_settled_synthetic_usage':amount(ledgers,'settled_synthetic_usage'),
                'all_retained_synthetic_budget':amount(ledgers,'retained_totals'),
                'jobs_inactive':len(cleanup),'jobs_with_recorded_pid':sum(w['recorded_pid'] is not None for w in cleanup),
                'server_threads_joined':len(services)+3,'unique_service_ports':len(ports),'remaining_listeners':0,
                'scope':'all current-phase attempts including failed/intermediate runs; no historical C2A HTTP; SQL-only clones excluded from sending/usage; final formal includes public CLI smoke'}
        log.update(status='PASS',gate='CONDITIONAL_GO',product_hashes=product,installations=installs,
                   installed_dependencies=versions,eval_pins=pins(),current_suites=suites,suite_attempts=attempts,
                   public_cli=clis,probes=probes,samples=sample_records,census=census,services=services,budget_ledgers=ledgers,
                   jobs=cleanup,listeners={'ports':sorted(ports),'remaining':listeners},readonly_database_hashes=db_hashes,
                   history_unchanged=historical_hashes,legacy_verification=legacy_path.relative_to(DOC).as_posix(),raw_archives=archives)
    except Exception as e:
        log['error']={'type':type(e).__name__,'reason':str(e)}
        raise
    finally:
        create(delivery,log)
        print(canonical({'status':log['status'],'delivery':str(delivery),'census':log.get('census')}))


def seal(delivery):
    delivery=Path(delivery).resolve()
    assert not (DOC/'evidence_manifest.json').exists(),'immutable manifest already exists'
    log=read(delivery);assert log['status']=='PASS'
    assert log['product_hashes']=={'src/actio/'+n:h for n,h in hashes(ROOT/'src/actio').items()}
    for n in ('01_contract.md','02_results.md','03_gate.md','04_usage.md','05_reuse.md','06_budget.md'):assert (DOC/n).exists()
    for doc in (ROOT/'README.md',*DOC.glob('*.md')):
        for link in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf8')):
            if re.match(r'\w+://',link) or link.startswith('#'):continue
            target=(doc.parent/link.split('#')[0].strip('<>')).resolve()
            assert target.exists() or target==DOC/'evidence_manifest.json',(doc,link)
    manifest={'phase':'1C2A.1','branch':BRANCH,'handoff':HANDOFF,'product_baseline':BASELINE,
              'publish':'normal push task branch only','gate':'CONDITIONAL_GO',
              'gates':{'transport_stub':'CONDITIONAL_GO','live_provider':'BLOCKED','human_calibration':'BLOCKED',
                       'judge':'BLOCKED','research_validity':'BLOCKED','evolution_promotion':'BLOCKED'},
              'model_requests':0,'external_provider_requests':0,'real_cost':0,'human_labels':0,'independent_research_units':0,
              'delivery':Path(delivery).relative_to(DOC).as_posix(),'delivery_sha256':file_hash(delivery),
              'aggregate_tests':sum(SUITES.values()),
              **{k:log[k] for k in ('product_hashes','current_suites','suite_attempts','public_cli','probes','census','legacy_verification','raw_archives')},
              'artifact_hashes':hashes(DOC),
              'lock_hashes':{n:file_hash(ROOT/n) for n in ('requirements.lock','requirements-eval.lock','requirements-eval-test.lock','pyproject.toml')},
              'test_hashes':{p.relative_to(ROOT).as_posix():file_hash(p) for p in (ROOT/'tests').glob('*.py')},
              'tooling_hashes':{p.relative_to(ROOT).as_posix():file_hash(p) for p in (ROOT/'scripts').glob('*') if p.suffix in ('.py','.mjs')},
              'entry_hashes':{n:file_hash(ROOT/n) for n in ('README.md','.gitattributes')},
              'preparation_logs':{p.relative_to(ROOT).as_posix():file_hash(p) for p in (ROOT/'.local').glob('phase1c2a1*.log')},
              'intermediate_source_archives':{p.relative_to(ROOT).as_posix():file_hash(p) for p in (ROOT/'.local').glob('phase1c2a1-*.zip')},
              'failure_accounting':'initial audit-tee disposal race, Windows architecture fallback failure, public smoke atomic-file race, all failed CLI/delivery attempts and intermediate passes retained',
              'limits':['fixed Windows pure-text trusted profile only; fetch wrapper is not a malicious-code sandbox',
                        'binary_source_mapping unproven; real tokenizer/billing bound unproven',
                        'no complete controller-process crash recovery; pending reservation blocks further sends',
                        'hashes are not signatures; raw archives local; public samples synthetic',
                        'no live provider/judge/calibration/research/evolution admission']}
    create(DOC/'evidence_manifest.json',manifest)
    print(canonical({'status':'PASS','manifest':str(DOC/'evidence_manifest.json'),'tests':sum(SUITES.values()),'census':log['census']}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seal',type=Path);args=p.parse_args()
    seal(args.seal) if args.seal else collect()
