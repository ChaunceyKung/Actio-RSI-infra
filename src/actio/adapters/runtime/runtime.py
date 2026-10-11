"""One shared RuntimePort for assistant and external Concordia entities."""
import importlib.metadata
import json
from pathlib import Path
import sys
import time

from actio.contracts.json import ContractError
from actio.contracts.json import digest
from actio.adapters.filesystem.common import file_hash
from actio.adapters.filesystem.common import uid
from actio.adapters.filesystem.common import write_json
from actio.adapters.runtime.facts import Facts
from actio.contracts.wire import wire
from actio.adapters.runtime.mcp_server import DESCRIPTION
from actio.adapters.runtime.mcp_server import SCHEMA
from actio.adapters.runtime.supervisor import Supervisor
from actio.adapters.runtime.supervisor import owned_root

PACKAGE=Path(__file__).resolve().parents[2]
TOOL='mcp__fixture__read_fixture'
REGISTRY=[{'name':TOOL,'description':DESCRIPTION,'parameters':SCHEMA}]
CONCORDIA='b71d202750e23444ce1bf28d9f114bcd88aa41db'
EXE_HASH='7ff077cfa28b81aa33f96aca97911969f8b6499bc1f85e4a6d3ddd16b8aa67d6'


def pins():
    return {'sdk':'0.1.5rc1','runtime':'0.1.5rc1','exe':EXE_HASH,'concordia':CONCORDIA,'mcp':'1.26.0',
            'sdk_wheel':'8d9897e97e8a95fd738cb2c3e2c563951d824e43847ec6f3b0fb172c0729b4d8',
            'runtime_wheel':'d031a5ab4919c572fd7e48c7ef19ec8b1896e93d93c44b0937bb958c528f8acf',
            'reviewed_dsh_source':'5badb15009ae1756c3afe0ae0cef1faafc290ccc','binary_source_mapping':'unproven',
            'profile':'sdk-minimal+actio-v1','provider':'actio-fixture','model':'fixed','policy':'static-read-v1',
            'registry':digest(REGISTRY),'code':{p.relative_to(PACKAGE).as_posix():file_hash(p) for p in sorted(PACKAGE.rglob('*'))
             if p.suffix in {'.py','.mjs','.sql','.json'}}}


def synthetic_spec(name):
    persona='SYNTHETIC_PERSONA_'+name
    return {'version':1,'persona':persona,'persona_source':'synthetic-inline-v1','persona_hash':digest(persona),
            'prompt_version':'fixture-v1','pins':pins(),'memory_shares':[['assistant','social']]}


def verify_runtime():
    for package,expected in [('deepseek-harness-sdk','0.1.5rc1'),('deepseek-harness-runtime-bin','0.1.5rc1'),('mcp','1.26.0')]:
        if importlib.metadata.version(package)!=expected:
            raise ContractError('installed distribution pin mismatch: '+package)
    dist=importlib.metadata.distribution('deepseek-harness-runtime-bin')
    exes=[dist.locate_file(p) for p in dist.files if Path(p).name=='deepseek-harness-sdk-runtime-win-x64.exe']
    if len(exes)!=1 or file_hash(exes[0])!=EXE_HASH:
        raise ContractError('runtime executable pin mismatch')


