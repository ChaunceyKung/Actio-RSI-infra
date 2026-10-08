"""Seal current validation references; retain every earlier attempt separately."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/validation/phase1b'


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def requirements(test):
    if 'cross_process' in test:return ['B1.1','B1.3','B1.4','privacy','frozen-start-reexecution']
    if 'two_turns' in test:return ['B1.1','B1.2','R2']
    if any(x in test for x in ('final_policy','call_id')):return ['B1.1','R1']
    if 'two_control' in test:return ['B1.1','lease-race']
    if 'accepted_receipt' in test:return ['B1.1','B1.2','R3','window-A','owner-death']
    if 'received_before_result' in test:return ['B1.1','B1.2','window-B']
    if 'flush_before_canonical' in test:return ['B1.2','R2','window-C']
    if 'commit_before_caller_ack' in test:return ['B1.3','R4','window-D']
    if 'memory_' in test or 'namespace_' in test:return ['B1.3','R4']
    if 'out_of_order' in test or 'barrier_' in test:return ['B1.2','R2']
    if 'identity_idempotency' in test:return ['B1.1','R3']
    return ['B1.1','R3','R5' if 'unsupported' in test else 'bounded-execution']


if __name__=='__main__':
    attempts=[];latest={}
    for path in sorted((DOC/'evidence').glob('20*.json')):
        data=json.loads(path.read_text(encoding='utf8'))
        if 'suite' not in data:continue
        attempts.append({'id':data['id'],'suite':data['suite'],'file':path.relative_to(DOC).as_posix(),
                         'sha256':sha(path),'exit_code':data['exit_code'],'tests_run':data['tests_run']})
        latest[data['suite']]=(path,data)
    assert set(latest)=={'contract','runtime','failures','processes'},latest.keys()
    expected={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'src').rglob('*') if p.suffix in {'.py','.mjs','.json','.sql'}}
    rows=[];current=[]
    archives=ROOT/'.local/evidence';archives.mkdir(parents=True,exist_ok=True)
    for suite,(path,data) in latest.items():
        assert data['exit_code']==0 and data['tests_run']>0 and data['tests'],(suite,'not passing')
        assert all(data['source_hashes'].get(k)==v for k,v in expected.items()),(suite,'product changed after test')
        relevant=['tests/test_'+suite+'.py']+(['tests/support.py'] if suite in {'failures','processes'} else [])
        for name in relevant:assert data['source_hashes'][name]==sha(ROOT/name),(suite,'test changed after execution',name)
        archive=archives/(data['id']+'.zip')
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for test in data['tests']:
                evidence=test.get('evidence',{})
                if 'root' not in evidence:continue
                root=Path(evidence['root'])
                for rel,h in evidence.get('files',{}).items():
                    source=root/rel
                    assert source.is_relative_to(root) and sha(source)==h,(test['id'],rel,'raw evidence changed')
                    z.write(source,test['id'].split('.')[-1]+'/'+rel)
        current.append({'suite':suite,'file':path.relative_to(DOC).as_posix(),'sha256':sha(path),'command':data['command'],
                        'exit_code':data['exit_code'],'raw_archive':archive.relative_to(ROOT).as_posix(),'raw_archive_sha256':sha(archive)})
        for test in data['tests']:
            assert test['status']=='PASS',test['id']
            rows.append({'id':'P1B-'+str(len(rows)+1).zfill(3),'test':test['id'],'requirements':requirements(test['id']),
                         'status':'PASS','mode':'SQLITE_CONTRACT' if suite=='contract' or 'two_control' in test['id'] else 'REAL_RUNTIME_FIXTURE_PROVIDER',
                         'evidence':path.relative_to(DOC).as_posix(),'command':data['command'],'exit_code':data['exit_code']})
    artifacts=sorted((DOC/'evidence').glob('artifacts-*.json'))[-1]
    artifact=json.loads(artifacts.read_text(encoding='utf8'))
    assert artifact['status']=='PASS'
    with zipfile.ZipFile(archives/'bootstrap-logs.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        boot=[]
        for p in sorted((ROOT/'.local').glob('bootstrap-*.log')):
            z.write(p,p.name);boot.append({'file':p.relative_to(ROOT).as_posix(),'sha256':sha(p)})
    result={'phase':'1B','gate':'CONDITIONAL_GO','base_commit':'56865acb920d309f787485e16a06f24df67c883d',
        'branch':'phase1b-persistent-vertical-slice','live_budget':0,'product_hashes':expected,
        'current_suites':current,'tests':rows,'aggregate_tests':len(rows),'history':attempts,
        'artifacts':{'file':artifacts.relative_to(DOC).as_posix(),'sha256':sha(artifacts),'status':'PASS','command':artifact['command']},
        'supporting_evidence':[{'file':p.relative_to(DOC).as_posix(),'sha256':sha(p)} for p in sorted((DOC/'evidence').glob('*.json')) if p.name.startswith(('concordia-','delivery'))],
        'bootstrap':{'successful_command':'python -X utf8 scripts/bootstrap.py --venv .local/final-venv --offline-wheels',
                     'exit_code':0,'source_sha256':sha(ROOT/'scripts/bootstrap.py'),'logs':boot,'raw_archive':'.local/evidence/bootstrap-logs.zip','raw_archive_sha256':sha(archives/'bootstrap-logs.zip'),
                     'historical_failures':['Initial online wheel download timeout (pip exit 2, bootstrap exit 1; tool transcript, no separate raw log file)',
                       'GitHub Concordia LF bytes rejected against original local CRLF pin; exact LF git/archive equivalence then verified',
                       'Isolated deep TEMP product wheel build WinError 3; task-owned short TEMP succeeded']},
        'controlled_cases':[{'requirement':'Job assignment failure cleanup','mode':'CONTROLLED_ENVELOPE','actual':'injected constructor rejection before gate release; real waiting child terminated'},
                            {'requirement':'window-C','mode':'REAL_RUNTIME_FIXTURE_PROVIDER + CONTROLLED_ENVELOPE','actual':'real native flush then explicit exception before canonical commit'}],
        'not_executed':[{'id':name,'status':status,'mode':'NOT_EXECUTED'} for name,status in [
            ('G2-live-provider-budget-zero','BLOCKED'),('research-evaluator/SOTOPIA','NOT_RUN'),('wire-bytes-before-SDK-decode','NOT_RUN'),
            ('disk-full','NOT_RUN'),('power-loss/device-cache','NOT_RUN'),('physical-generation-migration','NOT_RUN'),
            ('Linux/WSL','NOT_RUN'),('100-agent-scale','NOT_RUN'),('binary-source-build-provenance','UNPROVEN')]],
        'limits':['All data synthetic; fixed provider and GM outputs','No automatic dispatch on reconcile',
                  'SDK queues remain internally unbounded; Job memory/time containment only','Disk budget is monitored, not a filesystem hard quota',
                  'Full raw evidence is local and ignored; committed summaries retain assertions, source hashes and raw hashes',
                  'No push, merge, deployment or next-slice work authorized by this delivery']}
    (DOC/'evidence_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print('Sealed',len(rows),'current aggregate tests;',len(attempts),'retained suite attempts')
