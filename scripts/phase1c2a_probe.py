"""Real SDK/binary/official adapter -> loopback probe, using only a task-created fake key.

SSE fixture structure adapted from DeepSeek MIT mock-server.ts at fixed 5badb150.
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


def events():
    return [
        {'type':'message_start','message':{'id':'stub_message','model':'deepseek-v4-flash','usage':{'input_tokens':3,'output_tokens':0}}},
        {'type':'content_block_start','index':0,'content_block':{'type':'text','text':''}},
        {'type':'content_block_delta','index':0,'delta':{'type':'text_delta','text':'propose:morning'}},
        {'type':'content_block_stop','index':0},
        {'type':'message_delta','delta':{'stop_reason':'end_turn'},'usage':{'output_tokens':5}},
        {'type':'message_stop'}]


def main():
    p=argparse.ArgumentParser();p.add_argument('--case',choices=['success','429','explicit-adapter'],default='success');a=p.parse_args()
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    root=Path('D:/actio-c2a-probe')/stamp;root.mkdir(parents=True)
    log={'status':'FAIL','case':a.case,'root':str(root),'model_requests':0,'wire':[],'runtime_pins':pins()}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            self.connection.settimeout(3)
            size=int(self.headers.get('Content-Length','0'));assert 0<size<=65536
            raw=self.rfile.read(size)
            log['wire'].append({'path':self.path,'headers':dict(self.headers),'body':json.loads(raw)})
            if self.path!='/v1/messages' and not (a.case=='429' and self.path=='/chat/completions'):self.send_error(404);return
            if a.case=='429':
                self.send_response(429);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(b'{"error":{"type":"rate_limit_error","message":"local synthetic 429"}}');return
            self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
            self.wfile.write(''.join('data: '+canonical(e)+'\n\n' for e in events()).encode());self.wfile.flush()
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever);thread.start()
    class ProbePort(RuntimePort):
        def prepare(self):
            super().prepare();patch=json.loads((self.root/'profile.patch.yml').read_bytes())
            patch=[x for x in patch if x.get('id')!='llm-deepseek']
            patch[-1]['insert']=[x for x in patch[-1]['insert'] if x['id']=='actio-policy']
            patch[-1]['insert'].append({'id':'actio-probe','name':(ROOT/'scripts/phase1c2a_probe.mjs').as_uri(),'config':{'capture':str(self.root/'probe.jsonl'),'endpoint':f'http://127.0.0.1:{server.server_port}'}})
            patch.extend([{'id':'llm-retry','disabled':True},
                          {'id':'llm-deepseek','config':{'baseURL':f'http://127.0.0.1:{server.server_port}',
                           'apiKeyEnv':'ACTIO_STUB_KEY','thinking':'disabled','reasoningEffort':'off','maxTokens':64,
                           'streamIdleTimeoutMs':1500,'retryPolicy':{'mode':'normal','maxRetries':0}}}])
            if a.case=='explicit-adapter':
                provider=patch.pop();provider.update(id='explicit-messages',name='@deepseek-ai/dsh-llm-deepseek-api-key')
                patch.extend([{'id':'llm-deepseek','disabled':True},{'insert':[provider]}])
            write_json(self.root/'profile.patch.yml',patch)
            c=json.loads((self.root/'host-config.json').read_bytes());c['sdk'].update(provider='deepseek-official',model='deepseek-v4-flash',max_tokens=64,
                      env={'ACTIO_STUB_KEY':'actio-probe-fake-no-value'},reasoning_effort='off')
            write_json(self.root/'host-config.json',c)
    s=Store(root/'ledger.sqlite',create=True);port=None
    try:
        s.agent('PROBE',synthetic_spec('PROBE'));run,_=s.begin('probe',{'scenario':'assistant','agents':{'PROBE':s.agent('PROBE')['spec_hash']}})
        with ProbePort(s,run,'PROBE',root) as port:
            result=port.submit({'role':'proposer','public':'Pick a cleanup time.','own_available':['morning'],
                                'action_spec':{'output_type':'choice','options':['propose:morning','propose:afternoon'],'call_to_action':'Choose one action.','tag':None}})
        log['result']=result
        assert a.case=='success' and result['answer']=='propose:morning'
        assert len(log['wire'])==1
        assert 'answer' not in canonical(log['wire'][0]['body'])
        log['status']='PASS'
    except Exception as e:
        log['error']={'type':type(e).__name__,'reason':str(e)}
        if a.case=='429' and len(log['wire'])==1:log['status']='PASS_EXPECTED_PROTOCOL_FAILURE'
    finally:
        if port:port.close(force=True)
        server.shutdown();server.server_close();thread.join(5)
        captures=[json.loads(line) for p in root.rglob('probe.jsonl') for line in p.read_text(encoding='utf8').splitlines()]
        log.update(local_http_requests=len(log['wire']),server_thread_alive=thread.is_alive(),workers=s.rows('SELECT * FROM worker'),operations=s.rows('SELECT * FROM operation'),probe_capture=captures)
        s.close();log['files']={str(p.relative_to(root)):file_hash(p) for p in root.rglob('*') if p.is_file() and 'node_modules' not in p.parts}
        folder=ROOT/'docs/validation/phase1c2a/evidence';folder.mkdir(parents=True,exist_ok=True)
        with (folder/('probe-'+stamp+'.json')).open('x',encoding='utf8') as f:json.dump(log,f,ensure_ascii=False,indent=2)
    print(json.dumps({'status':log['status'],'root':str(root),'local_http_requests':len(log['wire']),'error':log.get('error')}))
    return 0 if log['status'].startswith('PASS') else 1


if __name__=='__main__':raise SystemExit(main())
