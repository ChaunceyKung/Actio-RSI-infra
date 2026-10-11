from actio.adapters.filesystem.credentials import scan
"""Explicit, finite TokenKey execution. Pure plan/verify paths never resolve a key."""
import json
from pathlib import Path
from actio.contracts.json import canonical
from actio.contracts.json import digest
from actio.adapters.filesystem.common import write_json
from actio.profiles.gateway_base import template
from actio.profiles.gateway_contract import validate
from actio.profiles.gateway_contract import plan
from actio.profiles.gateway_base import AUTH
from actio.contracts.json import require


def run_episode(root,cfg,ledger_path,secret,variant,runtime_type=None,*,store_factory,ledger_factory):
    from actio.application.transport import scheduling_transport
    from actio.tasks.registry import task_card
    from actio.application.export import export_bundle
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    s=store_factory(root/'ledger.sqlite',create=True)
    try:
        for name in ('ACTOR_A','ACTOR_B'):s.agent(name,s.ports.transport_spec(name,cfg))
        bindings={seat:{'agent':name,'spec_hash':s.agent(name)['spec_hash']} for seat,name in [('A','ACTOR_A'),('B','ACTOR_B')]}
        task=task_card(variant,bindings,cfg['mode']);error=None
        try:scheduling_transport(s,'episode',root,task=task,config=cfg,ledger_path=ledger_path,credential=secret,**({'runtime_type':runtime_type} if runtime_type else {}))
        except Exception as e:error={'type':type(e).__name__,'reason':str(e).replace(secret,'[credential omitted]')}
        run=s.run('episode');bundle=export_bundle(s.path,'episode',root/'bundle',store_factory=store_factory)
        return {'run':run,'error':error,'bundle':bundle,'workers':s.rows('SELECT * FROM worker')}
    finally:s.close()

def execute(c,root,secret,*,store_factory,ledger_factory,operation_authorization,runtime_type=None,receives=None):
    from actio.evidence.accounting import verify_snapshot
    from actio.application.transport_export import export_campaign
    validate(c);require(operation_authorization==AUTH,'independent explicit C2B1 operator instruction required')
    require(c['authority'] is not None,'execution authority not allocated')
    root=Path(root);require(not root.exists(),'new batch only; cannot replay prior execution')
    root.mkdir(parents=True)
    write_json(root/'execution-plan.json',plan(c))
    l=ledger_factory(root/'budget.sqlite',config=c);l.close();results=[];bundles=[]
    for i,variant in enumerate(c['plan']):
        ep=root/('episode-'+str(i));r=run_episode(ep,c,root/'budget.sqlite',secret,variant,runtime_type,store_factory=store_factory,ledger_factory=ledger_factory)
        results.append(r);bundles.append(ep/'bundle')
        if r['error'] or r['bundle']['verification']['scenario_completeness']!='complete':break
    ledger=ledger_factory(root/'budget.sqlite',readonly=True)
    try:snap=ledger.snapshot();verify_snapshot(snap)
    finally:ledger.close()
    campaign=export_campaign(root/'budget.sqlite',bundles,receives,root/'campaign',ledger_factory=ledger_factory)
    result={'schema':'tokenkey-execution.v1','contract_hash':digest(c),'root':str(root),'episodes':results,
            'planned_episodes':len(c['plan']),'not_run_episodes':len(c['plan'])-len(results),'campaign':campaign,
            'source_hashes':c['implementation'],'credential_scan':scan(root,secret),'account_settings_changed':False}
    write_json(root/'result.json',result);return result
