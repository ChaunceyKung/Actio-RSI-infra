import json
from pathlib import Path
import subprocess
import sys
import unittest
import uuid
from actio.common import clean_env
from actio.common import write_json
from actio.adapters.filesystem.credentials import scan
from actio.profiles.gateway_base import template
from actio.adapters.persistence.ledger import Ledger
from actio.interfaces.store import Store
from actio.adapters.transport.transport import transport_spec
from actio.adapters.transport.transport import TransportPort
from actio.adapters.transport.transport import PACKAGE
from actio.tasks.registry import task_card
from actio.interfaces.export import export_bundle
from actio.interfaces.transport_export import export_campaign
from gateway_stub import GatewayStub
import test_gateway

class GatewayLifecycle(unittest.TestCase):
    setUp=test_gateway.Gateway.setUp
    case=test_gateway.Gateway.case

    def test_01_two_controls_one_run_and_no_replay(self):
        with GatewayStub(self.root,[{'text':'propose:morning'},{'text':'accept'}],self.secret) as server:
            c=template(mode='tokenkey_rehearsal',endpoint=server.endpoint);c['plan']=['compatible']
            c['authority']={'id':uuid.uuid4().hex,'root':str(self.root/'authority')}
            l=Ledger(self.root/'budget.sqlite',config=c);l.close()
            s=Store(self.root/'ledger.sqlite',create=True)
            for a in ('A','B'):s.agent(a,transport_spec(a,c))
            task=task_card('compatible',{a:{'agent':a,'spec_hash':s.agent(a)['spec_hash']} for a in ('A','B')},c['mode']);s.close()
            write_json(self.root/'input.json',{'config':c,'task':task})
            code="""import sys,json,pathlib
from actio.interfaces.store import Store
from actio.application.transport import scheduling_transport
root=pathlib.Path(sys.argv[1]);data=json.loads((root/'input.json').read_bytes());secret=sys.stdin.readline().strip();s=Store(root/'ledger.sqlite')
try:
 r=scheduling_transport(s,'shared',root,task=data['task'],config=data['config'],ledger_path=root/'budget.sqlite',credential=secret)
 print(json.dumps({'run':r['id']}))
finally:s.close()
"""
            commands=[sys.executable,'-X','utf8','-I','-B','-c',code,str(self.root)]
            children=[subprocess.Popen(commands,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=self.root,env=clean_env(self.root)) for _ in range(2)]
            outputs=[]
            try:
                for child in children:child.stdin.write((self.secret+'\n').encode());child.stdin.flush()
                for child in children:
                    out,err=child.communicate(timeout=90);self.assertEqual(child.returncode,0,err.decode());outputs.append(json.loads(out))
            finally:
                for child in children:
                    if child.poll() is None:child.kill();child.wait(10)
        self.assertEqual(outputs[0]['run'],outputs[1]['run']);self.assertEqual(len(server.receives),2)
        s=Store(self.root/'ledger.sqlite')
        from actio.application.transport import scheduling_transport
        before=s.rows('SELECT * FROM worker');r=scheduling_transport(s,'shared',self.root,task=task,config=c,ledger_path=self.root/'budget.sqlite',credential=self.secret)
        self.assertEqual(s.rows('SELECT * FROM worker'),before);s.close()
        export_bundle(self.root/'ledger.sqlite','shared',self.root/'bundle')
        result=export_campaign(self.root/'budget.sqlite',[self.root/'bundle'],server.receives,self.root/'campaign')
        self.evidence.update(commands=commands,outputs=outputs,receives=server.receives,campaign=result,workers=before,credential_scan=scan(self.root,self.secret))

    def test_02_interruptions_keep_unknown_and_authority(self):
        for name,needle in [('reserved','const wireHash='),('sending',"log({kind:'sending'"),('before-settle',"a.response.chunks.push(chunk);yield chunk")]:
            class Interrupted(TransportPort):
                def prepare(port):
                    super().prepare();source=(PACKAGE/'adapters/transport/plugins/transport.mjs').read_text(encoding='utf8').replace("'./common.mjs'",repr((PACKAGE/'adapters/transport/plugins/common.mjs').as_uri()))
                    source=source.replace(needle,("if(chunk.type==='finish') process.exit(97)\n        " if name=='before-settle' else 'process.exit(97)\n    ')+needle)
                    p=port.root/'interrupt.mjs';p.write_text(source,encoding='utf8');cfg=json.loads((port.root/'profile.patch.yml').read_bytes())
                    for item in cfg:
                        for e in item.get('insert',[]):
                            if e['id']=='actio-transport':e['name']=p.as_uri()
                    write_json(port.root/'profile.patch.yml',cfg)
            v=self.case(name,[{'text':'propose:morning'}],runtime_type=Interrupted)
            self.assertEqual(len(v['receives']),1 if name=='before-settle' else 0)
            self.assertEqual(v['ledger']['attempts'][0]['state'],'unknown')
            self.assertIsNone(v['ledger']['totals']['cost_minor'])
            with self.assertRaises(FileExistsError):Ledger(Path(v['root'])/'replacement.sqlite',config=v['ledger']['meta']['config'])

if __name__=='__main__':unittest.main()
