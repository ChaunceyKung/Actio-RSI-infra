"""Finite C5 local fixtures; entry is never chosen by artifact-provided code."""
import json
from pathlib import Path
import sys
import uuid
from .common import canonical,digest,file_hash
from .eval_contract import seal,unseal
from .transport_contract import require
from .failure_fixtures import CASES,fault_response
from .failure_observation import from_entry
from .transport_diagnostics import sources,SUITE

MARKER='C5_SYNTHETIC_REASONING_DO_NOT_PROPAGATE'
TOOLS=('tests/gateway_stub.py','tests/chat_stub.py','tests/test_failure_observation.py',
       'scripts/phase1c2c5_validate.py','scripts/phase1c2c5_freeze.py','scripts/bootstrap.py')


def fixture(case):
    from . import robustness_campaign as c
    from .robustness_tasks import get
    from .task_diagnostic_data import visible
    from .task_diagnostic_policy import control
    unit=next(u for u in c.preregistration()['body']['units'] if u['family']==case['family'] and u['arm']=='baseline')
    card=get(unit['card']);a=control(visible(card,'A'),'conditional_argmax_first')
    b=control(visible(card,'B',[a]),'conditional_argmax_first')
    plans=[{'pilot':True,'model':'gpt-5.6','text':text,**({'reasoning':MARKER} if case['id']=='dual-success' else {})} for text in (a,b)]
    if case['fault']:
        i=1 if case['id']=='b-error' else 0;plans=plans[:i]+[{'fault':case['fault']}]
    return {'unit':unit,'plans':plans,'actions':[a,b]}


def review_entry(entry,case):
    pin=json.loads((Path(__file__).parent/'pins/c5_runtime.json').read_bytes())
    if digest(entry) in pin['entries'].values():require(digest(entry)==pin['entries'][case['id']],'frozen local case identity mismatch')
    observations=from_entry(entry,'local_official_runtime')
    ledger=entry['evidence']['ledger'];attempts=ledger['attempts']
    data=json.loads(next(iter(unseal(entry['evidence']['dataset'])['sources'].values()))['files']['evidence.json'])
    states=[a['state'] for a in attempts]
    counts={'assigned':2,'sent':sum(e['kind']=='sending' for e in ledger['events']),
        'responses':sum(a['response'] is not None for a in attempts),'received':len(entry['evidence']['receives']),
        'settled':states.count('settled'),'unknown':states.count('unknown'),
        'usage':sum(a['usage'] is not None for a in attempts),'admitted':sum(o['admission']['actually_admitted'] for o in observations),
        'not_run':2-len(attempts),'active':sum(s in ('authorized','reserved','sending') for s in states)}
    checks={k:counts[k]==case[k] for k in ('sends','settled','unknown','admitted') if k!='sends'}
    checks.update(sent=counts['sent']==counts['received']==counts['responses']==case['sends'],
        fake_credential_matched=all(r['credential_matched'] is True for r in entry['evidence']['receives']),
        no_retry=len(attempts)==case['sends'],active_zero=counts['active']==0,
        full_suffix=counts['not_run']==2-case['sends'],usage_source=counts['usage']==case['settled'],
        effects=len(data['world'])==len(data['domain_receipts'])==case['admitted'],
        reasoning_absent_from_domain=MARKER not in canonical({k:data[k] for k in ('world','domain_receipts','memory_proofs')}))
    slots=[]
    for seat in ('A','B'):
        ob=next((o for o in observations if o['identity']['seat']==seat),None)
        slots.append({'seat':seat,'state':'not_run' if ob is None else ob['accounting']['original_state'],
            'attempt':ob['identity']['attempt'] if ob else None})
    if len(attempts)==2:
        a_id=next(t['id'] for t in attempts if t['scope']['seat']=='A')
        a=next(o for o in data['operations'] if o['id']==a_id)['answer']
        b=next(t for t in attempts if t['scope']['seat']=='B')
        checks['B_actual_A_history']=all(MARKER not in canonical(b['scope']['task'][k]) for k in b['scope']['task']) and any(
            json.loads(o).get('public_actions')==[{'seat':'A','action':a}] for o in b['scope']['task']['observations'])
    for ob in observations:
        seat=ob['identity']['seat'];failed=case['fault'] and (seat=='B' if case['id']=='b-error' else seat=='A')
        expected='http_error_observed' if case['fault'] in ('429','503') else 'incomplete_or_unclassified' if case['fault']=='truncated' else 'provider_error_observed'
        checks[seat+'_classification']=ob['classification']==(expected if failed else 'success_control')
        checks[seat+'_native']=ob['adapter_native']['native_present'] and ob['adapter_native']['native_chunks_equal']
        checks[seat+'_admission']=ob['admission']['actually_admitted']==(not failed)
        if failed:checks[seat+'_unknown']=ob['accounting']['original_state']=='unknown' and ob['accounting']['verified_usage_preserved'] is None
    return {'case':case['id'],'status':'PASS' if all(checks.values()) else 'FAIL','expected':case,'observed':counts,
        'checks':checks,'slots':slots,'observations':observations,'entry_hash':digest(entry),
        'solver_success':not bool(case['fault']),'scenario_stop':'technical error' if case['fault'] else 'complete',
        'suite_continuation':'independent predeclared next fixture; no retry'}


