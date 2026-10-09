"""Bounded synthetic service; response plans never enter the actor/worker configuration.

Event shapes adapted from DeepSeek MIT mock-server.ts @ 183f08e9.
Copyright (c) 2026 DeepSeek; see docs/validation/phase1c2a1/DSH_LICENSE.txt.
"""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import hashlib
import json
import threading
import time

from actio.common import canonical,write_json


def response(plan):
    case=plan.get('case','attached');usage={'prompt_tokens':12,'completion_tokens':5,'total_tokens':17,
                                          'prompt_cache_hit_tokens':4,'prompt_cache_miss_tokens':8}
    if case=='negative':usage['completion_tokens']=-1
    if case=='fractional':usage['prompt_tokens']=1.5
    if case=='contradiction':usage['total_tokens']=99
    if case=='cache-conflict':usage['prompt_tokens_details']={'cached_tokens':2}
    if case=='over-limit':usage.update(completion_tokens=100,total_tokens=112)
    if case in ('429','500'):return int(case),json.dumps({'error':{'message':'synthetic '+case}}),'application/json'
    if case=='redirect':return 307,'','text/plain'
    if case=='empty':return 200,'data: [DONE]\n\n','text/event-stream'
    if case=='malformed':return 200,'data: {invalid}\n\ndata: [DONE]\n\n','text/event-stream'
    finish={'choices':[{'index':0,'delta':{},'finish_reason':'stop'}]}
    rows=[{'choices':[{'index':0,'delta':{'role':'assistant','content':plan['text']}}]},finish]
    if 'reasoning' in plan:
        rows[0]['choices'][0]['delta']={'role':'assistant','reasoning_content':plan['reasoning']}
        rows.insert(1,{'choices':[{'index':0,'delta':{'content':plan['text']}}]})
    if case not in ('missing-usage','trailing'):finish['usage']=usage
    if case in ('trailing','override'):
        if case=='override':finish['usage']={'prompt_tokens':2,'completion_tokens':1,'total_tokens':3}
        rows.append({'choices':[],'usage':usage})
    raw=''.join('data: '+json.dumps(r,separators=(',',':'))+'\n\n' for r in rows)
    if case!='missing-done':raw+='data: [DONE]\n\n'
    return 200,raw,'text/event-stream'


class ChatStub:
    def __init__(self,root,plans):
        self.root=root;self.plans=list(plans);self.receives=[];self.lock=threading.Lock();self.stop=threading.Event()
        owner=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):self.send_error(405)
            def do_POST(self):
                self.connection.settimeout(4)
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=65536 or self.path!='/chat/completions':self.send_error(403);return
                raw=self.rfile.read(size).decode('utf8')
                with owner.lock:
                    index=len(owner.receives)
                    plan=owner.plans[index] if index<len(owner.plans) else {'case':'429','text':'','exhausted':True}
                    status,body,kind=response(plan)
                    value={'index':index,'attempt':self.headers.get('X-Actio-Attempt'),'path':self.path,'method':'POST',
                           'raw':raw,'wire_hash':hashlib.sha256(raw.encode()).hexdigest(),'headers':dict(self.headers),
                           'response':{'status':status,'raw':body,'sha256':hashlib.sha256(body.encode()).hexdigest()},
                           'case':plan.get('case','attached')}
                    owner.receives.append(value);write_json(owner.root/'receives.json',owner.receives)
                try:
                    if plan.get('case')=='deadline':owner.stop.wait(4)
                    self.send_response(status);self.send_header('Content-Type',kind)
                    if status==307:self.send_header('Location','https://provider.invalid/not-authorized')
                    self.end_headers();self.wfile.write(body.encode());self.wfile.flush()
                except (BrokenPipeError,ConnectionError,OSError):pass
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever)
        self.endpoint=f'http://127.0.0.1:{self.server.server_port}'

    def __enter__(self):self.thread.start();return self
    def __exit__(self,*args):
        self.stop.set();self.server.shutdown();self.server.server_close();self.thread.join(5)
        assert not self.thread.is_alive()
        write_json(self.root/'service.json',{'endpoint':self.endpoint,'max_receives':len(self.plans),
            'receives':len(self.receives),'joined':True,'diagnostic':False,'model_requests':0})
