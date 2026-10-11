from actio.evidence.campaign import source_group, validate_dataset, summarize, verify_campaign, GROUP_RULE
"""Task-family campaign execution and independent, read-only completeness verification."""
import json
import os
from pathlib import Path
import uuid

from actio.contracts.json import ContractError
from actio.contracts.json import canonical
from actio.contracts.json import digest
from actio.adapters.filesystem.common import file_hash
from actio.evidence.eval_contract import make_spec
from actio.contracts.json import seal
from actio.contracts.json import unseal
from actio.evidence.evaluation import read_json
from actio.adapters.filesystem.artifacts import publish
from actio.evidence.evaluation import prepare
from actio.application.evaluation import evaluate
from actio.evidence.evaluation import verify_record
from actio.contracts.json import require
from actio.evidence.verify import verify_bundle
from actio.evidence.verify import MAX_BYTES
from actio.contracts.json import parse

GROUP_RULE={'version':'family-group.v1','seed':0,'assignment':'all observed scheduling family variants/seats/repeats/replays remain development',
            'groups':['development','calibration_pending'],'independent_units':0,'holdout':False}











def run_campaign(dataset,destination,*,worker):
    d=validate_dataset(dataset);dest=Path(destination).absolute()
    require(not dest.exists(),'campaign destination exists; immutable publication requires new destination')
    dest.parent.mkdir(parents=True,exist_ok=True);stage=dest.with_name('.'+dest.name+'.stage-'+uuid.uuid4().hex);stage.mkdir()
    try:
        dataset_path=publish(stage/'datasets',dataset);specs={m:make_spec(m,dataset['sha256']) for m in ('deterministic','controlled_response')}
        spec_paths={m:publish(stage/'specs',s) for m,s in specs.items()};records={};registrations=[];seen=set()
        for e in d['entries']:
            record,reused=evaluate(specs[e['mode']],d['sources'][e['source']],stage/'records',e['raw_response'],worker=worker)
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
