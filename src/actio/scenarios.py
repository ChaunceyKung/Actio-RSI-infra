"""Two fixed synthetic environments using the same product RuntimePort."""
import json
import sys
from pathlib import Path

from .common import ContractError,canonical,digest,file_hash
from .facts import Facts,wire
from .memory import Memory,namespace
from .runtime import RuntimePort,TOOL,CONCORDIA,PACKAGE,pins
from .terminal import seal_terminal, INPUT_CONTRACT


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


def final_source(store, result):
    events=Facts(store).certify(result['op'],result['marker'])
    receipt=result['marker']['receipt']
    start=max(e['seq'] for e in events if e['type']=='agent/inbox/spliced' and any(m.get('id')==receipt for m in e['data'].get('inserted',[])))
    candidates=[e for e in events if e['type']=='assistant/message' and start<e['seq']<=result['marker']['terminal']['seq']]
    if not candidates:
        raise ContractError('no final assistant source')
    return result['stream'],candidates[-1]['seq'],'assistant.final'


def assistant(store,key,agent,short_root,*,runtime_type=RuntimePort):
    request={'scenario':'assistant','agent':agent}
    def freeze():
        return {'input_contract':INPUT_CONTRACT,'request':request,'scenario':'assistant','agents':{agent:store.agent(agent)['spec_hash']},
            'memory':{agent:snapshot(store,agent,'assistant')},'pins':pins(),'fixture':'read-reference-v1'}
    run,fresh=store.begin(key,freeze,request=request)
    if not fresh:
        return run
    inputs=json.loads(run['input'])
    try:
        with runtime_type(store,run,agent,short_root) as port:
            result=port.submit({'answer':'Reference recorded.','tool':TOOL,'args':{'key':'ok'},'memory':inputs['memory'][agent]})
            events=Facts(store).certify(result['op'],result['marker'])
            blocks=[b for e in events if e['type']=='tool/result' for b in e['data'].get('message',{}).get('content',[]) if b.get('type')=='tool-result']
            success=len(blocks)==1 and blocks[0].get('isError') is False and 'SYNTHETIC_SHARED_REFERENCE_17' in wire(blocks[0])
            source=final_source(store,result)
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
            'order':['B','A'],'seed':0,'max_steps':2,'pins':pins(),'fixture':'cooperate-v1','illegal':illegal,
            'memory':{a:snapshot(store,a,'social','assistant',as_of),b:snapshot(store,b,'social')},
            'mid_run_restore':False}


UNSET = object()


def validate_replay(store, original, a, b):
    required={'scenario','engine','source','world','entities','agents','observations','gm_private','observation_policy',
              'action_spec','order','seed','max_steps','pins','fixture','illegal','memory','mid_run_restore'}
    if not required <= original.keys():
        raise ContractError('frozen replay required pin/snapshot missing')
    if original['scenario']!='social' or original['entities']!={'A':a,'B':b}:
        raise ContractError('replay manifest identity mismatch')
    if original['pins']!=pins() or original['agents']!={n:store.agent(n)['spec_hash'] for n in (a,b)}:
        raise ContractError('frozen replay pins unavailable')
    if set(original['memory'])!={a,b}:
        raise ContractError('frozen replay memory snapshot missing')
    for value in original['memory'].values():
        fields={'namespace','as_of','items','ordering','limit','content_byte_limit','truncated','target','context_hash'}
        if set(value)!=fields:
            raise ContractError('frozen replay required memory snapshot fields missing')
        if digest({k:v for k,v in value.items() if k!='context_hash'})!=value['context_hash']:
            raise ContractError('frozen replay memory snapshot hash mismatch')


def social(store,key,a,b,short_root,*,as_of=UNSET,replay=None,illegal=UNSET,runtime_type=RuntimePort):
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


