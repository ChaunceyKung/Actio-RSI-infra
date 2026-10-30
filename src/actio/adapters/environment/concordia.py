"""Pause native Entity.act through a queue; upstream still owns the run_loop.

Only the controller thread touches SQLite and RuntimePort. No simulator is
reimplemented here and no nested asyncio event loop is required.
"""
import json
from pathlib import Path
from queue import Queue, Empty
from threading import Thread
import sys

from actio.resources import data_path
from actio.contracts.json import ContractError
from actio.contracts.environment import Capabilities, Decision, Frame, Status, Resolution, Submission
from actio.adapters.environment.session import SessionAdmission
from actio.adapters.filesystem.common import file_hash
from actio.adapters.runtime.facts import Facts
from actio.contracts.wire import wire


def final_source(store, result):
    events = Facts(store).certify(result['op'], result['marker'])
    receipt = result['marker']['receipt']
    start = max(e['seq'] for e in events if e['type'] == 'agent/inbox/spliced' and
                any(m.get('id') == receipt for m in e['data'].get('inserted', [])))
    candidates = [e for e in events if e['type'] == 'assistant/message' and
                  start < e['seq'] <= result['marker']['terminal']['seq']]
    if not candidates:
        raise ContractError('no final assistant source')
    return result['stream'], candidates[-1]['seq'], 'assistant.final'


class _Cancelled(Exception):
    pass


