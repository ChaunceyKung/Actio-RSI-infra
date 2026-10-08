"""Read-only delivery audit plus a small independently recorded result."""
import ctypes as C
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys

from actio.common import file_hash,clean_env
from actio.supervisor import Job,kernel,owned_root

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/validation/phase1b'


if __name__=='__main__':
    manifest=json.loads((DOC/'evidence_manifest.json').read_text(encoding='utf8'))
    paths=[ROOT/'README.md',*DOC.glob('*.md'),ROOT/'docs/planning/12_implementation_backlog.md',ROOT/'docs/planning/13_architecture_decisions.md']
    links=[]
    for path in paths:
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf8')):
            if re.match(r'\w+://',link) or link.startswith('#'):continue
            target=(path.parent/link.split('#')[0].strip('<>')).resolve()
            assert target.exists(),(str(path),link)
            links.append((path.relative_to(ROOT).as_posix(),link))
    for p in (ROOT/'src').rglob('*'):
        if p.suffix in {'.py','.mjs'}:
            assert not re.search(r'probes[/.]|\._proc\b|_launch_args\b|initHang|\bfault\s*=',p.read_text(encoding='utf8')),p
    checked_jobs=[]
    for suite in manifest['current_suites']:
        path=DOC/suite['file'];assert file_hash(path)==suite['sha256']
        data=json.loads(path.read_text(encoding='utf8'))
        for test in data['tests']:
            root=test.get('evidence',{}).get('root')
            if not root:continue
            for dbpath in Path(root).rglob('ledger.sqlite'):
                db=sqlite3.connect(dbpath.as_uri()+'?mode=ro',uri=True)
                try:
                    for name, in db.execute('SELECT job FROM worker'):
                        k=kernel();handle=k.OpenJobObjectW(4,False,name)
                        if not handle:
                            assert C.get_last_error()==2,(name,C.get_last_error())
                            active=0
                        else:
                            job=object.__new__(Job);job.k=k;job.handle=handle
                            try:active=job.snapshot()['active']
                            finally:k.CloseHandle(handle)
                        assert active==0,(name,active)
                        checked_jobs.append({'job':name,'active':active})
                finally:db.close()
    env=clean_env(owned_root(Path(ROOT.anchor)/'actio-p1b-prepare','delivery-console'))
    console=Path(sys.executable).with_name('actio.exe')
    result=subprocess.run([str(console),'capabilities'],capture_output=True,text=True,env=env)
    assert result.returncode==0,result.stderr
    capabilities=json.loads(result.stdout)
    assert capabilities['fresh_session'] and not capabilities['resume'] and not capabilities['evaluator']
    record={'id':'P1B-delivery','status':'PASS','exit_code':0,'mode':'DELIVERY_AUDIT',
            'command':str(Path(sys.executable).relative_to(ROOT))+' -X utf8 scripts/check_delivery.py',
            'local_links_checked':len(links),'current_jobs_checked':checked_jobs,'console_capabilities':capabilities,
            'product_code_hashes_match_manifest':all(file_hash(ROOT/p)==h for p,h in manifest['product_hashes'].items()),
            'documents':{p.relative_to(ROOT).as_posix():file_hash(p) for p in paths},
            'limitations':['No graphical Markdown/Mermaid renderer required or used; local links and structured evidence verified']}
    assert record['product_code_hashes_match_manifest']
    (DOC/'evidence/delivery.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
    print('PASS:',len(links),'local links;',len(checked_jobs),'named jobs inactive; console entry and product source hashes verified')
