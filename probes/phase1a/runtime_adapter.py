"""EXPERIMENTAL shared assistant/Concordia adapter. Official SDK, no agent loop."""
import json
import sys
import threading
import time
from pathlib import Path
from deepseek_harness import DeepSeekHarness
from common import ROOT, digest, jsonl, write_json, file_hash

TOOL = 'mcp__fixture__read_fixture'

def make_policy(grants=(), *, max_calls=20, run='fixture-run', lease='lease-one'):
    tool_version = file_hash(ROOT/'fixtures/mcp_server.py')
    binding = {'run':run,'lease':lease,'tool':TOOL,'toolVersion':tool_version,
               'keys':['ok','error','timeout','hold','transport'],'maxCalls':max_calls}
    result = {'binding':binding,'grants':{}}
    for g in grants:
        op, scope = g['op'], g.get('scope','assistant')
        args = g.get('args', {'key':'ok','op':op})
        grant = {'requestHash':digest({'name':TOOL,'arguments':args}), 'policyHash':digest(binding),
                 'run':run,'scope':scope,'lease':lease,'expires':int(time.time()*1000)+300000,
                 'toolVersion':tool_version}
        grant.update(g.get('override',{}))
        result['grants'][op+':call'] = grant
    return result

class Adapter:
    def __init__(self, root, *, policy=None, persona='SYNTHETIC PERSONA', mcp=True, init_hang=False, initialize_timeout=20):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.records = []
        self.trace = self.root / 'plugin.jsonl'
        write_json(self.root / 'policy.json', policy or make_policy())
        write_json(self.root / 'data.json', {'ok':'SYNTHETIC FILE VALUE'})
        patch = [{'id':x,'disabled':True} for x in ['llm-deepseek','persistent-bash','persistent-pwsh','terminal-bash','terminal-pwsh','pty']]
        patch += [{'id':'tools','config':{'mode':'native'}},
                  {'id':'system-prompt','config':{'personaPrefix':persona,'includeHarnessIdentity':False,'includeRuntimeContext':False}},
                  {'id':'sessions','config':{'root':str(self.root/'home/sessions'),'compression':'none'}}]
        plugins = []
        if mcp:
            plugins.append({'id':'probe-mcp','name':'@deepseek-ai/dsh-mcp-client','config':{
                'serverName':'fixture','transport':'stdio','command':sys.executable,
                'args':[str(ROOT/'fixtures/mcp_server.py'),str(self.root)],'cwd':str(self.root),
                'toolCallTimeoutMs':700,'failOnStartupError':True,'reconnect':{'enabled':False}}})
        plugins.append({'id':'probe-provider-policy','name':(ROOT/'fixtures/provider_policy.mjs').as_uri(),
                        'config':{'trace':str(self.trace),'policy':str(self.root/'policy.json'),
                                  'mcpServer':str(ROOT/'fixtures/mcp_server.py'),'initHang':init_hang}})
        patch.append({'insert':plugins})
        write_json(self.root/'probe.patch.yml',patch)
        self.harness = DeepSeekHarness(provider='phase1a-fixture',model='fixed',max_tokens=100,
            cwd=str(self.root),runtime_cwd=str(self.root),dsh_home=str(self.root/'home'),profile='sdk-minimal',
            patches=(str(self.root/'probe.patch.yml'),),initialize_timeout_seconds=initialize_timeout,
            request_timeout_seconds=3,shutdown_timeout_seconds=0.5)
        self.pid = None

    def start(self):
        self.harness.start()
        # Inspection only; startup uses exclusively public profile/patch/config APIs.
        self.pid = self.harness.client._proc.pid
        return self

    def run(self, task, session='assistant', deadline=12, on_notification=None):
        self.start()
        box = {}
        def work():
            try: box['result'] = self.harness.run(json.dumps(task),session_id=session,on_notification=on_notification)
            except BaseException as e: box['error'] = e
        worker = threading.Thread(target=work,daemon=True)
        start = time.monotonic()
        worker.start()
        worker.join(deadline)
        if worker.is_alive():
            self.close()
            worker.join(2)
            self.records.append({'op':task['op'],'status':'unknown','reason':'run deadline; termination is not semantic cancellation','elapsed':time.monotonic()-start})
            raise TimeoutError('bounded run deadline; needs_reconcile; no automatic retry')
        if 'error' in box:
            self.records.append({'op':task['op'],'status':'unknown','error':str(box['error']),'elapsed':time.monotonic()-start})
            raise box['error']
        result = box['result']
        self.records.append({'op':task['op'],'session':session,'status':'idle-observed','elapsed':time.monotonic()-start,
            'answer':result.final_response,'finish_reason':result.finish_reason,'events':result.events,
            'notifications':[{'method':n.method,'payload':n.payload} for n in result.notifications]})
        return result

    def barrier(self, session, timeout=3):
        """Wait for a logged *explicit flush*, not just SDK idle."""
        until = time.monotonic()+timeout
        last = max((e.get('seq',-1) for r in self.records if r.get('session') == session for e in r.get('events',[])),default=-1)
        while time.monotonic()<until:
            found = [r for r in jsonl(self.trace) if r['kind']=='native-barrier' and r['session']==session and r.get('through',-1)>=last]
            if found: return found[-1]
            time.sleep(.01)
        raise TimeoutError('native flush marker missing')

    def close(self):
        proc=self.harness.client._proc
        started=time.monotonic()
        self.harness.close()
        if proc is not None:
            write_json(self.root/'runtime-close.json',{'pid':proc.pid,'returncode':proc.poll(),'elapsed_seconds':time.monotonic()-started})
        write_json(self.root/'sdk.json',self.records)

    def __enter__(self): return self.start()
    def __exit__(self,*_): self.close()
