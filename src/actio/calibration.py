"""Blinded, content-bound annotation handoff. No labels or consensus are invented."""
import argparse
import json
from pathlib import Path

from actio.contracts.json import ContractError, canonical, digest
from actio.contracts.json import seal, unseal
from .evaluation import read_json,verify_record
from .campaign import GROUP_RULE,source_group
from actio.contracts.json import require


def annotation_case(record):
    require(verify_record(record)['valid'],'invalid annotation evidence record')
    r=unseal(record);require(r['admission']['status']=='admitted' and r['input'] is not None,'annotation requires admitted complete evidence')
    inp=unseal(r['input']);v=inp['view']
    require(v.get('scenario')=='scheduling-input.v1' and len(v['actions'])==2,'annotation requires two actual task actions')
    require(all(a['action'] in v['action_specs'][v['aliases'][a['alias']]['seat']]['options'] for a in v['actions']),'annotation requires legal actual actions')
    names={a:'seat_'+str(i+1) for i,a in enumerate(sorted(v['aliases']))}
    public={'schema':'blinded-scheduling.v1','public':v['public'],
            'seats':{names[a]:{'role':v['aliases'][a]['role'],'goal':v['goals'][a],
                              'constraints':v['constraints'][a],'initial_relationship':v['relationships'][a],
                              'action_spec':v['action_specs'][v['aliases'][a]['seat']]} for a in names},
            'actions':[{'seat':names[a['alias']],'action':a['action']} for a in v['actions']],
            'rubric':v['rubric'],'cannot_judge':'Give an explicit reason when evidence cannot support a dimension.'}
    mapping={names[a]:v['aliases'][a] for a in names}
    binding={'task':v['task_hash'],'episode':digest(inp['run']),'trace':digest(v['actions']),
             'rubric':digest(v['rubric']),'view':digest(public),'alias':digest(mapping),
             'group':digest({'rule':GROUP_RULE,'membership':source_group(r['source'])})}
    return {'id':digest(binding),'binding':binding,'view':public}, {'aliases':mapping,'episode':inp['run'],
            'evaluation_input':inp['view_hash'],'source':r['request']['source'],'grouping':source_group(r['source'])}


def export_annotations(records,destination):
    cases={};private={}
    for record in records:
        case,mapping=annotation_case(record);cases[case['id']]=case;private[case['id']]=mapping
    require(bool(cases),'empty annotation queue')
    registry=seal({'schema':'annotation-registry.v1','cases':cases,'private':private,
                   'human_calibration':'BLOCKED','real_labels':0})
    root=Path(destination);root.mkdir(parents=True,exist_ok=False)
    (root/'internal.json').write_text(canonical(registry),encoding='utf8')
    (root/'cases.jsonl').write_text(''.join(canonical(c)+'\n' for c in cases.values()),encoding='utf8')
    templates=[{'case':c['id'],'binding':c['binding'],'rater':None,'provenance':None,
                'labels':{s:{d:{'status':'unlabelled','score':None,'reason':None} for d in ('goal','relationship')}
                          for s in c['view']['seats']}} for c in cases.values()]
    (root/'blank-labels.jsonl').write_text(''.join(canonical(c)+'\n' for c in templates),encoding='utf8')
    lines=['# Blinded scheduling annotation queue','',
           'No real labels yet. Judge each dimension independently; symbolic actions may be insufficient for relationship change.',
           'Use scored with an integer and reason, or cannot_judge with null score and a reason. Do not infer missing behavior.','']
    for c in cases.values():
        lines.extend(['## Case '+c['id'],'','Actual blinded view SHA256: `'+c['binding']['view']+'`','',
                      '```json',json.dumps(c['view'],ensure_ascii=False,indent=2),'```',''])
    (root/'annotation.md').write_text('\n'.join(lines),encoding='utf8')
    return {'cases':len(cases),'registry_hash':registry['sha256'],'human_calibration':'BLOCKED','real_labels':0}


