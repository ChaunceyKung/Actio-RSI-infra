import json
from pathlib import Path
import tempfile
import unittest

from actio.contracts.json import ContractError
from actio.adapters.filesystem.common import Lines
from actio.contracts.json import canonical
from actio.contracts.json import digest
from actio.adapters.runtime.facts import Facts
from actio.application.memory import Memory
from actio.application.memory import namespace
from actio.adapters.runtime.runtime import RuntimePort
from actio.adapters.runtime.runtime import synthetic_spec
from actio.interfaces.store import Store


class Contracts(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='actio-contract-')
        self.path=Path(self.temp.name)/'ledger.sqlite'
        self.s=Store(self.path,create=True)
        self.s.agent('A',synthetic_spec('A')); self.s.agent('B',synthetic_spec('B'))
        self.run,_=self.s.begin('key',{'scenario':'assistant','agents':{'A':self.s.agent('A')['spec_hash']}})
        self.stream=self.s.allocate_worker(self.run['id'],self.run['epoch'],self.temp.name,'unused-contract-job','A')
        self.facts=Facts(self.s)

    def tearDown(self):
        self.s.close(); self.temp.cleanup()

    def event(self,n,kind='assistant/message'):
        return {'seq':n,'type':kind,'time':1,'data':{'content':[{'type':'text','text':'synthetic'}]}}

    def valid_source(self):
        self.facts.ingest(self.stream['id'],self.event(0))
        self.s.db.execute("UPDATE stream SET integrity='valid' WHERE id=?",(self.stream['id'],))
        return (self.stream['id'],0,'assistant.final')

    def test_identity_idempotency_epoch_and_ttl(self):
        same,fresh=self.s.begin('key',{'scenario':'assistant','agents':{'A':self.s.agent('A')['spec_hash']}})
        self.assertFalse(fresh); self.assertEqual(same['id'],self.run['id'])
        with self.assertRaisesRegex(ContractError,'key conflict'):
            self.s.begin('key',{'different':True})
        self.s.db.execute('UPDATE run SET created=0')
        with self.assertRaisesRegex(ContractError,'TTL'):
            self.s.begin('different',{})
        with self.assertRaisesRegex(ContractError,'still alive'):
            self.s.recover(self.run["id"])
        with self.assertRaisesRegex(ContractError,'stale epoch'):
            self.s.intent(self.run['id'],self.run['epoch']-1,self.stream['id'],{})
        with self.assertRaisesRegex(ContractError,'deadline'):
            self.s.intent(self.run['id'],self.run['epoch'],self.stream['id'],{})
        original=self.s.agent('A')
        self.s.close(); self.s=Store(self.path,create=True)
        self.assertEqual(original,self.s.agent('A'))
        spec={**original['spec'],'persona':'changed'}
        with self.assertRaisesRegex(ContractError,'immutable'):
            self.s.agent('A',spec)

    def test_out_of_order_dedup_conflict_and_remap(self):
        sid=self.stream['id']
        for n,expected in [(2,-1),(0,0),(1,2)]:
            self.facts.ingest(sid,self.event(n))
            self.assertEqual(self.s.row('SELECT cursor FROM stream WHERE id=?',(sid,))['cursor'],expected)
        self.facts.ingest(sid,self.event(0)); self.facts.ingest(sid,self.event(0),mapper='v2')
        self.assertEqual(self.s.row('SELECT COUNT(*) n FROM occurrence')['n'],3)
        with self.assertRaisesRegex(ContractError,'conflicting'):
            self.facts.ingest(sid,{**self.event(0),'time':2})
        self.assertEqual(self.s.row('SELECT COUNT(*) n FROM conflict')['n'],1)
        self.assertEqual(json.loads(self.s.row('SELECT raw FROM occurrence WHERE seq=0')['raw'])['time'],1)
        self.s.db.execute("UPDATE worker SET state='reaped'")
        new=self.s.allocate_worker(self.run['id'],self.run['epoch'],self.temp.name+'/new','unused-new-job','A')
        self.facts.ingest(new['id'],self.event(0))
        self.assertEqual(self.s.row('SELECT COUNT(*) n FROM occurrence')['n'],4)

    def test_memory_atomic_cas_ack_loss_correction_and_mapper(self):
        source=self.valid_source(); memory=Memory(self.s); ns=namespace('A','assistant')
        first=memory.write(ns,'A',source,'PRIVATE_A',0)
        self.s.close(); self.s=Store(self.path,create=True); memory=Memory(self.s); self.facts=Facts(self.s)
        again=memory.write(ns,'A',source,'PRIVATE_A',0)
        self.assertEqual((first['memory_id'],first['revision']),(again['memory_id'],again['revision']))
        self.assertEqual(memory.revision(ns),1)
        self.facts.ingest(source[0],self.event(0),mapper='v2'); memory.migrate('v1','v2')
        memory.write(ns,'A',source,'PRIVATE_A',0)
        self.assertEqual(memory.revision(ns),1)
        with self.assertRaisesRegex(ContractError,'explicit correction'):
            memory.write(ns,'A',source,'changed',1)
        memory.write(ns,'A',source,'CORRECTED_A',1,correction=first['memory_id'])
        self.assertEqual(memory.retrieve(ns,'A',as_of=1)['items'][0]['content'],'PRIVATE_A')
        self.assertEqual(memory.retrieve(ns,'A')['items'][0]['content'],'CORRECTED_A')
        self.facts.ingest(source[0],self.event(1),mapper='v2')
        with self.assertRaisesRegex(ContractError,'CAS'):
            memory.write(ns,'A',(source[0],1,source[2]),'NEW',0)
        self.assertEqual(self.s.row('SELECT COUNT(*) n FROM effect')['n'],1)
        self.assertEqual(self.s.row('SELECT COUNT(*) n FROM memory')['n'],2)

    def test_namespace_source_slot_and_frozen_retrieval(self):
        source=self.valid_source(); m=Memory(self.s); ns=namespace('A','assistant')
        m.write(ns,'A',source,'PRIVATE_A',0)
        with self.assertRaises(ContractError): m.retrieve(ns,'B')
        with self.assertRaises(ContractError): namespace(None,'assistant')
        with self.assertRaises(ContractError): namespace('A','assistant',branch='other')
        with self.assertRaises(ContractError): namespace('A','assistant',project='other')
        with self.assertRaises(ContractError): m.write(namespace('B','assistant'),'B',source,'bad',0)
        with self.assertRaisesRegex(ContractError,'slot'): m.write(ns,'A',(source[0],0,'audit'),'bad',1)
        with self.assertRaisesRegex(ContractError,'16 KiB'): m.write(ns,'A',source,'x'*16385,1)
        shared=m.retrieve(ns,'A',target='social',as_of=1)
        self.assertEqual(shared['items'][0]['content'],'PRIVATE_A')
        b=synthetic_spec('C'); b['memory_shares']=[]; self.s.agent('C',b)
        with self.assertRaisesRegex(ContractError,'cross-environment'):
            m.retrieve(namespace('C','assistant'),'C',target='social')
        with self.assertRaises(ContractError): m.retrieve(ns,'A',as_of=99)
        self.assertTrue(self.s.row('SELECT * FROM retrieval WHERE id=?',(shared['context_ref'],)))

    def test_barrier_gap_old_marker_partial_tail_and_truncation(self):
        sid=self.stream['id']; op=self.s.intent(self.run['id'],self.run['epoch'],sid,{})
        events=[{'seq':0,'type':'agent/inbox/spliced','data':{'inserted':[{'id':'receipt'}]}},
                {'seq':1,'type':'assistant/message','data':{}},
                {'seq':2,'type':'turn/end','data':{'reason':{'kind':'completed'}}}]
        self.s.op_update(op,self.run['epoch'],receipt='receipt',terminal='completed')
        marker={'run':self.run['id'],'op':op,'epoch':self.run['epoch'],'creation':self.stream['creation'],
                'session':self.stream['native_id'],'receipt':'receipt','through':2,'terminal':{'seq':2,'reason':'completed'}}
        self.facts.ingest(sid,events[0]);self.facts.ingest(sid,events[2])
        with self.assertRaises(ContractError): self.facts.certify(op,marker)
        self.facts.ingest(sid,events[1]);self.s.db.execute("UPDATE stream SET integrity='valid'")
        self.facts.certify(op,marker)
        for key,bad in [('epoch',999),('op','old'),('creation','old'),('through',99),('receipt','old')]:
            with self.assertRaises(ContractError): self.facts.certify(op,{**marker,key:bad})
        # A separate managed native journal exercises incremental tail handling.
        journal=Path(self.temp.name)/'home/sessions/x/session.v3.jsonl';journal.parent.mkdir(parents=True)
        header={'type':'session','version':3,'id':self.stream['native_id'],'createdAt':1}
        journal.write_text(json.dumps(header)+'\n'+json.dumps(events[0])+'\n'+json.dumps(events[1])[:12],encoding='utf-8')
        # Fresh stream for exact raw bytes (direct envelope hashes above intentionally differ).
        self.s.db.execute('DELETE FROM projection');self.s.db.execute('DELETE FROM occurrence');self.s.db.execute("UPDATE stream SET cursor=-1,integrity='pending'")
        state=self.facts.collect(sid)
        self.assertEqual(state['integrity'],'partial_tail');self.assertEqual(state['cursor'],0)
        with self.assertRaises(ContractError):self.facts.certify(op,marker)
        journal.write_text('',encoding='utf-8')
        with self.assertRaisesRegex(ContractError,'truncation'):self.facts.collect(sid)
        journal.write_text(json.dumps({**header,'version':4})+'\n'+json.dumps(events[0])+'\n',encoding='utf-8')
        with self.assertRaisesRegex(ContractError,'unknown native header'):self.facts.collect(sid)

    def test_bounded_data_and_unsupported_capabilities(self):
        p=Path(self.temp.name)/'spool';p.write_bytes(b'{"ok":1}\n'+b'x'*32)
        reader=Lines(p,item=16)
        self.assertEqual(next(reader.poll()),{'ok':1})
        with self.assertRaisesRegex(ContractError,'limit'):list(reader.poll())
        self.assertEqual(reader.count,1)
        for value in [float('nan'),float('inf'),1.5,9007199254740992,'\ud800']:
            with self.assertRaises((ContractError,UnicodeError)):canonical(value)
        self.assertEqual(digest({'b':1,'a':[True,None,'汉字']}),digest({'a':[True,None,'汉字'],'b':1}))
        for capability in ['resume','fork','reopen','catchup','world_restore','semantic_cancel','evaluator','live_provider']:
            with self.assertRaisesRegex(ContractError,'unsupported'):RuntimePort.require(capability)


if __name__=='__main__':
    unittest.main()
