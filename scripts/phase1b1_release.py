"""Seal independently bound suites, preserved attempts, portable samples and delivery audit."""
import ctypes as C
import datetime
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import zipfile

from actio.common import file_hash
from actio.supervisor import Job,kernel
from actio.verify import verify_bundle

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/validation/phase1b1'
BASE='4e0a47346b02d36cb0ab99271e11fc294ab53ec7'
SUITES={'contract','runtime','failures','processes','schema','reliability','entry_concurrency','evidence'}
MODES={'contract':'SQLITE_CONTRACT','schema':'SQLITE_MIGRATION_AND_REAL_PROCESS_INTERRUPTION',
       'runtime':'REAL_DSH_FIXTURE_AND_CONCORDIA','failures':'REAL_DSH_FIXTURE_WITH_TEST_ONLY_INJECTION',
       'processes':'REAL_PROCESS_CRASH_AND_RECOVERY','reliability':'REAL_ENGINE_DSH_AND_CONTROLLED_BOUNDARIES',
       'entry_concurrency':'TWO_REAL_CONTROL_PROCESSES_BOTH_SCENARIO_ENTRIES',
       'evidence':'REAL_FIXTURE_EXPORT_AND_INDEPENDENT_OFFLINE_VERIFICATION'}


def ref(path):return {'file':path.relative_to(DOC).as_posix(),'sha256':file_hash(path)}


