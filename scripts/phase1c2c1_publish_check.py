"""Exact local secret scan only. Never print credential material or derivatives."""
import json
from pathlib import Path
import subprocess
from actio.common import canonical,file_hash
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2c1'


def main():
    names=subprocess.check_output(['git','diff','--name-only','03bfa2d5a0eef107de4b6ad2e81dec01c4e1490f'],cwd=ROOT,text=True,encoding='utf8').splitlines()
    names+=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True,encoding='utf8').splitlines()
    paths=[ROOT/n for n in sorted(set(names)) if (ROOT/n).is_file()]
    secret=(ROOT/'.local/credentials/token_key.txt').read_text(encoding='utf-8-sig').strip().encode()
    assert secret and all(secret not in p.read_bytes() for p in paths),'publication credential scan blocked'
    history=json.loads((ROOT/'docs/validation/phase1c2c0/samples/pilot.json').read_bytes())
    a=history['body']['entries'][7]['evidence']['ledger']['attempts'][0]
    reasoning=''.join(c['text'] for c in json.loads(a['response']['chunks_json']) if c['type']=='reasoning-delta').encode()
    assert reasoning and all(reasoning not in p.read_bytes() for p in paths),'historical reasoning copied into new publication'
    subprocess.run(['git','check-ignore','--quiet','.local/credentials/token_key.txt'],cwd=ROOT,check=True)
    assert not subprocess.check_output(['git','ls-files','.local/credentials/token_key.txt'],cwd=ROOT)
    subprocess.run(['git','diff','--check'],cwd=ROOT,check=True)
    print(canonical({'status':'PASS','files_scanned':len(paths),'exact_secret_matches':0,'historical_reasoning_copies':0,'credential_ignored_untracked':True}))


if __name__=='__main__':main()
