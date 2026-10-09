"""Author the fixed public-source trust registry; not an artifact-driven reader."""
import ast
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from actio.common import canonical, digest
from actio.task_diagnostics import extract_history, READER


def main():
    old = ROOT / 'docs/validation/phase1c2c2'
    names = ['samples/report.json', 'preregistration.json', 'samples/decision.json', 'samples/lineage.json',
             'evidence_manifest.json', 'controlled-delivery.json']
    values = {n: json.loads((old / n).read_bytes()) for n in names}
    source = ROOT / '.local/phase1c2c3-history/src/actio'
    persona = next(ast.literal_eval(n.value) for n in ast.parse((source / 'suite_contract.py').read_text(encoding='utf8')).body
                   if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'PERSONA' for t in n.targets))
    receipt = ROOT / 'docs/validation/phase1c2c3/historical-source.json'
    rc = json.loads(receipt.read_bytes())
    assert rc['reader_commit'] == READER and rc['exit_code'] == 0 and rc['result']['report_exact']
    registry = {'schema': 'task-diagnostic-trusted-sources.v1',
                'historical_files': {n: hashlib.sha256((old / n).read_bytes()).hexdigest() for n in names},
                'historical_source_hashes': {n: hashlib.sha256((source / n).read_bytes()).hexdigest()
                                           for n in ('suite_tasks.py', 'suite_oracle.py', 'suite_contract.py', 'candidate_contract.py', 'evaluation_measurement.py')},
                'persona': persona, 'source_receipt_file_hash': hashlib.sha256(receipt.read_bytes()).hexdigest()}
    history = extract_history(values['samples/report.json'], values['preregistration.json'],
                              values['samples/decision.json'], values['samples/lineage.json'], registry)
    registry['historical_excerpt_hash'] = digest(history)
    registry['certified_assurance'] = {'schema': 'task-diagnostic-assurance.v1',
        'source_assurance': 'fixed_reader_local_attested', 'raw_verified_here': False,
        'receipt_hash': registry['source_receipt_file_hash'], 'reader_commit': READER,
        'certification_result': rc['result'],
        'portable_scope': 'prior local fixed-reader certification recorded; package rechecks pinned public excerpt and synthetic logic only; not provider signature'}
    dest = ROOT / 'src/actio/task_diagnostic_trust.json'
    with dest.open('x', encoding='utf8', newline='\n') as f:
        f.write(canonical(registry))
    print(canonical({'status': 'created_fixed_registry', 'excerpt_hash': registry['historical_excerpt_hash'], 'old_files': len(names)}))


if __name__ == '__main__':
    main()
