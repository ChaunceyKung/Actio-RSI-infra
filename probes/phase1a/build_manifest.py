"""Index existing evidence; does not run tests or turn NOT_RUN into PASS."""
import json
from collections import Counter
from datetime import datetime,timezone
from common import ROOT,EVIDENCE,file_hash,write_json

PY='probes/phase1a/.local/venv/Scripts/python.exe'
CASES=['lifecycle','tools','policy-isolation','constraints','iserror','transport','timeout','init-timeout','run-timeout','eof','exit','tool-interruption','event-integration','receipt-loss','concordia']

def main():
    installed=json.loads((EVIDENCE/'installed-artifacts.json').read_text(encoding='utf-8'))
    artifact={'source_sha':'5badb15009ae1756c3afe0ae0cef1faafc290ccc','sdk':'0.1.5rc1','runtime_distribution':'0.1.5rc1',
        'executable_sha256':installed['executable']['sha256'],'binary_source_mapping':'UNPROVEN',
        'concordia_source':'b71d202750e23444ce1bf28d9f114bcd88aa41db','mcp_python':'1.26.0'}
    rows=[]
    current_failures=[]
    for name in [*CASES,'events','evaluation']:
        path=EVIDENCE/(name+'.json');data=json.loads(path.read_text(encoding='utf-8'))
        unit=name in ['events','evaluation']
        if (not unit and data.get('status')!='PASS') or not data.get('tests'):
            current_failures.append(name)
        command=f'{PY} probes/phase1a/'+({'events':'event_probe.py','evaluation':'eval_probe.py'}[name] if unit else 'run_runtime.py '+name)
        for test in data['tests']:
            t=test['test_id'];p=t.split('-')[0]
            fids=['F01'] if p=='P3' else (['F02','F03'] if p=='P2' else ['F04','F05'])
            bids={'P1':['B03','B05'],'P2':['B03','B08'],'P3':['B04','B05'],'P4':['B07'],'P5':['B09']}[p]
            rows.append({'evidence_id':f'Phase1A-E{len(rows)+1:03}', 'test_id':t,'requirements':[p,*fids,*bids],
                'artifact_versions':artifact,'platform':installed['platform'],'execution_mode':data.get('mode','REAL_RUNTIME_FIXTURE_PROVIDER'),
                'command':command,'exit_code':data.get('exit_code',0),'status':test['status'],
                'sanitized_log':{'ref':'evidence/'+path.name,'sha256':file_hash(path)},
                'raw_log':None if unit else {'ref':'probes/phase1a/.local/runs/'+data['raw_directory']+'/raw.zip',
                                            'sha256':data['raw_zip_sha256'],'committed':False,'recreated_by_command':True},
                'assertions':test.get('assertions',[{k:v for k,v in test.items() if k not in ['status','test_id']}]),
                'limitations':test.get('limits',[])+data.get('limits',[]),
                'probe_hashes':data.get('probe_hashes',{str((ROOT/('event_probe.py' if name=='events' else 'eval_probe.py')).relative_to(ROOT)):file_hash(ROOT/('event_probe.py' if name=='events' else 'eval_probe.py'))} if unit else {})})
    source_checked=all(r.get('text_equals_source') is True for r in installed['sdk_source_comparison'].values())
    extras=[('P0-artifact','PASS','ARTIFACT_INSPECTION','installed-artifacts.json',["wheel hashes checked against official PyPI; executable hashed separately",'SDK source equality checked' if source_checked else 'SDK source equality NOT_RUN in this invocation'],['binary to source build mapping unproven']),
        ('P2-native-cancel-compatibility','FAIL','REAL_RUNTIME_FIXTURE_PROVIDER','native-cancel-limitation.json',['historical source/wheel cancel mismatch observed; final profile uses verified deny'],['G1 semantic cancel unsupported; failure not rerun as an unsafe supported configuration']),
        ('HIST-initial-launch','FAIL','REAL_ARTIFACT_STARTUP','initial-launch-failure.json',['initial long-path/package-import startup failure retained'],['superseded by short-root structural provider interface success']),
        ('HIST-initial-fixture','FAIL','REAL_RUNTIME_FIXTURE_PROVIDER','initial-tool-fixture-failure.json',['initial fixture message-shape mismatch retained'],['superseded by source.kind/callId matching and 6-call fixture limit'])]
    for test,status,mode,filename,assertions,limits in extras:
        rows.append({'evidence_id':f'Phase1A-E{len(rows)+1:03}','test_id':test,'requirements':['F04','B01a','B03'],
            'artifact_versions':artifact,'platform':installed['platform'],'execution_mode':mode,
            'command':f'{PY} probes/phase1a/artifact_info.py' if test.startswith('P0') else 'Historical attempt, preserved evidence; final suite command above',
            'exit_code':0 if status=='PASS' else 1,'status':status,
            'sanitized_log':{'ref':'evidence/'+filename,'sha256':file_hash(EVIDENCE/filename)},'raw_log':None,'assertions':assertions,'limitations':limits})
    deferred=[('G2-live','BLOCKED','No authorized provider/model and positive budget; no keys inspected or live requests'),
        ('G1-full-lifecycle','NOT_RUN','Fine cancellation/status/online catchup/resume/fork unsupported via SDK'),
        ('P2-dynamic-approval-rpc','NOT_RUN','Static policy selected; no per-call Python request/response protocol'),
        ('P2-other-mcp-combinations','NOT_RUN','Only stdio Python SDK 1.26.0 and protocol 2025-11-25 exercised'),
        ('P3-wire-response-loss','NOT_RUN','Application receipt persistence loss tested; bytes lost before SDK response decode not injected'),
        ('P3-powerloss-generation','NOT_RUN','No power loss, disk-full, exact fsync interruption or physical-generation migration'),
        ('P4-midrun-restore','NOT_RUN','External Entity and engine/world full snapshots absent; start rerun only'),
        ('P5-sotopia-real-evaluator','NOT_RUN','Controlled envelope fixtures only; upstream parser/judge not run'),
        ('G1-platform-scale','NOT_RUN','Linux/WSL, remote worker, 100-agent load, viewer, graph and second simulator deferred'),
        ('Strands-fallback','NOT_RUN','DSH G0 did not require loop/storage replacement; trigger not met')]
    for test,status,why in deferred:
        rows.append({'evidence_id':f'Phase1A-E{len(rows)+1:03}','test_id':test,'requirements':[test.split('-')[0]],
            'artifact_versions':artifact,'platform':installed['platform'],'execution_mode':'NOT_EXECUTED','command':None,'exit_code':None,
            'status':status,'sanitized_log':None,'raw_log':None,'assertions':[],'limitations':[why]})
    files=[{'ref':'evidence/'+p.name,'sha256':file_hash(p),'bytes':p.stat().st_size} for p in sorted(EVIDENCE.glob('*.json'))]
    final_rows=[r for r in rows if r['test_id'] not in [x[0] for x in extras+deferred]]
    good=not current_failures and len(final_rows)==56 and all(r['status']=='PASS' for r in final_rows)
    write_json(EVIDENCE.parent/'evidence_manifest.json',{'schema_version':1,'baseline':'fad04fcf0d14ded6684d54dc0633f4ee213276f3',
        'created_utc':datetime.now(timezone.utc).isoformat(),'conclusion':'CONDITIONAL_GO' if good else 'BLOCKED pending failure review','G0':'PASS within documented configuration' if good else 'UNCONFIRMED','G1':'UNSUPPORTED / limitations','G2':'BLOCKED',
        'counts':dict(Counter(r['status'] for r in rows)),'tests':rows,'evidence_files':files,
        'note':'Historical failures included separately. Expected 56 final behavior checks plus artifact inspection. Offline fixture does not imply live/production readiness.',
        'current_case_failures':current_failures})
    print('manifest',dict(Counter(r['status'] for r in rows)))

if __name__=='__main__':main()
