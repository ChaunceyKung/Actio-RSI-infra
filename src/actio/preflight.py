"""Read-only configuration validation; Phase 1C1 has no live transport implementation."""
import argparse
import json
from pathlib import Path

ROLES=('solver','gm','judge','retries','other')


def template():
    return {'schema':'pilot-config.v1','authorization':None,
            'components':{r:{'provider':None,'model_version':None,'parameters':{},'tool_permissions':[],
                             'data_scope':None,'process_context':None,'depends_on':[]} for r in ('solver','gm','judge')},
            'budgets':{r:{'calls':0,'tokens':0,'cost':0,'currency':None,'quote':None} for r in ROLES},
            'failure_denominator':None,'stop_conditions':[],'ledger_owner':None}


def preflight(config):
    reasons=['live_transport_not_implemented_in_phase1c1'];configuration_errors=[]
    if not isinstance(config,dict) or set(config)!=set(template()) or config.get('schema')!='pilot-config.v1':
        configuration_errors.append('configuration_schema')
    else:
        if not isinstance(config['authorization'],str) or not config['authorization'].strip():configuration_errors.append('explicit_authorization_missing')
        components=config['components'];budgets=config['budgets']
        if not isinstance(components,dict) or set(components)!=set(template()['components']):configuration_errors.append('component_roles')
        else:
            for role,c in components.items():
                if not isinstance(c,dict) or set(c)!=set(template()['components'][role]):configuration_errors.append(role+'_configuration');continue
                if any(not isinstance(c[k],str) or not c[k].strip() for k in ('provider','model_version','data_scope','process_context')):configuration_errors.append(role+'_required_fields')
                if not isinstance(c['parameters'],dict) or not isinstance(c['tool_permissions'],list) or not isinstance(c['depends_on'],list):configuration_errors.append(role+'_parameters_permissions_dependencies')
        if not isinstance(budgets,dict) or set(budgets)!=set(ROLES):configuration_errors.append('budget_roles')
        else:
            for role,b in budgets.items():
                if not isinstance(b,dict) or set(b)!=set(template()['budgets'][role]):configuration_errors.append(role+'_budget');continue
                if any(type(b[k]) is not int or b[k]<0 for k in ('calls','tokens')) or type(b['cost']) not in (int,float) or not 0<=b['cost']<float('inf'):
                    configuration_errors.append(role+'_budget_values');continue
                if b['calls']==0 or b['tokens']==0 or b['cost']==0:configuration_errors.append(role+'_zero_budget')
                if any(not isinstance(b[k],str) or not b[k].strip() for k in ('currency','quote')):configuration_errors.append(role+'_price_unconfirmed')
        if any(not isinstance(config[k],str) or not config[k].strip() for k in ('failure_denominator','ledger_owner')) or not config['stop_conditions']:configuration_errors.append('ledger_stopping_failure_policy')
    return {'status':'BLOCKED','reasons':reasons+configuration_errors,'configuration_valid':not configuration_errors,
            'provider_compatibility':'UNVERIFIED','live_ready':False,'model_requests':0,'credential_reads':0,
            'clients_created':0,'workers_started':0,'human_calibration':'BLOCKED'}


def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('config',type=Path);a=p.parse_args(argv)
    try:
        with a.config.open('rb') as f:raw=f.read(262145)
        if len(raw)>262144:raise ValueError('configuration byte limit')
        result=preflight(json.loads(raw))
    except (OSError,ValueError,TypeError) as e:result={'status':'BLOCKED','reasons':[str(e)[:256]],'model_requests':0}
    print(json.dumps(result));return 2


if __name__=='__main__':raise SystemExit(main())
