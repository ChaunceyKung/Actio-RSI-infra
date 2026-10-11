"""Official DSH Chat Completions through a loopback-only, persistent request gate."""
import json
from pathlib import Path
import sys

from actio.contracts.json import canonical, digest, ContractError
from actio.adapters.filesystem.common import write_json
from .runtime import RuntimePort,PACKAGE,pins,synthetic_spec,CONCORDIA
from .transport_contract import validate_config, validate_manifest, INPUT, PROFILE, PROTOCOL, PROVIDER, MODEL, SOURCE, payload
from actio.adapters.persistence.ledger import Ledger
from .budget import priced, gateway, pilot, suite, metered, profile_for, validate_budget_config, endpoint_for


def transport_pins(config=None):
    if gateway(config):
        from .gateway_contract import ROUTE,PACKAGE as adapter
        return {**pins(),'provider':ROUTE,'model':config['model'],'profile':profile_for(config),'protocol':'openai-completions',
                'adapter':adapter,'policy':'sqlite-uncapped-attempt.v1','connection_mode':config['mode'],'registry':digest([]),'reviewed_dsh_source':SOURCE}
    if priced(config):
        return {**pins(),'provider':PROVIDER,'model':config['model'],'profile':profile_for(config),'protocol':PROTOCOL,
                'policy':'sqlite-priced-attempt.v1','connection_mode':config['mode'],'registry':digest([]),'reviewed_dsh_source':SOURCE}
    return {**pins(),'provider':PROVIDER,'model':MODEL,'profile':PROFILE,'protocol':PROTOCOL,
            'policy':'sqlite-attempt.v1','registry':digest([]),'reviewed_dsh_source':SOURCE}


def transport_spec(name,config=None):
    if gateway(config):
        from .gateway_contract import PERSONA,INPUT as gateway_input
        if pilot(config):
            from actio.tasks.scheduling_v2 import INPUT as gateway_input
        if suite(config):
            from .suite_contract import PERSONA
            from actio.tasks.finite import INPUT as gateway_input
        if config.get('schema')=='pilot-config.v8':
            from .candidate_campaign import INPUT as gateway_input
        if config.get('schema')=='pilot-config.v10':
            from .robustness_campaign import INPUT as gateway_input
        if config.get('schema')=='pilot-config.v9':
            from .evaluation_campaign import INPUT as gateway_input
        return {**synthetic_spec(name),'persona':PERSONA,'persona_hash':digest(PERSONA),'pins':transport_pins(config),'prompt_version':gateway_input}
    return {**synthetic_spec(name),'pins':transport_pins(config),'prompt_version':'scheduling-priced.v1' if priced(config) else INPUT}


