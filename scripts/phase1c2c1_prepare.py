"""Freeze current implementation and local plan after source-bound admission."""
import hashlib
import json
from pathlib import Path
import subprocess
from actio.common import canonical,file_hash
from actio.candidate_campaign import preregistration,implementation
from actio.candidate_contract import baseline,candidate,rejected_fixtures,POLICY
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2c1'


def write(name,value):
    with (DOC/name).open('x',encoding='utf8',newline='\n') as f:f.write(canonical(value))


def main():
    current={'src/actio/'+k:v for k,v in implementation().items()};passed={};failed=[];sidecar=None;fixtures=None
    for path in sorted((DOC/'evidence').glob('*.json')):
        d=json.loads(path.read_bytes())
        if 'suite' not in d:continue
        if d['exit_code']:failed.append({'file':path.relative_to(DOC).as_posix(),'sha256':file_hash(path)})
        if all(d['source_hashes'].get(k)==v for k,v in current.items()):
            for t in d['tests']:
                if t['status']=='PASS':
                    passed[t['id']]={'file':path.relative_to(DOC).as_posix(),'sha256':file_hash(path)}
                    if t['id'].endswith('test_historical_channel_compatibility_and_clock_semantics'):sidecar=t['evidence']
                    if t['id'].endswith('test_candidate_policy_and_complete_denominators'):fixtures=t['evidence']['policy_fixtures']
    for name in ('candidate.CandidatePure.test_channels_fsm_and_fail_closed','candidate.CandidatePure.test_store_atomicity_persistence_migration_and_corruption',
                 'candidate_runtime.CandidateRuntime.test_dual_channel_official_runtime_and_hidden_views',
                 'candidate_runtime.CandidateRuntime.test_actual_arm_pair_prepared_full_wire_and_tamper',
                 'candidate_runtime.CandidateRuntime.test_incomplete_stops_and_claim_is_not_reclaimed'):
        assert 'test_'+name in passed,'missing current-source admission: '+name
    assert sidecar and fixtures
    write('preregistration.json',preregistration());write('proposals.json',{'baseline':baseline(),'candidate':candidate(),'synthetic_rejections':rejected_fixtures()})
    write('policy.json',POLICY);write('policy-fixtures.json',fixtures);write('c2c0-compatibility.json',sidecar)
    write('local-acceptance.json',{'status':'PASS','implementation':implementation(),'tests':passed,'failed_attempts_retained':failed,
        'deadlines_unchanged':True,'production_31s_test':'C2C0 fixed historical evidence; not rerun','provider_requests':0})
    review=json.loads((ROOT/'docs/reviews/phase1c2c0_review_evidence.json').read_bytes());assets=[]
    for entry in review['reuse_assets']['source_files']:
        asset=entry['asset'];repo=Path(entry['local_path'])
        for _ in Path(entry['path']).parts:repo=repo.parent
        raw=subprocess.check_output(['git','show',entry['commit']+':'+entry['path']],cwd=repo)
        assert hashlib.sha256(raw).hexdigest()==entry['git_blob_sha256']
        assets.append({**entry,'rechecked_from_pinned_blob':True,'integration':'official runtime remains external; audit shape reference' if asset=='dsh' else 'formula/test and parent descriptor reference only; no Raven source copied'})
        if entry['path']=='LICENSE':(DOC/(asset.upper()+'_LICENSE.txt')).write_bytes(raw)
    raven=Path(next(x['local_path'] for x in assets if x['asset']=='raven' and x['path']=='LICENSE')).parent
    notice=subprocess.check_output(['git','show','3632e6040c7038a60ec418ce39ccae185c72c19f:NOTICES.md'],cwd=raven)
    (DOC/'RAVEN_NOTICES.md').write_bytes(notice)
    write('provenance.json',{'assets':assets,'raven_notice_sha256':hashlib.sha256(notice).hexdigest(),
        'raven_reference':'candidate minus baseline per-unit arithmetic; missing=null, no z/statistical promotion; immutable SQL replaces JSON archive ownership',
        'dsh_reference':'per-index reasoning/text lifecycle + bounded replay metadata; official translator unmodified',
        'binary_source_mapping':'unproven','dsh_exe_sha256':'7ff077cfa28b81aa33f96aca97911969f8b6499bc1f85e4a6d3ddd16b8aa67d6',
        'concordia':'b71d202750e23444ce1bf28d9f114bcd88aa41db','task_oracle':'unchanged C2C0 suite_tasks/suite_oracle; cards CC0-1.0',
        'upstream_tests_rerun':False,'network_requests':0})
    write('baseline.json',{'head_before_work':'03bfa2d5a0eef107de4b6ad2e81dec01c4e1490f','origin_main_before_work':'03bfa2d5a0eef107de4b6ad2e81dec01c4e1490f',
        'review_baseline':'e2e6691ef9bae5f61bccaaa97528e0478bd9a666','review_is_ancestor':True,'initial_worktree':'clean','provider_requests':0})
    print(canonical({'preregistration_hash':preregistration()['sha256'],'current_tests':len(passed),'failed_records':len(failed)}))


if __name__=='__main__':main()
