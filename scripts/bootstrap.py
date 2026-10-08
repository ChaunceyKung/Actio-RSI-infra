"""Install locked dependencies and the product in a new isolated environment."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SHA='b71d202750e23444ce1bf28d9f114bcd88aa41db'
sys.path.insert(0,str(ROOT/'src'))
from actio.common import clean_env
from actio.supervisor import owned_root


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--venv',type=Path,default=ROOT/'.local/venv')
    p.add_argument('--wheel-cache',type=Path)
    p.add_argument('--offline-wheels','--offline',dest='offline',action='store_true',
                   help='Disable pip index only; Concordia still downloads unless --concordia-source is supplied')
    p.add_argument('--concordia-source',type=Path)
    a=p.parse_args()
    if platform.system()!='Windows' or platform.machine()!='AMD64' or sys.version_info[:2]!=(3,12):
        raise SystemExit('requires Windows x64 Python 3.12')
    target=a.venv.resolve()
    prepare_root=owned_root(Path(ROOT.anchor)/'actio-p1b-prepare','phase1b-bootstrap')
    env=clean_env(prepare_root)
    if not target.exists():
        subprocess.run([sys.executable,'-m','venv',str(target)],check=True,env=env)
    python=target/'Scripts/python.exe'
    install=[str(python),'-m','pip','--isolated','install','--no-cache-dir','--disable-pip-version-check','--no-compile','--require-hashes','--only-binary=:all:',
             '-r',str(ROOT/'requirements.lock'), '--find-links',str(ROOT/'.local/wheels')]
    if a.wheel_cache:
        install += ['--find-links',str(a.wheel_cache.resolve())]
    if a.offline:
        install += ['--no-index']
    subprocess.run(install,check=True,env=env)
    if a.concordia_source:
        git=shutil.which('git')
        if not git:
            raise ValueError('git executable required for --concordia-source')
        raw=subprocess.check_output([git,'-c','core.autocrlf=false','-c','core.eol=lf','-C',str(a.concordia_source),'archive','--format=zip',SHA],env=env)
        prefix=''
    else:
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f'https://codeload.github.com/google-deepmind/concordia/zip/{SHA}',timeout=60) as response:
            raw=response.read(32*1024*1024+1)
        if len(raw)>32*1024*1024:
            raise ValueError('source archive limit')
        prefix=f'concordia-{SHA}/'
    pin=json.loads((ROOT/'src/actio/pins/concordia.json').read_text(encoding='utf-8'))
    if not a.concordia_source and hashlib.sha256(raw).hexdigest()!=pin['archive_sha256']:
        raise ValueError('Concordia archive hash mismatch')
    site=target/'Lib/site-packages'
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        source={n.removeprefix(prefix):z.read(n) for n in z.namelist() if not n.endswith('/') and
                (n.removeprefix(prefix).startswith('concordia/') and n.endswith('.py') or n.removeprefix(prefix)=='LICENSE')}
        if set(source)!=set(pin['files']):
            raise ValueError('Concordia source set mismatch')
        for name,data in source.items():
            if hashlib.sha256(data).hexdigest()!=pin['files'][name]:
                raise ValueError('Concordia source hash mismatch: '+name)
        for name,data in source.items():
            out=site/(name if name!='LICENSE' else 'actio-concordia.LICENSE')
            if not out.resolve().is_relative_to(site.resolve()):
                raise ValueError('unsafe source path')
            out.parent.mkdir(parents=True,exist_ok=True)
            out.write_bytes(data)
    (site/'actio-concordia-source.json').write_text(json.dumps({'commit':SHA,'archive_sha256':hashlib.sha256(raw).hexdigest(),
        'files':pin['files'],'mode':'verified minimal source imports; not full Concordia distribution'}),encoding='utf-8')
    subprocess.run([str(python),'-m','pip','--isolated','install','--no-cache-dir','--disable-pip-version-check','--no-deps','--no-build-isolation',str(ROOT)],check=True,env=env)
    subprocess.run([str(python),'-m','pip','--isolated','check'],check=True,env=env)
    print(str(python))


if __name__=='__main__':
    main()
