"""C5 serial pure/CLI acceptance; guarded children have no runtime authority."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from actio.common import canonical,file_hash
from actio.transport_diagnostics import sources,portable
from actio.eval_contract import seal
from test_suite import GUARD


def main():
    p=argparse.ArgumentParser();p.add_argument('--runtime-root',type=Path);a=p.parse_args()
    scratch=ROOT/'.local/phase1c2c5-validation'/uuid.uuid4().hex;scratch.mkdir(parents=True)
    log=io.StringIO();tests=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('test_failure_observation'))
    commands=[];passed=tests.wasSuccessful()
    runner=scratch/'guard.py'
    runner.write_text('import sys\nsys.dont_write_bytecode=True\n'+GUARD+'\nfrom actio.transport_diagnostics import main\nraise SystemExit(main())\n',encoding='utf8')
    pkg=scratch/'package.json';pkg.write_text(canonical(portable()),encoding='utf8')
    moved=scratch/'relocated';moved.mkdir();shutil.copyfile(pkg,moved/'package.json')
    bad=scratch/'bad.json';bad.write_text('{"schema":"unknown","schema":"duplicate"}',encoding='utf8')
    jobs=[(['plan'],0),(['analyze',str(pkg)],0),(['verify',str(moved/'package.json')],0),(['verify',str(bad)],2),
          (['run-local','--live'],2),(['run-local','--credential-ref','real'],2),(['run-local','--endpoint','https://external.invalid/v1'],2)]
    historical=next((ROOT/'.local/phase1c2c5-history').glob('*/c4-entry.json'))
    envelope=scratch/'historical.json';envelope.write_text(canonical(seal({'schema':'transport-diagnostic-controlled-entry.v1','origin':'historical_c4','entry':json.loads(historical.read_bytes())})),encoding='utf8')
    jobs.append((['analyze',str(envelope)],0))
    if a.runtime_root:
        jobs.extend((['analyze',str(f)],0) for f in sorted(a.runtime_root.glob('*/entry.json')))
    for argv,expected in jobs:
        guarded=argv[0]!='run-local'
        cmd=[sys.executable,'-X','utf8','-B','-I',*([str(runner)] if guarded else ['-m','actio.transport_diagnostics']),*argv]
        r=subprocess.run(cmd,capture_output=True,encoding='utf8',timeout=90)
        out=scratch/('command-'+str(len(commands))+'.json');out.write_text(r.stdout,encoding='utf8')
        passed &= r.returncode==expected
        commands.append({'argv':cmd,'expected_exit':expected,'exit':r.returncode,'stdout_hash':hashlib.sha256(r.stdout.encode()).hexdigest(),
                         'stderr_hash':hashlib.sha256(r.stderr.encode()).hexdigest(),'output':str(out),'guard':guarded})
    # Writer runs outside read-only guard and must refuse an existing directory.
    target=scratch/'export'
    for expected in (0,2):
        cmd=[sys.executable,'-X','utf8','-B','-I','-m','actio.transport_diagnostics','export',str(target)]
        r=subprocess.run(cmd,capture_output=True,encoding='utf8',timeout=90);passed &= r.returncode==expected
        commands.append({'argv':cmd,'expected_exit':expected,'exit':r.returncode,'stdout_hash':hashlib.sha256(r.stdout.encode()).hexdigest(),'guard':False})
    result={'status':'PASS' if passed else 'FAIL','sources':sources(),'tools':{n:file_hash(ROOT/n) for n in ('scripts/phase1c2c5_validate.py','tests/test_failure_observation.py','tests/test_suite.py')},
        'argv':sys.orig_argv,'tests':tests.testsRun,'log':log.getvalue(),'commands':commands,'controlled_root':str(scratch),
        'new_external_requests':0,'new_loopback_sends':0,'guard_scope':['key','env','network','runtime import','process','write']}
    dest=ROOT/'docs/validation/phase1c2c5'/('acceptance-'+scratch.name[:12]+'.json');dest.write_text(canonical(result),encoding='utf8',newline='\n')
    print(canonical({'status':result['status'],'receipt':str(dest),'tests':tests.testsRun,'commands':len(commands)}));return 0 if passed else 1


if __name__=='__main__':raise SystemExit(main())
