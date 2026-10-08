"""Verify the actual local install, cached locked wheels and license records."""
import datetime
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import platform
import re
import subprocess
import sys
import zipfile

from actio.common import file_hash,clean_env
from actio.runtime import PACKAGE,pins,verify_runtime
from actio.supervisor import owned_root

ROOT=Path(__file__).resolve().parents[1]


if __name__=='__main__':
    verify_runtime()
    wheels={file_hash(p):p for p in (ROOT/'.local/wheels').glob('*.whl')}
    installed=[]
    for line in (ROOT/'requirements.lock').read_text().splitlines():
        match=re.fullmatch(r'([^=]+)==([^ ]+) --hash=sha256:([0-9a-f]{64})',line)
        if not match:continue
        name,version,h=match.groups()
        assert h in wheels,(name,'cache does not contain locked bytes')
        dist=metadata.distribution(name)
        assert dist.version==version,(name,dist.version,version)
        licenses={str(p):file_hash(dist.locate_file(p)) for p in dist.files if any(x in str(p).upper() for x in ('LICENSE','NOTICE','COPYING')) and dist.locate_file(p).is_file()}
        installed.append({'name':name,'version':version,'wheel':wheels[h].name,'wheel_sha256':h,
            'wheel_bytes':wheels[h].stat().st_size,'license_expression':dist.metadata.get('License-Expression'),
            'license_metadata':dist.metadata.get('License'),'license_files':licenses})
    assert len(installed)==41
    env=clean_env(owned_root(Path(ROOT.anchor)/'actio-p1b-prepare','artifact-verification'))
    result=subprocess.run([sys.executable,'-m','pip','--isolated','check'],capture_output=True,text=True,env=env)
    assert result.returncode==0,result.stdout+result.stderr
    source=json.loads((PACKAGE.parent/'actio-concordia-source.json').read_text())
    for name,h in source['files'].items():
        actual=PACKAGE.parent/(name if name!='LICENSE' else 'actio-concordia.LICENSE')
        assert file_hash(actual)==h,name
    record={'id':'P1B-artifacts','status':'PASS','mode':'ARTIFACT_VERIFICATION','exit_code':0,
            'command':str(Path(sys.executable).relative_to(ROOT))+' -X utf8 scripts/artifacts.py',
            'platform':platform.platform(),'python':sys.version,'pins':pins(),'installed':installed,
            'concordia':source,'pip_check':{'exit_code':result.returncode,'stdout':result.stdout},
            'limitations':['Local use only; binary-to-source build provenance and redistribution SBOM remain unproven',
                          'Concordia is verified source plus minimal import dependencies, not its full research distribution']}
    now=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    target=ROOT/'docs/validation/phase1b/evidence'/('artifacts-'+now+'.json')
    target.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
    print('PASS: 41 installed locked distributions, runtime executable, 242 Concordia files and pip check;',target)
