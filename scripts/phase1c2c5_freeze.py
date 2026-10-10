"""Generate a pre-execution source/fixture freeze; commit it before the local matrix."""
import json
from pathlib import Path
import sys
from actio.common import canonical,file_hash,digest
from actio.transport_diagnostics import sources
from actio.failure_fixtures import CASES,portable_vectors
from actio.diagnostic_runtime import fixture,TOOLS

ROOT=Path(__file__).resolve().parents[1]


def main():
    dest=ROOT/'docs/validation/phase1c2c5/freeze.json'
    value={'schema':'transport-diagnostic-freeze.v1','sources':sources(),'tools':{n:file_hash(ROOT/n) for n in TOOLS},
        'contract_sha256':file_hash(ROOT/'docs/validation/phase1c2c5/CONTRACT.md'),'cases':CASES,
        'fixtures':[fixture(c) for c in CASES],'pure_vectors_sha256':digest(portable_vectors()),
        'maximum_loopback_sends':12,'matrix_scenarios':9,'external_requests':0,'argv':sys.orig_argv,
        'deadlines':{'ready':30,'rpc':5,'headers':60,'idle':60,'total':90,'result':115,'drain':5,'close':5,'worker':165}}
    with dest.open('x',encoding='utf8',newline='\n') as f:f.write(canonical(value))
    print(canonical({'file':str(dest),'sha256':file_hash(dest),'cases':9,'maximum_sends':12}))


if __name__=='__main__':main()
