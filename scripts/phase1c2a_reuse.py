"""Narrow readonly fixed-commit source/remote comparison; no model endpoint."""
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
REF=(ROOT/'../../codebase/01_deepseek-harness/repo').resolve()
PIN='5badb15009ae1756c3afe0ae0cef1faafc290ccc'
FILES=['LICENSE','packages/bundle/sdk-minimal/cordis.patch.yml',
       'packages/llm/llm-deepseek/src/adapter.ts','packages/llm/llm-deepseek/src/messages-api.ts',
       'packages/llm/llm-deepseek-api-key/src/index.ts','packages/llm/llm/src/index.ts',
       'packages/llm/llm/src/retry-policy.ts','packages/llm/llm-retry/src/index.ts',
       'packages/llm/llm-deepseek/tests/mock-server.ts','packages/llm/llm-deepseek/tests/stream.spec.ts',
       'packages/llm/llm-deepseek/package.json']


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REF,text=True).strip()==PIN
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=REF,text=True).strip()
    rows=[];opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for name in FILES:
        url=f'https://raw.githubusercontent.com/deepseek-ai/deepseek-harness/{PIN}/{name}'
        with opener.open(url,timeout=30) as r:raw=r.read(512001)
        assert len(raw)<=512000
        local=(REF/name).read_bytes();same=local.replace(b'\r\n',b'\n')==raw.replace(b'\r\n',b'\n');assert same,name
        rows.append({'path':name,'url':url,'local_sha256':hashlib.sha256(local).hexdigest(),'remote_sha256':hashlib.sha256(raw).hexdigest(),'normalized_equal':same})
    folder=ROOT/'docs/validation/phase1c2a/evidence';folder.mkdir(parents=True,exist_ok=True)
    result={'status':'PASS','commit':PIN,'license':'MIT Copyright (c) 2026 DeepSeek',
            'files':rows,'adopt':'official binary adapter unmodified; Messages mock event structure and bounded fault behaviors adapted with attribution',
            'not_adopted':['Files API','upstream live e2e','full test platform','implicit retry'],
            'binary_source_mapping':'unproven; source package version 0.2.1-alpha.1 versus installed runtime 0.1.5rc1; runtime probe required',
            'model_requests':0}
    with (folder/'reuse.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({'status':'PASS','files':len(rows)}))


if __name__=='__main__':main()
