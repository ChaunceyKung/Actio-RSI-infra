"""Inspect installed artifacts separately from reference source provenance."""
import argparse
import importlib.metadata as md
import json
import platform
import subprocess
import sys
from pathlib import Path
from deepseek_harness_runtime import bundled_runtime_path,bundled_package_dir
import deepseek_harness
from common import EVIDENCE, ROOT, file_hash, write_json

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dsh-source');a=p.parse_args()
    exe=bundled_runtime_path();pkg=bundled_package_dir()
    result={'status':'PASS','platform':platform.platform(),'python':sys.version,
        'distribution':{n:md.version(n) for n in ['deepseek-harness-sdk','deepseek-harness-runtime-bin','mcp','pydantic']},
        'executable':{'path_relative_to_probe':str(exe.relative_to(ROOT)).replace('\\','/'),'size':exe.stat().st_size,'sha256':file_hash(exe)},
        'runtime_metadata':json.loads((pkg/'deepseek-harness-runtime.json').read_text()),
        'binary_source_mapping':'UNPROVEN: no build attestation in installed artifact; do not infer from SDK file equality',
        'sdk_source_comparison':{},'license_files':[]}
    for name in ['api.py','client.py','models.py']:
        installed=Path(deepseek_harness.__file__).parent/name
        row={'installed_sha256':file_hash(installed)}
        if a.dsh_source:
            source=subprocess.check_output(['git','-C',a.dsh_source,'show','5badb15009ae1756c3afe0ae0cef1faafc290ccc:python/sdk/src/deepseek_harness/'+name]).decode()
            row['text_equals_source']=source.replace('\r\n','\n')==installed.read_text(encoding='utf-8').replace('\r\n','\n')
        result['sdk_source_comparison'][name]=row
    for distribution in ['deepseek-harness-sdk','deepseek-harness-runtime-bin','mcp']:
        d=md.distribution(distribution)
        for f in d.files or []:
            if 'license' in str(f).lower() or 'notice' in str(f).lower():
                path=Path(d.locate_file(f))
                result['license_files'].append({'distribution':distribution,'path':str(f),'sha256':file_hash(path),'size':path.stat().st_size})
    write_json(EVIDENCE/'installed-artifacts.json',result)
    print(json.dumps({'exe_sha256':result['executable']['sha256'],'sdk_comparison':result['sdk_source_comparison']}))
