"""Publication scan; real credential resolution is deferred until after live."""
import argparse
import json
from pathlib import Path
import re
import subprocess
from actio.common import canonical
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--live-root',type=Path);a=p.parse_args()
    names=subprocess.check_output(['git','-c','core.quotepath=false','diff','--name-only','5affb4785b537105c09cbcdaa4ef055061712ba6'],cwd=ROOT,text=True,encoding='utf8').splitlines()
    names+=subprocess.check_output(['git','-c','core.quotepath=false','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True,encoding='utf8').splitlines()
    paths=[ROOT/n for n in sorted(set(names)) if (ROOT/n).is_file()]
    raw=[p.read_bytes() for p in paths]
    assert not any(re.search(rb'\bsk-[A-Za-z0-9_-]{16,}|Bearer [A-Za-z0-9_-]{24,}',b) for b in raw),'secret pattern; publication blocked'
    historical=json.loads((ROOT/'docs/validation/phase1c2c0/samples/pilot.json').read_bytes())
    old=historical['body']['entries'][7]['evidence']['ledger']['attempts'][0]
    texts=[''.join(c['text'] for c in json.loads(old['response']['chunks_json']) if c['type']=='reasoning-delta')]
    if a.live_root:
        secret=(ROOT/'.local/credentials/token_key.txt').read_text(encoding='utf-8-sig').strip().encode()
        assert secret and not any(secret in b for b in raw),'exact credential scan blocked'
        campaign=json.loads((a.live_root/'matrix/pilot.json').read_bytes())
        for e in campaign['body']['entries']:
            if e['evidence']:
                for attempt in e['evidence']['ledger']['attempts']:
                    if attempt['response']:
                        texts.append(''.join(x['text'] for x in json.loads(attempt['response']['chunks_json']) if x['type']=='reasoning-delta'))
    assert not any(t.encode() in b for t in texts if t for b in raw),'reasoning copied into public artifact'
    subprocess.run(['git','check-ignore','--quiet','.local/credentials/token_key.txt'],cwd=ROOT,check=True)
    assert not subprocess.check_output(['git','ls-files','.local/credentials/token_key.txt'],cwd=ROOT)
    subprocess.run(['git','diff','--check'],cwd=ROOT,check=True)
    print(canonical({'status':'PASS','files_scanned':len(paths),'exact_secret_scan':'PASS' if a.live_root else 'deferred_until_after_execute',
        'historical_and_live_reasoning_copies':0,'credential_ignored_untracked':True,'key_read':bool(a.live_root)}))


if __name__=='__main__':main()
