"""Produce public projections and a recomputable synthetic package. No provider calls."""
import json
from pathlib import Path
import sys
from actio.common import canonical,file_hash,digest
from actio.eval_contract import seal
from actio.failure_observation import from_entry
from actio.transport_diagnostics import portable,sources,analyze
from actio.future_schedule import plan
from actio.runtime import verify_runtime,pins

ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/validation/phase1c2c5';CONTROL=Path('D:/actio-c2c5-formal-v1')


def create(name,value):
    with (DOC/name).open('x',encoding='utf8',newline='\n') as f:f.write(canonical(value))


def main():
    actual=sources();assert all(file_hash(ROOT/'src/actio'/n)==h for n,h in actual.items())
    acceptance=json.loads((DOC/'acceptance-cec45e1c4746.json').read_bytes());assert acceptance['status']=='PASS' and acceptance['sources']==actual
    runtime=json.loads((DOC/'runtime-recomputed-f6c627a96092.json').read_bytes());assert runtime['status']=='PASS' and runtime['sources']==actual
    old=json.loads((DOC/'formal-original.json').read_bytes());assert old['status']=='FAIL'
    assert old['totals']==runtime['totals']=={'active':0,'admitted':5,'assigned':18,'not_run':6,'received':12,'responses':12,'sent':12,'settled':5,'unknown':7,'usage':5}
    original_history=json.loads((DOC/'history-fe0824eda3f4.json').read_bytes())
    entry=json.loads((Path(original_history['controlled_root'])/'c4-entry.json').read_bytes())
    sidecar={'schema':'c4-failure-sidecar.v1','source_authentication':'fixed C4 reader complete raw delivery and readonly v4 DB',
        'reader_commit':'3750954ea7cc8dff64115039e27bb671fa618d01','c4_final_commit':'70fce468a229d82f7de1f697b2619a95f8503f4b',
        'observations':from_entry(entry,'historical_c4'),'original_counts':{'planned_episodes':64,'planned_slots':128,'sent':33,'response':33,
            'usage':32,'admitted':32,'unknown':1,'not_run':95,'full_episodes':16,'candidate_pairs':8,'hidden_pairs':0,'presentation_pairs':0},
        'original_decision':'infrastructure_failure','activation':False,'c4_status':'INCOMPLETE','provider_availability':'NOT_RETESTED',
        'cumulative_real_requests':172,'historical_catalog_get':1,'new_external_requests':0,'bill':'UNVERIFIED'}
    create('c4-error-sidecar.json',sidecar)
    projection={'schema':'c5-runtime-projection.v1','status':'PASS','totals':runtime['totals'],
        'rows':[{'case':r['case'],'status':r['status'],'expected':r['expected'],'observed':r['observed'],'checks':r['checks'],'slots':r['slots'],
            'classifications':[o['classification'] for o in r['observations']]} for r in runtime['rows']],
        'runtime_commit':runtime['runtime_commit'],'final_observer_sources':actual,
        'original_status':'FAIL','final_recomputation':'PASS','additional_sends':0,'report_sha256':file_hash(DOC/'runtime-recomputed-f6c627a96092.json')}
    create('runtime-summary.json',projection);create('future-schedule.json',plan());create('prefix-coverage.json',plan()['body']['curves'])
    package=portable(sidecar,projection);assert analyze(package)['valid'];create('package.json',package)
    create('cleanup.json',runtime['cleanup']);create('scan.json',json.loads((CONTROL/'scan.json').read_bytes()))
    create('controlled-delivery.json',{'root':str(CONTROL),'original_report':{'file':str(CONTROL/'report.json'),'sha256':file_hash(CONTROL/'report.json')},
        'entries':[{'case':c['case'],'entry_hash':c['entry_hash'],'database_sha256':c['database_sha256']} for c in runtime['authentication']['rows']],
        'inventory':{'path':str(CONTROL/'file-inventory.json'),'sha256':file_hash(CONTROL/'file-inventory.json')},
        'raw_distribution':'controlled local only; not in Git','public_scope':'structural summaries and synthetic recomputation',
        'stop_sha256':file_hash(CONTROL/'suite-stop.json'),'cleanup_sha256':file_hash(CONTROL/'cleanup.json')})
    verify_runtime()
    create('installation.json',{'status':'PASS','python':sys.version,'sources':actual,'runtime_pins':pins(),
        'source_equal':True,'bootstrap':'local wheels --offline; fixed local Concordia Git archive','new_network_requests':0,
        'logs':{n:file_hash(ROOT/'.local'/n) for n in ('phase1c2c5-bootstrap.log','phase1c2c5-install01.log','phase1c2c5-install02.log')},
        'formal_runtime_sources':runtime['runtime_sources'],'final_runtime_replayed':False})
    create('delivery-generation.json',{'status':'PASS','sources':actual,'tool_sha256':file_hash(Path(__file__)),'argv':sys.orig_argv,'package_hash':package['sha256']})
    print(canonical({'status':'PASS','package_hash':package['sha256'],'new_external_requests':0}))


if __name__=='__main__':main()
