"""Refresh the public inventory after documentation/scans, without raw reads."""
import json
from pathlib import Path
from actio.common import canonical,file_hash

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/validation/phase1c2c4'


def refresh():
    path=DOC/'evidence_manifest.json'
    manifest=json.loads(path.read_bytes())
    manifest['artifacts']={p.relative_to(DOC).as_posix():file_hash(p) for p in sorted(DOC.rglob('*'))
                           if p.is_file() and p!=path}
    manifest['tooling']={p.relative_to(ROOT).as_posix():file_hash(p)
                        for p in sorted((ROOT/'scripts').glob('phase1c2c4_*.py'))}
    manifest['entry_documents']={name:file_hash(ROOT/name) for name in ('README.md','MILESTONES.md')}
    path.write_text(canonical(manifest),encoding='utf8',newline='\n')
    print(canonical({'status':'PASS','artifacts':len(manifest['artifacts']),
                     'manifest_sha256':file_hash(path),'controlled_raw_read':False}))


if __name__=='__main__':refresh()
