"""Freeze product/plan and append historical semantic review without rewriting sources."""
import json
from pathlib import Path
import subprocess
import sys
from actio.common import canonical,file_hash
from actio.pilot_contract import preregistration
from actio.stream_audit import audit
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2b2'

def immutable(path,v):
    raw=canonical(v)
    if path.exists():assert path.read_text(encoding='utf8')==raw;return
    with path.open('x',encoding='utf8',newline='\n') as f:f.write(raw)

def main():
    pre=preregistration();records=[];sources={}
    for name in ('gpt56','claude'):
        root=ROOT/'docs/validation/phase1c2b1/samples'/name
        sources.update({p.relative_to(ROOT).as_posix():file_hash(p) for p in root.rglob('*') if p.is_file()})
        idx=json.loads((root/'campaign.json').read_bytes())['body']
        ledger=json.loads((root/idx['paths']['ledger']).read_bytes())['body']
        dataset=json.loads((root/idx['paths']['dataset']).read_bytes())['body']
        ops={o['id']:o for source in dataset['sources'].values() for o in json.loads(source['files']['evidence.json'])['operations']}
        for a in ledger['attempts']:
            records.append({'route':name,'operation':a['id'],'review':audit(a['response'],ops[a['id']]['answer']),'original_accounting_state':a['state']})
    assert len(records)==8
    assert all(file_hash(ROOT/n)==h for n,h in sources.items())
    immutable(DOC/'historical-text-review.json',{'reader_source_base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'reader_sha256':file_hash(ROOT/'src/actio/stream_audit.py'),'new_product_hashes':pre['body']['implementation'],
        'historical_reader_commit':'1e00535408e3a3dd12356dbb2cdf934134fb68e4','historical_files_unchanged':sources,
        'records':records,'writes_to_historical_files':0,'billing_reconciliation':'UNVERIFIED'})
    immutable(DOC/'preregistration.json',pre)
    print(canonical({'preregistration_hash':pre['sha256'],'planned_episodes':32,'planned_seats':64,'historical_records':8,'external_model_calls':0}))

if __name__=='__main__':main()
