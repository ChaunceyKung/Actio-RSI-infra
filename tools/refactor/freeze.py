"""Freeze installed product and finite local fixtures; never overwrite an old freeze."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from actio.contracts.json import canonical
from actio.contracts.json import digest
from actio.adapters.filesystem.common import file_hash
from actio.evidence.diagnostics.transport_diagnostics import sources
from actio.application.diagnostic_runtime import fixture
from actio.application.diagnostic_runtime import TOOLS
from actio.evidence.diagnostics.failure_fixtures import CASES
from actio.evidence.diagnostics.failure_fixtures import portable_vectors
ROOT=Path(__file__).resolve().parents[2]

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--wheel',type=Path,required=True);a=p.parse_args()
    value={'schema':'transport-diagnostic-freeze.v1','sources':sources(),'tools':{},'cases':CASES,
           'fixtures':[fixture(c) for c in CASES],'pure_vectors_sha256':digest(portable_vectors()),
           'maximum_loopback_sends':12,'matrix_scenarios':9,'external_requests':0,'argv':sys.orig_argv,
           'wheel_sha256':file_hash(a.wheel),'execution_tools':'installed product only; optional project verifies a source mirror',
           'harness_sources':{p.relative_to(ROOT).as_posix():file_hash(p) for p in sorted((ROOT/'tools/refactor').glob('*.py'))}}
    assert not TOOLS
    with a.output.open('x',encoding='utf8',newline='\n') as f:f.write(canonical(value))
    print(canonical({'file':str(a.output),'sha256':file_hash(a.output),'maximum_sends':12}))
if __name__=='__main__':main()
