"""Read only public fixed-SHA sources; no datasets, providers or reference checkout edits."""
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
REF=ROOT/'../../codebase/18_sotopia/repo'
SHA='a0aaafb440e570e5e61b7c44a44e5e417c545383'

if __name__=='__main__':
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REF,text=True).strip()==SHA
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=REF,text=True).strip()
    rows=[]
    for name in ('sotopia/database/persistent_profile.py','sotopia/cli/install/published_datasets.json','tests/envs/test_background.json','LICENSE'):
        url=f'https://raw.githubusercontent.com/sotopia-lab/sotopia/{SHA}/{name}'
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(url,timeout=30) as r:raw=r.read(1048576)
        local=(REF/name).read_bytes();equal=raw.replace(b'\r\n',b'\n')==local.replace(b'\r\n',b'\n');assert equal
        rows.append({'path':name,'url':url,'commit':SHA,'local_sha256':hashlib.sha256(local).hexdigest(),
                     'remote_sha256':hashlib.sha256(raw).hexdigest(),'lf_equal':equal})
        if name.endswith('published_datasets.json'):print(raw.decode())
    report={'schema':'phase1c1-reuse.v1','status':'PASS','files':rows,'code_license':'MIT / Copyright (c) 2023 Hao Zhu',
            'adopted':'scenario, agent_goals, relationship/background_story semantics; existing extracted parser/schema unchanged',
            'not_adopted':'Redis persistence and platform; incomplete test_background scenario; datasets not licensed as MIT',
            'task_data':'two Actio authored synthetic scheduling cards, CC0-1.0; no SOTOPIA dataset rows copied',
            'data_note':'registry lists CC-BY-SA-4.0 and AI2 Impact License; no concrete dataset adopted/downloaded, so no redistribution claim',
            'model_requests':0}
    p=ROOT/'docs/validation/phase1c1/evidence/reuse.json';p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8',newline='\n') as f:json.dump(report,f,ensure_ascii=False,indent=2)
