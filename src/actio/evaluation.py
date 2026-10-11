"""Immutable, offline evaluation CLI. No DB writes, providers, runtime or arbitrary plugins."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

from actio.contracts.json import ContractError, canonical, digest
from actio.adapters.filesystem.common import clean_env
from actio.contracts.json import require
from .verify import verify_bundle, sha, MAX_BYTES, VERIFIER
from actio.contracts.json import parse
from .eval_contract import VERSION, LIMITS, validate_spec, build_view, synthetic_input, synthetic_view, strict_response, deterministic, make_spec, bundle_aliases
from actio.contracts.json import seal, unseal


def read_json(path,maximum=MAX_BYTES*2):
    with Path(path).open('rb') as f:raw=f.read(maximum+1)
    require(len(raw)<=maximum,'input file byte limit')
    return parse(raw)


def publish(root,value):
    """Content-addressed atomic hardlink publication never replaces an existing inode."""
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    key=value['sha256'];target=root/(key+'.json')
    if target.exists():
        require(read_json(target)==value,'immutable artifact conflict');return target
    stage=root/('.'+key+'.'+uuid.uuid4().hex+'.staging')
    with stage.open('xb') as f:f.write(canonical(value).encode());f.flush();os.fsync(f.fileno())
    try:os.link(stage,target)
    except FileExistsError:require(read_json(target)==value,'immutable artifact race conflict')
    finally:stage.unlink()
    return target


def source_bundle(path):
    capture={};v=verify_bundle(path,capture=capture)
    source={'kind':'bundle','files':capture.get('files',{})}
    # A failed read may be represented by a bounded failure descriptor (no host paths).
    if v['bundle_integrity']!='valid':source['read_failure']=v['errors']
    return source,v,capture


def prepare(spec,source):
    b=validate_spec(spec);mode=b['mode'];data=None;view=None;mapping={}
    reasons=[];status='admitted';outcome='unknown';run=None;cluster=None
    if source['kind']=='bundle':
        capture={};v=verify_bundle(snapshot=source['files'],capture=capture)
        identity={'content':v.get('content_sha256',digest(source['files'])),
                  'source':capture.get('manifest',{}).get('source'), 'kind':'bundle'}
        if v['bundle_integrity']!='valid' or v['facts_consistency']=='invalid':
            status='rejected';reasons=v['errors'] or ['invalid evidence']
        else:
            data=capture['evidence'];m=parse(data['run']['input']);run=data['run']['id'];outcome=v['task_outcome']
            cluster=digest({k:x for k,x in m.items() if k not in ('request','replay_of')})
            identity['manifest_hash']=data['run']['input_hash']
            identity['aliases']=bundle_aliases(data)
            if v['scenario_completeness']!='complete' or v['facts_consistency']!='consistent':
                status='insufficient';reasons=v['missing'] or [v['scenario_completeness']]
            elif mode=='controlled_response' and m.get('input_contract')!='scheduling-input.v1':
                status='insufficient';reasons=['frozen social goals and initial relationship baselines absent; historical bundles cannot be backfilled']
            elif mode=='controlled_response' and (len(data['operations'])!=2 or any('rejected' in parse(r['body']) for r in data['domain_receipts'])):
                status='insufficient';reasons=['controlled task rubric requires two legal observed actions; no score for absent/rejected actor']
            else:view=build_view(data,mode);mapping=view['aliases'];identity['aliases']=mapping
    elif source['kind']=='synthetic':
        v={'verifier':VERIFIER,'kind':'sealed-synthetic-input.v1','bundle_integrity':'not_applicable'}
        identity={'content':source['input']['sha256'],'kind':'synthetic'}
        try:
            value,mapping=synthetic_input(source['input']);run=value['unit'];outcome=value['task_outcome'];cluster=identity['content']
            identity['aliases']=mapping
            require(mode=='controlled_response','synthetic source requires controlled_response')
            view=synthetic_view(value,mapping)
        except (ContractError,KeyError,TypeError,ValueError,AttributeError) as e:
            status='insufficient';reasons=[str(e)[:512]];view=None;mapping={}
    else:raise ContractError('unknown source kind')
    admission={'status':status,'reasons':reasons,'verification':v}
    inp=None
    if view is not None:
        inp=seal({'schema':'evaluation-input.v1','source_identity':identity,'spec_hash':spec['sha256'],
                  'run':run,'unit':run,'cluster':cluster,'aliases':mapping,'view':view,'view_hash':digest(view),
                  'selection':b['view'],'fixture':True})
    return identity,admission,outcome,inp,cluster


def execute_worker(payload,timeout):
    with tempfile.TemporaryDirectory(prefix='actio-eval-') as temp:
        env=clean_env(temp)
        command=[sys.executable,'-I','-B','-m','actio.eval_worker']
        try:
            p=subprocess.run(command,input=canonical(payload).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                             timeout=timeout,env=env,cwd=temp)
        except subprocess.TimeoutExpired as e:raise TimeoutError('local evaluator exceeded frozen deadline; child killed and waited') from e
        require(len(p.stdout)<=LIMITS['input_bytes'] and len(p.stderr)<=LIMITS['response_bytes'],'local evaluator output limit')
        if p.returncode:raise RuntimeError('local evaluator exit '+str(p.returncode)+': '+p.stderr.decode(errors='replace')[:256])
        return parse(p.stdout)


def evaluate(spec,source,output,raw_response=None):
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
            result=execute_worker({'mode':b['mode'],'view':inp['body']['view'],'raw_response':raw_response},b['limits']['timeout_seconds'])
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


def verify_record(record):
    try:
        r=unseal(record);require(r['schema']=='evaluation-record.v1','record version')
        identity,admission,outcome,inp,cluster=prepare(r['spec'],r['source'])
        require((admission,outcome,inp,cluster)==(r['admission'],r['task_outcome'],r['input'],r['cluster']),'record input/admission differs from source recomputation')
        raw=r['raw_response'];raw_hash=sha(raw.encode()) if raw is not None else None
        request={'schema':VERSION,'source':identity,'spec':r['spec']['sha256'],'raw_response_hash':raw_hash}
        require(r['request']==request and r['request_hash']==digest(request) and r['raw_response_hash']==raw_hash,'record request binding')
        m=r['measurement'];require(m['model_requests']==0 and r['fixture'] is True and r['mode']==unseal(r['spec'])['mode'],'mode/budget binding')
        if admission['status']!='admitted':
            require(m['evaluator_calls']==0 and m['status']=='not_run' and m['results'] is None,'nonadmitted evaluator execution')
        else:
            require(m['evaluator_calls']==1 and m['status'] in ('valid_measurement','invalid_measurement','measurement_error','timeout'),'invalid measurement axes')
            if m['status']=='valid_measurement':
                expected=deterministic(inp['body']['view']) if r['mode']=='deterministic' else strict_response(raw,inp['body']['aliases'])['scores']
                require(m['results']==expected and m['view_hash']==inp['body']['view_hash'],'measurement result/view mismatch')
                require(m['parser_calls']==(1 if r['mode']=='controlled_response' else 0),'parser execution count mismatch')
                require(m['audit']=={'network_attempts':0,'process_attempts':0,'runtime_import_attempts':0,'write_attempts':0},'offline worker audit mismatch')
            else:
                require(m['results'] is None and m['error'] is not None,'failed measurement needs null results and diagnostic')
                if m['status']=='invalid_measurement':
                    require(r['mode']=='controlled_response','deterministic failure is an internal error')
                    try:strict_response(raw,inp['body']['aliases'])
                    except ContractError:pass
                    else:raise ContractError('invalid response claim contradicts strict envelope')
        return {'valid':True,'record_hash':record['sha256'],'model_requests':0,'trust':'internal consistency; parser execution/errors are recorded local observations, not signed attestations'}
    except (ContractError,KeyError,TypeError,ValueError,AttributeError,RecursionError) as e:
        return {'valid':False,'error':str(e)[:512]}


def campaign(dataset,output):
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
        record,reused=evaluate(spec,source,root/'records',entry['raw_response'])
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


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
    c=s.add_parser('spec');c.add_argument('--mode',choices=['deterministic','controlled_response'],required=True);c.add_argument('--dataset-hash',required=True);c.add_argument('--output',type=Path,required=True)
    c=s.add_parser('run');c.add_argument('--spec',type=Path,required=True);g=c.add_mutually_exclusive_group(required=True);g.add_argument('--bundle',type=Path);g.add_argument('--synthetic',type=Path);c.add_argument('--response',type=Path);c.add_argument('--output',type=Path,required=True)
    c=s.add_parser('verify-record');c.add_argument('record',type=Path)
    c=s.add_parser('campaign');c.add_argument('dataset',type=Path);c.add_argument('--output',type=Path,required=True)
    a=p.parse_args(argv)
    try:
        if a.command=='spec':
            value=make_spec(a.mode,a.dataset_hash);print(json.dumps({'spec':str(publish(a.output,value))}));return 0
        if a.command=='verify-record':
            result=verify_record(read_json(a.record));print(json.dumps(result));return 0 if result['valid'] else 2
        if a.command=='campaign':
            print(json.dumps(campaign(read_json(a.dataset),a.output)));return 0
        spec=read_json(a.spec,LIMITS['input_bytes'])
        source=source_bundle(a.bundle)[0] if a.bundle else {'kind':'synthetic','input':read_json(a.synthetic,LIMITS['input_bytes'])}
        raw=None
        if a.response:
            with a.response.open('rb') as f:encoded=f.read(LIMITS['response_bytes']+1)
            # Full byte hashing of unbounded responses is not accepted. Reject at the input boundary.
            require(len(encoded)<=LIMITS['response_bytes'],'response file byte limit')
            raw=encoded.decode('utf8')
        record,reused=evaluate(spec,source,a.output,raw)
        r=record['body'];print(json.dumps({'record':str(a.output/(record['sha256']+'.json')),'reused':reused,
            'admission':r['admission']['status'],'task_outcome':r['task_outcome'],'measurement':r['measurement']['status']}))
        return 0 if r['measurement']['status']=='valid_measurement' else 2
    except (ContractError,OSError,KeyError,TypeError,ValueError) as e:
        print(json.dumps({'error':type(e).__name__,'reason':str(e)[:512]}));return 2


if __name__=='__main__':raise SystemExit(main())
