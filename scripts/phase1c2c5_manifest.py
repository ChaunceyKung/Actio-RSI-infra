"""Bind final documentation, source, acceptance and original-runtime reuse precisely."""
import json
from pathlib import Path
import sqlite3
import sys
from actio.common import canonical,file_hash
from actio.transport_diagnostics import sources,analyze
from actio.failure_fixtures import CASES

ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2c5'


def main():
    actual=sources();assert all(file_hash(ROOT/'src/actio'/n)==h for n,h in actual.items())
    for name in ('acceptance-cec45e1c4746.json','runtime-recomputed-f6c627a96092.json','portability-470bc5a4d9f7.json','publication-scan.json'):
        d=json.loads((DOC/name).read_bytes());assert d['status']=='PASS' and d['sources']==actual
    assert analyze(json.loads((DOC/'package.json').read_bytes()))['valid']
    leases=[]
    for case in CASES:
        p=Path('D:/actio-c2c5-formal-v1')/case['id']/'episode/domain.sqlite';before=file_hash(p)
        db=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True)
        try:count=db.execute('SELECT count(*) FROM lease').fetchone()[0]
        finally:db.close()
        assert count==0 and before==file_hash(p);leases.append({'case':case['id'],'active_lease_rows':0,'database_sha256':before})
    with (DOC/'authority-check.json').open('x',encoding='utf8',newline='\n') as f:f.write(canonical({'status':'PASS','rows':leases,'tool_sha256':file_hash(Path(__file__))}))
    files={p.relative_to(DOC).as_posix():file_hash(p) for p in sorted(DOC.rglob('*')) if p.is_file() and p.name!='evidence_manifest.json'}
    tooling={p.relative_to(ROOT).as_posix():file_hash(p) for pattern in ('scripts/phase1c2c5_*.py','scripts/install_failure_diagnostics.py','tests/test_failure_observation.py') for p in ROOT.glob(pattern)}
    result={'schema':'c5-evidence-manifest.v1','phase':'1C2C5','status':'PASS','files':files,'final_sources':actual,'final_tools':tooling,
        'entry_documents':{'README.md':file_hash(ROOT/'README.md'),'MILESTONES.md':file_hash(ROOT/'MILESTONES.md')},
        'design_commit':'b37463d','runtime_freeze_commit':'196e8a6f3327b9d17ee0c0ba3bc45c93c38334e0',
        'runtime_freeze_file':'freeze.json','original_runtime_status':'FAIL','final_diagnostic_recomputation_status':'PASS',
        'final_source_runtime_reexecuted':False,'reuse_scope':'unchanged official transport, ledger, domain, actual 12 local sends; all changed diagnostics and CLI revalidated offline',
        'failure_records':['development-cli01-failure.json','acceptance-18de8a178371.json','formal-original.json','development-portability01-failure.json'],
        'final_acceptance':'acceptance-cec45e1c4746.json','runtime_recomputation':'runtime-recomputed-f6c627a96092.json',
        'portability':'portability-470bc5a4d9f7.json','history_before':'history-fe0824eda3f4.json','history_after':'history-c0f4e5bf13e3.json',
        'formal_loopback_sends':12,'development_loopback_sends':0,'postfix_loopback_sends':0,'new_provider_requests':0,
        'new_catalog_get':0,'new_external_mcp':0,'cumulative_real_generation':172,'historical_catalog_get':1,
        'provider_availability':'NOT_RETESTED','C4':'INCOMPLETE','C1':'infrastructure_failure','research':'UNESTABLISHED',
        'activation':False,'binary_source_mapping':'unproven','full_controller_recovery':'unsupported',
        'publication':'ordinary task/main push and independent ls-remote; exact final SHA reported by delivery message, no self-referential hash',
        'argv':sys.orig_argv}
    with (DOC/'evidence_manifest.json').open('x',encoding='utf8',newline='\n') as f:f.write(canonical(result))
    print(canonical({'status':'PASS','files':len(files),'source_files':len(actual),'tools':len(tooling)}))


if __name__=='__main__':main()
