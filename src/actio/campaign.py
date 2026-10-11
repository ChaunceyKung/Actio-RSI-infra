"""Task-family campaign execution and independent, read-only completeness verification."""
import argparse
import json
import os
from pathlib import Path
import uuid

from actio.contracts.json import ContractError, canonical, digest
from actio.adapters.filesystem.common import file_hash
from .eval_contract import make_spec
from actio.contracts.json import seal, unseal
from .evaluation import read_json,publish,prepare,evaluate,verify_record
from actio.contracts.json import require
from .verify import verify_bundle, MAX_BYTES
from actio.contracts.json import parse

GROUP_RULE={'version':'family-group.v1','seed':0,'assignment':'all observed scheduling family variants/seats/repeats/replays remain development',
            'groups':['development','calibration_pending'],'independent_units':0,'holdout':False}


def source_group(source):
    capture={};v=verify_bundle(snapshot=source['files'],capture=capture)
    require('evidence' in capture,'campaign needs a readable evidence snapshot even for rejected facts')
    d=capture['evidence'];m=parse(d['run']['input']);t=m.get('task',{}).get('body',{})
    return {'family':t.get('family','legacy-fixture.'+m['scenario']), 'card':t.get('id',m['scenario']),
            'episode':d['run']['id'],'replay_of':m.get('replay_of'),
            'repeat_group':t.get('family','legacy-fixture.'+m['scenario']),
            'arm':'baseline','group':t.get('grouping',{}).get('group','development')}


def validate_dataset(dataset):
    d=unseal(dataset)
    require(set(d)=={'schema','group_rule','sources','entries'} and d['schema']=='task-campaign.v1','task campaign schema')
    require(d['group_rule']==GROUP_RULE,'unsupported family grouping rule')
    require(type(d['entries']) is list and 1<=len(d['entries'])<=128,'campaign entry limit')
    ids=[e['id'] for e in d['entries']];require(len(ids)==len(set(ids)) and all(type(i) is str and i for i in ids),'duplicate/missing registration ID')
    require(set(d['sources'])=={e['source'] for e in d['entries']} and all(digest(v)==k for k,v in d['sources'].items()),'missing/extra or changed campaign sources')
    families={}
    for e in d['entries']:
        require(set(e)=={'id','source','mode','raw_response','aliases','grouping'},'campaign registration fields')
        require(e['mode'] in ('deterministic','controlled_response'),'campaign mode')
        source=d['sources'][e['source']];g=source_group(source)
        require(e['grouping']==g,'campaign source/family/group/episode binding mismatch')
        require(g['group'] in GROUP_RULE['groups'] and g['arm']=='baseline','unimplemented arm or group')
        require(g['family'] not in families or families[g['family']]==g['group'],'family crosses development/calibration groups')
        families[g['family']]=g['group']
        spec=make_spec(e['mode'],dataset['sha256']);identity,*_=prepare(spec,source)
        require(e['aliases']==identity.get('aliases',{}),'frozen campaign alias mismatch')
    return d


def summarize(dataset,records,registrations):
    counts={'registered':len(registrations),'unique_evidence':len({digest(r['body']['request']['source']) for r in records.values()}),
            'unique_measurements':len(records),'admitted':0,'rejected':0,'insufficient':0,
            'task_failure':0,'infrastructure_failure':0,'valid_measurement':0,'invalid_measurement':0,'measurement_error':0,'timeout':0,'not_run':0}
    modes={}
    for record in records.values():
        r=unseal(record);counts[r['admission']['status']]+=1;counts[r['measurement']['status']]+=1
        if r['task_outcome'] in ('task_failure','infrastructure_failure'):counts[r['task_outcome']]+=1
        key=r['mode'];modes.setdefault(key,{'requests':0,'admitted':0,'valid':0});modes[key]['requests']+=1
        modes[key]['admitted']+=int(r['admission']['status']=='admitted');modes[key]['valid']+=int(r['measurement']['status']=='valid_measurement')
    return {'schema':'task-campaign-report.v1','dataset_hash':dataset['sha256'],'group_rule_hash':digest(GROUP_RULE),
            'registrations':registrations,'counts':counts,'mode_denominators':modes,'fixture':True,'model_requests':0,
            'independent_research_units':0,'denominator':'status counts use unique evaluation requests; registration includes duplicates; axes overlap'}


def run_campaign(dataset,destination):
    d=validate_dataset(dataset);dest=Path(destination).absolute()
    require(not dest.exists(),'campaign destination exists; immutable publication requires new destination')
    dest.parent.mkdir(parents=True,exist_ok=True);stage=dest.with_name('.'+dest.name+'.stage-'+uuid.uuid4().hex);stage.mkdir()
    try:
        dataset_path=publish(stage/'datasets',dataset);specs={m:make_spec(m,dataset['sha256']) for m in ('deterministic','controlled_response')}
        spec_paths={m:publish(stage/'specs',s) for m,s in specs.items()};records={};registrations=[];seen=set()
        for e in d['entries']:
            record,reused=evaluate(specs[e['mode']],d['sources'][e['source']],stage/'records',e['raw_response'])
            require(verify_record(record)['valid'],'generated record verification failed')
            rid=record['sha256'];records[rid]=record
            registrations.append({'id':e['id'],'record':rid,'duplicate_request':rid in seen,'grouping':e['grouping']});seen.add(rid)
        report=seal(summarize(dataset,records,registrations));report_path=publish(stage/'reports',report)
        files={p.relative_to(stage).as_posix():{'sha256':file_hash(p),'bytes':p.stat().st_size,'status':'current'} for p in stage.rglob('*') if p.is_file()}
        index=seal({'schema':'task-campaign-index.v1','dataset':dataset_path.relative_to(stage).as_posix(),
                    'specs':{m:p.relative_to(stage).as_posix() for m,p in spec_paths.items()},
                    'report':report_path.relative_to(stage).as_posix(),'files':files,'historical':[]})
        with (stage/'campaign.json').open('x',encoding='utf8') as f:f.write(canonical(index));f.flush();os.fsync(f.fileno())
        checked=verify_campaign(stage);require(checked['valid'],str(checked))
        stage.rename(dest)
        return {'directory':str(dest),'campaign_hash':index['sha256'],'counts':report['body']['counts']}
    except Exception as e:
        with (stage/'failure.json').open('x',encoding='utf8') as f:f.write(canonical({'error':type(e).__name__,'reason':str(e)[:512]}))
        raise


