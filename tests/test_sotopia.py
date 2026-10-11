import asyncio
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import unittest

from pydantic import create_model
from pydantic import field_validator
from actio._vendor.sotopia import LLMBaseModel
from actio._vendor.sotopia import LLMEvalBaseModel
from actio._vendor.sotopia import PositiveReasoningScore
from actio._vendor.sotopia import BidirectionalReasoningScore
from actio._vendor.sotopia import PydanticOutputParser
from actio._vendor.sotopia import EvaluationForAgents
from actio.adapters.runtime.eval_worker import controlled


class Sotopia(unittest.TestCase):
    def test_parser_actual_context_repair_value_properties_and_coercion(self):
        observations=[]
        class Seen(PositiveReasoningScore):
            @field_validator('score')
            @classmethod
            def seen(cls,v,info):
                observations.append(info.context);return v
        parser=PydanticOutputParser(pydantic_object=Seen)
        cases={'strict':'{"reasoning":"fixture","score":7}',
               'repair':"{reasoning: 'fixture', score: 7}",
               'value':'{"reasoning":{"value":"fixture"},"score":{"value":7}}',
               'properties':'{"properties":{"reasoning":"fixture","score":7}}'}
        results={}
        for name,raw in cases.items():
            for ctx in (None,{'test':'context'}):
                key=name+('/context' if ctx else '/no-context');observations.clear()
                try:
                    result=parser.parse(raw,context=ctx)
                    results[key]={'status':'PARSED','value':result.model_dump(),'validator_context':list(observations)}
                except Exception as e:results[key]={'status':'REJECTED','type':type(e).__name__}
        for name in ('repair','value'):
            self.assertEqual(results[name+'/context']['status'],'PARSED')
            self.assertEqual(results[name+'/no-context']['status'],'REJECTED')
        self.assertEqual(results['properties/context']['validator_context'],[None])
        coercion=[]
        for score in (True,'7'):
            value=parser.parse(json.dumps({'reasoning':'fixture','score':score})).model_dump()
            self.assertIs(type(value['score']),int);coercion.append({'input':score,'parsed':value})
        self.assertEqual(BidirectionalReasoningScore(reasoning='fixture',score=-5).score,-5)
        self.evidence={'parser':results,'coercion':coercion,'product_policy':'strict raw validation before this real parser; repair never admits input'}

    def test_strict_adapter_keeps_reverse_keys_and_three_identities(self):
        mapping={f'agent_{i}':{'agent':f'ID{i}','seat':str(i),'role':'participant'} for i in (1,2,3)}
        scores={f'agent_{i}':{'goal':{'reasoning':'preset','score':i},'relationship':{'reasoning':'preset','score':-i}} for i in (3,2,1)}
        result=controlled(json.dumps({'scores':scores}),mapping)
        self.assertEqual(result,{'scores':scores,'parser_calls':1})
        self.evidence={'normalized':result,'mapping':mapping,'mode':'CONTROLLED_RESPONSE'}

    def test_episode_original_definition_with_fixed_generation_seam(self):
        path=Path(__file__).parent/'fixtures/sotopia_episode.py'
        spec=importlib.util.spec_from_file_location('characterized_episode',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        dim=create_model('Nested',__base__=LLMEvalBaseModel,goal=(PositiveReasoningScore,...),relationship=(BidirectionalReasoningScore,...))
        pair=create_model('LegacyTupleShape',__base__=LLMEvalBaseModel,goal=(tuple[str,int],...))
        messages=[('First',module.Message(text='did nothing')),('Second',module.Message(text='spoke once'))]
        evidence={}
        async def run_case(name,shape,raw,msgs,history='',raise_error=False,structured=False):
            captures=[]
            async def generation(**kwargs):
                captures.append({'input_values':kwargs['input_values'],'structured_output':kwargs['structured_output']})
                if raise_error:raise RuntimeError('fixed generation failure')
                if structured:return EvaluationForAgents[shape].model_validate(json.loads(raw))
                return kwargs['output_parser'].parse(raw)  # Original raw-text parser is executed.
            module.agenerate=generation;module.supports_response_schema=lambda **kw: structured
            evaluator=module.EpisodeLLMEvaluator('local-fixed',EvaluationForAgents[shape])
            printed=io.StringIO()
            with contextlib.redirect_stdout(printed):result=await evaluator.__acall__(1,msgs,history=history)
            evidence[name]={'result':result,'generation_calls':len(captures),'captures':captures,
                            'caught_print':printed.getvalue()[:256]}
            return result
        nested=json.dumps({'evaluations':{f'agent_{i}':{'goal':{'reasoning':'preset','score':i},'relationship':{'reasoning':'preset','score':0}} for i in (2,1)}})
        tuples=json.dumps({'evaluations':{'agent_2':{'goal':['second',8]},'agent_1':{'goal':['first',2]}}})
        self.assertEqual(asyncio.run(run_case('standard_nested_raw',dim,nested,messages)),[])
        self.assertEqual(asyncio.run(run_case('standard_nested_structured',dim,nested,messages,structured=True)),[])
        result=asyncio.run(run_case('reverse_alias_tuple_shape',pair,tuples,messages))
        self.assertEqual(result[0],('agent_1',(('goal',8),'second')))
        self.assertEqual(asyncio.run(run_case('history_only',pair,tuples,None,history='frozen history')),[])
        self.assertEqual(asyncio.run(run_case('caught_generation_exception',pair,tuples,messages,raise_error=True)),[])
        history=evidence['reverse_alias_tuple_shape']['captures'][0]['input_values']['history']
        self.assertNotIn('did nothing',history)
        self.assertIn('exactly 2 agents',evidence['reverse_alias_tuple_shape']['captures'][0]['input_values']['agent_instruction'])
        self.evidence={'upstream_status':'COMPATIBILITY_FAIL_NOT_ADOPTED','experiments':evidence,
            'seams':['Message natural-language data shim','agenerate fixed raw or structured return','supports_response_schema boolean'],
            'unchanged':['EpisodeLLMEvaluator definition','PydanticOutputParser definition','pydantic validate_call','gin decorator'],
            'network_requests':0,'model_requests':0}


if __name__=='__main__':unittest.main()