class TransportPort(RuntimePort):
    def expected_pins(self):return transport_pins(self.candidate_config)

    def __init__(self,*args,ledger,credential=None,**kwargs):
        self.ledger_path=Path(ledger).resolve();self.accounted=False
        self.candidate_config=json.loads(args[1]['input'])['transport']['config'];self.credential=credential
        if priced(self.candidate_config):
            validate_budget_config(self.candidate_config)
            if self.candidate_config['mode']!='priced_rehearsal' or type(credential) is not str or not credential.startswith('ACTIO_FAKE_'):
                raise ContractError('C2B0 permits only explicit in-memory fake rehearsal credential')
            kwargs['deadlines']={k:self.candidate_config['timeouts'][k] for k in ('ready','result','drained','closed')}
        if gateway(self.candidate_config):
            validate_budget_config(self.candidate_config)
            if type(credential) is not str or not credential or (self.candidate_config['mode'] in ('tokenkey_rehearsal','tokenkey_pilot_rehearsal','tokenkey_suite_rehearsal','candidate_loopback','candidate_rehearsal','robustness_rehearsal') and not credential.startswith('ACTIO_FAKE_')):
                raise ContractError('explicit gateway credential required')
            kwargs['deadlines']={k:self.candidate_config['timeouts'][k] for k in ('ready','result','drained','closed')}
        super().__init__(*args,**kwargs)

    def prepare(self):
        m=json.loads(self.run['input']);validate_manifest(m);self.config=m['transport']['config']
        self.seat=next(s for s,a in m['entities'].items() if a==self.agent)
        with_ledger=Ledger(self.ledger_path)
        try:
            if with_ledger.meta['config_hash']!=m['transport']['config_hash'] or with_ledger.meta['campaign']!=m['transport']['campaign']:
                raise ContractError('wrong budget ledger')
        finally:with_ledger.close()
        super().prepare()
        if gateway(self.config):
            self.prepare_gateway();return
        patch=json.loads((self.root/'profile.patch.yml').read_bytes())
        patch=[x for x in patch if x.get('id')!='llm-deepseek']
        patch[-1]['insert']=[x for x in patch[-1]['insert'] if x['id']=='actio-policy']
        endpoint=endpoint_for(self.config)
        patch[-1]['insert'].append({'id':'actio-transport','name':(PACKAGE/'plugins/transport.mjs').as_uri(),
            'config':{'python':sys.executable,'ledger':str(self.ledger_path),'endpoint':endpoint,
                      'active':str(self.root/'active.json'),'capture':str(self.root/'transport.jsonl'),
                      'response':str(self.root/'transport-response.json'),'limits':self.supervisor.limits}})
        patch.extend([{'id':'session-title','disabled':True},{'id':'llm-retry','disabled':True},
                      {'id':'llm-deepseek','config':{'baseURL':endpoint,'apiKeyEnv':'ACTIO_STUB_KEY',
                       'thinking':'disabled','reasoningEffort':'off','maxTokens':64,'streamIdleTimeoutMs':1500,
                       'retryPolicy':{'mode':'normal','maxRetries':0}}}])
        write_json(self.root/'profile.patch.yml',patch)
        c=json.loads((self.root/'host-config.json').read_bytes())
        c['sdk'].update(provider=PROVIDER,model=MODEL,max_tokens=64,reasoning_effort='off',env={'ACTIO_STUB_KEY':'actio-loopback-fake-key'})
        if priced(self.config):
            from actio.adapters.filesystem.common import clean_env
            t=self.config['timeouts'];ref=self.config['credential_ref']
            gate=next(x for item in patch for x in item.get('insert',[]) if x['id']=='actio-transport')
            gate['config'].update(credential_env=ref,helper_env=clean_env(self.root),first_ms=t['first_response']*1000,total_ms=t['request']*1000)
            adapter=next(x for x in patch if x.get('id')=='llm-deepseek')
            adapter['config'].update(apiKeyEnv=ref,streamIdleTimeoutMs=t['idle']*1000)
            c['sdk'].pop('env',None);c['sdk'].update(model=self.config['model'],request_timeout_seconds=t['rpc'])
            c['credential_ref']=ref
            self.supervisor.launch_credential={'ref':ref,'value':self.credential};self.credential=None
            self.supervisor.total_seconds=t['worker']
            write_json(self.root/'profile.patch.yml',patch)
        write_json(self.root/'host-config.json',c)

    def prepare_gateway(self):
        from actio.adapters.filesystem.common import clean_env
        from .gateway_contract import ROUTE,PACKAGE as adapter
        cfg=self.config;t=cfg['timeouts'];ref=cfg['credential_env']
        patch=json.loads((self.root/'profile.patch.yml').read_bytes());insert=next(x for x in patch if 'insert' in x)
        insert['insert']=[x for x in insert['insert'] if x['id']=='actio-policy']
        patch.extend([{'id':x,'disabled':True} for x in ('session-title','llm-retry','deepseek-llm-api-extensions','session-log-deepseek','plugin-package-inventory-deepseek')])
        insert['insert'].extend([
            {'id':'actio-transport','name':(PACKAGE/'plugins/transport.mjs').as_uri(),'config':{
                'python':sys.executable,'ledger':str(self.ledger_path),'endpoint':cfg['endpoint'],
                'active':str(self.root/'active.json'),'capture':str(self.root/'transport.jsonl'),'response':str(self.root/'transport-response.json'),
                'limits':self.supervisor.limits,'gateway':True,'measurement':pilot(cfg),'deadline_audit':suite(cfg),'credential_env':ref,'helper_env':clean_env(self.root),
                'first_ms':t['first_response']*1000,'total_ms':t['request']*1000,'max_bytes':cfg['bounds']['response_bytes'],'max_chunks':cfg['bounds']['chunks']}},
            {'id':'llm-pi-ai','name':adapter,'config':{'providers':{ROUTE:{'apiKeyEnv':ref,'api':'openai-completions','baseURL':cfg['endpoint'],
                'models':[{'id':cfg['model'],'contextWindow':32768,'maxTokens':512,'reasoningEfforts':False}],
                'compat':{'maxTokensField':'max_tokens','supportsDeveloperRole':False,'supportsStore':False},
                'timeoutMs':t['request']*1000,'streamIdleTimeoutMs':t['idle']*1000,'retryPolicy':{'mode':'normal','maxRetries':0}}}}}])
        write_json(self.root/'profile.patch.yml',patch)
        host=json.loads((self.root/'host-config.json').read_bytes())
        host['sdk'].update(provider=ROUTE,model=cfg['model'],max_tokens=512,request_timeout_seconds=t['rpc'])
        host['credential_ref']=ref;host['gateway_contract']=cfg
        self.supervisor.launch_credential={'ref':ref,'value':self.credential};self.credential=None
        self.supervisor.total_seconds=t['worker'];write_json(self.root/'host-config.json',host)

    def start(self):
        if suite(self.candidate_config):
            from .pilot import now
            self.s.audit(self.run['id'],None,'deadline_boundary',{'stage':'worker_ready_start','utc':now(),'limits':self.candidate_config['timeouts']})
        return super().start()

    def bind_task(self,task):
        return task if pilot(self.candidate_config) else super().bind_task(task)

    def prepare_dispatch(self,task):
        m=json.loads(self.run['input']);scope={'campaign':m['transport']['campaign'],'run':self.run['id'],'op':self.op,
            'registration':self.run['id']+':'+self.seat,'seat':self.seat,'stream':self.stream['id'],'epoch':self.epoch,
            'worker':self.stream['worker'],'config_hash':m['transport']['config_hash'],'profile':profile_for(self.config),
            'endpoint':endpoint_for(self.config),'persona':self.spec['persona'],'task':task}
        ledger=Ledger(self.ledger_path)
        try:ledger.authorize(scope)
        finally:ledger.close()
        super().prepare_dispatch(task)

    def submit(self,task):
        from .facts import Facts
        complete=False;native_usage=None
        if suite(self.candidate_config):
            from .pilot import now
            self.s.audit(self.run['id'],None,'deadline_boundary',{'stage':'submit_result_start','utc':now(),'seconds':self.deadlines['result']})
        try:
            result=super().submit(task);complete=True
            events=Facts(self.s).certify(self.op,self.marker)
            finals=[e for e in events if e['type']=='assistant/message']
            native_usage=finals[-1]['data'].get('usage') if finals else None
            return result
        finally:
            if self.op:
                if not complete:
                    try:Facts(self.s).collect(self.stream['id'])
                    except (ContractError,OSError):pass
                    if metered(self.config):
                        events=[json.loads(r['raw']) for r in self.s.rows('SELECT raw FROM occurrence WHERE stream=? ORDER BY seq',(self.stream['id'],))]
                        finals=[e for e in events if e['type']=='assistant/message']
                        native_usage=finals[-1]['data'].get('usage') if finals else None
                p=self.root/'transport-response.json';response=json.loads(p.read_bytes()) if p.exists() else None
                if response is not None:
                    response['chunks_json']=json.dumps(response.pop('chunks'),separators=(',',':'),allow_nan=False)
                native_usage=json.dumps(native_usage,separators=(',',':'),allow_nan=False)
                ledger=Ledger(self.ledger_path)
                try:
                    # A constructor/authorization failure may precede ledger registration.
                    exists=ledger.db.execute('SELECT id FROM attempt WHERE id=?',(self.op,)).fetchone()
                    if exists:
                        a=ledger.finish(self.op,response,native_usage,complete)
                        self.s.audit(self.run['id'],self.op,'transport_attempt',a);self.accounted=True
                        if pilot(self.config) and (a['text_integrity'] or {}).get('status')!='verified':raise ContractError('pilot text evidence rejected; batch frozen')
                        if pilot(self.config) and complete:
                            from .channel_audit import for_config
                            for_config(self.config).audit(response,result['answer'],require_bytes=True,**({'native_blocks':finals[-1]['data']['message']['content']} if self.config['schema'] in ('pilot-config.v8','pilot-config.v9','pilot-config.v10') else {}))
                        if gateway(self.config) and a['state']=='unknown':raise ContractError('gateway usage/identity incomplete; batch frozen')
                finally:ledger.close()


