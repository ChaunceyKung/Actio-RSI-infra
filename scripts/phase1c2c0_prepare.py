"""Freeze only after current-source local admission, never after observing live scores."""
import json
from pathlib import Path
from actio.common import canonical,file_hash
from actio.suite_contract import preregistration,implementation
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2c0'

def main():
    pre=preregistration();current={'src/actio/'+k:v for k,v in implementation().items()};passed={};failed=[]
    for p in sorted((DOC/'evidence').glob('*.json')):
        d=json.loads(p.read_bytes())
        if 'suite' not in d:continue
        if d['exit_code']:failed.append({'file':p.relative_to(DOC).as_posix(),'sha256':file_hash(p)})
        if all(d['source_hashes'].get(k)==v for k,v in current.items()):
            for t in d['tests']:
                if t['status']=='PASS':passed[t['id']]={'file':p.relative_to(DOC).as_posix(),'sha256':file_hash(p)}
    for test in ('test_suite.SuitePure.test_01_exhaustive_independent_truth_and_sensitivity',
       'test_suite_runtime.SuiteRuntime.test_01_matrix_full_wire_and_portable_reader',
       'test_suite_runtime.SuiteRuntime.test_04_deadlines_production_31s_and_short_failure_boundaries',
       'test_suite_evidence.SuiteEvidence.test_rehashed_raw_contradiction_and_partial_plan'):
        assert test in passed,'local admission missing: '+test
    truth=next(t['evidence'] for d in (json.loads(x.read_bytes()) for x in sorted((DOC/'evidence').glob('*.json'))) for t in d.get('tests',[]) if t['id']=='test_suite.SuitePure.test_01_exhaustive_independent_truth_and_sensitivity' and t['status']=='PASS')
    for name,value in [('truth-table.json',truth['truth_table']),('metric-sensitivity.json',{'sensitivity':truth['sensitivity'],'controls':truth['controls'],'human_labels':0}),('preregistration.json',pre),('task-cards.json',pre['body']['cards']),
        ('local-acceptance.json',{'status':'PASS','implementation':implementation(),'tests':passed,'failed_attempts_retained':failed,'human_labels':0,'external_model_calls':0})]:
        with (DOC/name).open('x',encoding='utf8',newline='\n') as f:f.write(canonical(value))
    print(canonical({'preregistration_hash':pre['sha256'],'tests':len(passed),'planned_episodes':24,'maximum_sends':48}))

if __name__=='__main__':main()
