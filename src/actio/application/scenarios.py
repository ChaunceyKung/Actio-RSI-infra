"""Two fixed synthetic environments using the same product RuntimePort."""
import json

from actio.contracts.json import ContractError
from actio.contracts.json import canonical
from actio.contracts.json import digest
from actio.contracts.wire import wire
from actio.application.memory import Memory
from actio.application.memory import namespace
from actio.application.terminal import seal_terminal
from actio.evidence.bundles.terminal import INPUT_CONTRACT


def failed(store, run, error):
    """Keep the primary cause even when closing/finishing also fails."""
    store.audit(run['id'],None,'primary_failure',{'type':type(error).__name__,'reason':str(error)})
    try:
        store.finish(run['id'],run['epoch'],task='infrastructure_failure',reason=type(error).__name__+': '+str(error))
    except Exception as cleanup:
        store.audit(run['id'],None,'cleanup_failure',{'reason':str(cleanup)})
        error.add_note('cleanup/finish failed; lease retained: '+str(cleanup))


def snapshot(store,agent,environment,source=None,as_of=None):
    value=Memory(store).retrieve(namespace(agent,source or environment),agent,target=environment,as_of=as_of)
    # Lookup audit ID is not semantic input. Preserve stable frozen contents/hash.
    return {k:v for k,v in value.items() if k!='context_ref'}


def assistant(store,key,agent,short_root,*,runtime_type=None):
    runtime_type = runtime_type or store.ports.runtime
    request={'scenario':'assistant','agent':agent}
    def freeze():
        return {'input_contract':INPUT_CONTRACT,'request':request,'scenario':'assistant','agents':{agent:store.agent(agent)['spec_hash']},
            'memory':{agent:snapshot(store,agent,'assistant')},'pins':store.ports.pins(),'fixture':'read-reference-v1'}
    run,fresh=store.begin(key,freeze,request=request)
    if not fresh:
        return run
    inputs=json.loads(run['input'])
    try:
        with runtime_type(store,run,agent,short_root) as port:
            result=port.submit({'answer':'Reference recorded.','tool':TOOL,'args':{'key':'ok'},'memory':inputs['memory'][agent]})
            events=store.ports.facts(store).certify(result['op'],result['marker'])
            blocks=[b for e in events if e['type']=='tool/result' for b in e['data'].get('message',{}).get('content',[]) if b.get('type')=='tool-result']
            success=len(blocks)==1 and blocks[0].get('isError') is False and 'SYNTHETIC_SHARED_REFERENCE_17' in wire(blocks[0])
            source=store.ports.final_source(store,result)
            memory=None
            if success:
                memory=Memory(store).write(namespace(agent,'assistant'),agent,source,'PRIVATE_MEMORY_'+agent+': SYNTHETIC_SHARED_REFERENCE_17',inputs['memory'][agent]['as_of'])
            with store.tx():
                store.db.execute('INSERT INTO domain_receipt VALUES(?,?,?,?,?)',(result['op'],'success' if success else 'task_failure',source[0],source[1],wire({'memory':memory,'tool_success':success})))
            port.confirm_effect()
        seal_terminal(store,run['id'],run['epoch'],'success' if success else 'task_failure')
        return store.finish(run['id'],run['epoch'],task='success' if success else 'task_failure')
    except Exception as e:
        failed(store,run,e)
        raise


def social_manifest(store,a,b,*,as_of=None,illegal=False):
    return {'input_contract':INPUT_CONTRACT,'scenario':'social','engine':'concordia.Sequential','source':CONCORDIA,'world':[],
            'entities':{'A':a,'B':b},'agents':{n:store.agent(n)['spec_hash'] for n in (a,b)},
            'observations':{'A':'PRIVATE_ONLY_A','B':'PRIVATE_ONLY_B'},'gm_private':'GM_PRIVATE_FULL_LOG',
            'observation_policy':'own-only-v1','action_spec':{'options':['cooperate','wait'],'call_to_action':'Choose a legal action.','output_type':'choice','tag':None},
            'order':['B','A'],'seed':0,'max_steps':2,'pins':store.ports.pins(),'fixture':'cooperate-v1','illegal':illegal,
            'memory':{a:snapshot(store,a,'social','assistant',as_of),b:snapshot(store,b,'social')},
            'mid_run_restore':False}


from actio.contracts.scenarios import UNSET
TOOL='mcp__fixture__read_fixture'
CONCORDIA='b71d202750e23444ce1bf28d9f114bcd88aa41db'


