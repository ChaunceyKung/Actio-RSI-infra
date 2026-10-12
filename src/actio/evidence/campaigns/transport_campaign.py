"""Immutable transport campaign using existing bundle snapshots and sealed artifacts."""
import json
from pathlib import Path

from actio.contracts.json import digest
from actio.contracts.json import ContractError
from actio.adapters.filesystem.common import file_hash
from actio.evidence.audit.accounting import verify_snapshot
from actio.contracts.hashing import sha
from actio.profiles.registry import priced
from actio.profiles.registry import gateway
from actio.profiles.registry import pilot
from actio.contracts.json import seal
from actio.contracts.json import unseal
from actio.evidence.bundles.evaluation import read_json
from actio.contracts.transport import INPUT
from actio.contracts.json import require
from actio.evidence.bundles.verify import verify_bundle


def analyze(dataset,ledger,receives):
    verify_snapshot(ledger)
    cfg=ledger['meta']['config'];is_gateway=gateway(cfg);live=is_gateway and cfg['mode'] in ('tokenkey_live','tokenkey_pilot_live','tokenkey_suite_live','candidate_live','robustness_live')
    if live:require(receives is None,'live supplier receives must remain null without independent logs')
    received=[] if live else receives
    d=unseal(dataset);require(set(d)=={'schema','campaign','registrations','sources'} and d['schema']=='transport-dataset.v1','transport dataset schema')
    require(d['campaign']==ledger['meta']['campaign'] and d['registrations']==ledger['registrations'],'registration completeness/order')
    require(set(d['sources'])=={r['run'] for r in d['registrations']},'missing/extra run source')
    audits={};operation_rows={};states={}
    for run,source in d['sources'].items():
        capture={};v=verify_bundle(snapshot=source['files'],capture=capture)
        require(v['bundle_integrity']=='valid' and v['facts_consistency']!='invalid' and v['execution_mode'] in ('transport_stub','priced_rehearsal','tokenkey_live','tokenkey_rehearsal','tokenkey_pilot_live','tokenkey_pilot_rehearsal','tokenkey_suite_live','tokenkey_suite_rehearsal','candidate_loopback','candidate_live','candidate_rehearsal','robustness_live','robustness_rehearsal'),'transport bundle rejected: '+str(v['errors']))
        data=capture['evidence'];m=json.loads(data['run']['input'])
        require(data['run']['id']==run and m['input_contract']==('visible-robustness-tokenkey.v1' if cfg.get('schema')=='pilot-config.v10' else 'finite-candidate-tokenkey.v1' if cfg.get('schema')=='pilot-config.v9' else 'finite-candidate-loopback.v1' if cfg.get('schema')=='pilot-config.v8' else 'finite-suite-tokenkey.v1' if cfg.get('schema')=='pilot-config.v7' else 'scheduling-tokenkey.v2' if pilot(cfg) else 'scheduling-tokenkey.v1' if is_gateway else 'scheduling-priced.v1' if priced(ledger['meta']['config']) else INPUT) and m['transport']['config']==ledger['meta']['config'],'source run/config')
        require([r for r in d['registrations'] if r['run']==run]==sorted([
            {'id':run+':'+seat,'run':run,'seat':seat,'manifest_hash':digest(m),'task_hash':m['task']['sha256']} for seat in ('A','B')],key=lambda r:r['id']),'dataset seat/view/manifest binding')
        for row in data['audit']:
            if row['kind']=='transport_attempt':
                a=json.loads(row['body']);require(a['id'] not in audits,'cross-run duplicate attempt');audits[a['id']]=a
        operation_rows.update({o['id']:o for o in data['operations']})
        states[run]={'task_outcome':v['task_outcome'],'scenario_completeness':v['scenario_completeness'],
                     'world_effects':len(data['world']),'accounting':v['accounting']}
    require(audits=={a['id']:a for a in ledger['attempts']},'ledger/source missing/extra/changed attempt')
    ids=[r['attempt'] for r in received];require(len(ids)==len(set(ids)),'duplicate service receive')
    for r in received:
        require(r['attempt'] in audits,'service capture wrong attempt')
        a=audits[r['attempt']]
        require(any(e['attempt']==a['id'] and e['kind']=='sending' for e in ledger['events']),'receive without sending')
        require(r['wire_hash']==sha(r['raw'])==a['binding']['wire_hash'] and r['raw']==a['request']['raw'],'service/wire body mismatch')
        require(r['method']=='POST' and r['path']==('/v1/chat/completions' if is_gateway else '/chat/completions') and r['headers']['X-Actio-Attempt']==a['id'],'service method/attempt')
        require(r['response']['sha256']==sha(r['response']['raw']),'service response hash')
        if a['state']=='settled':
            require(r['response']['status']==200 and r['response']['raw']==a['response']['raw'],'settled raw service response')
            chunks=json.loads(a['response']['chunks_json']);texts=[c['block']['text'] for c in chunks if c['type']=='block-end' and c['block']['type']=='text']
            require(''.join(texts)==operation_rows[a['id']]['answer'],'official text/native answer mismatch')
    for a in audits.values():
        if a['state']=='settled':
            if not live:require(a['id'] in ids,'settled without receive')
            if is_gateway:
                chunks=json.loads(a['response']['chunks_json']);text=''.join(x['block']['text'] for x in chunks if x['type']=='block-end' and x['block']['type']=='text')
                if not pilot(cfg) or a['text_integrity']['status']=='verified':require(text==operation_rows[a['id']]['answer'],'gateway text/native answer mismatch')
        if a['state'] in ('denied','released'):require(a['id'] not in ids,'unsent state had receive')
    counts={'registered':len(d['registrations']),'attempted':len(audits),'not_run':len(d['registrations'])-len(audits),
            'send_attempts':sum(e['kind']=='sending' for e in ledger['events']),'received':None if live else len(received),
            **{k:sum(a['state']==k for a in audits.values()) for k in ('settled','unknown','denied','released')},
            'real_model_requests':sum(e['kind']=='sending' for e in ledger['events']) if live else 0,'real_cost':None if live else 0}
    if is_gateway:
        counts.update(observed_responses=sum(bool(a['response'] and a['response']['status']) for a in audits.values()),usage_bearing_verified_responses=sum(a['usage'] is not None for a in audits.values()))
    return {'schema':'transport-report.v1','campaign':d['campaign'],'counts':counts,'totals':ledger['totals'],'runs':states,
            'usage_basis':'TokenKey reported usage; cost unverified' if live else 'pi-ai local simulation; cost unverified' if is_gateway else 'simulated usage; USD frozen-quote estimate; not a supplier bill' if priced(ledger['meta']['config']) else 'synthetic; no real tokenizer/billing bound',
            **({'gateway_cost_observations':[{'attempt':a['id'],'value':a['usage']['gateway_reported_cost_raw'],'currency':None,'unit':None} for a in audits.values() if a['usage']],'gateway':'TokenKey','requested_model':cfg['model'],'upstream_identity_verified':False} if is_gateway else {}),
            'supplier_received':None,'supplier_bill_minor':None,'billing_reconciliation':'UNVERIFIED','independent_units':0}





