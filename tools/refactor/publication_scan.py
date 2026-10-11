"""Exact secret and raw reasoning exclusion; never logs any credential property."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid
from actio.common import canonical,digest,file_hash

ROOT=Path(__file__).resolve().parents[2];BASE='6ba6573'


def main():
    p=argparse.ArgumentParser();p.add_argument('--live-root',type=Path)
    p.add_argument('--verify-only',action='store_true',help='verify final files without adding a new receipt')
    a=p.parse_args()
    def git(*args):return subprocess.check_output(['git','-c','core.quotepath=false',*args],cwd=ROOT,text=True,encoding='utf8')
    names=set(git('diff','--name-only',BASE).splitlines()+git('ls-files','--others','--exclude-standard').splitlines())
    paths=[ROOT/n for n in sorted(names) if (ROOT/n).is_file()]
    data=[p.read_bytes() for p in paths]
    assert not any(re.search(rb'\bsk-[A-Za-z0-9_-]{16,}|Bearer [A-Za-z0-9_-]{24,}',v) for v in data),'credential pattern detected'
    # User explicitly requests an exact publication scan. This read is only for
    # in-memory comparison, separate from execute's later provider injection.
    secret=(ROOT/'.local/credentials/token_key.txt').read_text(encoding='utf-8-sig').strip().encode()
    assert secret and not any(secret in v for v in data),'exact credential publication blocked'
    texts=[]
    roots=[Path('D:/actio-c2c2-live-v1')]+([a.live_root] if a.live_root else [])
    for root in roots:
        campaign=json.loads((root/'matrix/pilot.json').read_bytes())
        for entry in campaign['body']['entries']:
            if not entry['evidence']:continue
            for attempt in entry['evidence']['ledger']['attempts']:
                if attempt['response']:
                    texts.append(''.join(x['text'] for x in json.loads(attempt['response']['chunks_json']) if x['type']=='reasoning-delta'))
    assert not any(text.encode() in v for text in texts if text for v in data),'raw reasoning publication blocked'
    assert not any(p.suffix in ('.sqlite','.exe','.zip','.whl') or p.name in ('delivery.json','pilot.json') for p in paths),'controlled raw file publication blocked'
    subprocess.run(['git','check-ignore','--quiet','.local/credentials/token_key.txt'],cwd=ROOT,check=True)
    assert not git('ls-files','.local/credentials/token_key.txt')
    subprocess.run(['git','diff','--check'],cwd=ROOT,check=True)
    result={'status':'PASS','argv':sys.orig_argv,'files_scanned':len(paths),'exact_secret_scan':'PASS',
        'raw_reasoning_copies':0,'credential_ignored_untracked':True,'credential_read_scope':'in-memory publication scan only',
        'new_provider_requests':0,'file_hash_kind':'SHA256 file bytes',
        'file_hashes':{p.relative_to(ROOT).as_posix():file_hash(p) for p in paths}}
    if a.verify_only:
        print(canonical({'status':'PASS','files_scanned':len(paths),'receipt_written':False}));return
    dest=ROOT/'docs/validation/refactor_modularity'/('publication-scan-'+uuid.uuid4().hex[:12]+'.json')
    with dest.open('x',encoding='utf8') as f:f.write(canonical(result))
    print(canonical({'status':'PASS','files_scanned':len(paths),'receipt':str(dest)}))


if __name__=='__main__':main()
