from actio.evidence.task_diagnostics import read_json, load_history, assurance, build, manifest, gates, ZERO
from pathlib import Path
from actio.contracts.json import canonical
from actio.tasks.registry import require
from actio.tasks.diagnostic import dataset
SCHEMA = 'task-diagnostic-package.v1'
READER = '3bef7e15b0eb21beeb10888eb508056592b977b0'
PACKAGE_FILES = ['plan.json', 'dataset.json', 'policies.json', 'metrics.json', 'historical-actions.json',
                 'source-assurance.json', 'retrospective.json', 'synthetic-report.json', 'overlap.json']
ZERO = {'new_model_requests': 0, 'new_provider_requests': 0, 'new_catalog_get': 0,
        'new_mcp_calls': 0, 'new_dsh_workers': 0, 'credential_reads': 0}

def analyze(source, output, *, receipt=None, data_path=None):
    output = Path(output)
    require(not output.exists(), 'output must be a new directory; no overwrite')
    data = dataset() if data_path is None else read_json(data_path)
    values = build(load_history(source), assurance(receipt), data)
    values['manifest.json'] = manifest(values)
    # Parent must already exist: no implicit writes outside the requested directory.
    output.mkdir(exist_ok=False)
    for name, value in values.items():
        with (output / name).open('x', encoding='utf8', newline='\n') as f:
            f.write(canonical(value))
    return {'valid': True, 'manifest_hash': values['manifest.json']['sha256'], 'gates': gates(values), **ZERO}
