"""Experimental real Concordia Sequential Engine + shared DSH adapter."""
import dataclasses
import json
from pathlib import Path
import sys
from common import LOCAL, ROOT, write_json, jsonl, digest
sys.path.insert(0,str(LOCAL/'concordia'))
from concordia.environment.engines.sequential import Sequential, EVENT_TAG, PUTATIVE_EVENT_TAG
from concordia.environment import engine as engine_lib
from concordia.environment.step_controller import StepController
from concordia.typing import entity as entity_lib
from runtime_adapter import Adapter

START={
    'source':'b71d202750e23444ce1bf28d9f114bcd88aa41db','engine':'Sequential',
    'order':['B','A'],'options':['cooperate','wait'],'private':{'A':'PRIVATE_ONLY_A','B':'PRIVATE_ONLY_B'},
    'gm_private':'GM_PRIVATE_FULL_LOG','fixture_model':'fixed','max_steps':2,
    'covers':['initial scenario','entity identities','observation policy','ActionSpec','model fixture','profile code hash'],
    'excludes':['native session mid-run resume','engine cursor snapshot','external world state','live model response'],
    'mid_run_complete_restore':False,
}

class ExternalEntity(entity_lib.Entity):
    def __init__(self,name,adapter,illegal=False):self._name=name;self.adapter=adapter;self.observations=[];self.records=[];self.illegal=illegal
    @property
    def name(self):return self._name
    def observe(self,observation):self.observations.append(observation)
    def act(self,action_spec):
        op='act-'+self.name
        task={'op':op,'answer':'INVALID' if self.illegal else 'cooperate',
              'observations':list(self.observations),'action_spec':action_spec.to_dict()}
        result=self.adapter.run(task,session=self.name)
        barrier=self.adapter.barrier(self.name)
        self.records.append({'op':op,'session':self.name,'intent':result.final_response,'action_spec':action_spec.to_dict(),
            'seqs':[e['seq'] for e in result.events],'barrier':barrier})
        # Engine expects external entities to honor ActionSpec; adapter enforces it.
        action_spec.validate(result.final_response)
        return result.final_response

class GM(entity_lib.Entity):
    """Deterministic GM output fixture. Actual Engine owns dispatch/resolve flow."""
    def __init__(self):self.world=[];self.pending=None;self.calls=[];self.resolutions=[];self.private=START['gm_private']
    @property
    def name(self):return 'FixtureGM'
    def observe(self,observation):
        if observation.startswith(PUTATIVE_EVENT_TAG):self.pending=observation
        if observation.startswith(EVENT_TAG):self.world.append(observation)
    def act(self,action_spec):
        self.calls.append(action_spec.output_type.value)
        match action_spec.output_type:
            case entity_lib.OutputType.TERMINATE:return 'Yes' if len(self.world)>=2 else 'No'
            case entity_lib.OutputType.NEXT_GAME_MASTER:return self.name
            case entity_lib.OutputType.NEXT_ACTING:return START['order'][len(self.world)]
            case entity_lib.OutputType.NEXT_ACTION_SPEC:
                return engine_lib.action_spec_to_string(entity_lib.ActionSpec(call_to_action='Choose a legal action.',output_type=entity_lib.OutputType.CHOICE,options=START['options']))
            case entity_lib.OutputType.MAKE_OBSERVATION:
                who='A' if 'A' in action_spec.call_to_action else 'B'
                return START['private'][who]
            case entity_lib.OutputType.RESOLVE:
                result=f'resolved[{len(self.world)}]: {self.pending}'
                self.resolutions.append({'source':'GM.act(RESOLVE)','value':result,'pending':self.pending})
                return result
            case _:raise ValueError(action_spec)

def episode(root,illegal=False):
    world=GM();steps=[]
    with Adapter(root,persona='SHARED_SYNTHETIC_AGENT') as adapter:
        entities=[ExternalEntity(n,adapter,illegal=illegal and n=='B') for n in ['A','B']]
        engine=Sequential()
        assert isinstance(engine,engine_lib.Engine)
        try:
            loop_return=engine.run_loop(game_masters=[world],entities=entities,max_steps=2,
                step_controller=StepController(start_paused=False),step_callback=lambda s:steps.append(dataclasses.asdict(s)))
        except ValueError:
            if not illegal:raise
            assert world.world==[] and world.resolutions==[]
            loop_return=None
        if not illegal:
            assert len(world.world)==2 and [s['acting_entity'] for s in steps]==['B','A']
            assert len(world.resolutions)==2 and loop_return is None
        captures=[r for r in jsonl(adapter.trace) if r['kind']=='provider-input']
        for capture in captures:
            own=capture['op'].removeprefix('act-');other='B' if own=='A' else 'A'
            text=json.dumps(capture['messages'])
            assert START['private'][own] in text
            assert START['private'][other] not in text and START['gm_private'] not in text
        return {'world':world.world,'resolutions':world.resolutions,'steps':steps,'gm_calls':world.calls,
                'entities':{e.name:e.records for e in entities},'loop_return':loop_return,'provider_requests':len(captures)}

if __name__=='__main__':
    assert sys.stdin.readline().strip()=='go'
    root=Path(sys.argv[2]);root.mkdir(parents=True,exist_ok=True)
    write_json(root/'start-manifest.json',{**START,'adapter_hash':digest((ROOT/'runtime_adapter.py').read_text()),
        'plugin_hash':digest((ROOT/'fixtures/provider_policy.mjs').read_text())})
    try:
        first=episode(root/'start-one');again=episode(root/'start-two');bad=episode(root/'illegal',True)
        assert first['world']==again['world'] and first['steps']==again['steps']
        tests=[{'test_id':'P4-real-engine','status':'PASS','assertions':['real Sequential scheduling/observe/act/resolve; order B,A; ActionSpec validated','same runtime_adapter.Adapter as assistant','actual GM.act(RESOLVE) and GM.observe(EVENT) captured; no fabricated resolve return']},
               {'test_id':'P4-private-input','status':'PASS','assertions':['all actual provider inputs exclude other entity private marker and GM full log']},
               {'test_id':'P4-illegal','status':'PASS','assertions':['invalid DSH output rejected by actual ActionSpec.validate; world and resolution ledger remain empty']},
               {'test_id':'P4-start-rerun','status':'PASS','assertions':['two fresh episodes match world and order from start manifest; mid-run resume unsupported']}]
        write_json(root/'result.json',{'tests':tests,'start_manifest':START,'first':first,'rerun':again,'illegal':bad})
    except BaseException as e:
        write_json(root/'failure.json',{'type':type(e).__name__,'error':str(e)});raise
