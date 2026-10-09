"""Serial standard-library acceptance with source-bound PASS and failure records."""
import hashlib
import io
import json
from pathlib import Path
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests')]
from actio.common import canonical
from actio.task_diagnostics import source_pins


def main():
    source = source_pins()
    files = ['tests/test_task_diagnostics.py', 'scripts/phase1c2c3_validate.py']
    tooling = {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in files}
    log = io.StringIO()
    start = time.time()
    suite = unittest.defaultTestLoader.loadTestsFromName('test_task_diagnostics')
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    evidence = {'schema': 'task-diagnostic-acceptance.v1', 'source': source, 'tooling': tooling,
                'argv': [sys.executable, *sys.orig_argv[1:]], 'tests_run': result.testsRun,
                'status': 'PASS' if result.wasSuccessful() else 'FAIL', 'log': log.getvalue(),
                'elapsed_ms': int((time.time() - start) * 1000), 'new_model_requests': 0, 'new_workers': 0}
    folder = ROOT / 'docs/validation/phase1c2c3/evidence'
    folder.mkdir(exist_ok=True)
    name = 'tests-' + hashlib.sha256(canonical(evidence).encode()).hexdigest()[:12] + '.json'
    with (folder / name).open('x', encoding='utf8', newline='\n') as f:
        f.write(canonical(evidence))
    print(log.getvalue())
    print(canonical({'record': name, 'status': evidence['status'], 'tests': result.testsRun}))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
