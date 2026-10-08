"""Record current clean install against unchanged dependency/source pins."""
import datetime
import argparse
import importlib.metadata as metadata
import json
from pathlib import Path
import platform
import re
import sys

from actio.common import file_hash
from actio.runtime import PACKAGE,pins,verify_runtime

ROOT=Path(__file__).resolve().parents[1]

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--bootstrap-log',type=Path)
    args=parser.parse_args()
    verify_runtime()
    wheels={file_hash(p):p for p in (ROOT/'.local/wheels').glob('*.whl')}
    distributions=[]
    for name,version,h in re.findall(r'^([^#\s=]+)==([^ ]+) --hash=sha256:([0-9a-f]{64})$',(ROOT/'requirements.lock').read_text(),re.M):
        assert h in wheels and metadata.version(name)==version,name
        distributions.append({'name':name,'version':version,'wheel_sha256':h,'wheel':wheels[h].name})
    assert len(distributions)==41
    concordia=json.loads((PACKAGE.parent/'actio-concordia-source.json').read_text())
    for name,h in concordia['files'].items():
        assert file_hash(PACKAGE.parent/(name if name!='LICENSE' else 'actio-concordia.LICENSE'))==h,name
    product={p.relative_to(ROOT).as_posix():file_hash(p) for p in (ROOT/'src').rglob('*') if p.suffix in ('.py','.mjs','.sql','.json')}
    for p,h in product.items():assert file_hash(PACKAGE/Path(p).relative_to('src/actio'))==h,p
    result={'status':'PASS','exit_code':0,'command':str(Path(sys.executable).relative_to(ROOT))+' -X utf8 scripts/phase1b1_artifacts.py',
            'platform':platform.platform(),'python':sys.version,'distributions':distributions,'pins':pins(),
            'concordia':concordia,'product_hashes':product,'bootstrap_log_sha256':file_hash(args.bootstrap_log) if args.bootstrap_log else None,
            'limits':['Local cached locked wheels; no full network acquisition in this round','Binary-to-source provenance remains unproven']}
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    target=ROOT/'docs/validation/phase1b1/evidence'/('artifacts-'+stamp+'.json')
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print('PASS: 41 wheels, exact installed product, Concordia source and DSH executable',target)
