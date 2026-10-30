"""Real backend conformance, orchestration, plugin loading and failure cleanup."""
from dataclasses import replace
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

from actio.adapters.environment.pettingzoo import create as tictactoe
from actio.adapters.environment.concordia import create as concordia
from actio.application.experiment import experiment
from actio.contracts.json import ContractError
from actio.interfaces.environments import resolve
from actio.interfaces.export import export_bundle
from actio.evidence.bundles.verify import analyze
from actio.interfaces.store import Store

ROOT = Path(__file__).resolve().parents[1]
PLAN = json.loads((ROOT / 'examples/environments/tictactoe.json').read_bytes())
SOCIAL = {'order': ['B', 'A'], 'observations': {'A': 'private A', 'B': 'private B'},
          'action_spec': {'call_to_action': 'Choose.', 'output_type': 'choice',
                          'options': ['cooperate', 'wait'], 'tag': None}}


class SessionConformance(unittest.TestCase):
    def backends(self):
        return [('pettingzoo', tictactoe, {'seed': 1}), ('concordia', concordia, SOCIAL)]

    def test_real_backends_finish_reject_illegal_and_idempotent(self):
        for name, factory, config in self.backends():
            with self.subTest(name=name):
                session = factory(config)
                try:
                    self.assertFalse(session.capabilities.snapshot)
                    first = session.observe()
                    self.assertEqual(first, session.observe())
                    agent = first.decisions[0].agent
                    bad = session.submit({agent: 'INVALID'}, operation='illegal', expected_revision=0)
                    self.assertEqual(bad.status, 'rejected')
                    self.assertEqual(first, session.observe())
                    self.assertFalse(session.poll())
                    stale = session.submit({agent: first.decisions[0].legal_actions[0]}, operation='stale', expected_revision=1)
                    self.assertEqual(stale.reason, 'stale_revision')
                    wrong = session.submit({'unknown': 0}, operation='wrong', expected_revision=0)
                    self.assertEqual(wrong.reason, 'wrong_acting_agents')
                    steps, actors, cursor = 0, [], 0
                    while not session.status().done:
                        frame = session.observe()
                        d = frame.decisions[0]
                        actors.append(d.agent)
                        actions = {d.agent: d.legal_actions[0]}
                        reply = session.submit(actions, operation=str(steps), expected_revision=frame.revision)
                        self.assertEqual(reply.status, 'accepted')
                        self.assertEqual(session.poll(cursor), reply.outcomes)
                        cursor = reply.outcomes[-1].cursor
                        self.assertEqual(reply, session.submit(actions, operation=str(steps), expected_revision=frame.revision))
                        with self.assertRaisesRegex(ContractError, 'conflict'):
                            session.submit(actions, operation=str(steps), expected_revision=99)
                        steps += 1
                        self.assertLess(steps, 12)
                    self.assertEqual(len(set(actors)), 2)
                    self.assertFalse(session.observe().decisions)
                    self.assertEqual(session.submit({}, operation='after', expected_revision=session.observe().revision).reason, 'episode_done')
                    if name == 'pettingzoo':
                        self.assertEqual(session.status().results['rewards'], {'player_1': 1, 'player_2': -1})
                finally:
                    session.close()
                    session.close()
                with self.assertRaisesRegex(ContractError, 'closed'):
                    session.observe()

    def test_close_while_waiting_and_native_engine_exception(self):
        session = concordia(SOCIAL)
        session.close()
        self.assertFalse(session.thread.is_alive())
        broken = copy.deepcopy(SOCIAL)
        broken['order'] = ['unknown', 'A']
        with self.assertRaises(Exception):
            concordia(broken)
        self.assertFalse(any(t.name == 'actio-concordia' for t in threading.enumerate()))

    def test_native_settlement_precedes_next_engine_failure(self):
        from unittest.mock import patch
        from concordia.environment.engines.sequential import Sequential
        original = Sequential.run_loop
        def injected(engine, *args, **kwargs):
            def callback(step):
                raise RuntimeError('after committed event')
            kwargs['step_callback'] = callback
            return original(engine, *args, **kwargs)
        with patch.object(Sequential, 'run_loop', injected):
            session = concordia(SOCIAL)
            try:
                reply = session.submit({'B': 'cooperate'}, operation='first', expected_revision=0)
                self.assertEqual(reply.status, 'accepted')
                self.assertTrue(reply.outcomes[0].effects['resolved'].startswith('[event]'))
                with self.assertRaisesRegex(RuntimeError, 'committed event'):
                    session.status()
                self.assertEqual(len(session.poll()), 1)
            finally:
                session.close()


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        (ROOT / '.local').mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / '.local')
        self.root = Path(self.tmp.name)
        self.store = Store(self.root / 'runs.sqlite', create=True)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def execute(self, key='test', plan=None, factory=None, **kwargs):
        creator, identity = resolve('pettingzoo.tictactoe.v3')
        return experiment(self.store, key, plan or PLAN, environment_factory=factory or creator,
                          environment_identity=identity, **kwargs)

    def test_multi_episode_export_and_idempotent_run(self):
        result = self.execute()
        self.assertEqual(len(result['runs']), 3)
        self.assertTrue(all(r['trajectory'] == 'complete' and r['task'] == 'success' for r in result['runs']))
        self.assertIsNone(self.store.row('SELECT * FROM lease'))
        self.assertEqual(result, self.execute(factory=lambda c: self.fail('reexecuted')))
        exported = export_bundle(self.store.path, result['runs'][0]['id'], self.root / 'bundle')
        self.assertEqual(exported['verification']['facts_consistency'], 'valid')
        evidence = json.loads((self.root / 'bundle/evidence.json').read_bytes())
        source = json.loads((self.root / 'bundle/manifest.json').read_bytes())['source']
        changed = copy.deepcopy(evidence)
        intent = next(r for r in changed['audit'] if r['kind'] == 'environment_intent')
        body = json.loads(intent['body']);body['actions']['player_1'] = 99
        intent['body'] = json.dumps(body)
        self.assertEqual(analyze(changed, source)['facts_consistency'], 'invalid')
        changed_plan = {**PLAN, 'episodes': 1}
        with self.assertRaisesRegex(ContractError, 'request key conflict'):
            self.execute(plan=changed_plan)

    def test_policy_failure_action_limit_and_cleanup_failure(self):
        sessions = []
        def factory(config):
            session = tictactoe(config);sessions.append(session);return session
        def broken(decision):
            raise RuntimeError('policy failed')
        with self.assertRaisesRegex(RuntimeError, 'policy failed'):
            self.execute(factory=factory, policy=broken)
        self.assertTrue(sessions[-1].closed)
        self.assertEqual(self.store.run('test:0')['task'], 'infrastructure_failure')
        self.assertIsNone(self.store.row('SELECT * FROM lease'))
        with self.assertRaisesRegex(ContractError, 'action limit'):
            self.execute(key='bounded', plan={**PLAN, 'max_actions': 1}, factory=factory)
        self.assertTrue(sessions[-1].closed)
        self.assertIsNone(self.store.row('SELECT * FROM lease'))
        def failing_close(config):
            session = factory(config)
            def close():
                raise RuntimeError('close failed')
            session.close = close
            return session
        with self.assertRaisesRegex(RuntimeError, 'policy failed') as caught:
            self.execute(key='cleanup', factory=failing_close, policy=broken)
        self.assertIn('cleanup failed', str(caught.exception.__notes__))
        self.assertIsNotNone(self.store.row('SELECT * FROM lease'))
        sessions[-1].env.close()

    def test_factory_failure_and_unsupported_async_are_explicit(self):
        def broken(config):
            raise RuntimeError('open failed')
        with self.assertRaisesRegex(RuntimeError, 'open failed'):
            self.execute(factory=broken)
        self.assertIsNone(self.store.row('SELECT * FROM lease'))
        created = []
        def asynchronous(config):
            session = tictactoe(config)
            session.capabilities = replace(session.capabilities, asynchronous=True)
            created.append(session)
            return session
        with self.assertRaisesRegex(ContractError, 'synchronous'):
            self.execute(key='async', factory=asynchronous)
        self.assertTrue(created[0].closed)

    def test_cli_and_external_entry_point_without_core_change(self):
        # A separate installed distribution advertises the same adapter under a
        # new environment name. No application registry/conditional is edited.
        plugin = self.root / 'external_env-1.0.dist-info'
        plugin.mkdir()
        (plugin / 'METADATA').write_text('Name: external-env\nVersion: 1.0\n')
        (plugin / 'entry_points.txt').write_text('[actio.environments]\nexternal.game = actio.adapters.environment.pettingzoo:create\n')
        sys.path.insert(0, str(self.root))
        try:
            factory, identity = resolve('external.game')
            self.assertEqual(identity['distribution'], 'external-env')
            plan = {**PLAN, 'environment': 'external.game', 'episodes': 1}
            result = experiment(self.store, 'external', plan, environment_factory=factory, environment_identity=identity)
            self.assertEqual(result['runs'][0]['state'], 'execution_complete')
        finally:
            sys.path.remove(str(self.root))
        command = [sys.executable, '-m', 'actio', 'run', '--db', str(self.store.path),
                   'experiment', '--key', 'cli', '--config', str(ROOT / 'examples/environments/tictactoe.json')]
        p = subprocess.run(command, capture_output=True, text=True, timeout=40)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(len(json.loads(p.stdout)['runs']), 3)


if __name__ == '__main__':
    unittest.main()
