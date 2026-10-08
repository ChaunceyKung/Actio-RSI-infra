"""Official DSH Chat Completions through a loopback-only, persistent request gate."""
import json
from pathlib import Path
import sys

from .common import canonical,digest,write_json,ContractError
from .runtime import RuntimePort,PACKAGE,pins,synthetic_spec,CONCORDIA
from .transport_contract import (validate_config,validate_manifest,INPUT,PROFILE,PROTOCOL,PROVIDER,MODEL,SOURCE,payload)
from .budget import Ledger


def transport_pins():
    return {**pins(),'provider':PROVIDER,'model':MODEL,'profile':PROFILE,'protocol':PROTOCOL,
            'policy':'sqlite-attempt.v1','registry':digest([]),'reviewed_dsh_source':SOURCE}


def transport_spec(name):
    return {**synthetic_spec(name),'pins':transport_pins(),'prompt_version':INPUT}


class TransportPort(RuntimePort):
    @staticmethod
    def expected_pins():return transport_pins()

    def __init__(self,*args,ledger,**kwargs):
        self.ledger_path=Path(ledger).resolve();self.accounted=False
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
        patch=json.loads((self.root/'profile.patch.yml').read_bytes())
        patch=[x for x in patch if x.get('id')!='llm-deepseek']
        patch[-1]['insert']=[x for x in patch[-1]['insert'] if x['id']=='actio-policy']
        solver=self.config['roles']['solver'];endpoint=solver['endpoint']
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
        write_json(self.root/'host-config.json',c)

    def prepare_dispatch(self,task):
        m=json.loads(self.run['input']);scope={'campaign':m['transport']['campaign'],'run':self.run['id'],'op':self.op,
            'registration':self.run['id']+':'+self.seat,'seat':self.seat,'stream':self.stream['id'],'epoch':self.epoch,
            'worker':self.stream['worker'],'config_hash':m['transport']['config_hash'],'profile':PROFILE,
            'endpoint':self.config['roles']['solver']['endpoint'],'persona':self.spec['persona'],'task':task}
        ledger=Ledger(self.ledger_path)
        try:ledger.authorize(scope)
        finally:ledger.close()
        super().prepare_dispatch(task)

    def submit(self,task):
        from .facts import Facts
        complete=False;native_usage=None
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
                finally:ledger.close()


def scheduling_transport(store,key,short_root,*,task,config,ledger_path,runtime_type=TransportPort):
    from .scenarios import snapshot,run_engine,failed
    from .terminal import seal_terminal
    from .task_contract import validate_task
    validate_config(config);t=validate_task(task)
    if t['mode']!='transport_stub':raise ContractError('explicit transport task required')
    for seat in t['seats'].values():
        a=store.agent(seat['agent'])
        if a['spec_hash']!=seat['spec_hash'] or a['spec']['pins']!=transport_pins():raise ContractError('transport identity/spec mismatch')
    ledger=Ledger(ledger_path)
    try:
        if ledger.meta['config_hash']!=digest(config):raise ContractError('config not frozen in ledger')
        campaign=ledger.meta['campaign']
        entities={s:t['seats'][s]['agent'] for s in ('A','B')}
        request={'scenario':'social','task_hash':task['sha256'],'a':entities['A'],'b':entities['B'],
                 'config_hash':digest(config),'campaign':campaign,'mode':'transport_stub'}
        def freeze():
            m={'input_contract':INPUT,'execution_mode':'transport_stub','scenario':'social','task':task,'entities':entities,
               'agents':{s['agent']:s['spec_hash'] for s in t['seats'].values()},'memory':{a:snapshot(store,a,'social') for a in entities.values()},
               'pins':transport_pins(),'engine':'concordia.Sequential','source':CONCORDIA,'order':['A','B'],'max_steps':2,'seed':0,'world':[],
               'observation_policy':'scheduling-own-plus-public.v2','gm_private':'SCHEDULING_GM_PRIVATE_AUDIT_ONLY',
               'request':request,'replay_of':None,'transport':{'config':config,'config_hash':digest(config),'campaign':campaign,'profile':PROFILE}}
            validate_manifest(m);return m
        run,fresh=store.begin(key,freeze,request=request)
        if not fresh:return run
        ledger.register(run['id'],json.loads(run['input']))
    finally:ledger.close()
    try:
        def port(*args,**kwargs):return runtime_type(*args,ledger=ledger_path,**kwargs)
        outcome=run_engine(store,run,json.loads(run['input']),short_root,port)
        seal_terminal(store,run['id'],run['epoch'],outcome)
        return store.finish(run['id'],run['epoch'],task=outcome)
    except Exception as e:failed(store,run,e);raise
