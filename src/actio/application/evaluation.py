from actio.adapters.filesystem.artifacts import publish
from actio.evidence.evaluation import verify_record
from actio.evidence.evaluation import prepare
from actio.evidence.evaluation import read_json
"""Immutable, offline evaluation CLI. No DB writes, providers, runtime or arbitrary plugins."""
import json
import os
from pathlib import Path

from actio.contracts.json import ContractError
from actio.contracts.json import canonical
from actio.contracts.json import digest
from actio.contracts.json import require
from actio.evidence.verify import sha
from actio.contracts.json import parse
from actio.evidence.eval_contract import VERSION
from actio.evidence.eval_contract import LIMITS
from actio.evidence.eval_contract import make_spec
from actio.contracts.json import seal
from actio.contracts.json import unseal





def evaluate(spec,source,output,raw_response=None,*,worker):
    identity,admission,outcome,inp,cluster=prepare(spec,source)
    b=unseal(spec)
    # Raw response content is part of the normalized request, even for invalid responses.
    response_hash=sha(raw_response.encode()) if raw_response is not None else None
    request={'schema':VERSION,'source':identity,'spec':spec['sha256'],'raw_response_hash':response_hash}
    key=digest(request);root=Path(output);root.mkdir(parents=True,exist_ok=True)
    index=root/(key+'.request.json')
    if index.exists():
        record=read_json(root/(read_json(index)['record']+'.json'))
        require(unseal(record)['request']==request,'measurement idempotency conflict')
        require(verify_record(record)['valid'],'existing record verification failed')
        return record,True
    # Claim before evaluation: a crash never causes automatic re-execution on retry.
    claim=root/(key+'.claim')
    try:
        with claim.open('x',encoding='utf8') as f:f.write(canonical({'request':request,'state':'claimed; no automatic retry'}));f.flush();os.fsync(f.fileno())
    except FileExistsError:raise ContractError('measurement already claimed or interrupted; no automatic retry')
    measurement={'status':'not_run','results':None,'error':None,'evaluator_calls':0,'parser_calls':0,
                 'model_requests':0,'view_hash':None,'audit':None}
    if admission['status']=='admitted':
        measurement['evaluator_calls']=1
        try:
            result=worker({'mode':b['mode'],'view':inp['body']['view'],'raw_response':raw_response},b['limits']['timeout_seconds'])
            require(result['view_hash']==inp['body']['view_hash'],'evaluator received view hash mismatch')
            measurement.update(result)
        except TimeoutError as e:measurement.update(status='timeout',error={'type':type(e).__name__,'reason':str(e)[:512]})
        except Exception as e:measurement.update(status='measurement_error',error={'type':type(e).__name__,'reason':str(e)[:512]})
    record=seal({'schema':'evaluation-record.v1','request':request,'request_hash':key,'spec':spec,
                 'source':source,'admission':admission,'task_outcome':outcome,'measurement':measurement,
                 'input':inp,'cluster':cluster,'mode':b['mode'],'fixture':True,'raw_response':raw_response,
                 'raw_response_hash':response_hash,'limits':'hashes show consistency, not authorship or measurement validity; preset scores are not model judgments'})
    path=publish(root,record)
    # Publish the request -> record pointer atomically, without overwriting another pointer.
    stage=root/(key+'.index.staging');stage.write_bytes(canonical({'record':record['sha256']}).encode())
    try:os.link(stage,index)
    finally:stage.unlink()
    return record,False


def campaign(dataset,output,*,worker):
    """Frozen fixture registry. Every registration references a retained record, including duplicates."""
    d=unseal(dataset)
    require(set(d)=={'schema','split','independent_units','sources','entries'} and d['schema']=='fixture-campaign.v1','campaign schema')
    require(d['split']=='synthetic-engineering-fixture' and d['independent_units']==0,'no research independence/holdout claim supported')
    require(type(d['entries']) is list and 1<=len(d['entries'])<=128,'campaign registration limit')
    require(len({e['id'] for e in d['entries']})==len(d['entries']),'duplicate campaign registration id')
    require(all(digest(v)==k for k,v in d['sources'].items()),'campaign source content hash mismatch')
    root=Path(output);published=publish(root/'datasets',dataset)
    specs={mode:make_spec(mode,dataset['sha256']) for mode in ('deterministic','controlled_response')}
    for spec in specs.values():publish(root/'specs',spec)
    registrations=[];records={};unique_evidence=set();clusters={}
    for entry in d['entries']:
        require(set(entry)=={'id','source','mode','raw_response','aliases','provenance'},'campaign entry fields')
        source=d['sources'][entry['source']];spec=specs[entry['mode']]
        identity,admission,outcome,inp,cluster=prepare(spec,source)
        require(entry['aliases']==identity.get('aliases',{}),'campaign frozen alias mismatch')
        record,reused=evaluate(spec,source,root/'records',entry['raw_response'],worker=worker)
        require(verify_record(record)['valid'],'campaign record failed verification')
        body=record['body'];records[record['sha256']]=body
        unit=digest(identity);unique_evidence.add(unit)
        if cluster:clusters.setdefault(cluster,set()).add(unit)
        registrations.append({'id':entry['id'],'record':record['sha256'],'source_identity':unit,
                              'cluster':cluster,'reused':reused,'provenance':entry['provenance']})
    counts={'registered':len(registrations),'unique_evidence':len(unique_evidence),'unique_measurements':len(records),
            'admitted':0,'rejected':0,'insufficient':0,'task_failure':0,'infrastructure_failure':0,
            'valid_measurement':0,'invalid_measurement':0,'measurement_error':0,'timeout':0,'not_run':0}
    for r in records.values():
        counts[r['admission']['status']]+=1;counts[r['measurement']['status']]+=1
        if r['task_outcome'] in ('task_failure','infrastructure_failure'):counts[r['task_outcome']]+=1
    report=seal({'schema':'fixture-campaign-report.v1','dataset_hash':dataset['sha256'],
                 'specs':{k:v['sha256'] for k,v in specs.items()},'registrations':registrations,'counts':counts,
                 'clusters':{k:sorted(v) for k,v in clusters.items()},'independent_research_units':0,
                 'denominators':'registration count includes duplicate packages; all status counts use unique measurement requests; modes have separate applicability; task/admission/measurement axes overlap',
                 'model_requests':sum(r['measurement']['model_requests'] for r in records.values()),
                 'validity':'synthetic engineering fixtures only; no holdout, confidence interval or capability claim'})
    path=publish(root/'reports',report)
    return {'report':str(path),'dataset':str(published),'counts':counts}
