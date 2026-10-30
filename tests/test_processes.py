import ctypes as C
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import unittest
import uuid

from actio.contracts.json import ContractError
from actio.adapters.filesystem.common import Lines
from actio.adapters.filesystem.common import clean_env
from actio.adapters.filesystem.common import file_hash
from actio.adapters.filesystem.common import write_json
from actio.adapters.runtime.facts import Facts
from actio.application.memory import Memory
from actio.application.memory import namespace
from actio.application.scenarios import assistant
from actio.interfaces.store import Store
from actio.adapters.runtime.supervisor import Job
from actio.adapters.runtime.supervisor import kernel
from actio.adapters.runtime.supervisor import process_birth

DRIVER=Path(__file__).with_name('child_case.py')


class Processes(unittest.TestCase):
    def setUp(self):
        self.root=(Path(__file__).resolve().parents[2]/'t')/uuid.uuid4().hex[:12];self.root.mkdir(parents=True)
        write_json(self.root/'owner.json',{'test':self.id()})
        self.evidence={'root':str(self.root),'cases':[]};self.children=[]

    def tearDown(self):
        for p in self.children:
            if p.poll() is None:p.kill();p.wait(timeout=5)
            if p.stdin:p.stdin.close()
        self.evidence['files']={p.relative_to(self.root).as_posix():file_hash(p) for p in self.root.rglob('*') if p.is_file() and 'node_modules' not in p.parts and p.suffix in {'.json','.jsonl','.sqlite','.log'}}

    def spawn(self,mode,root):
        root.mkdir(exist_ok=True)
        p=subprocess.Popen([sys.executable,str(DRIVER),mode,str(root)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                           env=clean_env(root),creationflags=subprocess.CREATE_NO_WINDOW)
        self.children.append(p);return p

    def wait_for(self,condition,seconds=25):
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            result=condition()
            if result:return result
            time.sleep(.015)
        self.fail('observable boundary did not arrive within deadline')

    def job_active(self,name):
        k=kernel();handle=k.OpenJobObjectW(4,False,name)
        if not handle:
            self.assertEqual(C.get_last_error(),2);return 0
        j=object.__new__(Job);j.k=k;j.handle=handle
        try:return j.snapshot()['active']
        finally:k.CloseHandle(handle)

    def test_two_control_processes_one_lease(self):
        Store(self.root/'ledger.sqlite',create=True).close()
        ps=[self.spawn('race',self.root) for _ in range(2)]
        self.wait_for(lambda:len(list(self.root.glob('ready-*')))==2)
        for p in ps:p.stdin.write(b'go\n');p.stdin.flush()
        results=[]
        for p in ps:
            out,err=p.communicate(timeout=10);self.assertEqual(p.returncode,0,err.decode());results.append(json.loads(out))
        self.assertEqual(sum(r['winner'] for r in results),1)
        s=Store(self.root/'ledger.sqlite')
        try:
            s.recover(s.row('SELECT run FROM lease')['run']);self.assertIsNone(s.row('SELECT * FROM lease'))
        finally:s.close()
        self.evidence['cases']=results

    def test_abrupt_owner_exit_and_accepted_receipt_loss(self):
        for mode,exit_code in [('owner',83),('A',81)]:
            root=self.root/mode;p=self.spawn(mode,root)
            out,err=p.communicate(timeout=40);self.assertEqual(p.returncode,exit_code,err.decode())
            marker=json.loads((root/'crash-marker.json').read_text())
            self.assertGreaterEqual(marker['job_before']['active'],2)
            self.wait_for(lambda:self.job_active(marker['job'])==0,5)
            self.assertIsNone(process_birth(marker['sdk_pid']))
            s=Store(root/'ledger.sqlite')
            try:
                run=s.run('crash-A' if mode=='A' else 'owner');s.recover(run['id']);run=s.run(run['id'])
                self.assertEqual(run['state'],'needs_reconcile')
                if mode=='A':
                    op=s.row('SELECT * FROM operation');self.assertIsNone(op['receipt']);self.assertEqual(op['state'],'needs_reconcile')
                    before=s.row('SELECT COUNT(*) n FROM worker')['n']
                    same=assistant(s,'crash-A','A',root)
                    self.assertEqual(same['id'],run['id']);self.assertEqual(s.row('SELECT COUNT(*) n FROM worker')['n'],before)
                    Facts(s).reconcile(run['id']);self.assertEqual(s.run(run['id'])['trajectory'],'incomplete')
                    newer,fresh=s.begin('after-owner-death',{'scenario':'assistant'})
                    self.assertTrue(fresh);self.assertGreater(newer['epoch'],run['epoch'])
                    with self.assertRaisesRegex(ContractError,'stale epoch'):
                        s.op_update(op['id'],run['epoch'],state='execution_complete')
                    s.finish(newer['id'],newer['epoch'],task='unknown',reason='lease transition test')
                self.evidence['cases'].append({'mode':mode,'marker':marker,'run':run,'automatic_retries':0,'job_active_after_owner_exit':0})
            finally:s.close()

    def test_mcp_received_before_result_real_sdk_host_kill(self):
        root=self.root/'B';p=self.spawn('B',root)
        def received():
            for path in root.rglob('mcp.jsonl'):
                rows=list(Lines(path).poll())
                if any(r['kind']=='received' for r in rows):return path
        path=self.wait_for(received)
        s=Store(root/'ledger.sqlite')
        try:
            worker=s.row("SELECT * FROM worker WHERE state='running'")
            self.assertEqual(Path(worker['root']),path.parent)
            self.assertIsNotNone(process_birth(worker['pid']))
            os.kill(worker['pid'],signal.SIGTERM)
            out,err=p.communicate(timeout=15);self.assertEqual(p.returncode,82,err.decode())
            run=s.run('crash-B');self.assertEqual(run['state'],'needs_reconcile')
            self.assertEqual(sum(r['kind']=='received' for r in Lines(path).poll()),1)
            bridge=list(Lines(path.parent/'bridge.jsonl').poll())
            self.assertFalse(any(r['kind']=='tool-result' for r in bridge))
            report=json.loads(s.row('SELECT report FROM worker')['report']);self.assertEqual(report['after']['active'],0)
            self.evidence['cases'].append({'window':'B','sdk_host_killed':worker['pid'],'run':run,'received':1,'tool_results':0,'report':report})
        finally:s.close()

    def test_memory_commit_before_caller_ack_process_death(self):
        root=self.root/'D';p=self.spawn('D',root)
        out,err=p.communicate(timeout=40);self.assertEqual(p.returncode,84,err.decode())
        s=Store(root/'ledger.sqlite')
        try:
            s.recover('crash-D');m=Memory(s);ns=namespace('A','assistant')
            memory=m.retrieve(ns,'A');self.assertEqual(memory['as_of'],1);self.assertEqual(len(memory['items']),1)
            item=memory['items'][0]
            ack=m.write(ns,'A',item['source'],item['content'],0)
            self.assertEqual(ack['memory_id'],item['id'])
            self.assertEqual(s.row('SELECT COUNT(*) n FROM memory')['n'],1)
            self.assertEqual(s.row('SELECT COUNT(*) n FROM effect')['n'],1)
            self.assertEqual(s.run('crash-D')['state'],'needs_reconcile')
            self.evidence['cases'].append({'window':'D','memory':memory,'recovered_ack':ack,'memory_rows':1,'effect_rows':1})
        finally:s.close()


if __name__=='__main__':unittest.main()
