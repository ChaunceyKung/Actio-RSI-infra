import json
from pathlib import Path
import subprocess
import sys
import unittest
import uuid

from actio.common import ContractError
from actio.common import Lines
from actio.common import clean_env
from actio.common import file_hash
from actio.common import write_json
from actio.adapters.runtime.facts import Facts
from actio.application.memory import Memory
from actio.application.memory import namespace
from actio.adapters.runtime.runtime import RuntimePort
from actio.adapters.runtime.runtime import TOOL
from actio.adapters.runtime.runtime import synthetic_spec
from actio.adapters.environment.concordia import final_source
from actio.interfaces.store import Store


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.root=Path('D:/actio-p1b-tests')/uuid.uuid4().hex[:12]
        self.root.mkdir(parents=True)
        write_json(self.root/'owner.json',{'owner':'phase1b-validation','test':self.id()})
        self.db=self.root/'ledger.sqlite'
        self.evidence={'root':str(self.root),'commands':[]}

    def cli(self,*args,code=0):
        command=[sys.executable,'-m','actio','--db',str(self.db),'--short-root',str(self.root),*args]
        result=subprocess.run(command,env=clean_env(self.root),capture_output=True,text=True,encoding='utf-8',timeout=90)
        self.evidence['commands'].append({'args':list(args),'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        self.assertEqual(result.returncode,code,result.stderr)
        return json.loads(result.stdout) if result.stdout else None

    def tearDown(self):
        self.evidence['files']={p.relative_to(self.root).as_posix():file_hash(p) for p in self.root.rglob('*')
                              if p.is_file() and 'node_modules' not in p.parts and p.suffix in {'.jsonl','.json','.sqlite','.log','.yml'}}
        self.evidence['transcripts']={p.relative_to(self.root).as_posix():list(Lines(p).poll()) for name in ('provider.jsonl','bridge.jsonl','mcp.jsonl') for p in self.root.rglob(name)}

    def test_cross_process_dual_scenario_replay_and_privacy(self):
        self.cli('init'); a=self.cli('agent','A','--create'); self.cli('agent','B','--create')
        first=self.cli('assistant','--agent','A','--key','assistant-one')
        self.assertEqual((first['state'],first['task'],first['trajectory']),('execution_complete','success','complete'))
        again=self.cli('assistant','--agent','A','--key','assistant-one')
        self.assertEqual(first,again)
        self.assertEqual(self.cli('agent','A')['spec_hash'],a['spec_hash'])
        memory=self.cli('memory','--agent','A','--environment','assistant','--target','social','--revision','1')
        self.assertEqual(len(memory['items']),1)
        social=self.cli('social','--a','A','--b','B','--key','social-one','--memory-revision','1')
        self.assertEqual(social['task'],'success')
        replay=self.cli('social','--a','A','--b','B','--key','social-replay','--replay',social['id'])
        one=self.cli('query',social['id']);two=self.cli('query',replay['id'])
        self.assertEqual([w['resolved'] for w in one['world']],[w['resolved'] for w in two['world']])
        self.assertNotEqual(one['streams'][0]['creation'],two['streams'][0]['creation'])
        self.assertEqual(self.cli('memory','--agent','A','--environment','assistant')['as_of'],1)
        bad=self.cli('social','--a','A','--b','B','--key','illegal','--illegal')
        self.assertEqual(bad['task'],'task_failure')
        self.assertEqual(self.cli('query',bad['id'])['world'],[])
        self.cli('require','resume',code=2)
        self.cli('reconcile',first['id'])
        s=Store(self.db)
        try:
            workers=s.rows('SELECT w.*,s.agent FROM worker w JOIN stream s ON s.worker=w.id')
            social_ids={social['id'],replay['id'],bad['id']}
            for worker in workers:
                report=json.loads(worker['report']);self.assertEqual(report['after']['active'],0)
                if worker['run'] not in social_ids:continue
                for capture in Lines(Path(worker['root'])/'provider.jsonl').poll():
                    text=json.dumps(capture['messages'])
                    who=worker['agent'];other='B' if who=='A' else 'A'
                    self.assertIn('PRIVATE_ONLY_'+who,text)
                    self.assertNotIn('PRIVATE_ONLY_'+other,text)
                    self.assertNotIn('GM_PRIVATE_FULL_LOG',text)
                    if who=='A':self.assertIn('PRIVATE_MEMORY_A',text)
                    else:self.assertNotIn('PRIVATE_MEMORY_A',text)
            self.assertEqual(s.row('SELECT COUNT(*) n FROM memory')['n'],1)
            self.assertEqual(s.row('SELECT COUNT(*) n FROM effect')['n'],1)
            self.assertIsNone(s.row('SELECT * FROM lease'))
            self.evidence['operations']=s.rows('SELECT * FROM operation')
            self.evidence['workers']=workers
        finally:s.close()

    def test_current_host_two_turns_have_distinct_receipt_barriers(self):
        s=Store(self.db,create=True);s.agent('A',synthetic_spec('A'))
        run,_=s.begin('two-turns',{'scenario':'assistant','agents':{'A':s.agent('A')['spec_hash']}})
        markers=[]
        try:
            with RuntimePort(s,run,'A',self.root) as port:
                for revision in range(2):
                    result=port.submit({'tool':TOOL,'args':{'key':'ok'},'answer':'turn '+str(revision)})
                    source=final_source(s,result)
                    ack=Memory(s).write(namespace('A','assistant'),'A',source,'episode '+str(revision),revision)
                    with s.tx():
                        s.db.execute('INSERT INTO domain_receipt VALUES(?,?,?,?,?)',(result['op'],'success',source[0],source[1],json.dumps(ack)))
                    port.confirm_effect();markers.append(result['marker'])
                self.assertNotEqual(markers[0]['receipt'],markers[1]['receipt'])
                self.assertGreater(markers[1]['through'],markers[0]['through'])
                with self.assertRaisesRegex(ContractError,'stale'):
                    Facts(s).certify(result['op'],markers[0])
            final=s.finish(run['id'],run['epoch'],task='success')
            self.assertEqual(final['trajectory'],'incomplete')  # Two RuntimePort turns are not a one-step assistant episode.
            self.assertTrue(all(o['state']=='execution_complete' for o in s.rows('SELECT * FROM operation')))
            self.assertEqual(s.row('SELECT COUNT(*) n FROM worker')['n'],1)
            self.assertEqual(s.row('SELECT COUNT(*) n FROM memory')['n'],2)
            self.evidence['markers']=markers
        finally:s.close()


if __name__=='__main__':unittest.main()
