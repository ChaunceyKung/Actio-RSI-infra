"""Maintained local regression runner. Receipts never publish raw test evidence."""
import argparse
import datetime
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[2]
SUITES = {
    'environment': ['environment'],
    'settings': ['settings'],
    'pure': ['modularity','preflight','transport_config','readiness_config','suite','pilot','task_diagnostics','failure_observation'],
    'state': ['contract','schema','candidate','evaluation_candidate','robustness','input_binding'],
    'runtime-local': ['runtime','failures','processes','reliability','entry_concurrency','evidence','evaluation','sotopia','task','transport','budget','readiness','gateway','gateway_lifecycle','pilot_runtime','suite_runtime','suite_evidence','candidate_runtime','evaluation_candidate_runtime','robustness_runtime'],
}

def hashes(root):
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file() and p.suffix in ('.py','.json','.sql','.mjs','.txt')}

class Result(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.evidence=[];self.executed=[]
    def startTest(self,test):
        self.executed.append(test.id());super().startTest(test)
    def stopTest(self,test):
        self.evidence.append({'id':test.id(),'evidence':getattr(test,'evidence',{})})
        super().stopTest(test)


def main():
    from actio.profiles.settings import load_settings
    temporary = load_settings(ROOT / 'actio.toml').paths['temp']
    temporary.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(temporary)
    p=argparse.ArgumentParser();p.add_argument('suite',choices=[*SUITES,'all-local']);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--only',nargs='+',help='Run named modules within the selected suite; report is scoped accordingly')
    a=p.parse_args();import actio
    expected=hashes(ROOT/'src/actio');actual=hashes(Path(actio.__file__).parent)
    if expected!=actual:raise SystemExit('installed product/source mismatch: install the current wheel first')
    if (ROOT/'src') in Path(actio.__file__).parents:raise SystemExit('installed wheel required')
    selected=sum(SUITES.values(),[]) if a.suite=='all-local' else SUITES[a.suite]
    if a.only:
        if not set(a.only)<=set(selected):raise SystemExit('unknown suite member')
        selected=a.only
    sys.path.insert(0,str(ROOT/'tests'))
    a.output.mkdir(parents=True,exist_ok=False)
    rows=[];matrix=None;saved_argv=sys.argv[:]
    for name in selected:
        sys.argv=[saved_argv[0]]
        if name=='suite_evidence':
            if matrix is None:raise SystemExit('suite_evidence requires the current suite_runtime result in this run')
            sys.argv=[saved_argv[0],'suite_evidence','refactor',str(matrix)]
        log=io.StringIO();start=datetime.datetime.now(datetime.timezone.utc).isoformat()
        suite=unittest.defaultTestLoader.loadTestsFromName('test_'+name)
        def ids(t):
            if isinstance(t,unittest.TestSuite):return [i for child in t for i in ids(child)]
            return [t.id()]
        collected=ids(suite)
        result=unittest.TextTestRunner(stream=log,verbosity=2,resultclass=Result).run(suite)
        complete=collected==result.executed and len(set(collected))==len(collected)
        (a.output/(name+'-controlled-evidence.json')).write_text(json.dumps(result.evidence,default=str),encoding='utf8')
        if name=='suite_runtime':
            for item in result.evidence:
                if item['id'].endswith('test_01_matrix_full_wire_and_portable_reader'):
                    matrix=Path(item['evidence']['root'])/'pilot.json'
        content=log.getvalue();(a.output/(name+'.log')).write_text(content,encoding='utf8')
        row={'suite':name,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
             'status':'PASS' if complete and result.wasSuccessful() and not result.skipped else 'FAIL','started':start,
             'collection_execution_match':complete,
             'collected':collected,'executed':result.executed,
             'failed_ids':[t.id() for t,_ in result.failures],'error_ids':[t.id() for t,_ in result.errors],
             'log_sha256':hashlib.sha256(content.encode()).hexdigest()}
        rows.append(row);print(json.dumps(row),flush=True)
        (a.output/'receipt.json').write_text(json.dumps({'status':'RUNNING','rows':rows,'sources':expected},indent=2),encoding='utf8')
    receipt={'status':'PASS' if all(r['status']=='PASS' for r in rows) else 'FAIL','group':a.suite,'rows':rows,'sources':expected,
             'suite_manifest':SUITES,'argv':sys.orig_argv,'scope':'current maintained tests; not a complete G1-G8 acceptance claim'}
    (a.output/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
    return 0 if receipt['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
