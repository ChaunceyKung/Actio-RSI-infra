"""Bounded Windows supervisor. Every SDK child inherits only clean_env()."""
import argparse
import json
import subprocess
import shutil
import sys
import tempfile
import time
import uuid
import zipfile
from pathlib import Path
from common import ROOT, LOCAL, EVIDENCE, clean_env, write_json, jsonl, file_hash
from winjob import Job

def run(case,script='runtime_cases.py',deadline=120):
    saved=LOCAL/'runs'/f'{case}-{uuid.uuid4().hex[:8]}'
    # Bundled native koffi extraction exceeds MAX_PATH under long repo paths.
    # Keep all runtime state in a task-owned short temp root, then archive raw logs.
    root=Path(tempfile.mkdtemp(prefix='actio-p1a-',dir=ROOT.anchor))
    started=time.monotonic()
    with (root/'process.log').open('w',encoding='utf-8') as log:
        p=subprocess.Popen([sys.executable,str(ROOT/script),case,str(root)],env=clean_env(root/'environment'),
                           cwd=root,stdin=subprocess.PIPE,stdout=log,stderr=log,text=True,encoding='utf-8')
        job=Job(p)
        timed_out=False
        try:
            p.stdin.write('go\n');p.stdin.flush();p.stdin.close()
            try:p.wait(timeout=deadline)
            except subprocess.TimeoutExpired:timed_out=True
        finally:
            cleanup=job.close()
            p.wait(timeout=5)
    outcome=json.loads((root/'result.json').read_text(encoding='utf-8')) if (root/'result.json').exists() else {'tests':[]}
    outcome.update({'case':case,'exit_code':p.returncode,'timed_out':timed_out,'elapsed_seconds':time.monotonic()-started,
        'cleanup':cleanup,'raw_directory':saved.name,'status':'PASS' if p.returncode==0 and not timed_out else 'FAIL'})
    if (root/'failure.json').exists(): outcome['failure']=json.loads((root/'failure.json').read_text())
    # Commit actual compact trace excerpts and full provider inputs for isolation review.
    excerpts=[]
    for path in root.rglob('plugin.jsonl'):
        entries=jsonl(path)
        excerpts.append({'path':str(path.relative_to(root)),'sha256':file_hash(path),
            'records':[e for e in entries if e['kind']!='native-observed'],
            'native_events':[e for e in entries if e['kind']=='native-observed'][:3],
            'native_event_count':sum(e['kind']=='native-observed' for e in entries)})
    outcome['transcripts']=excerpts
    outcome['mcp_records']=[{'path':str(p.relative_to(root)),'records':jsonl(p)} for p in root.rglob('mcp.jsonl')]
    outcome['runtime_close']=[{'path':str(p.relative_to(root)),**json.loads(p.read_text(encoding='utf-8'))} for p in root.rglob('runtime-close.json')]
    outcome['probe_hashes']={str(p.relative_to(ROOT)).replace('\\','/'):file_hash(p) for p in
        [ROOT/script,ROOT/'runtime_adapter.py',ROOT/'fixtures/provider_policy.mjs',ROOT/'fixtures/mcp_server.py',ROOT/'run_runtime.py',ROOT/'winjob.py',ROOT/'common.py',ROOT/'event_probe.py']}
    # Cache extraction is reproducible and large; archive only synthetic test artifacts.
    saved.mkdir(parents=True)
    with zipfile.ZipFile(saved/'raw.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for path in root.rglob('*'):
            if path.is_file() and path.relative_to(root).parts[0]!='environment':archive.write(path,str(path.relative_to(root)))
    outcome['raw_zip_sha256']=file_hash(saved/'raw.zip')
    write_json(saved/'location.json',{'root':str(root),'archive_sha256':outcome['raw_zip_sha256']})
    text=json.dumps(outcome,ensure_ascii=False,indent=2).replace(str(root).replace('\\','\\\\'),'<CASE_ROOT>')
    (EVIDENCE).mkdir(parents=True,exist_ok=True)
    (EVIDENCE/f'{case}.json').write_text(text,encoding='utf-8')
    print(case,outcome['status'],'exit',p.returncode,'seconds',round(outcome['elapsed_seconds'],2),flush=True)
    if p.returncode:
        print((root/'process.log').read_text(encoding='utf-8')[-8000:],flush=True)
    return outcome

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('cases',nargs='*',default=['lifecycle','tools','policy-isolation','constraints','iserror','transport','timeout','init-timeout','run-timeout','eof','exit','tool-interruption','event-integration','receipt-loss','concordia'])
    args=parser.parse_args()
    results=[run(case,'concordia_case.py' if case=='concordia' else 'runtime_cases.py') for case in args.cases]
    sys.exit(0 if all(r['status']=='PASS' for r in results) else 1)
