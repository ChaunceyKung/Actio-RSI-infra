from actio.resources import data_path
import json
import sys
from pathlib import Path
from actio.contracts.json import ContractError
from actio.adapters.filesystem.common import file_hash
from actio.adapters.runtime.facts import Facts
from actio.contracts.wire import wire
from actio.adapters.runtime.runtime import PACKAGE

def final_source(store, result):
    events=Facts(store).certify(result['op'],result['marker'])
    receipt=result['marker']['receipt']
    start=max(e['seq'] for e in events if e['type']=='agent/inbox/spliced' and any(m.get('id')==receipt for m in e['data'].get('inserted',[])))
    candidates=[e for e in events if e['type']=='assistant/message' and start<e['seq']<=result['marker']['terminal']['seq']]
    if not candidates:
        raise ContractError('no final assistant source')
    return result['stream'],candidates[-1]['seq'],'assistant.final'

def run_engine(store,run,manifest,short_root,runtime_type):
    from actio.tasks.registry import CONTRACT
    from actio.tasks.registry import actor_observation
    from actio.tasks.registry import resolved_text
    from actio.tasks.registry import task_result
    transport=manifest.get('input_contract') in ('scheduling-transport.v1','scheduling-priced.v1','scheduling-tokenkey.v1','scheduling-tokenkey.v2','finite-suite-tokenkey.v1','finite-candidate-loopback.v1','finite-candidate-tokenkey.v1','visible-robustness-tokenkey.v1')
    scheduling=manifest.get('input_contract')==CONTRACT or transport
    import concordia
    pin=json.loads(data_path('pins','concordia.json').read_text(encoding='utf-8'))
    base=Path(concordia.__file__).parent.parent
    for name,h in pin['files'].items():
        if name!='LICENSE' and file_hash(base/name)!=h:
            raise ContractError('Concordia source changed: '+name)
    from concordia.environment.engines.sequential import Sequential
    from concordia.environment.engines.sequential import EVENT_TAG
    from concordia.environment.engines.sequential import PUTATIVE_EVENT_TAG
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
            task={'observations':self.observations,'memory':manifest['memory'][who],'action_spec':action_spec.to_dict()}
            if manifest.get('input_contract') in ('scheduling-tokenkey.v2','finite-suite-tokenkey.v1','finite-candidate-loopback.v1','finite-candidate-tokenkey.v1','visible-robustness-tokenkey.v1'):
                from actio.evidence.audit.transport_contract import payload
                task=payload(manifest,self.label,self.observations)
            if not transport:
                task['answer']=manifest['scripted_actions'][self.label] if scheduling else ('INVALID' if manifest['illegal'] and self.label=='B' else 'cooperate')
            self.result=self.port.submit(task)
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
