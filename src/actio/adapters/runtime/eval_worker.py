"""Single bounded local evaluation child. Input is data on stdin; no runtime, network or tools."""
import importlib.metadata
import json
import sys


def lockdown():
    counters={'network_attempts':0,'process_attempts':0,'runtime_import_attempts':0,'write_attempts':0}
    denied={'actio.adapters.runtime.runtime','actio.adapters.runtime.supervisor','actio.adapters.transport','actio.adapters.environment','actio.interfaces.store','actio.application.store','actio.application.scenarios','actio.runtime','actio.scenarios','actio.store','actio.interfaces.workers.host','actio.supervisor',
            'actio.host','actio.mcp_server','actio.interfaces.workers.mcp_server','actio.adapters.runtime.host','actio.adapters.runtime.mcp_server','deepseek_harness','concordia','redis','redis_om','litellm','openai','sotopia'}
    def audit(event,args):
        reason=None
        if event.startswith('socket.'):reason='network_attempts'
        elif event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.spawn'):reason='process_attempts'
        elif event=='import' and any(args[0]==n or args[0].startswith(n+'.') for n in denied):reason='runtime_import_attempts'
        elif event=='open':
            mode=args[1];flags=args[2]
            if (isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags & (1|2|64|512|1024)):
                reason='write_attempts'
        if reason:
            counters[reason]+=1
            raise RuntimeError('offline evaluator denied: '+reason)
    sys.addaudithook(audit)
    return counters


def controlled(raw,mapping):
    from actio.evidence.bundles.eval_contract import strict_response
    from actio.evidence.bundles.eval_contract import DEPENDENCIES
    # Validate original bytes/types before any repair/coercion.
    value=strict_response(raw,mapping)
    for name,version in DEPENDENCIES.items():
        if importlib.metadata.version(name)!=version:
            raise RuntimeError('eval optional dependency pin mismatch: '+name)
    from pydantic import create_model
    from actio._vendor.sotopia import LLMEvalBaseModel
    from actio._vendor.sotopia import PositiveReasoningScore
    from actio._vendor.sotopia import BidirectionalReasoningScore
    from actio._vendor.sotopia import EvaluationForAgents
    from actio._vendor.sotopia import PydanticOutputParser
    dimensions=create_model('ActioGoalRelationship',__base__=LLMEvalBaseModel,
                            goal=(PositiveReasoningScore,...),relationship=(BidirectionalReasoningScore,...))
    parser=PydanticOutputParser(pydantic_object=EvaluationForAgents[dimensions])
    # Envelope spelling is Actio-owned. Alias keys and validated scores are unchanged.
    parsed=parser.parse(json.dumps({'evaluations':value['scores']}),context={'actio':'strict-prevalidated-v1'})
    normalized=parsed.model_dump()['evaluations']
    if normalized!=value['scores']:raise RuntimeError('upstream normalization changed validated values')
    return {'scores':normalized,'parser_calls':1}


def main():
    counters=lockdown()
    from actio.contracts.json import ContractError
    from actio.contracts.json import digest
    from actio.evidence.bundles.eval_contract import LIMITS
    from actio.evidence.bundles.eval_contract import deterministic
    response={'status':'measurement_error','results':None,'error':None,'parser_calls':0,
              'model_requests':0,'audit':counters,'view_hash':None}
    try:
        raw=sys.stdin.buffer.read(LIMITS['input_bytes']+LIMITS['response_bytes']*2+4096)
        payload=json.loads(raw);view=payload['view'];response['view_hash']=digest(view)
        if payload['mode']=='deterministic':response['results']=deterministic(view)
        else:
            parsed=controlled(payload['raw_response'],view['aliases'])
            response.update(results=parsed['scores'],parser_calls=parsed['parser_calls'])
        response['status']='valid_measurement'
    except ContractError as e:
        response.update(status='invalid_measurement',error={'type':type(e).__name__,'reason':str(e)[:512]})
    except Exception as e:
        response.update(status='measurement_error',error={'type':type(e).__name__,'reason':str(e)[:512]})
    print(json.dumps(response,ensure_ascii=False))


if __name__=='__main__':main()