def scheduling_transport(store,key,short_root,*,task,config,ledger_path,runtime_type=TransportPort,credential=None):
    from .scenarios import snapshot,run_engine,failed
    from .terminal import seal_terminal
    from actio.tasks.scheduling import validate_task
    validate_budget_config(config);t=validate_task(task);mode=config['mode'] if gateway(config) else 'priced_rehearsal' if priced(config) else 'transport_stub'
    if t['mode']!=mode:raise ContractError('explicit transport task required')
    for seat in t['seats'].values():
        a=store.agent(seat['agent'])
        if a['spec_hash']!=seat['spec_hash'] or a['spec']['pins']!=transport_pins(config):raise ContractError('transport identity/spec mismatch')
    ledger=Ledger(ledger_path)
    try:
        if ledger.meta['config_hash']!=digest(config):raise ContractError('config not frozen in ledger')
        campaign=ledger.meta['campaign']
        entities={s:t['seats'][s]['agent'] for s in ('A','B')}
        request={'scenario':'social','task_hash':task['sha256'],'a':entities['A'],'b':entities['B'],
                 'config_hash':digest(config),'campaign':campaign,'mode':mode}
        def freeze():
            m={'input_contract':'visible-robustness-tokenkey.v1' if config.get('schema')=='pilot-config.v10' else 'finite-candidate-tokenkey.v1' if config.get('schema')=='pilot-config.v9' else 'finite-candidate-loopback.v1' if config.get('schema')=='pilot-config.v8' else 'finite-suite-tokenkey.v1' if suite(config) else 'scheduling-tokenkey.v2' if pilot(config) else 'scheduling-tokenkey.v1' if gateway(config) else 'scheduling-priced.v1' if priced(config) else INPUT,'execution_mode':mode,'scenario':'social','task':task,'entities':entities,
               'agents':{s['agent']:s['spec_hash'] for s in t['seats'].values()},'memory':{a:snapshot(store,a,'social') for a in entities.values()},
               'pins':transport_pins(config),'engine':'concordia.Sequential','source':CONCORDIA,'order':['A','B'],'max_steps':2,'seed':0,'world':[],
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
