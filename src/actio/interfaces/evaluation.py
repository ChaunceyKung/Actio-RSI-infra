from actio.evidence.bundles.eval_contract import LIMITS
"""Evaluation CLI and local worker assembly."""
import argparse
import json
from pathlib import Path
from actio.contracts.json import ContractError, canonical, digest, seal, unseal, require, parse
from actio.evidence.bundles.eval_contract import make_spec
from actio.evidence.bundles.evaluation import read_json, source_bundle, verify_record
from actio.adapters.filesystem.artifacts import publish
from actio.application import evaluation as use_cases

def evaluate(*args, **kwargs):
    return use_cases.evaluate(*args, worker=execute_worker, **kwargs)

def campaign(*args, **kwargs):
    return use_cases.campaign(*args, worker=execute_worker, **kwargs)

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




def execute_worker(payload, timeout):
    from actio.adapters.runtime.evaluator import execute_worker as execute
    return execute(payload, timeout)

if __name__=='__main__':raise SystemExit(main())