class ConcordiaSession(SessionAdmission):
    capabilities = Capabilities(clock='native-engine-step')

    def __init__(self, manifest):
        super().__init__()
        import concordia
        pin = json.loads(data_path('pins', 'concordia.json').read_bytes())
        base = Path(concordia.__file__).parent.parent
        for name, expected in pin['files'].items():
            if name != 'LICENSE' and file_hash(base / name) != expected:
                raise ContractError('Concordia source changed: ' + name)
        self.manifest = manifest
        self.messages, self.commands = Queue(), Queue()
        self.waiting = None
        self.needs_advance = False
        self.terminal = Status()
        self.thread = Thread(target=self._loop, name='actio-concordia')
        self.thread.start()
        try:
            self._advance()
        except BaseException:
            self.close()
            raise

    def _read(self):
        try:
            kind, value = self.messages.get(timeout=30)
        except Empty as error:
            raise TimeoutError('Concordia bridge deadline') from error
        if kind == 'error':
            raise value
        return kind, value

    def _advance(self):
        kind, value = self._read()
        if kind == 'decision':
            self.waiting = value
        elif kind == 'done':
            self.waiting = None
            self.terminal = value
        else:
            raise ContractError('unexpected Concordia bridge message: ' + kind)
        self.needs_advance = False

    def _ready(self):
        if self.needs_advance:
            self._advance()

    def observe(self):
        self.check_open()
        self._ready()
        return Frame(self.revision, (self.waiting[0],) if self.waiting else ())

    def status(self):
        self.check_open()
        self._ready()
        return self.terminal

    def submit(self, actions, *, operation, expected_revision):
        cached = self.admit(actions, operation, expected_revision)
        if cached is not None:
            return cached
        self._ready()
        reason = None
        if not self.waiting:
            reason = 'episode_done'
        elif set(actions) != {self.waiting[0].agent}:
            reason = 'wrong_acting_agents'
        else:
            try:
                self.waiting[1].validate(actions[self.waiting[0].agent])
            except (ValueError, TypeError):
                reason = 'illegal_action'
        if reason:
            return self.remember(actions, operation, expected_revision,
                                 Submission(operation, 'rejected', self.revision, reason))
        self.waiting = None
        self.commands.put(next(iter(actions.values())))
        kind, effect = self._read()
        if kind != 'resolved':
            raise ContractError('Concordia did not settle accepted intent')
        self.revision += 1
        outcome = Resolution(len(self.outcomes) + 1, self.revision, operation, effect)
        self.outcomes.append(outcome)
        # Deliver the committed native effect before reading the next native
        # decision/error. The controller must persist this prefix even if the
        # Engine fails while selecting the following actor.
        self.needs_advance = True
        return self.remember(actions, operation, expected_revision,
            Submission(operation, 'accepted', self.revision, outcomes=(outcome,)))

    def _loop(self):
        try:
            self._native_loop()
        except _Cancelled:
            pass
        except BaseException as error:
            self.messages.put(('error', error))

    def _native_loop(self):
        from concordia.environment.engines.sequential import Sequential, EVENT_TAG, PUTATIVE_EVENT_TAG
        from concordia.environment import engine as engine_lib
        from concordia.environment.step_controller import StepController
        from concordia.typing import entity as entity_lib
        from actio.tasks.registry import actor_observation, resolved_text, task_result

        session, manifest = self, self.manifest
        scheduling = 'task' in manifest

        class External(entity_lib.Entity):
            def __init__(self, label):
                self.label, self.observations, self.answer = label, [], None
            @property
            def name(self):
                return self.label
            def observe(self, observation):
                self.observations.append(observation)
            def act(self, action_spec):
                decision = Decision(self.label, list(self.observations), tuple(action_spec.options),
                                    {'action_spec': action_spec.to_dict()})
                session.messages.put(('decision', (decision, action_spec)))
                self.answer = session.commands.get()
                if self.answer is None:
                    raise _Cancelled()
                return self.answer

        entities = {label: External(label) for label in ('A', 'B')}

        class GM(entity_lib.Entity):
            def __init__(self):
                self.world, self.actions = [], []
                self.acting, self.pending = None, None
            @property
            def name(self):
                return 'FixtureGM'
            def observe(self, observation):
                if observation.startswith(PUTATIVE_EVENT_TAG):
                    self.pending = observation
                if observation.startswith(EVENT_TAG):
                    answer = entities[self.acting].answer
                    self.actions.append(answer)
                    result = task_result(manifest['task']['body'], self.actions) if scheduling else None
                    self.world.append(observation)
                    session.messages.put(('resolved', {'acting': self.acting, 'intent': answer,
                        'resolved': observation, 'putative': self.pending,
                        'resolution': self.resolution, 'task_result': result}))
            def act(self, action_spec):
                match action_spec.output_type:
                    case entity_lib.OutputType.TERMINATE:
                        return 'Yes' if len(self.world) >= 2 else 'No'
                    case entity_lib.OutputType.NEXT_GAME_MASTER:
                        return self.name
                    case entity_lib.OutputType.NEXT_ACTING:
                        self.acting = manifest['order'][len(self.world)]
                        return self.acting
                    case entity_lib.OutputType.NEXT_ACTION_SPEC:
                        spec = manifest['task']['body']['action_specs'][self.acting] if scheduling else manifest['action_spec']
                        return engine_lib.action_spec_to_string(entity_lib.action_spec_from_dict(spec))
                    case entity_lib.OutputType.MAKE_OBSERVATION:
                        label = action_spec.call_to_action.removeprefix('OBSERVE:')
                        return actor_observation(manifest, label, self.actions) if scheduling else manifest['observations'][label]
                    case entity_lib.OutputType.RESOLVE:
                        self.resolution = resolved_text(manifest['task']['body'], self.actions + [entities[self.acting].answer]) if scheduling else f'resolved[{len(self.world)}]: {self.pending}'
                        return self.resolution
                    case _:
                        raise ContractError('unsupported GM action spec')

        gm = GM()
        Sequential(call_to_make_observation='OBSERVE:{name}').run_loop(
            game_masters=[gm], entities=list(entities.values()), max_steps=2,
            step_controller=StepController(start_paused=False))
        if len(gm.world) != 2:
            raise ContractError('Engine did not resolve both turns')
        result = task_result(manifest['task']['body'], gm.actions) if scheduling else None
        self.messages.put(('done', Status(True, reason='two_entities_resolved',
            results={'task': 'success' if not result or result['status'] == 'agreed' else 'task_failure'})))

    def close(self):
        if self.closed:
            return
        self.commands.put(None)
        self.thread.join(timeout=5)
        if self.thread.is_alive():
            raise ContractError('Concordia thread cleanup unconfirmed')
        self.closed = True