def validate_replay(store, original, a, b):
    required={'scenario','engine','source','world','entities','agents','observations','gm_private','observation_policy',
              'action_spec','order','seed','max_steps','pins','fixture','illegal','memory','mid_run_restore'}
    if not required <= original.keys():
        raise ContractError('frozen replay required pin/snapshot missing')
    if original['scenario']!='social' or original['entities']!={'A':a,'B':b}:
        raise ContractError('replay manifest identity mismatch')
    if original['pins']!=store.ports.pins() or original['agents']!={n:store.agent(n)['spec_hash'] for n in (a,b)}:
        raise ContractError('frozen replay pins unavailable')
    if set(original['memory'])!={a,b}:
        raise ContractError('frozen replay memory snapshot missing')
    for value in original['memory'].values():
        fields={'namespace','as_of','items','ordering','limit','content_byte_limit','truncated','target','context_hash'}
        if set(value)!=fields:
            raise ContractError('frozen replay required memory snapshot fields missing')
        if digest({k:v for k,v in value.items() if k!='context_hash'})!=value['context_hash']:
            raise ContractError('frozen replay memory snapshot hash mismatch')


def social(store,key,a,b,short_root,*,as_of=UNSET,replay=None,illegal=UNSET,runtime_type=None):
    if a==b:
        raise ContractError('two distinct identities required')
    if replay and (as_of is not UNSET or illegal is not UNSET):
        raise ContractError('frozen replay rejects explicit illegal/memory-revision overrides')
    as_of=None if as_of is UNSET else as_of
    illegal=False if illegal is UNSET else illegal
    request={'scenario':'social','a':a,'b':b,'as_of':as_of,'replay':replay,'illegal':illegal}
    def freeze():
        if replay:
            source_run=store.run(replay)
            original=json.loads(source_run['input'])
            validate_replay(store,original,a,b)
            if digest(original)!=source_run['input_hash']:
                raise ContractError('frozen replay manifest hash mismatch')
            manifest={k:v for k,v in original.items() if k not in {'request','replay_of'}}
        else:
            manifest=social_manifest(store,a,b,as_of=as_of,illegal=illegal)
        return {**manifest,'request':request,'replay_of':replay}
    run,fresh=store.begin(key,freeze,request=request)
    if not fresh:
        return run
    manifest=json.loads(run['input'])
    try:
        outcome=run_engine(store,run,manifest,short_root,runtime_type)
        seal_terminal(store,run['id'],run['epoch'],outcome)
        return store.finish(run['id'],run['epoch'],task=outcome)
    except Exception as e:
        failed(store,run,e)
        raise


def scheduling(store,key,short_root,*,task=UNSET,script=UNSET,replay=None,runtime_type=None):
    """Validate immutable authored task before run allocation; reuse the existing Engine adapter."""
    from actio.tasks.registry import validate_task
    from actio.tasks.registry import CONTRACT
    from actio.evidence.bundles.task_evidence import validate_manifest
    if replay:
        if task is not UNSET or script is not UNSET:raise ContractError('frozen task replay rejects explicit overrides')
        original=store.run(replay);m=json.loads(original['input'])
        validate_manifest(m)
        if original['input_hash']!=digest(m) or m['pins']!=store.ports.pins():raise ContractError('frozen task replay pins/hash unavailable')
        task=m['task'];script=m['scripted_actions']
    else:
        if task is UNSET:raise ContractError('TaskSpec required before run allocation')
    t=validate_task(task)
    task=json.loads(canonical(task))
    if script is UNSET:script={'A':'propose:morning','B':'accept'}
    if type(script) is not dict or set(script)!={'A','B'} or not all(type(a) is str and 0<len(a)<=64 for a in script.values()):
        raise ContractError('bounded fixture script required')
    script=json.loads(canonical(script))
    for seat in t['seats'].values():
        agent=store.agent(seat['agent'])
        if agent['spec_hash']!=seat['spec_hash'] or agent['spec']['pins']!=store.ports.pins():raise ContractError('task identity/spec pins unavailable; create new identity')
    entities={s:t['seats'][s]['agent'] for s in ('A','B')}
    request={'scenario':'social','task_hash':task['sha256'],'a':entities['A'],'b':entities['B'],
             'script_hash':digest(script),'replay':replay}
    def freeze():
        if replay:
            value={**m,'request':request,'replay_of':replay}
        else:
            value={'input_contract':CONTRACT,'scenario':'social','task':task,'entities':entities,
                   'agents':{s['agent']:s['spec_hash'] for s in t['seats'].values()},'scripted_actions':script,
                   'memory':{a:snapshot(store,a,'social') for a in entities.values()},'pins':store.ports.pins(),
                   'engine':'concordia.Sequential','source':CONCORDIA,'order':['A','B'],'max_steps':2,'seed':0,'world':[],
                   'fixture':'scheduling-script.v1','observation_policy':'scheduling-own-plus-public.v1',
                   'gm_private':'SCHEDULING_GM_PRIVATE_AUDIT_ONLY','request':request,'replay_of':None}
        validate_manifest(value)
        return value
    run,fresh=store.begin(key,freeze,request=request)
    if not fresh:return run
    try:
        outcome=run_engine(store,run,json.loads(run['input']),short_root,runtime_type)
        seal_terminal(store,run['id'],run['epoch'],outcome)
        return store.finish(run['id'],run['epoch'],task=outcome)
    except Exception as e:
        failed(store,run,e);raise


def run_engine(store, run, manifest, short_root, runtime_type):
    return store.ports.environment(store, run, manifest, short_root,
                                   runtime_type or store.ports.runtime)