def main():
    current={};attempts=[]
    for path in sorted((DOC/'evidence').glob('20*.json')):
        data=json.loads(path.read_text(encoding='utf8'))
        if 'suite' not in data:continue
        attempts.append({**ref(path),'suite':data['suite'],'exit_code':data['exit_code'],'tests_run':data['tests_run']})
        current[data['suite']]=(path,data)
    assert set(current)==SUITES
    product={p.relative_to(ROOT).as_posix():file_hash(p) for p in (ROOT/'src').rglob('*') if p.suffix in ('.py','.mjs','.sql','.json')}
    roots=set();tests=[];suites=[]
    archive_dir=ROOT/'.local/phase1b1-evidence';archive_dir.mkdir(exist_ok=True)
    for suite,(path,data) in sorted(current.items()):
        assert data['exit_code']==0 and all(t['status']=='PASS' for t in data['tests']),suite
        assert all(data['source_hashes'].get(p)==h for p,h in product.items()),(suite,'product changed after suite')
        relevant=['tests/test_'+suite+'.py']
        if suite in ('processes','failures'):
            relevant+=['tests/support.py']+[p.relative_to(ROOT).as_posix() for p in (ROOT/'tests/fixtures').glob('*') if p.is_file()]
        if suite=='processes':relevant+=['tests/child_case.py']
        if suite=='entry_concurrency':relevant+=['tests/entry_race.py']
        assert all(data['source_hashes'].get(p)==file_hash(ROOT/p) for p in relevant),(suite,'relevant tests changed')
        suite_roots=set()
        for t in data['tests']:
            if t['evidence'].get('root'):suite_roots.add(Path(t['evidence']['root']))
            tests.append({'id':t['id'],'suite':suite,'status':'PASS','mode':t['evidence'].get('mode',MODES[suite]),
                          'evidence':path.relative_to(DOC).as_posix(),'command':data['command'],'exit_code':0})
        roots|=suite_roots
        archive=archive_dir/(data['id']+'.zip')
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for root in sorted(suite_roots):
                for p in sorted(root.rglob('*')):
                    if p.is_file() and 'node_modules' not in p.parts and p.suffix in ('.sqlite','.json','.jsonl','.yml','.log'):
                        z.write(p,root.name+'/'+p.relative_to(root).as_posix())
        suites.append({'suite':suite,**ref(path),'command':data['command'],'exit_code':0,'tests_run':data['tests_run'],
                       'mode':MODES[suite],'relevant_test_hashes':{p:file_hash(ROOT/p) for p in relevant},
                       'raw_archive':archive.relative_to(ROOT).as_posix(),'raw_archive_sha256':file_hash(archive)})
    smoke_path=sorted((DOC/'evidence').glob('smoke-*.json'))[-1]
    smoke=json.loads(smoke_path.read_text(encoding='utf8'));assert smoke['status']=='PASS'
    assert all(smoke['source_hashes'].get(p)==h for p,h in product.items())
    roots.add(Path(smoke['root']))
    artifact_path=sorted((DOC/'evidence').glob('artifacts-*.json'))[-1]
    artifact=json.loads(artifact_path.read_text(encoding='utf8'))
    assert artifact['status']=='PASS' and artifact['product_hashes']==product
    samples={}
    for p in sorted((DOC/'samples').iterdir()):
        if not p.is_dir():continue
        result=verify_bundle(p)
        assert result['bundle_integrity']=='valid' and result['facts_consistency']!='invalid',(p,result)
        samples[p.name]={'files':{f.name:file_hash(f) for f in p.iterdir() if f.is_file()},'verification':result}
    # Query only managed Job names registered by these tests/smoke.
    jobs=set()
    for root in roots:
        for path in root.rglob('ledger.sqlite'):
            db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
            try:
                jobs.update(r[0] for r in db.execute('SELECT job FROM worker'))
            finally:db.close()
    cleanup=[]
    for name in sorted(jobs):
        k=kernel();handle=k.OpenJobObjectW(4,False,name)
        if not handle:
            assert C.get_last_error()==2,(name,C.get_last_error());active=0
        else:
            job=object.__new__(Job);job.k=k;job.handle=handle
            try:active=job.snapshot()['active']
            finally:k.CloseHandle(handle)
        assert active==0,(name,active)
        cleanup.append({'job':name,'active':active})
    paths=[ROOT/'README.md',*DOC.glob('*.md'),DOC/'samples/README.md',ROOT/'docs/planning/12_implementation_backlog.md']
    links=[]
    for path in paths:
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf8')):
            if re.match(r'\w+://',link) or link.startswith('#'):continue
            target=(path.parent/link.split('#')[0].strip('<>')).resolve()
            # Manifest is produced at the end of this same check.
            assert target.exists() or target==DOC/'evidence_manifest.json',(path,link)
            links.append({'file':path.relative_to(ROOT).as_posix(),'link':link})
    historical=['docs/validation/phase1a','docs/validation/phase1b','probes/phase1a','requirements.lock','src/actio/pins/concordia.json']
    p=subprocess.run(['git','diff','--exit-code',BASE,'--',*historical],cwd=ROOT,capture_output=True,text=True)
    assert p.returncode==0,'historical evidence or dependency pins modified'
    bootstrap=Path(smoke['bootstrap_log'])
    assert file_hash(bootstrap)==smoke['bootstrap_log_sha256']==artifact['bootstrap_log_sha256']
    boot_copy=archive_dir/'bootstrap.log'
    boot_copy.write_bytes(bootstrap.read_bytes())
    # Failed semantic classification attempt remains separate, including its raw package hashes.
    failed_raw=[]
    for attempt in attempts:
        if attempt['exit_code']==0:continue
        data=json.loads((DOC/attempt['file']).read_text(encoding='utf8'))
        for t in data['tests']:
            for name,directory in t.get('evidence',{}).get('bundles',{}).items():
                for f in Path(directory).glob('*.json'):
                    failed_raw.append({'test':t['id'],'bundle':name,'file':str(f),'sha256':file_hash(f)})
    audit={'status':'PASS','exit_code':0,'command':str(Path(sys.executable).relative_to(ROOT))+' -X utf8 scripts/phase1b1_release.py',
           'local_links_checked':len(links),'jobs':cleanup,'historical_paths_unchanged':historical,
           'samples':samples,'documents':{p.relative_to(ROOT).as_posix():file_hash(p) for p in paths},
           'source_and_suite_bindings':'All current product hashes plus suite-specific test/fixture hashes checked; unrelated recorder/document additions do not invalidate earlier suites'}
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    delivery=DOC/'evidence'/('delivery-'+stamp+'.json')
    delivery.write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
    manifest={'phase':'1B.1','gate':'CONDITIONAL_GO','product_baseline':'668754fc51915a56818c25d1c0d6b3715f7f5396','handoff_baseline':BASE,
              'branch':'phase1b1-reliability-and-evidence-export','live_budget':0,'product_hashes':product,
              'current_suites':suites,'aggregate_tests':len(tests),'tests':tests,'history':attempts,
              'historical_mode_note':'Early generic runner top-level mode labels for new suites are superseded by the explicit modes above and per-test evidence; records are retained unchanged.',
              'failed_attempt_raw_package_hashes':failed_raw,'artifacts':ref(artifact_path),'clean_install_public_cli':ref(smoke_path),
              'retained_draft_samples':{'archive':'.local/phase1b1-evidence/pre-inventory-draft-samples.zip',
                  'sha256':file_hash(archive_dir/'pre-inventory-draft-samples.zip'),
                  'note':'Pre-release draft lacked sidecar inventory coverage; retained only as historical bytes, not a current passing bundle'},
              'bootstrap':{'command':smoke['bootstrap_command'],'exit_code':0,'log':str(boot_copy.relative_to(ROOT)),'sha256':file_hash(boot_copy),'network':smoke['network']},
              'delivery':ref(delivery),'samples':samples,
              'requirements':{'B1R1':'reliability + runtime + evidence','B1R2':'entry_concurrency + reliability + processes',
                              'B1R3':'reliability + processes + public CLI','B1R4':'reliability + runtime + public CLI',
                              'H2':'schema + evidence + public CLI','H3':'evidence + samples + public CLI','H4':'all current suites + artifacts + delivery'},
              'not_proven':['live models/evaluation/ability gains','binary-source provenance/signatures','power loss/device caches/disk-full',
                            'native resume/fork/catchup','full world restore or semantic cancellation','multi-active-run/multi-platform/scale',
                            'predecessor episode completeness beyond selected memory source proof']}
    (DOC/'evidence_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
    print('PASS:',len(tests),'aggregate tests;',len(cleanup),'inactive named Jobs;',len(links),'local links;',len(samples),'portable bundles')


if __name__=='__main__':main()
