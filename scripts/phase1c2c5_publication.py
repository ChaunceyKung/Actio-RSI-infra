"""Local exact exclusion scan only; real credential never leaves memory."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from actio.common import canonical,file_hash
from actio.transport_diagnostics import sources

ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2c5'
BASE='d7563a39a1164a68c6fbb60cdb55063b2f28e93c'


def main():
    # Authorized only for exact local exclusion scanning, no properties exported.
    secret=(ROOT/'.local/credentials/token_key.txt').read_text(encoding='utf-8-sig').strip().encode()
    assert secret
    delivery=json.loads(Path('D:/actio-c2c4-live-v1/delivery.json').read_bytes());private=[]
    for entry in delivery['body']['campaign']['body']['entries']:
        if entry['evidence'] is None:continue
        for attempt in entry['evidence']['ledger']['attempts']:
            private.append(attempt['request']['raw'].encode());private.append(attempt['response']['raw'].encode());reasoning=[]
            for line in attempt['response']['raw'].splitlines():
                if not line.startswith('data: ') or line=='data: [DONE]':continue
                obj=json.loads(line[6:])
                if isinstance(obj.get('error'),dict) and obj['error'].get('message'):private.append(obj['error']['message'].encode())
                for choice in obj.get('choices',[]):
                    value=choice.get('delta',{}).get('reasoning_content')
                    if value:reasoning.append(value)
            if reasoning:private.append(''.join(reasoning).encode())
    private=[x for x in private if x]
    def git(*args):return subprocess.check_output(['git','-c','core.quotepath=false',*args],cwd=ROOT,text=True,encoding='utf8').splitlines()
    changed=set(git('diff','--name-only','--diff-filter=AM',BASE))|set(git('ls-files','--others','--exclude-standard'))
    selected=sorted(n for n in changed if (ROOT/n).is_file())
    publication={}
    for n in selected:
        p=ROOT/n;assert p.suffix.lower() not in ('.sqlite','.db','.log','.exe','.whl','.zip','.pyc')
        data=p.read_bytes();assert secret not in data and not any(x in data for x in private),'publication exclusion failed'
        publication[n]=hashlib.sha256(data).hexdigest()
    # All new generated material is scanned, including retained failures and cache.
    roots=[Path('D:/actio-c2c5-formal-v1')]
    roots.extend(ROOT/'.local'/n for n in ('phase1c2c5-validation','phase1c2c5-recomputed','phase1c2c5-history','phase1c2c5-portability'))
    files={p for root in roots for p in root.rglob('*') if p.is_file()}
    files.update(ROOT/'.local'/n for n in ('phase1c2c5-bootstrap.log','phase1c2c5-install01.log','phase1c2c5-install02.log','phase1c2c5-formal-v1.log','phase1c2c5-pure-dev01.log'))
    inventory=[];fake=re.compile(rb'ACTIO_FAKE_[0-9a-f]{32}');limit=max(len(secret),128)
    for path in sorted(files):
        assert not path.is_symlink() and not path.is_junction();h=hashlib.sha256();tail=b''
        with path.open('rb') as f:
            while chunk:=f.read(1024*1024):
                h.update(chunk);data=tail+chunk;assert secret not in data and not fake.search(data),'generated secret scan failed'
                tail=data[-limit:]
        inventory.append({'file':str(path),'bytes':path.stat().st_size,'sha256':h.hexdigest()})
    inventory_root=ROOT/'.local/phase1c2c5-publication';inventory_root.mkdir(exist_ok=True)
    out=inventory_root/('inventory-'+hashlib.sha256(canonical(inventory).encode()).hexdigest()[:12]+'.json')
    with out.open('x',encoding='utf8',newline='\n') as f:f.write(canonical(inventory))
    historical=[str(p.relative_to(ROOT)) for p in (ROOT/'docs/validation').iterdir() if p.name!='phase1c2c5']
    subprocess.run(['git','diff','--exit-code',BASE,'--',*historical],cwd=ROOT,check=True,capture_output=True)
    claims=json.loads((ROOT/'docs/validation/phase1c2c4/execution-claims.json').read_bytes())
    assert all(file_hash(Path(claims['namespace'])/n)==v['sha256'] for n,v in claims['files'].items())
    result={'status':'PASS','sources':sources(),'tool_sha256':file_hash(Path(__file__)),'argv':sys.orig_argv,
        'publication_files':publication,'publication_file_count':len(publication),'generated_files_scanned':len(inventory),
        'generated_inventory':str(out),'generated_inventory_sha256':file_hash(out),'credential_found':False,
        'historical_error_message_raw_request_raw_reasoning_found_in_publication':False,'historical_claims_unchanged':19,
        'old_validation_directories_unchanged':True,'scope':'exact local key exclusion only; no key properties exported; no directory skips',
        'network_requests':0,'provider_requests':0}
    with (DOC/'publication-scan.json').open('x',encoding='utf8',newline='\n') as f:f.write(canonical(result))
    print(canonical({'status':'PASS','publication_files':len(publication),'generated_files':len(inventory)}))


if __name__=='__main__':main()
