"""Freeze source, old authoritative lineage and source-bound local admission."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from actio.common import canonical,file_hash
from actio import evaluation_campaign as c
from actio.evaluation_store import plan
from actio.store import Store
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2c2'


def write(name,value):
    with (DOC/name).open('x',encoding='utf8',newline='\n') as f:f.write(canonical(value))


def main():
    implementation=c.implementation();passed={};failed=[];matrix=None
    for path in sorted((DOC/'evidence').glob('*.json')):
        d=json.loads(path.read_bytes())
        if 'suite' not in d:continue
        if d['exit_code']:failed.append({'file':path.relative_to(DOC).as_posix(),'sha256':file_hash(path)})
        if all(d['source_hashes'].get('src/actio/'+k)==v for k,v in implementation.items()):
            for test in d['tests']:
                if test['status']=='PASS':
                    passed[test['id']]={'file':path.relative_to(DOC).as_posix(),'sha256':file_hash(path)}
                    if test['id'].endswith('test_02_complete_rehearsal_behavior_and_dynamic_history'):matrix=test['evidence']['root']
    required=['test_evaluation_candidate.EvaluationPure.test_versions_identities_denominators_policy',
        'test_evaluation_candidate.EvaluationPure.test_copy_history_atomic_claim_decision_reopen_corruption',
        *['test_evaluation_candidate_runtime.EvaluationRuntime.'+x for x in ('test_02_complete_rehearsal_behavior_and_dynamic_history',
            'test_03_unknown_stops_suffix_and_claim','test_04_controller_failure_keeps_inventory_when_verifier_fails')]]
    assert all(t in passed for t in required),[t for t in required if t not in passed]
    cli=[json.loads(p.read_bytes()) for p in (DOC/'evidence').glob('cli-*.json')]
    assert any(d.get('status')=='PASS' and d.get('implementation')==implementation for d in cli)
    source=Path('D:/actio-c2c1-main-v1/candidates.sqlite');old=Store(source,readonly=True)
    try:history=old.candidate_lineage()
    finally:old.close()
    published=json.loads((ROOT/'docs/validation/phase1c2c1/samples/lineage.json').read_bytes());assert published==history
    legacy={'database':str(source),'database_sha256':file_hash(source),'lineage_sha256':history['sha256'],
        'published_lineage_file_sha256':file_hash(ROOT/'docs/validation/phase1c2c1/samples/lineage.json'),'reader':c.LEGACY_READER}
    assert json.loads((DOC/'history.json').read_bytes())['status']=='PASS'
    write('preregistration.json',c.preregistration());write('evaluation-plan.json',plan(c.preregistration(),'live_development_exploratory'))
    write('evaluation-policy.json',c.POLICY);write('legacy-source.json',legacy)
    write('local-acceptance.json',{'status':'PASS','implementation':implementation,'tests':passed,'failed_attempts_retained':failed,
        'rehearsal_root':matrix,'legacy_source':legacy,'new_provider_requests':0,
        'deadline_evidence':'C2C0 fixed historical 31-second test retained; v9 wiring observed in actual new runtime tests',
        'prohibited':'no current capability pass, no live retry, no activation'})
    oldproof=json.loads((ROOT/'docs/validation/phase1c2c1/provenance.json').read_bytes());assets=[]
    for entry in oldproof['assets']:
        repo=Path(entry['local_path'])
        for _ in Path(entry['path']).parts:repo=repo.parent
        raw=subprocess.check_output(['git','show',entry['commit']+':'+entry['path']],cwd=repo)
        assert hashlib.sha256(raw).hexdigest()==entry['git_blob_sha256'];assets.append(entry)
    write('provenance.json',{'assets':assets,'rechecked_pinned_git_blobs':True,'new_frameworks':False,
        'dsh_reference':'official pi-ai unchanged; stream.ts two-channel lifecycle and replayState shape',
        'raven_reference':'per-unit paired arithmetic and immutable ancestry concept; SQL owns facts, no root fork',
        'licenses':'existing C2C1 DSH_LICENSE.txt, RAVEN_LICENSE.txt and RAVEN_NOTICES.md remain in repository',
        'binary_source_mapping':'unproven','concordia':oldproof['concordia'],'dsh_exe_sha256':oldproof['dsh_exe_sha256']})
    write('baseline.json',{'head_before_work':'5affb4785b537105c09cbcdaa4ef055061712ba6','origin_main_before_work':'5affb4785b537105c09cbcdaa4ef055061712ba6',
        'review_baseline':c.LEGACY_READER,'review_is_ancestor':True,'initial_worktree':'clean',
        'remote':'https://github.com/ChaunceyKung/Actio-RSI-infra','branch':c.BRANCH})
    print(canonical({'status':'PASS','plan':c.preregistration()['sha256'],'source_bound_tests':len(passed),'rehearsal':matrix}))


if __name__=='__main__':main()
