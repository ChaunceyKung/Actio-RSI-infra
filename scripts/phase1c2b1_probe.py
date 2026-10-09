"""Real SDK/binary/official adapter -> loopback probe, using only a task-created fake key.

Chat Completions events adapted from DeepSeek MIT mock-server.ts at fixed 183f08e9.
Copyright (c) 2026 DeepSeek; license: docs/validation/phase1c2a1/DSH_LICENSE.txt.
No upstream SDK/serialization/adapter code replaced. Raw failures are append-only.
"""
import argparse
import datetime
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import threading
import uuid

from actio.common import canonical,write_json,file_hash
from actio.runtime import RuntimePort,synthetic_spec,PACKAGE,pins
from actio.store import Store

ROOT=Path(__file__).resolve().parents[1]


def events(case):
    usage={'prompt_tokens':12,'completion_tokens':5,'total_tokens':17,'prompt_cache_hit_tokens':4,'prompt_cache_miss_tokens':8}
    finish={'choices':[{'index':0,'delta':{},'finish_reason':'stop'}]}
    if case!='trailing':finish['usage']=usage
    rows=[{'choices':[{'index':0,'delta':{'role':'assistant','content':'propose:morning'}}]},finish]
    if case=='trailing':rows.append({'choices':[],'usage':usage})
    return ['data: '+canonical(r)+'\n\n' for r in [{**r,'id':'chatcmpl-local','model':'gpt-5.6','object':'chat.completion.chunk','created':0} for r in rows]]+([] if case=='missing-done' else ['data: [DONE]\n\n'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--case',choices=['attached','trailing','missing-done'],required=True);a=p.parse_args()
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    root=Path('D:/actio-c2b1-probe')/stamp;root.mkdir(parents=True)
    secret='ACTIO_FAKE_'+uuid.uuid4().hex
    log={'status':'FAIL','case':a.case,'root':str(root),'model_requests':0,'wire':[],'runtime_pins':pins(),'diagnostic':True,'max_receives':1}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            self.connection.settimeout(3)
            size=int(self.headers.get('Content-Length','0'));assert 0<size<=65536
            raw=self.rfile.read(size)
            log['wire'].append({'path':self.path,'credential_present':bool(self.headers.get('Authorization')),'body':json.loads(raw)})
            if self.path!='/v1/chat/completions' or len(log['wire'])>1:self.send_error(403);return
            self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
            self.wfile.write(''.join(events(a.case)).encode());self.wfile.flush()
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever);thread.start()
    class ProbePort(RuntimePort):
        def prepare(self):
            super().prepare();patch=json.loads((self.root/'profile.patch.yml').read_bytes())
            patch.extend([{'id':x,'disabled':True} for x in ['deepseek-llm-api-extensions','session-log-deepseek','plugin-package-inventory-deepseek']])
            insertion=next(x for x in patch if 'insert' in x)
            insertion['insert']=[x for x in insertion['insert'] if x['id']=='actio-policy']
            insertion['insert'].append({'id':'actio-probe','name':(ROOT/'scripts/phase1c2b1_probe.mjs').as_uri(),'config':{'capture':str(self.root/'probe.jsonl'),'endpoint':f'http://127.0.0.1:{server.server_port}'}})
            patch.extend([{'id':'session-title','disabled':True},{'id':'llm-retry','disabled':True}])
            insertion['insert'].append({'id':'llm-pi-ai','name':'@deepseek-ai/dsh-llm-pi-ai','config':{'providers':{'actio-tokenkey':{
                'apiKeyEnv':'ACTIO_SOLVER_KEY','api':'openai-completions','baseURL':f'http://127.0.0.1:{server.server_port}/v1',
                'models':[{'id':'gpt-5.6','contextWindow':32768,'maxTokens':512,'reasoningEfforts':False}],
                'compat':{'maxTokensField':'max_tokens','supportsDeveloperRole':False,'supportsStore':False},
                'streamIdleTimeoutMs':8000,'retryPolicy':{'mode':'normal','maxRetries':0}}}}})
            write_json(self.root/'profile.patch.yml',patch)
            c=json.loads((self.root/'host-config.json').read_bytes());c['sdk'].update(provider='actio-tokenkey',model='gpt-5.6',max_tokens=256)
            c['credential_ref']='ACTIO_SOLVER_KEY'
            self.supervisor.launch_credential={'ref':'ACTIO_SOLVER_KEY','value':secret}
            write_json(self.root/'host-config.json',c)
    s=Store(root/'ledger.sqlite',create=True);port=None
    try:
        s.agent('PROBE',synthetic_spec('PROBE'));run,_=s.begin('probe',{'scenario':'assistant','agents':{'PROBE':s.agent('PROBE')['spec_hash']}})
        with ProbePort(s,run,'PROBE',root) as port:
            result=port.submit({'role':'proposer','public':'Pick a cleanup time.','own_available':['morning'],
                                'action_spec':{'output_type':'choice','options':['propose:morning','propose:afternoon'],'call_to_action':'Choose one action.','tag':None}})
        log['result']=result
        assert a.case in ('attached','trailing') and result['answer']=='propose:morning'
        assert len(log['wire'])==1
        assert 'answer' not in canonical(log['wire'][0]['body'])
        log['status']='PASS'
    except Exception as e:
        log['error']={'type':type(e).__name__,'reason':str(e)}
        if a.case=='missing-done' and len(log['wire'])==1:log['status']='PASS_EXPECTED_INCOMPLETE'
    finally:
        if port:port.close(force=True)
        server.shutdown();server.server_close();thread.join(5)
        captures=[json.loads(line) for p in root.rglob('probe.jsonl') for line in p.read_text(encoding='utf8').splitlines()]
        log.update(source_hashes={n:file_hash(ROOT/n) for n in ('scripts/phase1c2b1_probe.py','scripts/phase1c2b1_probe.mjs')},local_http_requests=len(log['wire']),server_thread_alive=thread.is_alive(),workers=s.rows('SELECT * FROM worker'),operations=s.rows('SELECT * FROM operation'),probe_capture=captures)
        s.close();log['files']={str(p.relative_to(root)):file_hash(p) for p in root.rglob('*') if p.is_file() and 'node_modules' not in p.parts}
        assert all(secret.encode() not in p.read_bytes() for p in root.rglob('*') if p.is_file()),'fake credential persisted'
        log['credential_scan']='PASS'
        folder=ROOT/'docs/validation/phase1c2b1/evidence';folder.mkdir(parents=True,exist_ok=True)
        with (folder/('probe-'+stamp+'.json')).open('x',encoding='utf8') as f:json.dump(log,f,ensure_ascii=False,indent=2)
    print(json.dumps({'status':log['status'],'root':str(root),'local_http_requests':len(log['wire']),'error':log.get('error')}))
    return 0 if log['status'].startswith('PASS') else 1


if __name__=='__main__':raise SystemExit(main())