def create(config):
    return ConcordiaSession(config)


create.identity = lambda: {'concordia': json.loads(data_path('pins', 'concordia.json').read_bytes())['sha']}


def run_engine(store, run, manifest, short_root, runtime_type):
    """Compatibility driver: preserve DSH facts, receipts and legacy outcomes."""
    transport = manifest.get('input_contract') in (
        'scheduling-transport.v1', 'scheduling-priced.v1', 'scheduling-tokenkey.v1',
        'scheduling-tokenkey.v2', 'finite-suite-tokenkey.v1', 'finite-candidate-loopback.v1',
        'finite-candidate-tokenkey.v1', 'visible-robustness-tokenkey.v1')
    scheduling = 'task' in manifest
    session, ports = None, []
    try:
        session = ConcordiaSession(manifest)
        while not session.status().done:
            frame = session.observe()
            decision = frame.decisions[0]
            label = decision.agent
            who = manifest['entities'][label]
            port = runtime_type(store, run, who, short_root)
            ports.append(port)
            port.start()
            task = {'observations': decision.observation, 'memory': manifest['memory'][who],
                    'action_spec': decision.constraints['action_spec']}
            if manifest.get('input_contract') in ('scheduling-tokenkey.v2', 'finite-suite-tokenkey.v1',
                    'finite-candidate-loopback.v1', 'finite-candidate-tokenkey.v1', 'visible-robustness-tokenkey.v1'):
                from actio.evidence.audit.transport_contract import payload
                task = payload(manifest, label, decision.observation)
            if not transport:
                task['answer'] = manifest['scripted_actions'][label] if scheduling else (
                    'INVALID' if manifest['illegal'] and label == 'B' else 'cooperate')
            result = port.submit(task)
            source = final_source(store, result)
            reply = session.submit({label: result['answer']}, operation=result['op'], expected_revision=frame.revision)
            if reply.status == 'rejected':
                with store.tx():
                    store.db.execute('INSERT INTO domain_receipt VALUES(?,?,?,?,?)', (result['op'],
                        'task_failure', source[0], source[1], wire({'rejected': 'illegal_action', 'world_unchanged': True})))
                port.confirm_effect()
                port.close()
                return 'task_failure'
            effect = reply.outcomes[0].effects
            with store.tx():
                store.audit(run['id'], result['op'], 'gm_resolve', {'intent': effect['putative'],
                    'resolved': effect['resolution'], 'source': 'GM.act(RESOLVE)'})
                store.db.execute('INSERT INTO world VALUES(?,?,?,?,?,?,?)', (run['id'], frame.revision,
                    who, result['answer'], effect['resolved'], source[0], source[1]))
                store.db.execute('INSERT INTO domain_receipt VALUES(?,?,?,?,?)', (result['op'],
                    'task_failure' if effect['task_result'] and effect['task_result']['status'] == 'not_agreed' else 'success',
                    source[0], source[1], wire({'resolved': effect['resolved'], 'producer': 'GM.observe(EVENT)',
                        'putative': effect['putative'], **({'task_result': effect['task_result']} if scheduling else {})})))
                store.audit(run['id'], None, 'engine_step', {'acting_entity': label})
            port.confirm_effect()
            port.close()
        return session.status().results['task']
    finally:
        primary, errors = sys.exception(), []
        for resource in [*ports, *([session] if session else [])]:
            try:
                resource.close(force=True) if resource in ports else resource.close()
            except Exception as error:
                errors.append(error)
                store.audit(run['id'], None, 'cleanup_failure', {'reason': str(error)})
        if errors:
            if primary:
                primary.add_note('cleanup failure: ' + str(errors[0]))
            else:
                raise errors[0]