def cleanup(workers,endpoints):
    import ctypes as C
    import socket
    from .supervisor import kernel,Job
    rows=[]
    for w in workers:
        k=kernel();h=k.OpenJobObjectW(4,False,w['job'])
        if not h:require(C.get_last_error()==2,'Job query failed');active=0
        else:
            j=object.__new__(Job);j.k=k;j.handle=h
            try:active=j.snapshot()['active']
            finally:k.CloseHandle(h)
        require(active==0 and w['state']=='reaped','C5 Worker still active')
        rows.append({'job':w['job'],'root':w['root'],'active':active,'state':w['state'],'report':json.loads(w['report'])})
    ports=[]
    for endpoint in endpoints:
        port=int(endpoint.split(':')[-1].split('/')[0])
        with socket.socket() as s:
            s.settimeout(.5);require(s.connect_ex(('127.0.0.1',port))!=0,'C5 listener remains')
        ports.append({'port':port,'listening':False,'probe':'literal loopback connect_ex'})
    return {'status':'PASS','jobs':rows,'ports':ports,'new_named_jobs_only':True}


def scan_generated(roots,secret,output):
    """One streaming pass; identical hardlinked cache content is checked once."""
    import hashlib
    import re
    tokens=[secret.encode()];fake=re.compile(rb'ACTIO_FAKE_[0-9a-f]{32}')
    inventory=[];seen={};cache_content={};byte_count=0;dedup=0
    for root in sorted(set(roots)):
        for path in sorted(root.rglob('*')):
            require(not path.is_symlink() and not path.is_junction(),'scan reparse path rejected')
            if not path.is_file():continue
            stat=path.stat();identity=(stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns)
            cache='node_modules' in path.parts or '__pycache__' in path.parts
            if cache and identity in seen:
                h=seen[identity];dedup+=1;scope='unchanged hardlink cache; identical file identity,size,mtime'
            else:
                h=hashlib.sha256();tail=b''
                with path.open('rb') as f:
                    while block:=f.read(1024*1024):
                        h.update(block);byte_count+=len(block);content=tail+block
                        require(not any(t in content for t in tokens) and not fake.search(content),'credential persisted; scan blocked')
                        tail=content[-256:]
                h=h.hexdigest();scope='dependency content scanned' if cache else 'generated material scanned'
                after=path.stat();require((after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)==identity,'file changed during scan')
                if cache:seen[identity]=h
            if cache:cache_content.setdefault(h,{'bytes':stat.st_size,'first_path':str(path)})
            inventory.append({'path':str(path),'bytes':stat.st_size,'sha256':h,'scope':scope})
            if len(inventory)%1000==0:
                print(canonical({'scan_progress_files':len(inventory),'read_bytes':byte_count}),file=sys.stderr,flush=True)
    from .pilot import create
    create(output,{'files':inventory,'dependency_content_inventory':cache_content})
    return {'status':'PASS','files':len(inventory),'bytes_read':byte_count,'identical_hardlink_reuse':dedup,
        'inventory':str(output),'inventory_sha256':file_hash(output),'scope':'all generated paths including logs DB native and cache; no directory skipped',
        'credential_found':False}


