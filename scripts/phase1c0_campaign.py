"""Freeze a small registry of synthetic engineering fixtures, then use the public campaign CLI."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from actio.common import canonical,digest,write_json
from actio.eval_contract import make_spec,seal
from actio.evaluation import source_bundle,prepare,publish,read_json
from actio.verify import sha

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from test_input_binding import SAMPLES,mutate_bundle,frozen_edit
from test_evaluation import synthetic,response


def main():
    runtime=read_json(sys.argv[1]);assert runtime['status']=='PASS'
    destination=ROOT/'docs/validation/phase1c0/campaign'
    sources={};entries=[]
    def add(name,source,mode='deterministic',raw=None,provenance='Phase 1B.1 committed synthetic runtime bundle'):
        source_id=digest(source);sources[source_id]=source
        identity=prepare(make_spec(mode,digest('pending')),source)[0]
        entries.append({'id':name,'source':source_id,'mode':mode,'raw_response':raw,
                        'aliases':identity.get('aliases',{}),'provenance':provenance})
    originals={k:source_bundle(SAMPLES/k)[0] for k in ('assistant','social','rejected','partial','unknown')}
    for name,source in originals.items():add(name,source)
    add('identical-social-package',originals['social'])
    changed=copy.deepcopy(originals['social']);meta=json.loads(changed['files']['export.json']);meta['exported_at']='synthetic alternate export metadata'
    changed['files']['export.json']=canonical(meta);m=json.loads(changed['files']['manifest.json']);raw=changed['files']['export.json'].encode()
    next(e for e in m['files'] if e['path']=='export.json').update(bytes=len(raw),sha256=sha(raw))
    changed['files']['manifest.json']=canonical(m);add('same-run-alternate-export',changed)
    add('historical-social-missing-goals',originals['social'],'controlled_response',canonical(response()))
    with tempfile.TemporaryDirectory() as tmp:
        for name,change in [('observation',lambda m:m['observations'].update(A='REHASHED_CHANGE')),
                            ('action-spec',lambda m:m['action_spec'].update(call_to_action='REHASHED_CHANGE'))]:
            path=Path(tmp)/name;mutate_bundle(path,lambda d:frozen_edit(d,change))
            add('contradiction-'+name,source_bundle(path)[0],provenance='controlled rehashed frozen-manifest contradiction; native raw unchanged')
    syn={'kind':'synthetic','input':synthetic()}
    add('controlled-valid',syn,'controlled_response',canonical(response()),'separate sealed synthetic goals/initial relationships; preset scores have no measurement validity')
    add('controlled-invalid-null',syn,'controlled_response','{"scores":null}','same synthetic input; deliberate invalid response retained')
    for name in ('c0-social','c0-replay'):
        add(name,source_bundle(runtime['bundles'][name])[0],provenance='new synthetic identities, actual DSH/Concordia run; replay shares frozen start cluster')
    dataset=seal({'schema':'fixture-campaign.v1','split':'synthetic-engineering-fixture','independent_units':0,'sources':sources,'entries':entries})
    path=publish(destination/'datasets',dataset)
    examples=ROOT/'docs/validation/phase1c0/examples';examples.mkdir(exist_ok=True)
    publish(examples,synthetic());response_path=examples/'controlled-response.json';response_bytes=canonical(response()).encode()
    if response_path.exists():assert response_path.read_bytes()==response_bytes
    else:
        with response_path.open('xb') as f:f.write(response_bytes)
    command=[sys.executable,'-I','-m','actio.evaluation','campaign',str(path),'--output',str(destination)]
    result=subprocess.run(command,capture_output=True,text=True,timeout=120)
    log={'command':command,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'mode':'OFFLINE_FIXTURE_CAMPAIGN','model_requests':0}
    publish(ROOT/'docs/validation/phase1c0/evidence',seal(log))
    print(result.stdout);print(result.stderr)
    if result.returncode:raise SystemExit(result.returncode)
    report=read_json(json.loads(result.stdout)['report'])['body']
    assert report['counts']['registered']==14 and report['counts']['unique_measurements']==12, report['counts']
    replay=[r for r in report['registrations'] if r['id'] in ('c0-social','c0-replay')]
    assert replay[0]['cluster']==replay[1]['cluster'] and replay[0]['record']!=replay[1]['record']
    assert report['model_requests']==0


if __name__=='__main__':main()
