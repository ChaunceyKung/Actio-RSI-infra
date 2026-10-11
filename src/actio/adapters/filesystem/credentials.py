from pathlib import Path
from actio.contracts.json import require

def scan(root,secret):
    count=0;token=secret.encode()
    for p in Path(root).rglob('*'):
        if not p.is_file():continue
        with p.open('rb') as f:
            tail=b''
            while chunk:=f.read(1024*1024):
                data=tail+chunk;require(token not in data,'credential found in generated files; publication prohibited')
                tail=data[-len(token):]
        count+=1
    return {'files_scanned':count,'credential_found':False}

def resolve_credential(project):
    # Only the explicit execute branch calls this. The value and metadata never leave memory.
    import subprocess
    target=Path(project).resolve()/'.local/credentials/token_key.txt'
    require(subprocess.run(['git','check-ignore','--quiet',str(target)],cwd=project,capture_output=True).returncode==0,'credential path must be ignored')
    require(not subprocess.check_output(['git','ls-files','--',str(target)],cwd=project).strip(),'credential must not be tracked')
    if not target.exists():
        source=Path('D:/调研/CausalEngine/api_key/token_key.txt');target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(source.read_bytes())
    value=target.read_text(encoding='utf-8-sig').strip()
    require(bool(value) and '\n' not in value and '\r' not in value,'credential file format invalid')
    return value