def validate_registry(registry):
    b=unseal(registry);require(b['schema']=='annotation-registry.v1','registry schema')
    require(set(b['cases'])==set(b['private']) and bool(b['cases']),'registry case mapping')
    for key,c in b['cases'].items():
        p=b['private'][key];binding=c['binding']
        require(c['id']==key==digest(binding) and binding['view']==digest(c['view']) and
                binding['rubric']==digest(c['view']['rubric']) and binding['alias']==digest(p['aliases']) and
                binding['episode']==digest(p['episode']) and
                binding['group']==digest({'rule':GROUP_RULE,'membership':p['grouping']}),'registry content binding')
        require(set(c['view']['seats'])==set(p['aliases']),'registry seats')
    return b


def import_labels(registry,rows,raters):
    """Validation report retains disagreement; does not promote labels to gold or calibrate."""
    b=validate_registry(registry);require(len(raters)>=1 and len(set(raters))==len(raters) and all(type(x) is str and x for x in raters),'explicit unique raters required')
    errors=[];accepted={};duplicates=[]
    for i,row in enumerate(rows):
        try:
            require(set(row)=={'case','binding','rater','provenance','labels'},'label row fields')
            c=b['cases'][row['case']];require(row['binding']==c['binding'],'task/episode/trace/rubric/view/alias/group binding mismatch')
            require(row['rater'] in raters,'unknown or missing rater')
            require(row['provenance'] in ('human','synthetic_label_fixture'),'explicit annotation provenance required')
            require(set(row['labels'])==set(c['view']['seats']),'wrong or missing seat')
            for seat,dimensions in row['labels'].items():
                require(set(dimensions)=={'goal','relationship'},'missing or extra dimension')
                for d,label in dimensions.items():
                    require(set(label)=={'status','score','reason'},'label fields')
                    require(type(label['reason']) is str and 0<len(label['reason'].strip())<=2048,'missing bounded reasoning')
                    low,high=c['view']['rubric'][d]['range']
                    require((label['status']=='scored' and type(label['score']) is int and low<=label['score']<=high) or
                            (label['status']=='cannot_judge' and label['score'] is None),'missing/invalid score or cannot_judge')
            key=(row['case'],row['rater'])
            if key in accepted:
                duplicates.append({'case':key[0],'rater':key[1],'conflict':accepted[key]!=row})
                raise ContractError('duplicate/conflicting label; no overwrite')
            accepted[key]=row
        except (ContractError,KeyError,TypeError,ValueError) as e:errors.append({'row':i,'reason':str(e)[:256]})
    missing=[{'case':c,'rater':r} for c in b['cases'] for r in raters if (c,r) not in accepted]
    disagreement=[]
    for cid,c in b['cases'].items():
        for seat in c['view']['seats']:
            for d in ('goal','relationship'):
                values={r:accepted[(cid,r)]['labels'][seat][d] for r in raters if (cid,r) in accepted}
                if len({(v['status'],v['score']) for v in values.values()})>1:
                    disagreement.append({'case':cid,'seat':seat,'dimension':d,'ratings':values})
    return {'schema':'annotation-import.v1','valid':not errors and not missing,'errors':errors,'missing':missing,
            'duplicates':duplicates,'disagreements':disagreement,'accepted':list(accepted.values()),
            'provenance_counts':{p:sum(r['provenance']==p for r in accepted.values()) for p in ('human','synthetic_label_fixture')},
            'human_calibration':'BLOCKED','reason':'import validation does not establish calibration or adjudicated gold'}


def main(argv=None):
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True)
    e=s.add_parser('export');e.add_argument('records',nargs='+',type=Path);e.add_argument('--output',type=Path,required=True)
    e=s.add_parser('import-labels');e.add_argument('registry',type=Path);e.add_argument('labels',type=Path);e.add_argument('--raters',nargs='+',required=True)
    a=p.parse_args(argv)
    try:
        result=export_annotations([read_json(x) for x in a.records],a.output) if a.command=='export' else import_labels(read_json(a.registry),[json.loads(x) for x in a.labels.read_text(encoding='utf8').splitlines() if x.strip()],a.raters)
        print(json.dumps(result));return 0 if result.get('valid',True) else 2
    except (ContractError,OSError,KeyError,TypeError,ValueError) as e:
        print(json.dumps({'valid':False,'reason':str(e)[:512]}));return 2


if __name__=='__main__':raise SystemExit(main())
