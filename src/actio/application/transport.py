from actio.profiles.registry import metered
"""One episode with a persistent pre-send gate and injected runtime/environment."""
import json
from actio.contracts.json import ContractError, digest
from actio.contracts.transport import INPUT
from actio.profiles.registry import validate_budget_config, gateway, priced, pilot, suite, profile_for
from actio.evidence.audit.transport_contract import validate_manifest
CONCORDIA='b71d202750e23444ce1bf28d9f114bcd88aa41db'

def scheduling_transport(store,key,short_root,*,task,config,ledger_path,runtime_type=None,credential=None):
    from actio.application.scenarios import snapshot
    from actio.application.scenarios import run_engine
    from actio.application.scenarios import failed
    from actio.application.terminal import seal_terminal
    from actio.tasks.registry import validate_task
    runtime_type = runtime_type or store.ports.transport
    validate_budget_config(config);t=validate_task(task);mode=config['mode'] if gateway(config) else 'priced_rehearsal' if priced(config) else 'transport_stub'
    if t['mode']!=mode:raise ContractError('explicit transport task required')
    for seat in t['seats'].values():
        a=store.agent(seat['agent'])
        if a['spec_hash']!=seat['spec_hash'] or a['spec']['pins']!=store.ports.transport_pins(config):raise ContractError('transport identity/spec mismatch')
    ledger=store.ports.ledger(ledger_path)
    try:
        if ledger.meta['config_hash']!=digest(config):raise ContractError('config not frozen in ledger')
        campaign=ledger.meta['campaign']
        entities={s:t['seats'][s]['agent'] for s in ('A','B')}
        request={'scenario':'social','task_hash':task['sha256'],'a':entities['A'],'b':entities['B'],
                 'config_hash':digest(config),'campaign':campaign,'mode':mode}
        def freeze():
            m={'input_contract':'visible-robustness-tokenkey.v1' if config.get('schema')=='pilot-config.v10' else 'finite-candidate-tokenkey.v1' if config.get('schema')=='pilot-config.v9' else 'finite-candidate-loopback.v1' if config.get('schema')=='pilot-config.v8' else 'finite-suite-tokenkey.v1' if suite(config) else 'scheduling-tokenkey.v2' if pilot(config) else 'scheduling-tokenkey.v1' if gateway(config) else 'scheduling-priced.v1' if priced(config) else INPUT,'execution_mode':mode,'scenario':'social','task':task,'entities':entities,
               'agents':{s['agent']:s['spec_hash'] for s in t['seats'].values()},'memory':{a:snapshot(store,a,'social') for a in entities.values()},
               'pins':store.ports.transport_pins(config),'engine':'concordia.Sequential','source':CONCORDIA,'order':['A','B'],'max_steps':2,'seed':0,'world':[],
               'observation_policy':'scheduling-own-plus-public.v3' if pilot(config) else 'scheduling-own-plus-public.v2','gm_private':'SCHEDULING_GM_PRIVATE_AUDIT_ONLY',
               'request':request,'replay_of':None,'transport':{'config':config,'config_hash':digest(config),'campaign':campaign,'profile':profile_for(config)}}
            if config.get('schema') in ('pilot-config.v8','pilot-config.v9','pilot-config.v10'):
                from actio.tasks.candidate import binding
                m['transport']['scaffold_binding']=binding(m)
            validate_manifest(m);return m
        run,fresh=store.begin(key,freeze,request=request)
        if not fresh:return run
        ledger.register(run['id'],json.loads(run['input']))
    finally:ledger.close()
    try:
        def port(*args,**kwargs):return runtime_type(*args,ledger=ledger_path,**({'credential':credential} if metered(config) else {}),**kwargs)
        outcome=run_engine(store,run,json.loads(run['input']),short_root,port)
        seal_terminal(store,run['id'],run['epoch'],outcome)
        return store.finish(run['id'],run['epoch'],task=outcome)
    except Exception as e:failed(store,run,e);raise
