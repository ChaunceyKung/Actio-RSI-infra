from actio.adapters.filesystem.publication import create
from actio.adapters.filesystem.publication import now
"""Finite C2B2 controller. One immutable child ledger per preregistered episode."""
import json
from pathlib import Path
import time
from actio.contracts.json import canonical
from actio.contracts.json import ContractError
from actio.adapters.filesystem.common import uid
from actio.contracts.json import seal
from actio.contracts.json import unseal
from actio.contracts.json import require
from actio.profiles.pilot_contract import validate_preregistration
from actio.profiles.pilot_contract import config
from actio.profiles.pilot_contract import AUTH


def run_unit(root,cfg,secret,*,store_factory,ledger_factory,receives=None,runtime_type=None):
    from actio.application.transport import scheduling_transport
    from actio.tasks.scheduling_v2 import card
    if cfg.get('schema')=='pilot-config.v7':
        from actio.tasks.finite import card
    from actio.application.export import export_bundle
    from actio.application.transport_export import export_campaign
    root=Path(root);root.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    create(root/'config.json',cfg)
    ledger=ledger_factory(root/'budget.sqlite',config=cfg);ledger.close()
    s=store_factory(root/'domain.sqlite',create=True);error=None
    try:
        for name in ('ACTOR_A','ACTOR_B'):s.agent(name,s.ports.transport_spec(name,cfg))
        bindings={seat:{'agent':name,'spec_hash':s.agent(name)['spec_hash']} for seat,name in [('A','ACTOR_A'),('B','ACTOR_B')]}
        if cfg.get('schema') in ('pilot-config.v8','pilot-config.v9','pilot-config.v10'):
            if cfg['schema']=='pilot-config.v10':
                from actio.tasks.robustness import card
            elif cfg['schema']=='pilot-config.v9':
                from actio.tasks.evaluation import card
            else:
                from actio.tasks.candidate import card
            task=card(cfg['plan'][0],bindings,cfg['mode'],cfg['scaffold'])
        else:task=card(cfg['plan'][0],bindings,cfg['mode'])
        try:
            scheduling_transport(s,'episode',root,task=task,config=cfg,ledger_path=root/'budget.sqlite',credential=secret,
                                 **({'runtime_type':runtime_type} if runtime_type else {}))
        except Exception as e:error={'type':type(e).__name__,'reason':str(e).replace(secret,'[credential omitted]')[:1024]}
        bundle=export_bundle(s.path,'episode',root/'bundle',store_factory=store_factory)
        workers=s.rows('SELECT * FROM worker')
        require(all(w['state']=='reaped' and json.loads(w['report']).get('after',json.loads(w['report']))['active']==0 for w in workers),'Worker cleanup incomplete')
    finally:s.close()
    ledger=ledger_factory(root/'budget.sqlite',readonly=True)
    try:snapshot=ledger.snapshot()
    finally:ledger.close()
    # A shared local service can cover multiple children; bind only this ledger's receives.
    selected=None if receives is None else [r for r in receives if r['attempt'] in {a['id'] for a in snapshot['attempts']}]
    campaign=export_campaign(root/'budget.sqlite',[root/'bundle'],selected,root/'campaign',ledger_factory=ledger_factory)
    index=unseal(json.loads((root/'campaign/campaign.json').read_bytes()))
    dataset=json.loads((root/'campaign'/index['paths']['dataset']).read_bytes())
    result={'error':error,'bundle_verification':bundle['verification'],'campaign':campaign,'workers':workers}
    create(root/'result.json',result)
    entry={'unit':cfg['experiment']['unit'],'evidence':{'dataset':dataset,'ledger':snapshot,'receives':selected},
           'reason':canonical(error) if error else None,'episode_ms':round((time.monotonic()-started)*1000)}
    return entry,result





