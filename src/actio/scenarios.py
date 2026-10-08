"""Two fixed synthetic environments using the same product RuntimePort."""
import json
from pathlib import Path

from .common import ContractError,canonical,digest,file_hash
from .facts import Facts,wire
from .memory import Memory,namespace
from .runtime import RuntimePort,TOOL,CONCORDIA,PACKAGE,pins


def existing(store,key,request):
    old=store.row('SELECT * FROM run WHERE request_key=?',(key,))
    if old:
        if json.loads(old['input'])['request']!=request:
            raise ContractError('request key conflict')
        return old


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
    old=existing(store,key,request)
    if old:
        return old
    inputs={'request':request,'scenario':'assistant','agents':{agent:store.agent(agent)['spec_hash']},
            'memory':{agent:snapshot(store,agent,'assistant')},'pins':pins(),'fixture':'read-reference-v1'}
    run,_=store.begin(key,inputs)
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
        return store.finish(run['id'],run['epoch'],task='success' if success else 'task_failure')
    except Exception as e:
        store.finish(run['id'],run['epoch'],task='infrastructure_failure',reason=str(e))
        raise


def social_manifest(store,a,b,*,as_of=None,illegal=False):
    return {'scenario':'social','engine':'concordia.Sequential','source':CONCORDIA,'world':[],
            'entities':{'A':a,'B':b},'agents':{n:store.agent(n)['spec_hash'] for n in (a,b)},
            'observations':{'A':'PRIVATE_ONLY_A','B':'PRIVATE_ONLY_B'},'gm_private':'GM_PRIVATE_FULL_LOG',
            'observation_policy':'own-only-v1','action_spec':{'options':['cooperate','wait'],'call_to_action':'Choose a legal action.'},
            'order':['B','A'],'seed':0,'max_steps':2,'pins':pins(),'fixture':'cooperate-v1','illegal':illegal,
            'memory':{a:snapshot(store,a,'social','assistant',as_of),b:snapshot(store,b,'social')},
            'mid_run_restore':False}


def social(store,key,a,b,short_root,*,as_of=None,replay=None,illegal=False,runtime_type=RuntimePort):
    if a==b:
        raise ContractError('two distinct identities required')
    request={'scenario':'social','a':a,'b':b,'as_of':as_of,'replay':replay,'illegal':illegal}
    old=existing(store,key,request)
    if old:
        return old
    if replay:
        original=json.loads(store.run(replay)['input'])
        if original['scenario']!='social' or original['entities']!={'A':a,'B':b}:
            raise ContractError('replay manifest identity mismatch')
        manifest={k:v for k,v in original.items() if k not in {'request','replay_of'}}
        if manifest['pins']!=pins() or any(store.agent(n)['spec_hash']!=h for n,h in manifest['agents'].items()):
            raise ContractError('frozen replay pins unavailable')
    else:
        manifest=social_manifest(store,a,b,as_of=as_of,illegal=illegal)
    inputs={**manifest,'request':request,'replay_of':replay}
    run,_=store.begin(key,inputs)
    try:
        outcome=run_engine(store,run,manifest,short_root,runtime_type)
        return store.finish(run['id'],run['epoch'],task=outcome)
    except Exception as e:
        store.finish(run['id'],run['epoch'],task='infrastructure_failure',reason=str(e))
        raise


def run_engine(store,run,manifest,short_root,runtime_type):
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
            self.port=runtime_type(store,run,who,short_root).start()
            self.result=self.port.submit({'answer':'INVALID' if manifest['illegal'] and self.label=='B' else 'cooperate',
                'observations':self.observations,'memory':manifest['memory'][who],'action_spec':action_spec.to_dict()})
            try:
                action_spec.validate(self.result['answer'])
            except ValueError:
                source=final_source(store,self.result)
                with store.tx():
                    store.db.execute('INSERT INTO domain_receipt VALUES(?,?,?,?,?)',(self.result['op'],'task_failure',source[0],source[1],wire({'rejected':'illegal_action','world_unchanged':True})))
                self.port.confirm_effect()
                self.port.close()
                raise
            return self.result['answer']

    entities={label:External(label) for label in ('A','B')}
    class GM(entity_lib.Entity):
        def __init__(self):
            self.world=[]; self.pending=None; self.acting=None; self.resolved=None
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
                    store.db.execute('INSERT INTO domain_receipt VALUES(?,?,?,?,?)',(acting.result['op'],'success',source[0],source[1],wire({'resolved':observation,'producer':'GM.observe(EVENT)','putative':self.pending})))
                self.world.append(observation)
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
                    return engine_lib.action_spec_to_string(entity_lib.ActionSpec(call_to_action=manifest['action_spec']['call_to_action'],
                        output_type=entity_lib.OutputType.CHOICE,options=manifest['action_spec']['options']))
                case entity_lib.OutputType.MAKE_OBSERVATION:
                    label=action_spec.call_to_action.removeprefix('OBSERVE:')
                    return manifest['observations'][label]
                case entity_lib.OutputType.RESOLVE:
                    self.resolved=f'resolved[{len(self.world)}]: {self.pending}'
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
        except ValueError:
            if not manifest['illegal'] or gm.world or gm.resolved:
                raise
            return 'task_failure'
        if len(gm.world)!=2:
            raise ContractError('Engine did not resolve both turns')
        return 'success'
    finally:
        for entity in entities.values():
            if entity.port:
                entity.port.close(force=True)
