import json
from pathlib import Path
import subprocess
import sys
import time
import unittest
import uuid

from actio.common import ContractError
from actio.common import Lines
from actio.common import clean_env
from actio.common import write_json
from actio.adapters.runtime.runtime import synthetic_spec
from actio.application.scenarios import assistant
from actio.application.scenarios import social
from actio.interfaces.store import Store


class EntryConcurrency(unittest.TestCase):
    def test_assistant_and_social_atomic_winner_across_control_processes(self):
        root=Path('D:/actio-p1b1-tests')/uuid.uuid4().hex[:12];root.mkdir(parents=True)
        write_json(root/'owner.json',{'test':self.id()})
        self.evidence={'root':str(root),'mode':'TWO_REAL_CONTROL_PROCESSES_REAL_RUNTIME_FIXTURE','cases':[]}
        for scenario in ('assistant','social'):
            r=root/scenario;r.mkdir()
            s=Store(r/'ledger.sqlite',create=True)
            for agent in ('A','B'):s.agent(agent,synthetic_spec(agent))
            s.close()
            command=[sys.executable,str(Path(__file__).with_name('entry_race.py')),str(r),scenario]
            children=[subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                        env=clean_env(r),creationflags=subprocess.CREATE_NO_WINDOW) for _ in range(2)]
            try:
                deadline=time.monotonic()+15
                while len(list(r.glob('ready-*')))!=2 and time.monotonic()<deadline:time.sleep(.01)
                self.assertEqual(len(list(r.glob('ready-*'))),2)
                for p in children:p.stdin.write(b'go\n');p.stdin.flush()
                outputs=[]
                for p in children:
                    out,err=p.communicate(timeout=70)
                    self.assertEqual(p.returncode,0,err.decode());outputs.append(json.loads(out))
                self.assertEqual(outputs[0]['run'],outputs[1]['run'])
                loser=[o for o in outputs if o['finish_denied']]
                self.assertEqual(len(loser),1);self.assertIn('owner claim',loser[0]['finish_denied'])
                paths=list(Lines(r/'runtime-paths.jsonl').poll())
                self.assertEqual(len(paths),1 if scenario=='assistant' else 2)
                self.assertEqual(len({p['pid'] for p in paths}),1)
                s=Store(r/'ledger.sqlite')
                run=s.run('same');self.assertEqual(run['trajectory'],'complete')
                self.assertEqual(s.row('SELECT COUNT(*) n FROM effect')['n'],1 if scenario=='assistant' else 0)
                self.assertEqual(sum(x['kind']=='received' for f in r.rglob('mcp.jsonl') for x in Lines(f).poll()),1 if scenario=='assistant' else 0)
                workers=s.rows('SELECT * FROM worker')
                for w in workers:self.assertEqual(json.loads(w['report'])['after']['active'],0)
                # Changed memory revision must not change the frozen request winner.
                repeat=assistant(s,'same','A',r) if scenario=='assistant' else social(s,'same','A','B',r)
                self.assertEqual(repeat,run)
                with self.assertRaisesRegex(ContractError,'key conflict'):
                    if scenario=='assistant':assistant(s,'same','B',r)
                    else:social(s,'same','B','A',r)
                s.db.execute("UPDATE run SET state='needs_reconcile',task='unknown',trajectory='incomplete' WHERE id=?",(run['id'],))
                again=assistant(s,'same','A',r) if scenario=='assistant' else social(s,'same','A','B',r)
                self.assertEqual(again['state'],'needs_reconcile')
                self.assertEqual(s.rows('SELECT * FROM worker'),workers)
                self.evidence['cases'].append({'scenario':scenario,'command':command,'exit_codes':[p.returncode for p in children],
                    'outputs':outputs,'runtime_paths':paths,'workers':workers,'unknown_retry_mode':'CONTROLLED_LEDGER_STATE_AFTER_REAL_COMPLETE_RUN'})
                s.close()
            finally:
                for p in children:
                    if p.poll() is None:p.kill();p.wait(timeout=5)