def run(root,project,freeze_path):
    # No supplied endpoint, credential reference, live flag or dynamic code selector exists.
    from .pilot import create,run_unit
    from . import robustness_campaign as c
    from .runtime import verify_runtime
    from .preflight import loopback_endpoint
    root=root.resolve();project=project.resolve();require(not root.exists(),'new C5 root required')
    frozen=json.loads(freeze_path.read_bytes());require(frozen['sources']==sources(),'frozen product differs')
    require(frozen['cases']==CASES and frozen['fixtures']==[fixture(c) for c in CASES],'frozen fixtures differ')
    require(frozen['tools']=={n:file_hash(project/n) for n in TOOLS},'frozen trusted tools differ')
    require(all(file_hash(project/'src/actio'/n)==h for n,h in sources().items()),'installed/source mismatch')
    verify_runtime()
    sys.path.insert(0,str(project/'tests'))
    import gateway_stub
    original=gateway_stub.planned
    def planned(p,i):return fault_response(p['fault']) if p.get('fault') else original(p,i)
    gateway_stub.planned=planned
    root.mkdir(parents=True);secret='ACTIO_FAKE_'+uuid.uuid4().hex;workers=[];endpoints=[];rows=[];entries=[];cleanup_result=None
    create(root/'intent.json',{'schema':SUITE,'freeze_sha256':file_hash(freeze_path),'sources':sources(),'cases':CASES,
        'slots':[{'case':c['id'],'seat':s,'state':'planned'} for c in CASES for s in ('A','B')],
        'maximum_sends':12,'external_requests':0,'argv':sys.orig_argv})
    try:
        for case in CASES:
            case_root=root/case['id'];case_root.mkdir();f=fixture(case);entry=None;result=None
            try:
                with gateway_stub.GatewayStub(case_root,f['plans'],secret) as service:
                    endpoints.append(service.endpoint);require(loopback_endpoint(service.endpoint[:-3]),'literal loopback only')
                    cfg=c.config(f['unit']['id'],mode=c.REHEARSAL,endpoint=service.endpoint,
                        authority={'id':uuid.uuid4().hex,'root':str(case_root/'local-namespace')})
                    entry,result=run_unit(case_root/'episode',cfg,secret,receives=service.receives)
                    workers.extend(result['workers']);entries.append(entry)
                    create(case_root/'entry.json',seal({'schema':'transport-diagnostic-controlled-entry.v1','origin':'local_official_runtime','entry':entry}))
                    create(case_root/'stop-inventory.json',{'ledger':entry['evidence']['ledger'],
                        'workers':result['workers'],'native_roots':[w['root'] for w in result['workers']],
                        'slots':[{'seat':s,'attempts':[a['id'] for a in entry['evidence']['ledger']['attempts'] if a['scope']['seat']==s]} for s in ('A','B')],
                        'original_error':result['error'],'analysis_started':False})
                require(not service.thread.is_alive(),'service join missing')
                # Service and Workers are stopped before any new diagnostics or scanning.
                row=review_entry(entry,case)
            except Exception as e:
                if result is None and (case_root/'episode/domain.sqlite').exists():
                    from .store import Store
                    from .budget import Ledger
                    s=Store(case_root/'episode/domain.sqlite',readonly=True)
                    try:discovered=s.rows('SELECT * FROM worker')
                    finally:s.close()
                    workers.extend(w for w in discovered if w['job'] not in {x['job'] for x in workers})
                    ledger=Ledger(case_root/'episode/budget.sqlite',readonly=True)
                    try:snapshot=ledger.snapshot()
                    finally:ledger.close()
                    create(case_root/'fallback-stop-inventory.json',{'ledger':snapshot,'workers':discovered,
                        'slots':[{'seat':s,'attempts':[x['id'] for x in snapshot['attempts'] if x['scope']['seat']==s]} for s in ('A','B')]})
                create(case_root/'diagnostic-failure.json',{'type':type(e).__name__,'entry_retained':entry is not None,
                    'original_result_retained':result is not None,'raw_paths':str(case_root),'no_retry':True})
                row={'case':case['id'],'status':'FAIL','failure_type':type(e).__name__,'original_evidence_retained':entry is not None}
            rows.append(row);create(case_root/'observation.json',row)
            print(canonical({'case':case['id'],'status':row['status'],'observed':row.get('observed')}),file=sys.stderr,flush=True)
    finally:
        gateway_stub.planned=original
        create(root/'suite-stop.json',{'entries':len(entries),'workers':workers,'endpoints':endpoints,'rows':rows,
            'unstarted_cases':[c['id'] for c in CASES if c['id'] not in {r['case'] for r in rows}],
            'export_started':False,'scan_started':False})
        cleanup_result=cleanup(workers,endpoints);create(root/'cleanup.json',cleanup_result)
    totals={k:sum(r.get('observed',{}).get(k,0) for r in rows) for k in ('assigned','sent','responses','received','settled','unknown','usage','admitted','not_run','active')}
    report={'schema':SUITE,'status':'PASS' if len(rows)==9 and all(r['status']=='PASS' for r in rows) else 'FAIL',
        'sources':sources(),'freeze_sha256':file_hash(freeze_path),'rows':rows,'totals':totals,
        'cleanup':cleanup_result,'external_provider_requests':0,'catalog_get':0,'external_mcp_calls':0,
        'candidate_evaluation_created':False,'activation':False}
    create(root/'report.json',report)
    try:scanned=scan_generated([root],secret,root/'file-inventory.json')
    except Exception as e:
        create(root/'scan-incomplete.json',{'status':'INCOMPLETE','type':type(e).__name__,'model_rerun':False});raise
    create(root/'scan.json',scanned)
    return {'status':report['status'],'root':str(root),'totals':totals,'scan':scanned,'jobs':len(workers),'services':len(endpoints)}