def run_engine(store,run,manifest,short_root,runtime_type):
    from .task_contract import CONTRACT,actor_observation,resolved_text,task_result
    scheduling=manifest.get('input_contract')==CONTRACT
    import concordia
    pin=json.loads((PACKAGE/'pins/concordia.json').read_text(encoding='utf-8'))
    base=Path(concordia.__file__).parent.parent
    for name,h in pin['files'].items():
        if name!='LICENSE' and file_hash(base/name)!=h:
            raise ContractError('Concordia source changed: '+name)
    from concordia.environment.engines.sequential import Sequential,EVENT_TAG,PUTATIVE_EVENT_TAG
    from concordia.environment import engine as engine_lib
    from concordia.environment.step_controller import StepController
    from concordia.typing import entity as entity_lib

    class IllegalAction(ValueError):
        pass

    class External(entity_lib.Entity):
        def __init__(self,label):
            self.label=label; self.observations=[]; self.port=None; self.result=None
        @property
        def name(self):
            return self.label
        def observe(self,observation):
            self.observations.append(observation)
        def act(self,action_spec):
            who=manifest['entities'][self.label]
            self.port=runtime_type(store,run,who,short_root)
            self.port.start()
            answer=manifest['scripted_actions'][self.label] if scheduling else ('INVALID' if manifest['illegal'] and self.label=='B' else 'cooperate')
            self.result=self.port.submit({'answer':answer,
                'observations':self.observations,'memory':manifest['memory'][who],'action_spec':action_spec.to_dict()})
            try:
                action_spec.validate(self.result['answer'])
            except ValueError:
                source=final_source(store,self.result)
                with store.tx():
                    store.db.execute('INSERT INTO domain_receipt VALUES(?,?,?,?,?)',(self.result['op'],'task_failure',source[0],source[1],wire({'rejected':'illegal_action','world_unchanged':True})))
                self.port.confirm_effect()
                self.port.close()
                raise IllegalAction('explicit illegal action rejected before world mutation')
            return self.result['answer']

    entities={label:External(label) for label in ('A','B')}
    class GM(entity_lib.Entity):
        def __init__(self):
            self.world=[]; self.pending=None; self.acting=None; self.resolved=None;self.actions=[]
        @property
        def name(self):
            return 'FixtureGM'
        def observe(self,observation):
            if observation.startswith(PUTATIVE_EVENT_TAG):
                self.pending=observation
            if observation.startswith(EVENT_TAG):
                acting=entities[self.acting]
                source=final_source(store,acting.result)
                with store.tx():
                    store.db.execute('INSERT INTO world VALUES(?,?,?,?,?,?,?)',(run['id'],len(self.world),manifest['entities'][self.acting],acting.result['answer'],observation,source[0],source[1]))
                    result=task_result(manifest['task']['body'],self.actions+[acting.result['answer']]) if scheduling else None
                    store.db.execute('INSERT INTO domain_receipt VALUES(?,?,?,?,?)',(acting.result['op'],'task_failure' if result and result['status']=='not_agreed' else 'success',source[0],source[1],wire({'resolved':observation,'producer':'GM.observe(EVENT)','putative':self.pending,**({'task_result':result} if scheduling else {})})))
                self.world.append(observation)
                self.actions.append(acting.result['answer'])
                acting.port.confirm_effect()
                acting.port.close()
        def act(self,action_spec):
            # MAKE_OBSERVATION is called by Engine's threads; it only reads immutable data.
            match action_spec.output_type:
                case entity_lib.OutputType.TERMINATE:
                    return 'Yes' if len(self.world)>=2 else 'No'
                case entity_lib.OutputType.NEXT_GAME_MASTER:
                    return self.name
                case entity_lib.OutputType.NEXT_ACTING:
                    self.acting=manifest['order'][len(self.world)]
                    return self.acting
                case entity_lib.OutputType.NEXT_ACTION_SPEC:
                    if scheduling:
                        return engine_lib.action_spec_to_string(entity_lib.action_spec_from_dict(manifest['task']['body']['action_specs'][self.acting]))
                    return engine_lib.action_spec_to_string(entity_lib.ActionSpec(call_to_action=manifest['action_spec']['call_to_action'],
                        output_type=entity_lib.OutputType.CHOICE,options=manifest['action_spec']['options']))
                case entity_lib.OutputType.MAKE_OBSERVATION:
                    label=action_spec.call_to_action.removeprefix('OBSERVE:')
                    if scheduling:return actor_observation(manifest,label,self.actions)
                    return manifest['observations'][label]
                case entity_lib.OutputType.RESOLVE:
                    self.resolved=resolved_text(manifest['task']['body'],self.actions+[entities[self.acting].result['answer']]) if scheduling else f'resolved[{len(self.world)}]: {self.pending}'
                    store.audit(run['id'],entities[self.acting].result['op'],'gm_resolve',{'intent':self.pending,'resolved':self.resolved,'source':'GM.act(RESOLVE)'})
                    return self.resolved
                case _:
                    raise ContractError('unsupported GM action spec')
    gm=GM()
    engine=Sequential(call_to_make_observation='OBSERVE:{name}')
    try:
        try:
            engine.run_loop(game_masters=[gm],entities=list(entities.values()),max_steps=2,
                step_controller=StepController(start_paused=False),step_callback=lambda step:store.audit(run['id'],None,'engine_step',{'acting_entity':step.acting_entity}))
        except IllegalAction:
            if scheduling:return 'task_failure'
            if not manifest['illegal'] or gm.world or gm.resolved:
                raise
            return 'task_failure'
        if len(gm.world)!=2:
            raise ContractError('Engine did not resolve both turns')
        return ('success' if task_result(manifest['task']['body'],gm.actions)['status']=='agreed' else 'task_failure') if scheduling else 'success'
    finally:
        primary=sys.exception()
        cleanup_errors=[]
        for entity in entities.values():
            if entity.port:
                try:
                    entity.port.close(force=True)
                except Exception as cleanup:
                    cleanup_errors.append(cleanup)
                    store.audit(run['id'],None,'cleanup_failure',{'reason':str(cleanup),'entity':entity.label})
        if cleanup_errors:
            if primary is not None:
                primary.add_note('cleanup failure: '+str(cleanup_errors[0]))
            else:
                raise cleanup_errors[0]


def scheduling(store,key,short_root,*,task=UNSET,script=UNSET,replay=None,runtime_type=RuntimePort):
    """Validate immutable authored task before run allocation; reuse the existing Engine adapter."""
    from .task_contract import validate_task,validate_manifest,CONTRACT
    if replay:
        if task is not UNSET or script is not UNSET:raise ContractError('frozen task replay rejects explicit overrides')
        original=store.run(replay);m=json.loads(original['input'])
        validate_manifest(m)
        if original['input_hash']!=digest(m) or m['pins']!=pins():raise ContractError('frozen task replay pins/hash unavailable')
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
        if agent['spec_hash']!=seat['spec_hash'] or agent['spec']['pins']!=pins():raise ContractError('task identity/spec pins unavailable; create new identity')
    entities={s:t['seats'][s]['agent'] for s in ('A','B')}
    request={'scenario':'social','task_hash':task['sha256'],'a':entities['A'],'b':entities['B'],
             'script_hash':digest(script),'replay':replay}
    def freeze():
        if replay:
            value={**m,'request':request,'replay_of':replay}
        else:
            value={'input_contract':CONTRACT,'scenario':'social','task':task,'entities':entities,
                   'agents':{s['agent']:s['spec_hash'] for s in t['seats'].values()},'scripted_actions':script,
                   'memory':{a:snapshot(store,a,'social') for a in entities.values()},'pins':pins(),
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
