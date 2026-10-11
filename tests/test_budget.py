import json
from pathlib import Path
import subprocess
import sys
import unittest
import uuid

from actio.common import canonical
from actio.common import write_json
from actio.common import clean_env
from actio.common import ContractError
from actio.adapters.persistence.ledger import Ledger
from actio.evidence.accounting import verify_snapshot
from actio.adapters.transport.transport import TransportPort
from actio.adapters.transport.transport import PACKAGE
from actio.profiles.transport import config
from actio.interfaces.transport_export import export_campaign
from chat_stub import ChatStub

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from support.transport_case import run


class Budget(unittest.TestCase):
    def setUp(self):
        self.root=Path('D:/actio-c2a1-budget')/uuid.uuid4().hex[:12];self.root.mkdir(parents=True)
        self.evidence={'root':str(self.root),'cases':[],'model_requests':0}

    def test_01_two_independent_controls_compete_for_last_real_send(self):
        with ChatStub(self.root,[{'text':'propose:morning'}]) as service:
            cfg=config(service.endpoint,1);path=self.root/'budget.sqlite';ledger=Ledger(path,config=cfg);ledger.close()
            write_json(self.root/'config.json',cfg)
            code='''import sys,json,pathlib
sys.path.insert(0,sys.argv[1])
from support.transport_case import run
from actio.common import write_json
root=pathlib.Path(sys.argv[2]);cfg=json.loads((root.parent/'config.json').read_bytes())
r=run(root,cfg['roles']['solver']['endpoint'],root.parent/'budget.sqlite',cfg)
write_json(root/'child-result.json',r)
'''
            children=[]
            for name in ('one','two'):
                folder=self.root/name;folder.mkdir()
                isolated=clean_env(folder);isolated.update(DEEPSEEK_API_KEY='synthetic-wrong-key-never-use',
                    DEEPSEEK_BASE_URL='https://provider.invalid',HTTP_PROXY='http://proxy.invalid:1',HTTPS_PROXY='http://proxy.invalid:1')
                p=subprocess.Popen([sys.executable,'-X','utf8','-I','-B','-c',code,str(ROOT/'tests'),str(folder)],
                    cwd=folder,env=isolated,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                children.append((name,p))
            transcripts=[]
            try:
                for name,p in children:
                    stdout,stderr=p.communicate(timeout=100)
                    transcripts.append({'name':name,'exit':p.returncode,'stdout':stdout.decode('utf8'),'stderr':stderr.decode('utf8')})
                    self.assertEqual(p.returncode,0,stderr.decode('utf8'))
            finally:
                for _,p in children:
                    if p.poll() is None:p.kill();p.wait(10)
        ledger=Ledger(path,readonly=True)
        try:snap=ledger.snapshot();verify_snapshot(snap)
        finally:ledger.close()
        self.assertEqual(len(service.receives),1);self.assertEqual(snap['totals']['calls'],1)
        self.assertEqual(sum(e['kind']=='sending' for e in snap['events']),1)
        report=export_campaign(path,[self.root/n/'bundle' for n in ('one','two')],service.receives,self.root/'campaign')
        self.assertTrue(report['valid']);self.assertEqual(report['report']['counts']['registered'],4)
        self.evidence.update(budget=snap,receives=service.receives,report=report,children=transcripts)

    def test_02_worker_interruptions_retain_unknown_and_do_not_retry(self):
        for case,needle in [('reserved','const wireHash='),('sending',"log({kind:'sending'"),('before-settle',"a.response.chunks.push(chunk);yield chunk")]:
            folder=self.root/case;folder.mkdir()
            class Interrupted(TransportPort):
                def prepare(self):
                    super().prepare()
                    original=(PACKAGE/'adapters/transport/plugins/transport.mjs').read_text(encoding='utf8')
                    if case=='before-settle':changed=original.replace(needle,"if(chunk.type==='finish') process.exit(97)\n        "+needle)
                    else:changed=original.replace(needle,'process.exit(97)\n    '+needle)
                    self_test.assertNotEqual(original,changed)
                    # Test-owned plugin, unshipped. Reuse the unchanged hash/writer helpers.
                    changed=changed.replace("'./common.mjs'",repr((PACKAGE/'adapters/transport/plugins/common.mjs').as_uri()))
                    fault=self.root/'fault.mjs';fault.write_text(changed,encoding='utf8')
                    patch=json.loads((self.root/'profile.patch.yml').read_bytes())
                    for item in patch:
                        for entry in item.get('insert',[]):
                            if entry['id']=='actio-transport':entry['name']=fault.as_uri()
                    write_json(self.root/'profile.patch.yml',patch)
            self_test=self
            with ChatStub(folder,[{'text':'propose:morning'},{'text':'accept'}]) as service:
                cfg=config(service.endpoint);path=folder/'budget.sqlite';ledger=Ledger(path,config=cfg);ledger.close()
                result=run(folder,service.endpoint,path,cfg,runtime_type=Interrupted)
            ledger=Ledger(path,readonly=True)
            try:snap=ledger.snapshot();verify_snapshot(snap)
            finally:ledger.close()
            self.assertIsNotNone(result['error']);self.assertEqual(snap['attempts'][0]['state'],'unknown')
            self.assertEqual(snap['totals']['calls'],1)
            self.assertEqual(len(service.receives),1 if case=='before-settle' else 0)
            sends=sum(e['kind']=='sending' for e in snap['events'])
            self.assertEqual(sends,0 if case=='reserved' else 1)
            report=export_campaign(path,[folder/'bundle'],service.receives,folder/'campaign');self.assertTrue(report['valid'])
            self.evidence['cases'].append({'case':case,'budget':snap,'receives':service.receives,'report':report,'error':result['error']})

    def test_03_wrong_body_ticket_and_proven_unsent_release(self):
        # Obtain a real official wire shape first; subsequent checks exercise SQLite authority only.
        with ChatStub(self.root,[{'text':'propose:morning'},{'text':'accept'}]) as service:
            cfg=config(service.endpoint);path=self.root/'original.sqlite';ledger=Ledger(path,config=cfg);ledger.close()
            result=run(self.root,service.endpoint,path,cfg)
        ledger=Ledger(path,readonly=True)
        try:snapshot=ledger.snapshot()
        finally:ledger.close()
        self.assertIsNone(result['error']);first=snapshot['attempts'][0]
        manifest=json.loads(result['run']['input']);scope=first['scope']
        for variant in ('release','wrong-body','pending-blocks'):
            db=Ledger(self.root/(variant+'.sqlite'),config=cfg,campaign=snapshot['meta']['campaign'])
            try:
                db.register(scope['run'],manifest);db.authorize(scope)
                request=json.loads(canonical(first['request']))
                if variant=='wrong-body':
                    body=json.loads(request['raw']);body['messages'][1]['content']='{}';request['raw']=canonical(body)
                    self.assertFalse(db.reserve(scope['op'],request)['allowed'])
                elif variant=='release':
                    self.assertTrue(db.reserve(scope['op'],request)['allowed'])
                    with self.assertRaises(ContractError):db.sending(scope['op'],'0'*64)
                    db.release(scope['op'])
                    with self.assertRaises(ContractError):db.sending(scope['op'],first['binding']['wire_hash'])
                    with self.assertRaises(ContractError):db.reserve(scope['op'],request)
                else:
                    self.assertTrue(db.reserve(scope['op'],request)['allowed'])
                    other=next(a for a in snapshot['attempts'] if a['id']!=first['id'])
                    db.authorize(other['scope'])
                    self.assertFalse(db.reserve(other['id'],other['request'])['allowed'])
                snap=db.snapshot();verify_snapshot(snap);self.assertEqual(snap['totals']['calls'],1 if variant=='pending-blocks' else 0)
                self.evidence['cases'].append({'kind':'SQLITE_AUTHORITY_ONLY','case':variant,'budget':snap,'local_http_requests':0})
            finally:db.close()
        self.evidence.update(receives=service.receives,original_budget=snapshot)

    def test_04_real_gate_blocks_unbound_egress_and_duplicate_fetch(self):
        class BoundaryPort(TransportPort):
            def prepare(self):
                super().prepare();source=(PACKAGE/'adapters/transport/plugins/transport.mjs').read_text(encoding='utf8')
                source=source.replace("'./common.mjs'",repr((PACKAGE/'adapters/transport/plugins/common.mjs').as_uri()))
                injection="""for(const url of [config.endpoint+'/files','https://provider.invalid','http://localhost:1']) {
                    try {await globalThis.fetch(url,{method:'POST',body:'{}'});throw new Error('TEST_UNEXPECTED_SEND')}
                    catch(e){if(String(e).includes('TEST_UNEXPECTED_SEND')) throw e;log({kind:'test-egress-rejected',url})}
                }
                """
                source=source.replace("  log({kind:'profile'",injection+"  log({kind:'profile'")
                source=source.replace('      active=null',"""      try {await globalThis.fetch(config.endpoint+'/chat/completions',{method:'POST',body:'{}'});throw new Error('TEST_DUPLICATE_SEND')}
                  catch(e){if(String(e).includes('TEST_DUPLICATE_SEND')) throw e;log({kind:'test-duplicate-rejected'})}
                  active=null""")
                p=self.root/'boundary-test.mjs';p.write_text(source,encoding='utf8')
                patch=json.loads((self.root/'profile.patch.yml').read_bytes())
                for item in patch:
                    for entry in item.get('insert',[]):
                        if entry['id']=='actio-transport':entry['name']=p.as_uri()
                write_json(self.root/'profile.patch.yml',patch)
        with ChatStub(self.root,[{'text':'propose:morning'},{'text':'accept'}]) as service:
            cfg=config(service.endpoint);path=self.root/'budget.sqlite';l=Ledger(path,config=cfg);l.close()
            result=run(self.root,service.endpoint,path,cfg,runtime_type=BoundaryPort)
        self.assertIsNone(result['error']);self.assertEqual(len(service.receives),2)
        captures=[json.loads(line) for p in self.root.glob('*/transport.jsonl') for line in p.read_text(encoding='utf8').splitlines()]
        self.assertEqual(sum(r['kind']=='test-egress-rejected' for r in captures),6)
        self.assertEqual(sum(r['kind']=='test-duplicate-rejected' for r in captures),2)
        self.evidence.update(receives=service.receives,gate_observations=captures)


if __name__=='__main__':unittest.main()