def verify_campaign(directory):
    try:
        root=Path(directory).resolve();require(not any(p.is_symlink() or p.is_junction() for p in (root,*root.parents)),'reparse campaign path')
        index=unseal(read_json(root/'campaign.json'));require(set(index)=={'schema','paths','files'} and index['schema']=='transport-campaign.v1','transport campaign index')
        actual=[]
        for p in root.rglob('*'):
            require(not p.is_symlink() and not p.is_junction(),'reparse campaign entry')
            if p.is_file() and p.name!='campaign.json':actual.append(p.relative_to(root).as_posix())
        require(set(actual)==set(index['files']) and len(actual)==4,'campaign files completeness')
        require(set(index['paths'])=={'dataset','ledger','receives','report'} and set(index['paths'].values())==set(actual),'campaign object scope')
        require(sum((root/n).stat().st_size for n in actual)<=64*1024*1024,'campaign byte bound')
        for n,h in index['files'].items():require(file_hash(root/n)==h,'campaign file hash')
        values={k:read_json(root/n) for k,n in index['paths'].items()}
        result=analyze(values['dataset'],unseal(values['ledger']),unseal(values['receives']))
        require(unseal(values['report'])==result,'campaign counts/accounting tampering')
        return {'valid':True,'report':result,'model_requests':0,'evaluator_calls':0}
    except (OSError,ContractError,ValueError,KeyError,TypeError,IndexError,StopIteration) as e:
        return {'valid':False,'error':str(e)[:512],'model_requests':0,'evaluator_calls':0}
