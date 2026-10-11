from actio.domain.roles import validate
from actio.domain.roles import parse_config
"""Role-aware offline configuration validation. No live execution/credential path."""
import argparse
import json
from pathlib import Path

from actio.contracts.json import ContractError

ROLES=('solver','gm','judge','retries','other')
MODES=('disabled','deterministic_local','transport_stub','future_live')
STUB_MODEL='deepseek-v4-flash'


def preflight(config):
    errors=[]
    try:
        if type(config) is dict and config.get('schema')=='pilot-config.v10':
            from actio.profiles.robustness_campaign import validate as validate_evaluation
            from actio.profiles.robustness_campaign import plan
            validate_evaluation(config);return plan()
        if type(config) is dict and config.get('schema')=='pilot-config.v9':
            from actio.profiles.evaluation_campaign import validate as validate_evaluation
            from actio.profiles.evaluation_campaign import plan
            validate_evaluation(config);return plan()
        if type(config) is dict and config.get('schema')=='pilot-config.v8':
            from actio.profiles.candidate_campaign import validate as validate_candidate
            from actio.profiles.candidate_campaign import plan
            validate_candidate(config);return plan()
        if type(config) is dict and config.get('schema')=='pilot-config.v7':
            from actio.profiles.suite_contract import validate as validate_suite
            from actio.profiles.suite_contract import plan
            validate_suite(config);return plan()
        if type(config) is dict and config.get('schema')=='pilot-config.v6':
            from actio.profiles.pilot_contract import validate as validate_pilot
            from actio.profiles.pilot_contract import plan
            validate_pilot(config);return plan()
        if type(config) is dict and config.get('schema')=='pilot-config.v5':
            from actio.profiles.gateway_contract import plan
            return plan(config)
        if type(config) is dict and config.get('schema')=='pilot-config.v4-clock.v1':
            from actio.profiles.readiness_contract import plan
            return plan(config)
        if type(config) is dict and config.get('schema')=='pilot-config.v3':
            from actio.profiles.transport import validate_config
            validate_config(config)
        else:validate(config)
    except (ContractError,KeyError,TypeError,ValueError,RecursionError) as e:errors.append(str(e)[:512])
    return {'status':'BLOCKED','reasons':['no_live_execution_in_phase1c2a',*errors],
            'configuration_valid':not errors,'transport_validated':False,'live_authorized':False,'live_ready':False,
            'provider_compatibility':'UNVERIFIED','model_requests':0,'credential_reads':0,'clients_created':0,
            'workers_started':0,'human_calibration':'BLOCKED'}


def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('config',type=Path);a=p.parse_args(argv)
    try:
        with a.config.open('rb') as f:raw=f.read(262145)
        if len(raw)>262144:raise ContractError('configuration byte limit')
        result=preflight(parse_config(raw))
    except (OSError,ValueError,TypeError,RecursionError) as e:result={'status':'BLOCKED','reasons':[str(e)[:512]],'configuration_valid':False,'live_authorized':False,'live_ready':False,'model_requests':0}
    print(json.dumps(result));return 2


if __name__=='__main__':raise SystemExit(main())
