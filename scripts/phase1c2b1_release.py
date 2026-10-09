"""Read-only collection of this phase's local/live evidence; immutable final seal."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import ctypes as C
import datetime
import hashlib
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
from actio.common import canonical,file_hash,clean_env
from actio.runtime import verify_runtime
from actio.supervisor import Job,kernel
from actio.gateway import scan
from actio.transport_campaign import verify_campaign

ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2b1'
START='47790607db24a187258035ff990fad544124074d'
SUITES={'gateway':5,'gateway_lifecycle':2,'preflight':5,'transport_config':3,'readiness_config':3,'transport':4,'budget':4,'readiness':6,
        'task':7,'runtime':2,'reliability':8,'evidence':7,'schema':5,'input_binding':3,'sotopia':3,'evaluation':8}
HISTORY=['docs/validation/'+p for p in ('phase1a','phase1b','phase1b1','phase1c0','phase1c1','phase1c2a','phase1c2a1','phase1c2b0')]+['docs/reviews','docs/prompts','requirements.lock','requirements-eval.lock','requirements-eval-test.lock','src/actio/pins','src/actio/_vendor']

def read(p):return json.loads(Path(p).read_bytes())
def create(p,v):
    with Path(p).open('x',encoding='utf8',newline='\n') as f:f.write(canonical(v))
def files(root):
    for base,dirs,names in os.walk(root):
        dirs[:]=[d for d in dirs if d not in ('__pycache__','node_modules','.cache')]
        for n in names:yield Path(base)/n
def hashes(root):return {p.relative_to(root).as_posix():file_hash(p) for p in sorted(files(root))}

def collect():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    local=Path('D:/actio-c2b1-release')/stamp;local.mkdir(parents=True)
    log={'status':'FAIL','root':str(local),'actual_argv':sys.orig_argv,'commands':[]}
    def command(args,cwd=ROOT):
        args=list(map(str,args));env=clean_env(local);env['PATH']=str(Path(shutil.which('git')).parent)+';'+env['PATH']
        p=subprocess.run(args,cwd=cwd,env=env,capture_output=True,text=True,encoding='utf8',timeout=90)
        log['commands'].append({'argv':args,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr});assert p.returncode==0,p.stderr
        return p.stdout
    try:
        verify_runtime();source=hashes(ROOT/'src/actio');product={'src/actio/'+n:h for n,h in source.items()}
        installs={}
        for n in ('runtime','release'):
            site=ROOT/f'.local/phase1c2b1-{n}-venv/Lib/site-packages/actio';assert hashes(site)==source,n
            installs[n]={'path':str(site),'files':len(source),'byte_match':True}
        current={};attempts=[];roots=set()
        for p in sorted((DOC/'evidence').glob('*.json')):
            d=read(p)
            if 'suite' in d:
                current[d['suite']]=(p,d);attempts.append({'file':p.relative_to(DOC).as_posix(),'sha256':file_hash(p),'suite':d['suite'],'tests':d['tests_run'],'exit_code':d['exit_code'],'actual_argv':d['actual_argv']})
                roots.update(Path(t['evidence']['root']) for t in d['tests'] if t.get('evidence',{}).get('root'))
            elif p.name.startswith(('probe-','cli-','live-')) and d.get('root'):roots.add(Path(d['root']))
        assert set(current)==set(SUITES)
        suites=[]
        for name,(p,d) in sorted(current.items()):
            assert d['exit_code']==0 and d['tests_run']==SUITES[name] and all(t['status']=='PASS' for t in d['tests']),name
            assert all(d['source_hashes'].get(n)==h for n,h in product.items() if Path(n).suffix in ('.py','.mjs','.sql','.json')),(name,'product pins')
            assert d['source_hashes']['tests/test_'+name+'.py']==file_hash(ROOT/'tests'/('test_'+name+'.py'))
            suites.append({'name':name,'file':p.relative_to(DOC).as_posix(),'tests':d['tests_run'],'actual_argv':d['actual_argv'],'sha256':file_hash(p)})
        cli_file=sorted((DOC/'evidence').glob('cli-*.json'))[-1];cli=read(cli_file)
        assert cli['status']=='PASS' and cli['product_hashes']==product
        roots.add(Path(cli['smoke']['root']))
        live=[]
        for p in sorted((DOC/'evidence').glob('live-*.json')):
            if p.name.startswith('live-intent-'):continue
            d=read(p);live.append({'file':p.relative_to(DOC).as_posix(),'sha256':file_hash(p),'status':d['status'],'model':d['model'],'root':d['root'],'report':(d.get('result') or {}).get('campaign',{}).get('report')})
        assert {r['model'] for r in live if r['status']=='PASS'}=={'gpt-5.6','claude-sonnet-4-6'},'formal live models incomplete'
        samples={}
        for r in live:
            if r['status']!='PASS':continue
            name='gpt56' if r['model']=='gpt-5.6' else 'claude';src=Path(r['root'])/'run/campaign';dest=DOC/'samples'/name
            if dest.exists():assert hashes(dest)==hashes(src)
            else:shutil.copytree(src,dest)
            v=verify_campaign(dest);assert v['valid'];samples[name]={'source':str(src),'hashes':hashes(dest),'verification':v}
        legacy_file=sorted((DOC/'evidence').glob('legacy-*.json'))[-1];legacy=read(legacy_file);assert legacy['status']=='PASS'
        for phase,count in (('phase1c0',12),('phase1c1',22)):
            assert len(legacy['versions'][phase]['result']['records'])==count
        for phase,count in (('phase1c2a1',3),('phase1c2b0',4)):
            assert len(legacy['versions'][phase]['samples'])==count and all(r['valid'] for r in legacy['versions'][phase]['samples'].values())
        for v in legacy['versions'].values():assert file_hash(Path(v['source_archive']['path']))==v['source_archive']['sha256']
        command(['git','diff','--exit-code',START,'--',*HISTORY])
        historical=command(['git','ls-tree','-r','--name-only',START,'--',*HISTORY]).splitlines()
        history={p:file_hash(ROOT/p) for p in historical}
        # Explicit user-authorized publication scan; value/length/hash are never recorded.
        secret=(ROOT/'.local/credentials/token_key.txt').read_text(encoding='utf-8-sig').strip()
        # Only read-only disk scans overlap. Builds, installs, suites and live batches stay sequential.
        with ThreadPoolExecutor(max_workers=8) as pool:
            scans=list(pool.map(lambda root:{'root':str(root),**scan(root,secret)},sorted(roots)))
        scans.append({'root':str(DOC),**scan(DOC,secret)})
        allfiles={p for root in roots for p in files(root)}
        fake=re.compile(rb'ACTIO_FAKE_[0-9a-f]{32}')
        assert all(not fake.search(p.read_bytes()) for p in allfiles),'fake sentinel persisted'
        jobs={};services=[];ledgers=[];readonly={};ports=set()
        for p in sorted(allfiles):
            if p.name=='service.json':
                d=read(p);received=read(p.with_name('receives.json')) if p.with_name('receives.json').exists() else []
                assert d['joined'] and len(received)==d['receives']<=d['max_receives']
                from urllib.parse import urlsplit
                ports.add(urlsplit(d['endpoint']).port)
                services.append({'file':str(p),'sha256':file_hash(p),'receives':len(received),'mode':d.get('mode','transport_stub'),'joined':True})
            if p.suffix!='.sqlite':continue
            h=file_hash(p);db=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
            try:
                tables={r[0] for r in db.execute('SELECT name FROM sqlite_master')}
                if 'worker' in tables:
                    for r in db.execute('SELECT * FROM worker'):jobs.setdefault(r['job'],dict(r))
                if {'meta','attempt','registration','event'}<=tables and p.name in ('budget.sqlite','original.sqlite'):
                    c=json.loads(db.execute('SELECT body FROM meta').fetchone()[0])['config'];rows=[json.loads(r[0]) for r in db.execute('SELECT body FROM attempt')]
                    mode=c.get('mode','transport_stub');sending=db.execute("SELECT count(*) FROM event WHERE kind='sending'").fetchone()[0]
                    usage=[r['usage'] for r in rows if r['usage'] is not None]
                    ledgers.append({'file':str(p),'sha256':h,'mode':mode,'model':c.get('model'),'sending':sending,'registered':db.execute('SELECT count(*) FROM registration').fetchone()[0],
                        'states':{s:sum(r['state']==s for r in rows) for s in ('authorized','reserved','sending','settled','unknown','denied','released')},
                        'observed_responses':sum(bool(r['response'] and r['response']['status']) for r in rows),
                        'verified_usage_responses':len(usage),'input_tokens':sum(u['input_tokens'] for u in usage),'output_tokens':sum(u['output_tokens'] for u in usage),
                        'gateway_cost_fields':sum(u.get('gateway_reported_cost_raw') is not None for u in usage),
                        'supplier_received':None,'supplier_bill':None})
            finally:db.close()
            assert file_hash(p)==h;readonly[str(p)]=h
        cleanup=[]
        for name,w in sorted(jobs.items()):
            k=kernel();handle=k.OpenJobObjectW(4,False,name)
            if not handle:assert C.get_last_error()==2;active=0
            else:
                job=object.__new__(Job);job.k=k;job.handle=handle
                try:active=job.snapshot()['active']
                finally:k.CloseHandle(handle)
            assert active==0 and w['state']=='reaped',(name,w['state'])
            cleanup.append({'job':name,'active':active,'pid':w['pid'],'state':w['state'],'report':json.loads(w['report']) if w['report'] else None})
        probes=[]
        for p in (DOC/'evidence').glob('probe-*.json'):
            d=read(p);assert not d['server_thread_alive'];probes.append({'file':p.relative_to(DOC).as_posix(),'receives':d['local_http_requests']})
            # Probe endpoint is also bound in its saved profile patch.
            for patch in Path(d['root']).glob('*/profile.patch.yml'):
                for row in read(patch):
                    for entry in row.get('insert',[]):
                        if entry['id']=='actio-probe':ports.add(int(entry['config']['endpoint'].rsplit(':',1)[1]))
        ps=shutil.which('pwsh') or shutil.which('powershell')
        listeners=json.loads(command([ps,'-NoProfile','-NonInteractive','-Command','$ports=@('+','.join(map(str,sorted(ports)))+'); ConvertTo-Json -Compress -InputObject @(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -in $ports })']))
        assert listeners==[]
        archive_root=ROOT/'.local/phase1c2b1-raw';archive_root.mkdir(exist_ok=True);archives=[]
        for root in sorted(roots | {ROOT/'.local/phase1c2b1-upstream'}):
            selected={p.relative_to(root).as_posix():file_hash(p) for p in files(root) if p.suffix in ('.json','.jsonl','.sqlite','.log','.py','.mjs','.yml','.yaml','.txt','.ts','.md') or p.name=='LICENSE' or '.sqlite-' in p.name}
            target=archive_root/(root.parent.name+'-'+root.name+'.zip')
            if not target.exists():
                with zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED) as z:
                    for name in sorted(selected):z.write(root/name,name)
            with zipfile.ZipFile(target) as z:assert {n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}==selected
            archives.append({'root':str(root),'file':target.relative_to(ROOT).as_posix(),'sha256':file_hash(target),'files':selected,'bytes':target.stat().st_size})
        counts={}
        for mode in sorted({l['mode'] for l in ledgers}):
            rows=[l for l in ledgers if l['mode']==mode]
            counts[mode]={k:sum(r[k] for r in rows) for k in ('sending','registered','observed_responses','verified_usage_responses','input_tokens','output_tokens','gateway_cost_fields')}
            counts[mode]['states']={s:sum(r['states'][s] for r in rows) for s in rows[0]['states']}
            counts[mode]['local_receives']=sum(s['receives'] for s in services if s['mode']==mode) if mode!='tokenkey_live' else None
        log.update(status='PASS',product_hashes=product,installations=installs,current_suites=suites,suite_attempts=attempts,
                   live=live,public_cli={'file':cli_file.relative_to(DOC).as_posix(),'sha256':file_hash(cli_file)},samples=samples,
                   census={'modes':counts,'local_probe_receives':sum(p['receives'] for p in probes),'all_local_receives':sum(s['receives'] for s in services)+sum(p['receives'] for p in probes),
                           'new_live_generation_attempts':sum(r['sending'] for r in ledgers if r['mode']=='tokenkey_live'),'new_direct_api_diagnostics':0,
                           'prior_review_diagnostics':{'generation_attempts':14,'catalog_get':1,'source':'docs/reviews/phase1c2b1_tokenkey_evidence.json'},
                           'supplier_received':None,'actual_cost':None,'jobs_inactive':len(cleanup),'services_joined':len(services)+len(probes),'remaining_listeners':0},
                   budget_ledgers=ledgers,services=services,probes=probes,jobs=cleanup,ports=sorted(ports),readonly_database_hashes=readonly,
                   credential_scans=scans,credential_scan_workers=8,raw_archives=archives,history_unchanged=history,legacy=legacy_file.relative_to(DOC).as_posix())
    except Exception as e:log['error']={'type':type(e).__name__,'reason':str(e)};raise
    finally:
        target=DOC/'evidence'/('delivery-'+stamp+'.json');create(target,log)
        print(canonical({'status':log['status'],'delivery':str(target),'census':log.get('census')}))

def seal(path):
    path=Path(path).resolve()
    d=read(path);assert d['status']=='PASS';assert d['product_hashes']=={'src/actio/'+n:h for n,h in hashes(ROOT/'src/actio').items()}
    for p in ('01_contract.md','02_results.md','03_gate.md','04_usage.md','05_accounting.md','06_adapter.md','07_models.md'):assert (DOC/p).exists()
    for p in (ROOT/'README.md',*DOC.glob('*.md')):
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
            if re.match(r'\w+://',link) or link.startswith('#'):continue
            target=(p.parent/link.split('#')[0].strip('<>')).resolve();assert target.exists() or target==DOC/'evidence_manifest.json',(p,link)
    gates={'local_engineering':'CONDITIONAL_GO','dsh_concordia_tokenkey_live':'CONDITIONAL_GO','live_authorization':'AUTHORIZED_C2B1_SCOPE',
           'billing_reconciliation':'UNVERIFIED','upstream_model_identity':'UNVERIFIED','binary_source_mapping':'unproven','full_controller_recovery':'unsupported',
           'judge':'BLOCKED','human_calibration':'BLOCKED','research_validity':'BLOCKED','evolution_promotion':'BLOCKED'}
    m={'phase':'1C2B1','start':START,'product_baseline':'f65045a11d1a4728b98b5564623e4827365f91c8','branch':'phase1c2b1-gated-solver-smoke','publish':'normal push task branch and main',
       'gates':gates,'tests':sum(SUITES.values()),'delivery':Path(path).relative_to(DOC).as_posix(),'delivery_sha256':file_hash(path),
       **{k:d[k] for k in ('product_hashes','current_suites','suite_attempts','census','live','public_cli','legacy','raw_archives')},
       'artifact_hashes':hashes(DOC),'test_hashes':{p.relative_to(ROOT).as_posix():file_hash(p) for p in (ROOT/'tests').glob('*.py')},
       'tooling_hashes':{p.relative_to(ROOT).as_posix():file_hash(p) for p in (ROOT/'scripts').glob('*') if p.suffix in ('.py','.mjs')},
       'entry_hashes':{p:file_hash(ROOT/p) for p in ('README.md','.gitattributes','pyproject.toml','AGENTS.md')},
       'entry_git_hashes':{p:hashlib.sha256(subprocess.check_output(['git','show',':'+p],cwd=ROOT)).hexdigest() for p in ('README.md','.gitattributes','pyproject.toml','AGENTS.md')},
       'lock_hashes':{p:file_hash(ROOT/p) for p in ('requirements.lock','requirements-eval.lock','requirements-eval-test.lock')},
       'preparation_logs':{p.relative_to(ROOT).as_posix():file_hash(p) for p in (ROOT/'.local').glob('phase1c2b1*.log')},
       'source_snapshots':{p.relative_to(ROOT).as_posix():file_hash(p) for p in (ROOT/'.local').glob('phase1c2b1-*.zip')},
       'limits':['Gateway labels are not upstream identity proof; no supplier receipt logs or reconciled bill.','Unknown costs preserved; uncapped does not mean unlimited retries.','No judge, calibration, research promotion or deployment.','Hashes establish internal consistency, not signatures or binary-source reproducibility.']}
    create(DOC/'evidence_manifest.json',m);print(canonical({'status':'PASS','manifest':str(DOC/'evidence_manifest.json'),'tests':m['tests']}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seal',type=Path);a=p.parse_args();seal(a.seal) if a.seal else collect()
