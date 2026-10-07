"""Verify delivered hashes, local links, JSON, code syntax and bounded cleanup."""
import ast
import json
import re
import subprocess
from pathlib import Path
from common import ROOT,EVIDENCE,file_hash,write_json

def main():
    repo=ROOT.parents[1]
    manifest=json.loads((EVIDENCE.parent/'evidence_manifest.json').read_text(encoding='utf-8'))
    failures=[];links=0;tables=0;mermaid=0
    files=[*list((repo/'docs/planning').glob('*.md')),*list(EVIDENCE.parent.glob('*.md')),ROOT/'README.md']
    for path in files:
        text=path.read_text(encoding='utf-8')
        for url in re.findall(r'\]\(([^)]+)\)',text):
            target=url.split('#')[0].strip('<>')
            if not target or re.match(r'^[a-zA-Z]+:',target) or target.startswith('/'):continue
            links+=1
            if not (path.parent/target).exists():failures.append(f'broken link {path.name}: {url}')
        assert text.count('```')%2==0,path
        width=None
        for line in text.splitlines():
            if line.startswith('|'):
                w=len(re.split(r'(?<!\\)\|',line))
                if width is not None and w!=width:failures.append(f'table width {path.name}: {line[:50]}')
                if width is None:tables+=1
                width=w
            else:width=None
        for block in re.findall(r'```mermaid\n(.*?)```',text,re.S):
            mermaid+=1
            if block.count('[')!=block.count(']'):failures.append(f'mermaid bracket {path.name}')
            opening=sum(bool(re.match(r'\s*(subgraph|alt|loop|opt|par)\b',l)) for l in block.splitlines())
            closing=sum(l.strip()=='end' for l in block.splitlines())
            if opening!=closing:failures.append(f'mermaid block {path.name}')
    for p in EVIDENCE.glob('*.json'):json.loads(p.read_text(encoding='utf-8'))
    for p in ROOT.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
    ast.parse((ROOT/'fixtures/mcp_server.py').read_text(encoding='utf-8'))
    ids=[]
    for row in manifest['tests']:
        ids.append(row['test_id'])
        ref=row.get('sanitized_log')
        if ref:assert file_hash(EVIDENCE.parent/ref['ref'])==ref['sha256'],ref
    assert len(set(ids))==len(ids)
    case_files=[p for p in EVIDENCE.glob('*.json') if 'probe_hashes' in json.loads(p.read_text(encoding='utf-8'))]
    for p in case_files:
        r=json.loads(p.read_text(encoding='utf-8'))
        assert r['status']=='PASS' and r['cleanup']['after']['active']==0,p
        for name,h in r['probe_hashes'].items():assert file_hash(ROOT/name)==h,(p,name)
        raw=ROOT/'.local/runs'/r['raw_directory']/'raw.zip'
        assert file_hash(raw)==r['raw_zip_sha256'],raw
    check=subprocess.run([str(ROOT/'.local/venv/Scripts/python.exe'),'-m','pip','check'],capture_output=True,text=True)
    assert check.returncode==0,check.stdout
    result={'status':'PASS' if not failures else 'FAIL','json_files':len(list(EVIDENCE.glob('*.json'))),
        'local_links_checked':links,'tables_checked':tables,'mermaid_blocks_statically_checked':mermaid,
        'mermaid_render':'NOT_RUN: no existing mmdc/renderer discovered; no large renderer stack installed',
        'runtime_cases_verified':len(case_files),'manifest_tests':len(ids),'pip_check':check.stdout.strip(),
        'reference_repositories':'DSH/Concordia status clean at pinned HEAD after probes (separate shell verification)',
        'failures':failures}
    write_json(EVIDENCE/'delivery-checks.json',result)
    print(json.dumps(result,ensure_ascii=False))
    assert not failures,failures

if __name__=='__main__':main()
