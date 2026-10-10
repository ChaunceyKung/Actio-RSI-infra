"""Freeze only after complete final-product local admission. No credential reads."""
import json
from pathlib import Path
import subprocess
import sys
from actio.common import canonical,digest,file_hash
from actio import robustness_campaign as c
from actio.evaluation_store import plan
from actio.runtime import verify_runtime,pins
from actio.pilot import create

ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2c4'


def main():
    implementation=c.implementation();passed={};failed=[];cli=[];censuses=[]
    for path in sorted((DOC/'evidence').glob('*.json')):
        d=json.loads(path.read_bytes());ref={'file':path.relative_to(DOC).as_posix(),'sha256':file_hash(path)}
        if d.get('status')=='FAIL' or d.get('exit_code',0):failed.append(ref)
        if all(d.get('source_hashes',{}).get('src/actio/'+k)==v for k,v in implementation.items()):
            for test in d.get('tests',[]):
                if test['status']=='PASS':passed[test['id']]=ref
        if d.get('status')=='PASS' and d.get('implementation')==implementation:
            if d.get('kind')=='full_rehearsal':cli.append((d,ref))
            if 'census' in d:censuses.append((d,ref))
    required=['test_robustness.RobustnessPure.'+n for n in (
        'test_01_schedule_mapping_and_closed_old_domains','test_02_exhaustive_independent_mapping_truth',
        'test_03_metrics_missing_applicability_and_pair_denominators','test_04_consistent_copy_historical_dispatch_claims_and_decision',
        'test_05_once_claim_concurrent_roots_and_unknown_plan')]
    required+=['test_robustness_runtime.RobustnessRuntime.'+n for n in (
        'test_01_behavior_errors_and_actual_own_arm_history','test_02_unknown_stops_suffix_duplicate_execute_denied',
        'test_03_headers_timeout_and_cleanup','test_04_controller_and_verifier_failure_preserve_inventory',
        'test_05_equal_hidden_world_A_wire_allows_different_output')]
    assert all(t in passed for t in required),[t for t in required if t not in passed]
    assert cli and censuses
    local,cli_ref=cli[-1];census,census_ref=censuses[-1]
    assert local['rehearsal_counts']['sent']==local['rehearsal_counts']['admitted']==128
    assert census['census']['full_rehearsal']['sent']==128 and census['census']['live']['sent']==0
    assert len([x for x in local['commands'] if x['guard']])==5
    history=json.loads((DOC/'history.json').read_bytes());assert history['status']=='PASS'
    source=Path('D:/actio-c2c2-live-v1/candidates.sqlite');sourcehash=history['readers'][0]['result']['database_sha256']
    assert file_hash(source)==sourcehash
    assert all(file_hash(ROOT/'src/actio'/name)==h for name,h in implementation.items())
    verify_runtime()
    create(DOC/'preregistration.json',c.preregistration())
    create(DOC/'evaluation-plan.json',plan(c.preregistration(),'live_development_exploratory'))
    create(DOC/'evaluation-policy.json',c.POLICY)
    create(DOC/'local-acceptance.json',{'status':'PASS','implementation':implementation,'tests':passed,
        'failed_attempts_retained':failed,'full_rehearsal':cli_ref,'cleanup':census_ref,'rehearsal_root':local['root'],
        'source_database_sha256':sourcehash,'historical_source_receipt_sha256':file_hash(DOC/'history.json'),
        'historical_lineage_sha256':history['readers'][0]['result']['lineage_sha256'],
        'argv':sys.orig_argv,'new_provider_requests':0,'research_validity':'UNESTABLISHED','activation':False})
    create(DOC/'installation.json',{'python':sys.version,'implementation':implementation,'runtime':pins(),
        'installed_source_equal':True,'runtime_verified':True,'dependency_install':'requirements.lock local wheels, --offline',
        'concordia':'fixed local Git archive, minimal import closure',
        'bootstrap_argv':['.local/phase1c2c2-runtime-venv/Scripts/python.exe','-X','utf8','scripts/bootstrap.py','--venv',
            '.local/phase1c2c4-runtime-venv','--offline','--concordia-source',r'D:\调研\RSI_AI训AI\agentic_evolution_infrastructure\codebase\15_concordia\repo'],
        'bootstrap_exit_code':0,'post_edit_install_argv':['.local/phase1c2c4-runtime-venv/Scripts/python.exe','-m','pip','install','--no-index','--no-deps','--no-build-isolation','.'],
        'post_edit_install_exit_code':0})
    create(DOC/'baseline.json',{'head_before_work':'dbb0f815c5d1baae28e37ddaeb8f68b6b442f0dc',
        'origin_main_before_work':'dbb0f815c5d1baae28e37ddaeb8f68b6b442f0dc','initial_worktree':'clean',
        'branch':c.BRANCH,'remote':'https://github.com/ChaunceyKung/Actio-RSI-infra',
        'ancestors':{sha:subprocess.run(['git','merge-base','--is-ancestor',sha,'HEAD'],cwd=ROOT).returncode==0 for sha in (
            'b50b6da28c25ef34da6a620b2b45a576ead5330f','0a66334d61a0de302bbf8f5e15ee1db1b9d2e8fb','3bef7e15b0eb21beeb10888eb508056592b977b0','6466e2be6f31e0ac5861a379d761d2e7bf39c5eb')},
        'fetch':'two schannel handshake failures; ordinary HTTP/1.1 fetch then succeeded; TLS verification retained'})
    print(canonical({'status':'PASS','tests':len(required),'preregistration':c.preregistration()['sha256'],'rehearsal':local['rehearsal_counts']}))


if __name__=='__main__':main()
