"""Code-selected archived readers; guarded children never execute artifact code."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import uuid
import zipfile

ROOT=Path(__file__).resolve().parents[1]
PINS={'c2c2':'3bef7e15b0eb21beeb10888eb508056592b977b0',
      'c2c3':'0a66334d61a0de302bbf8f5e15ee1db1b9d2e8fb',
      'c2c4':'3750954ea7cc8dff64115039e27bb671fa618d01'}


def main():
    sys.path.insert(0,str(ROOT/'tests'))
    from test_suite import GUARD
    records=[];dest=ROOT/'.local/phase1c2c5-history'/uuid.uuid4().hex;dest.mkdir(parents=True)
    for name,pin in PINS.items():
        scratch=dest/name;scratch.mkdir()
        raw=subprocess.check_output(['git','archive','--format=zip',pin,'src'],cwd=ROOT)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for n in z.namelist():
                assert n.startswith('src/') and '..' not in Path(n).parts
                if n.endswith('/'):continue
                p=scratch/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
        code="import sys,pathlib\nsys.path.insert(0,str(pathlib.Path(__file__).parent/'src'))\n"+GUARD+"\nfrom actio.common import digest,file_hash\nroot=pathlib.Path(sys.argv[1])\n"
        if name=='c2c3':
            code+="from actio.task_diagnostics import verify\nr=verify(root/'docs/validation/phase1c2c3/package');assert r['valid'],r\nprint(json.dumps({'valid':True,'result':r}))\n"
        else:
            module='robustness' if name=='c2c4' else 'candidate_evaluation'
            code+=f"from actio.{module} import verify\nfrom actio.store import Store\ndelivery=pathlib.Path('D:/actio-{name}-live-v1/delivery.json')\ndatabase=delivery.with_name('candidates.sqlite')\n"
            code+='''
before={str(p):file_hash(p) for p in (delivery,database)}
d=json.loads(delivery.read_bytes());r=verify(d);assert r['valid'],r
s=Store(database,readonly=True)
try:
 assert s.version==4
 lineage=s.evaluation_lineage();assert lineage==d['body']['lineage']
finally:s.close()
assert all(file_hash(pathlib.Path(p))==h for p,h in before.items())
'''
            code+=f"assert r['report']==json.loads((root/'docs/validation/phase1{name}/samples/report.json').read_bytes())\n"
            code+="result={'valid':True,'file_hashes':before,'lineage_sha256':lineage['sha256'],'lineage':r['lineage'],'counts':r['report']['counts'],'report_hash':digest(r['report'])}\n"
            if name=='c2c4':
                code+="result['controlled_entry']=d['body']['campaign']['body']['entries'][16]\nresult['entry_hash']=digest(result['controlled_entry'])\n"
            code+="print(json.dumps(result))\n"
        runner=scratch/'reader.py';runner.write_text(code,encoding='utf8',newline='\n')
        argv=[sys.executable,'-X','utf8','-I','-S','-B',str(runner),str(ROOT)]
        run=subprocess.run(argv,capture_output=True,text=True,encoding='utf8',timeout=240)
        value=json.loads(run.stdout) if run.returncode==0 else None
        if value and 'controlled_entry' in value:
            entry=value.pop('controlled_entry');(dest/'c4-entry.json').write_text(json.dumps(entry,ensure_ascii=False),encoding='utf8')
        records.append({'name':name,'reader':pin,'argv':argv,'archive_sha256':hashlib.sha256(raw).hexdigest(),
            'runner_sha256':hashlib.sha256(runner.read_bytes()).hexdigest(),'exit_code':run.returncode,
            'stderr_hash':hashlib.sha256(run.stderr.encode()).hexdigest(),'result':value,
            'sources':{p.relative_to(scratch/'src').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((scratch/'src').rglob('*')) if p.is_file()}})
        if run.returncode:break
    claims=json.loads((ROOT/'docs/validation/phase1c2c4/execution-claims.json').read_bytes())
    preserved={n:hashlib.sha256((Path(claims['namespace'])/n).read_bytes()).hexdigest() for n in claims['files']}
    assert all(h==claims['files'][n]['sha256'] for n,h in preserved.items())
    result={'status':'PASS' if len(records)==3 and all(r['exit_code']==0 for r in records) else 'FAIL',
        'readers':records,'controlled_root':str(dest),'claims':preserved,'guard':['key','env','network','process','runtime import','write'],
        'outer_harness':'fixed Git archive extraction and guarded reader launch; not itself process-free',
        'tool_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'argv':sys.orig_argv,'new_provider_requests':0}
    doc=ROOT/'docs/validation/phase1c2c5';out=doc/('history-'+dest.name[:12]+'.json')
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8',newline='\n')
    print(json.dumps({'status':result['status'],'receipt':str(out),'controlled_root':str(dest),'claims':len(preserved),'readers':[{k:r[k] for k in ('name','exit_code')} for r in records]}))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
