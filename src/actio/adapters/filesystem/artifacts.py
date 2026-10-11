from actio.contracts.json import parse

def read_json(path):
    return parse(Path(path).read_bytes())
import os
from pathlib import Path
import uuid
from actio.contracts.json import canonical
from actio.contracts.json import require
from actio.contracts.json import parse

def publish(root,value):
    """Content-addressed atomic hardlink publication never replaces an existing inode."""
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    key=value['sha256'];target=root/(key+'.json')
    if target.exists():
        require(read_json(target)==value,'immutable artifact conflict');return target
    stage=root/('.'+key+'.'+uuid.uuid4().hex+'.staging')
    with stage.open('xb') as f:f.write(canonical(value).encode());f.flush();os.fsync(f.fileno())
    try:os.link(stage,target)
    except FileExistsError:require(read_json(target)==value,'immutable artifact race conflict')
    finally:stage.unlink()
    return target
