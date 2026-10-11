"""Build a standard wheel from a fresh source copy, excluding stale build/lib output."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
def main():
    if any(b'\r\n' in path.read_bytes() for path in (ROOT/'src/actio').rglob('*.py')):
        raise SystemExit('source Python must use repository LF bytes before wheel/freeze construction')
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    source=a.output/'source';source.mkdir();shutil.copyfile(ROOT/'pyproject.toml',source/'pyproject.toml')
    shutil.copytree(ROOT/'src/actio',source/'src/actio',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    subprocess.run([sys.executable,'-m','pip','--isolated','wheel','--no-index','--no-deps','--no-build-isolation','--wheel-dir',str(a.output.resolve()),str(source.resolve())],check=True)
    wheel=next(a.output.glob('*.whl'));print(json.dumps({'wheel':str(wheel),'sha256':hashlib.sha256(wheel.read_bytes()).hexdigest()}))
if __name__=='__main__':main()