class RuntimePort:
    @staticmethod
    def expected_pins():return pins()
    capabilities={'fresh_session':True,'sequential_turn':True,'readonly_mcp':True,'bounded_stop':True,
                  'local_status':True,'resume':False,'reopen':False,'fork':False,'catchup':False,
                  'semantic_cancel':False,'world_restore':False,'evaluator':False,'live_provider':False}

    @classmethod
    def require(cls, capability):
        if not cls.capabilities.get(capability,False):
            raise ContractError('unsupported_capability: '+capability)

    def __init__(self, store, run, agent, short_root, *, deadlines=None, limits=None):
        self.s,self.run,self.agent=store,run,agent
        self.epoch=run['epoch']
        store.fence(run['id'],self.epoch)
        self.spec=store.agent(agent)['spec']
        if self.spec['pins']!=self.expected_pins():
            raise ContractError('immutable spec runtime pins changed; create a new explicit spec identity')
        inputs=json.loads(run['input'])
        if inputs['agents'].get(agent)!=store.agent(agent)['spec_hash']:
            raise ContractError('agent spec not frozen in run')
        self.deadlines={'ready':25,'result':15,'drained':4,'closed':3,**(deadlines or {})}
        self.root=owned_root(short_root,run['id'])
        self.job_name='Local\\Actio-'+uid()
        self.stream=store.allocate_worker(run['id'],self.epoch,self.root,self.job_name,agent)
        self.binding={'run':run['id'],'epoch':self.epoch,'creation':self.stream['creation'],'session':self.stream['native_id'],'nonce':uid()}
        self.supervisor=Supervisor(self.root,self.job_name,limits=limits)
        self.policy={'binding':self.binding,'tool':TOOL,'toolHash':file_hash(PACKAGE/'mcp_server.py'),
                     'registryHash':digest(REGISTRY),'keys':['ok'],'maxCalls':4,'expires':int(time.time()*1000)+120000}
        self.op=None
        self.marker=None
        self.closed=False
        try:
            self.prepare()
        except BaseException as error:
            self.cleanup_after_error(error)
            raise

    def cleanup_after_error(self, error):
        try:
            self.close(force=True)
        except Exception as cleanup:
            self.s.audit(self.run['id'],self.op,'cleanup_failure',{'reason':str(cleanup)})
            error.add_note('cleanup failed; lease retained: '+str(cleanup))

    def prepare(self):
        """Frozen config assembled before launch; no dynamic approval transport."""
        limits=self.supervisor.limits
        write_json(self.root/'policy.json',self.policy)
        write_json(self.root/'active.json',{**self.binding,'op':'not-dispatched'})
        patch=[{'id':x,'disabled':True} for x in ['llm-deepseek','persistent-bash','persistent-pwsh','terminal-bash','terminal-pwsh','pty']]
        patch += [{'id':'tools','config':{'mode':'native'}},
                  {'id':'system-prompt','config':{'personaPrefix':self.spec['persona'],'includeHarnessIdentity':False,'includeRuntimeContext':False}},
                  {'id':'sessions','config':{'root':str(self.root/'home/sessions'),'compression':'none'}},
                  {'insert':[
                    {'id':'actio-mcp','name':'@deepseek-ai/dsh-mcp-client','config':{'serverName':'fixture','transport':'stdio','command':sys.executable,
                     'args':['-m','actio.mcp_server',str(self.root)],'cwd':str(self.root),'toolCallTimeoutMs':10000,'failOnStartupError':True,'reconnect':{'enabled':False}}},
                    {'id':'actio-policy','name':(PACKAGE/'adapters/transport/plugins/guard.mjs').as_uri(),'config':{'policy':str(self.root/'policy.json'),'binding':self.binding,
                     'tool':str(PACKAGE/'mcp_server.py'),'spool':str(self.root/'bridge.jsonl'),'active':str(self.root/'active.json'),'limits':limits}},
                    {'id':'actio-fixture','name':(PACKAGE/'adapters/transport/fixtures/provider.mjs').as_uri(),'config':{'capture':str(self.root/'provider.jsonl'),'limits':limits}}]}]
        write_json(self.root/'profile.patch.yml',patch)
        write_json(self.root/'host-config.json',{'limits':limits,'sdk':{'provider':'actio-fixture','model':'fixed','max_tokens':128,
            'cwd':str(self.root),'runtime_cwd':str(self.root),'dsh_home':str(self.root/'home'),'profile':'sdk-minimal',
            'patches':[str(self.root/'profile.patch.yml')],'initialize_timeout_seconds':20,'request_timeout_seconds':5,'shutdown_timeout_seconds':1}})

    def start(self):
        try:
            verify_runtime()
            self.s.dispatch_fence(self.run['id'],self.epoch)
            self.supervisor.start()
            self.s.db.execute("UPDATE worker SET pid=?,state='running' WHERE id=?",(self.supervisor.proc.pid,self.stream['worker']))
            self.supervisor.wait('ready',self.deadlines['ready'],self.record)
        except BaseException as error:
            self.cleanup_after_error(error)
            raise
        return self

    def record(self, record):
        self.s.fence(self.run['id'],self.epoch)
        if any(self.root.glob('*.limit')):
            raise ContractError('data_limit_exceeded; prefix retained')
        self.s.audit(self.run['id'],self.op,'host_'+record['kind'],record)
        if record['kind']=='accepted':
            if record['op']!=self.op:
                raise ContractError('unbound receipt')
            self.s.op_update(self.op,self.epoch,receipt=record['receipt'],state='accepted')

    def submit(self, task):
        self.s.fence(self.run['id'],self.epoch)
        self.op=self.s.intent(self.run['id'],self.epoch,self.stream['id'],task)
        task=self.bind_task(task)
        if task.get('tool'):
            task={**task,'callId':task.get('callId',uid()),'args':{**task['args'],'op':self.op}}
        try:
            self.prepare_dispatch(task)
            self.supervisor.send({'kind':'submit','session':self.stream['native_id'],'op':self.op,'task':task})
            result=self.supervisor.wait('result',self.deadlines['result'],self.record)
            self.s.op_update(self.op,self.epoch,state='draining',answer=result['answer'],terminal=result['terminal'])
            self.supervisor.send({'kind':'drain','op':self.op})
            drained=self.supervisor.wait('drained',self.deadlines['drained'],self.record)
            self.marker=drained['marker']
            if self.marker.get('nonce')!=self.binding['nonce']:
                raise ContractError('untrusted flush origin')
            self.s.op_update(self.op,self.epoch,barrier=wire(self.marker))
            self.drain()
            return {'op':self.op,'answer':result['answer'],'stream':self.stream['id'],'marker':self.marker}
        except BaseException as e:
            try:
                self.s.op_update(self.op,self.epoch,state='needs_reconcile',reason=type(e).__name__+': '+str(e))
            except Exception as record_error:
                e.add_note('failure ledger update failed: '+str(record_error))
            self.cleanup_after_error(e)
            raise

    def bind_task(self,task):
        return {**task,'op':self.op}

    def prepare_dispatch(self,task):
        write_json(self.root/'active.json',{**self.binding,'op':self.op})

    def drain(self):
        facts=Facts(self.s)
        facts.collect(self.stream['id'],**{k:self.supervisor.limits[k] for k in ('item','total','count')})
        facts.certify(self.op,self.marker)
        self.s.audit(self.run['id'],self.op,'canonical_committed',{'through':self.marker['through'],'stream':self.stream['id']})
        # Domain owners must explicitly confirm their effect before execution_complete.
        self.s.op_update(self.op,self.epoch,state='awaiting_domain_effect')

    def confirm_effect(self):
        o=self.s.row('SELECT * FROM operation WHERE id=?',(self.op,))
        Facts(self.s).certify(self.op,json.loads(o['barrier']))
        effect=self.s.row('SELECT * FROM domain_receipt WHERE op=? AND stream=?',(self.op,self.stream['id']))
        if not effect or effect['seq']>self.marker['through']:
            raise ContractError('required domain effect not committed')
        self.s.op_update(self.op,self.epoch,state='execution_complete')

    def stop(self, reason='explicit stop request; no semantic cancellation'):
        self.s.fence(self.run['id'],self.epoch)
        with self.s.tx():
            self.s.fence(self.run['id'],self.epoch)
            self.s.db.execute('UPDATE run SET stop_requested=1 WHERE id=?',(self.run['id'],))
            self.s.audit(self.run['id'],self.op,'stop_requested',{'reason':reason})
        if self.op:
            self.s.op_update(self.op,self.epoch,state='needs_reconcile',reason=reason)
        self.close(force=True)

    def close(self, force=False):
        if self.closed:
            return
        error=None
        try:
            if not force and self.supervisor.proc and self.supervisor.proc.poll() is None:
                self.supervisor.send({'kind':'close'})
                self.supervisor.wait('closed',self.deadlines['closed'],self.record)
        except Exception as e:
            error=e
            if self.op:
                self.s.op_update(self.op,self.epoch,state='needs_reconcile',reason='close failed: '+str(e))
        finally:
            report=self.supervisor.close()
            self.s.db.execute("UPDATE worker SET state='reaped',report=? WHERE id=?",(wire(report),self.stream['worker']))
            self.closed=True
        if error:
            raise error

    def __enter__(self):
        return self.start()

    def __exit__(self, typ, value, tb):
        try:
            self.close(force=typ is not None)
        except Exception as cleanup:
            if value is None:
                raise
            self.s.audit(self.run['id'],self.op,'cleanup_failure',{'reason':str(cleanup)})
            value.add_note('cleanup failure: '+str(cleanup))
