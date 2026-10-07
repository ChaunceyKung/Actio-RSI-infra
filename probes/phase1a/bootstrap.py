"""Reproduce Phase 1A locally without global installs. Python 3.12 Windows x64."""
import argparse
import io
import json
import platform
import subprocess
import sys
import urllib.request
import venv
import zipfile
from common import ROOT, LOCAL, EVIDENCE, file_hash, write_json

SHA='b71d202750e23444ce1bf28d9f114bcd88aa41db'

def prepare_concordia(source=None):
    target=LOCAL/'concordia'
    marker=target/'.phase1a-source.json'
    if marker.exists():
        assert json.loads(marker.read_text())['sha']==SHA
        return
    if source:
        archive=subprocess.check_output(['git','-C',str(source),'archive','--format=zip',SHA])
        origin='https://github.com/google-deepmind/concordia'
        prefix=''
    else:
        origin=f'https://codeload.github.com/google-deepmind/concordia/zip/{SHA}'
        archive=urllib.request.urlopen(origin,timeout=60).read()
        prefix=f'concordia-{SHA}/'
    target.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        for entry in z.infolist():
            name=entry.filename.removeprefix(prefix)
            if not name or entry.is_dir():continue
            dest=(target/name).resolve()
            if not dest.is_relative_to(target.resolve()):raise ValueError('unsafe archive path')
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(z.read(entry))
    record={'sha':SHA,'origin':origin,'mode':'unaltered source import; no full upstream dependency installation',
        'license':file_hash(target/'LICENSE'),
        'files':{str(p.relative_to(target)).replace('\\','/'):file_hash(p) for p in target.rglob('*.py')}}
    write_json(marker,record)
    write_json(EVIDENCE/'concordia-source.json',{k:v for k,v in record.items() if k!='files'})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--concordia-source');p.add_argument('--source-only',action='store_true')
    a=p.parse_args()
    if platform.system()!='Windows' or sys.version_info[:2]!=(3,12):raise SystemExit('Validated lock is Windows x64 Python 3.12 only')
    if not a.source_only:
        target=LOCAL/'venv'
        if not target.exists():venv.create(target,with_pip=True)
        subprocess.run([str(target/'Scripts/python.exe'),'-m','pip','install','--require-hashes','--only-binary=:all:',
            '--find-links',str(LOCAL/'wheels'),'-r',str(ROOT/'requirements.lock'),'--disable-pip-version-check','--timeout','45','--retries','1'],check=True)
    prepare_concordia(a.concordia_source)
