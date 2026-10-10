"""One explicit live CLI launch; record exit/argv/source outside the clean checkout."""
import json
from pathlib import Path
import subprocess
import sys
import uuid
from actio.common import canonical,clean_env,digest
from actio.pilot_contract import implementation
from actio.pilot import create,now

ROOT=Path(__file__).resolve().parents[1]


def main():
    root=Path('D:/actio-c2c4-live-v1')
    if root.exists() or (ROOT/'.local/phase1c2c4-claims/live-once.json').exists():
        raise SystemExit('existing live root/claim: no second launch')
    scratch=ROOT/'.local/phase1c2c4-launch'/uuid.uuid4().hex;scratch.mkdir(parents=True)
    argv=[sys.executable,'-X','utf8','-I','-B','-m','actio.robustness','execute','--project',str(ROOT),
          '--root',str(root),'--source-database','D:/actio-c2c2-live-v1/candidates.sqlite','--authorized-phase1c2c4']
    record={'argv':argv,'implementation':implementation(),'started_utc':now(),'scope':'single launch; no wrapper retry'}
    create(scratch/'intent.json',record)
    # Per-request and Worker limits belong to the frozen controller; the
    # launcher must not impose an unrelated whole-campaign cutoff.
    result=subprocess.run(argv,cwd=scratch,env=clean_env(scratch),capture_output=True,text=True,encoding='utf8')
    (scratch/'stdout.txt').write_text(result.stdout,encoding='utf8');(scratch/'stderr.txt').write_text(result.stderr,encoding='utf8')
    record.update(exit_code=result.returncode,finished_utc=now(),stdout_hash=digest(result.stdout),stderr_hash=digest(result.stderr))
    create(scratch/'receipt.json',record)
    print(canonical({'exit_code':result.returncode,'receipt':str(scratch/'receipt.json'),'root':str(root)}))
    return result.returncode


if __name__=='__main__':raise SystemExit(main())
