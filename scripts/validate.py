"""Append-only evidence runs, including failures. Run after installing current source."""
import datetime
import hashlib
import io
import json
from pathlib import Path
import platform
import sys
import unittest
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))


class Result(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.records=[]
    def addSuccess(self,test):
        super().addSuccess(test);self.records.append({'id':test.id(),'status':'PASS','evidence':getattr(test,'evidence',{})})
    def addFailure(self,test,err):
        super().addFailure(test,err);self.records.append({'id':test.id(),'status':'FAIL','error':self._exc_info_to_string(err,test),'evidence':getattr(test,'evidence',{})})
    def addError(self,test,err):
        super().addError(test,err);self.records.append({'id':test.id(),'status':'FAIL','error':self._exc_info_to_string(err,test),'evidence':getattr(test,'evidence',{})})
    def addSubTest(self,test,subtest,err):
        super().addSubTest(test,subtest,err)
        if err:
            self.records.append({'id':str(subtest),'status':'FAIL','error':self._exc_info_to_string(err,test),'evidence':getattr(test,'evidence',{})})


if __name__=='__main__':
    which=sys.argv[1] if len(sys.argv)>1 else 'contract'
    name='test_'+which
    hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('src','tests','scripts') for p in (ROOT/folder).rglob('*') if p.suffix in {'.py','.mjs','.sql','.json'}}
    import actio
    installed=Path(actio.__file__).parent
    for path,h in hashes.items():
        if path.startswith('src/actio/'):
            other=installed/Path(path).relative_to('src/actio')
            if not other.exists() or hashlib.sha256(other.read_bytes()).hexdigest()!=h:
                raise SystemExit('install current source before validating: '+path)
    suite=unittest.defaultTestLoader.loadTestsFromName(name)
    output=io.StringIO()
    result=unittest.TextTestRunner(stream=output,verbosity=2,resultclass=Result).run(suite)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    phase=sys.argv[2] if len(sys.argv)>2 else 'phase1b1'
    if phase not in ('phase1b1','phase1c0','phase1c1','phase1c2a','phase1c2a1','phase1c2b0'):raise SystemExit('unknown evidence phase')
    target=ROOT/'docs/validation'/phase/'evidence';target.mkdir(parents=True,exist_ok=True)
    log=output.getvalue()
    try:
        executable=Path(sys.executable).relative_to(ROOT).as_posix()
    except ValueError:
        executable=str(Path(sys.executable))
    data={'id':stamp,'suite':which,'command':f'{executable} -X utf8 scripts/validate.py {which} {phase}',
          'mode':{'contract':'SQLITE_CONTRACT','schema':'SQLITE_MIGRATION_AND_REAL_PROCESS_INTERRUPTION',
                  'reliability':'REAL_ENGINE_DSH_AND_CONTROLLED_BOUNDARIES','entry_concurrency':'TWO_CONTROL_PROCESS_ENTRY_RACES',
                  'evidence':'REAL_FIXTURE_EXPORT_AND_OFFLINE_VERIFICATION',
                  'input_binding':'OFFLINE_FROZEN_INPUT_COUNTEREXAMPLES', 'evaluation':'OFFLINE_EVALUATION',
                  'sotopia':'REAL_EXTRACTED_SOTOPIA_CONTROLLED_SEAMS',
                  'transport':'OFFICIAL_CHAT_ADAPTER_LOOPBACK_AND_READONLY_CAMPAIGN',
                  'budget':'REAL_SEND_GATE_CONCURRENCY_INTERRUPTION_AND_SQLITE_BOUNDARIES',
                  'transport_config':'PURE_VERSIONED_CHAT_CONFIGURATION',
                  'readiness_config':'PURE_CANDIDATE_PRICE_APPROVAL_NO_SIDE_EFFECTS',
                  'readiness':'REAL_OFFICIAL_PRICED_REHEARSAL_CREDENTIAL_TIMEOUT_AND_BUDGET',
                  'preflight':'PURE_ROLE_CONFIGURATION_NO_TRANSPORT'}.get(which,'REAL_RUNTIME_FIXTURE_PROVIDER'),
          'platform':platform.platform(),'python':sys.version,'tests':result.records,'tests_run':result.testsRun,
          'exit_code':0 if result.wasSuccessful() else 1,'source_hashes':hashes,'log':log,
          'log_sha256':hashlib.sha256(log.encode()).hexdigest()}
    (target/(stamp+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(log)
    print('Evidence:',target/(stamp+'.json'))
    raise SystemExit(data['exit_code'])