def execute(root,pre,secret,*,store_factory,ledger_factory,freeze=None,endpoint=None,authority_root,operation_authorization,receives=None,runtime_type=None,contract=None):
    from actio.adapters.filesystem.credentials import scan
    from actio.evidence.pilot_measurement import analyze_pilot
    if contract:
        from actio.evidence.suite_measurement import analyze_pilot
        if contract.CONFIG in ('pilot-config.v8','pilot-config.v9','pilot-config.v10'):
            from actio.evidence.campaign_registry import analyzer
            analyze_pilot=analyzer(contract.CONFIG)
    p=(contract.validate_preregistration if contract else validate_preregistration)(pre);require(operation_authorization==AUTH,'explicit C2B2 operator instruction required')
    if contract and contract.CONFIG=='pilot-config.v8':require(endpoint is not None,'candidate campaign loopback only')
    live=endpoint is None;root=Path(root).resolve();require(not root.exists(),'new experiment root required')
    require(not live or freeze and freeze['preregistration_hash']==pre['sha256'] and freeze['commit']==freeze['remote_main']==freeze['remote_branch'],'published preregistration required')
    authority=Path(authority_root).resolve();authority.mkdir(parents=True,exist_ok=True)
    # One persistent claim per preregistration across arbitrary output roots.
    create(authority/(pre['sha256']+'.json'),{'preregistration_hash':pre['sha256'],'root':str(root),'first_intent_utc':now()})
    root.mkdir(parents=True);create(root/'preregistration.json',pre)
    f={**freeze,'first_intent_utc':now()} if freeze else None
    if f:create(root/'freeze.json',f)
    entries=[{'unit':u,'evidence':None,'reason':'not_started','episode_ms':None} for u in p['units']]
    state='stopped';reason=None
    create(root/'intent.json',{'preregistration_hash':pre['sha256'],'freeze':f,'entries':entries})
    try:
        for i,u in enumerate(p['units']):
            cfg=(contract.config if contract else config)(u['id'],authority={'id':uid(),'root':str(authority)},**({'mode':contract.REHEARSAL if contract else 'tokenkey_pilot_rehearsal','endpoint':endpoint} if not live else {}))
            entry,result=run_unit(root/u['id'],cfg,secret,store_factory=store_factory,ledger_factory=ledger_factory,receives=receives,runtime_type=runtime_type);entries[i]=entry
            if contract and contract.CONFIG in ('pilot-config.v9','pilot-config.v10'):
                create(root/('entry-'+u['id']+'.json'),entry)
            snapshot=seal({'schema':contract.EVIDENCE if contract else 'pilot-evidence.v1','preregistration':pre,'freeze':f,'entries':entries,'phase_state':'first-block' if i==1 else 'stopped'})
            report=analyze_pilot(snapshot)
            create(root/('checkpoint-'+u['id']+'.json'),{'observed_through':u['id'],'counts':report['counts'],'error':result['error']})
            if result['error'] or any(s['protocol_error'] for s in report['rows'][i]['seats']) or contract and contract.CONFIG in ('pilot-config.v9','pilot-config.v10') and not report['rows'][i]['execution_resolved']:
                reason='infrastructure stop at '+u['id'];break
            if i==1:create(root/'first-pair-check.json',{'basis':'integrity/cleanup only; behavioral scores not consulted','passed':True,'continues_same_preregistration':True})
        else:state='completed'
    except Exception as e:
        reason=type(e).__name__+': '+str(e).replace(secret,'[credential omitted]')[:1024]
        create(root/'controller-failure.json',{'reason':reason,'current_unit':u['id'],'raw_directory_retained':str(root/u['id'])})
        if not contract or contract.CONFIG not in ('pilot-config.v9','pilot-config.v10'):raise
    finally:
        for e in entries:
            if e['evidence'] is None:e['reason']=reason or 'not_started'
        evidence=seal({'schema':contract.EVIDENCE if contract else 'pilot-evidence.v1','preregistration':pre,'freeze':f,'entries':entries,'phase_state':state})
        create(root/'pilot.json',evidence)
        if contract and contract.CONFIG in ('pilot-config.v9','pilot-config.v10'):
            # Persist raw accounting before any verifier can fail. This inventory
            # is a projection, not permission to reclaim or retry a child.
            inventory=[]
            for path in sorted(root.glob('ep-*/budget.sqlite')):
                ledger=ledger_factory(path,readonly=True)
                try:inventory.append({'unit':path.parent.name,'ledger':ledger.snapshot()})
                finally:ledger.close()
            create(root/'raw-attempt-inventory.json',{'ledgers':inventory,'full_unrun_suffix':[e['unit']['id'] for e in entries if e['evidence'] is None]})
            try:
                report=analyze_pilot(evidence);create(root/'report.json',report)
            except Exception as error:
                report={'valid':False,'engineering':'INCOMPLETE','candidate_decision':'infrastructure_failure',
                    'reason':type(error).__name__+': '+str(error).replace(secret,'[credential omitted]')[:512],
                    'raw_inventory':'raw-attempt-inventory.json','evidence':'pilot.json','full_controller_recovery':'unsupported'}
                create(root/'verification-failure.json',report)
            finally:create(root/'credential-scan.json',scan(root,secret))
        else:
            report=analyze_pilot(evidence);create(root/'report.json',report)
            create(root/'credential-scan.json',scan(root,secret))
    return report