def verify_campaign(directory):
    """Never calls evaluate/run_campaign, imports runtime, or writes files. No record-selected code."""
    try:
        root=Path(directory).absolute();require(not any(p.is_symlink() or p.is_junction() for p in (root,*root.parents)),'campaign reparse root')
        index=read_json(root/'campaign.json');i=unseal(index)
        require(set(i)=={'schema','dataset','specs','report','files','historical'} and i['schema']=='task-campaign-index.v1','campaign index schema')
        actual=set();total=0;contents={}
        for p in root.rglob('*'):
            require(not p.is_symlink() and not p.is_junction(),'campaign reparse entry')
            if p.is_file() and p!=root/'campaign.json':actual.add(p.relative_to(root).as_posix())
        require(actual==set(i['files']),'missing/extra campaign files')
        require(len(actual)<=512 and len(i['historical'])==len(set(i['historical'])),'campaign inventory limit/history duplicate')
        for name,entry in i['files'].items():
            p=Path(name);require(not p.is_absolute() and '..' not in p.parts and p.as_posix()==name,'unsafe campaign inventory name')
            require((root/p).stat().st_size<=MAX_BYTES*2-total,'campaign byte limit')
            raw=(root/p).read_bytes();total+=len(raw);require(total<=MAX_BYTES*2,'campaign byte limit')
            require(entry=={'sha256':__import__('hashlib').sha256(raw).hexdigest(),'bytes':len(raw),
                            'status':'historical' if name in i['historical'] else 'current'},'campaign inventory hash/status mismatch')
            if entry['status']=='current':contents[name]=parse(raw)
        require(set(i['historical'])<=actual and set(i['specs'])=={'deterministic','controlled_response'},'invalid history/spec inventory')
        dataset=contents[i['dataset']];d=validate_dataset(dataset);report=unseal(contents[i['report']])
        specs={m:contents[n] for m,n in i['specs'].items()}
        require(all(s==make_spec(m,dataset['sha256']) for m,s in specs.items()),'campaign spec/dataset/pins mismatch')
        registrations=report['registrations'];require([r['id'] for r in registrations]==[e['id'] for e in d['entries']],'missing/extra/reordered registrations')
        records={};expected_files={i['dataset'],i['report'],*i['specs'].values()};seen=set()
        for e,r in zip(d['entries'],registrations):
            rid=r['record'];name='records/'+rid+'.json';record=contents[name];body=unseal(record)
            require(record['sha256']==rid and verify_record(record)['valid'],'invalid campaign record')
            identity,admission,outcome,inp,cluster=prepare(specs[e['mode']],d['sources'][e['source']])
            require(body['request']['source']==identity and body['spec']==specs[e['mode']] and body['raw_response']==e['raw_response'], 'record wrong source/spec/response')
            require((body['admission'],body['input'],body['task_outcome'],body['cluster'])==(admission,inp,outcome,cluster),'record wrong view/admission')
            require(r=={'id':e['id'],'record':rid,'duplicate_request':rid in seen,'grouping':e['grouping']},'duplicate/group registration mismatch')
            request=body['request_hash'];pointer='records/'+request+'.request.json';claim='records/'+request+'.claim'
            require(contents[pointer]=={'record':rid} and contents[claim]=={'request':body['request'],'state':'claimed; no automatic retry'},'request/record publication binding')
            expected_files|={name,pointer,claim};records[rid]=record;seen.add(rid)
        require(set(contents)==expected_files,'extra or wrong current record/file; historical must be explicitly listed')
        require(report==summarize(dataset,records,registrations),'campaign counts/denominators/fixture/budget mismatch')
        return {'valid':True,'campaign_hash':index['sha256'],'counts':report['counts'],'evaluator_calls':0,'model_requests':0,
                'scope':'complete relative to sealed dataset and inventory; hashes do not prove authorship'}
    except (OSError,ContractError,KeyError,TypeError,ValueError,AttributeError,RecursionError) as e:
        return {'valid':False,'error':str(e)[:512],'evaluator_calls':0,'model_requests':0}


def main(argv=None):
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True)
    c=s.add_parser('run');c.add_argument('dataset',type=Path);c.add_argument('--output',type=Path,required=True)
    c=s.add_parser('verify-campaign');c.add_argument('directory',type=Path)
    a=p.parse_args(argv)
    try:
        result=verify_campaign(a.directory) if a.command=='verify-campaign' else run_campaign(read_json(a.dataset),a.output)
        print(json.dumps(result));return 0 if result.get('valid',True) else 2
    except (ContractError,OSError,KeyError,TypeError,ValueError) as e:
        print(json.dumps({'error':type(e).__name__,'reason':str(e)[:512]}));return 2


if __name__=='__main__':raise SystemExit(main())
