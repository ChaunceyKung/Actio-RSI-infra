"""Campaign export from a read-only snapshot of the original Ledger."""
from pathlib import Path
from actio.contracts.json import require, seal
from actio.adapters.filesystem.common import uid, file_hash, write_json
from actio.adapters.filesystem.artifacts import publish
from actio.evidence.evaluation import source_bundle
from actio.evidence.transport_campaign import analyze, verify_campaign

def export_campaign(ledger_path,bundles,receives,destination,*,ledger_factory):
    dest=Path(destination);require(not dest.exists(),'immutable campaign destination exists');stage=dest.with_name(dest.name+'.stage-'+uid());stage.mkdir(parents=True)
    ledger=ledger_factory(ledger_path,readonly=True)
    try:snapshot=ledger.snapshot()
    finally:ledger.close()
    sources={}
    for bundle in bundles:
        source,v,capture=source_bundle(bundle);sources[capture['evidence']['run']['id']]=source
    dataset=seal({'schema':'transport-dataset.v1','campaign':snapshot['meta']['campaign'],'registrations':snapshot['registrations'],'sources':sources})
    report=seal(analyze(dataset,snapshot,receives))
    objects={'dataset':dataset,'ledger':seal(snapshot),'receives':seal(receives),'report':report}
    paths={k:publish(stage/k,v).relative_to(stage).as_posix() for k,v in objects.items()}
    files={p.relative_to(stage).as_posix():file_hash(p) for p in stage.rglob('*') if p.is_file()}
    write_json(stage/'campaign.json',seal({'schema':'transport-campaign.v1','paths':paths,'files':files}))
    result=verify_campaign(stage);require(result['valid'],str(result));stage.rename(dest);return result
