"""Verify the actual staged Git bytes against the immutable C2B1 manifest."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile
from actio.common import canonical,file_hash

ROOT=Path(__file__).resolve().parents[1]
DOC='docs/validation/phase1c2b1/'

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)

def main():
    m=json.loads((ROOT/DOC/'evidence_manifest.json').read_bytes())
    expected={DOC+n:h for n,h in m['artifact_hashes'].items()}
    for k in ('product_hashes','test_hashes','tooling_hashes','entry_hashes','lock_hashes'):expected.update(m[k])
    for name,h in expected.items():
        assert file_hash(ROOT/name)==h,('working file changed',name)
        gh=m['entry_git_hashes'].get(name,h)
        assert hashlib.sha256(git('show',':'+name)).hexdigest()==gh,('staged Git bytes differ',name)
    assert git('show',':'+DOC+'evidence_manifest.json')==(ROOT/DOC/'evidence_manifest.json').read_bytes()
    for k in ('preparation_logs','source_snapshots'):
        for name,h in m[k].items():assert file_hash(ROOT/name)==h,name
    for a in m['raw_archives']:
        p=ROOT/a['file'];assert file_hash(p)==a['sha256']
        with zipfile.ZipFile(p) as z:
            assert {n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}==a['files']
    credential='.local/credentials/token_key.txt'
    assert subprocess.run(['git','check-ignore','--quiet',credential],cwd=ROOT).returncode==0
    assert not git('ls-files','--',credential).strip()
    # Explicitly authorized publication scan. Never report secret metadata or matches.
    secret=(ROOT/credential).read_text(encoding='utf-8-sig').strip().encode()
    names=git('diff','--cached','--name-only','-z').decode('utf8').split('\0')
    names=[n for n in names if n]
    assert names,'no staged task changes'
    allowed=set(expected)|{DOC+'evidence_manifest.json'}
    assert set(names)<=allowed,'unmanifested staged file'
    for n in names:
        staged=git('show',':'+n)
        assert staged==(ROOT/n).read_bytes(),('changed task file must preserve exact bytes',n)
        assert secret not in staged,'credential publication prohibited'
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
    print(canonical({'status':'PASS','manifested_git_files':len(expected)+1,'staged_task_files':len(names),
                     'raw_archives_verified':len(m['raw_archives']),'credential_found':False,'credential_ignored_untracked':True}))

if __name__=='__main__':main()
