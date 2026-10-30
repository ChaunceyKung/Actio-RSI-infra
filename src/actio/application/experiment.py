"""Bounded experiment orchestration over injected environment sessions."""
from dataclasses import asdict
import json
import time

from actio.contracts.json import ContractError, canonical, digest
from actio.application.terminal import seal_terminal


def validate_plan(plan):
    if type(plan) is not dict or set(plan) != {'environment', 'config', 'agents', 'episodes', 'max_actions', 'deadline_seconds'}:
        raise ContractError('invalid experiment fields')
    for name, limit in [('episodes', 1000), ('max_actions', 10000), ('deadline_seconds', 170)]:
        if type(plan[name]) is not int or not 1 <= plan[name] <= limit:
            raise ContractError('invalid experiment bound: ' + name)
    if not isinstance(plan['environment'], str) or not plan['environment'] or type(plan['config']) is not dict:
        raise ContractError('environment name/config required')
    if type(plan['agents']) is not dict or not plan['agents'] or any(
            not isinstance(agent, str) or not agent or policy != 'first-legal' for agent, policy in plan['agents'].items()):
        raise ContractError('named first-legal rule agents required')
    return json.loads(canonical(plan))


def first_legal(decision):
    if not decision.legal_actions:
        raise ContractError('rule agent requires enumerated legal actions')
    return decision.legal_actions[0]


def experiment(store, key, plan, *, environment_factory, environment_identity, policy=first_legal):
    """Each episode is a normal Store run/lease; repeated keys never reexecute."""
    plan = validate_plan(plan)
    agents = {}
    for agent, name in plan['agents'].items():
        spec = {'kind': 'rule', 'policy': name, 'version': 1}
        agents[agent] = store.agent(agent, spec)['spec_hash']
    runs = []
    for episode in range(plan['episodes']):
        request = {'scenario': 'environment', 'experiment': key, 'episode': episode, 'plan': plan,
                   'environment_identity': environment_identity}
        manifest = {'input_contract': 'environment-session.v1', 'scenario': 'environment',
                    'request': request, 'agents': agents, 'execution_mode': 'rule',
                    'environment': environment_identity, 'plan_hash': digest(plan)}
        run, fresh = store.begin(f'{key}:{episode}', manifest, request=request)
        if fresh:
            run = _episode(store, run, plan, environment_factory, policy)
        runs.append(run)
    return {'experiment': key, 'plan_hash': digest(plan), 'runs': runs}


def _episode(store, run, plan, factory, policy):
    session, primary, cleaned = None, None, False
    deadline = time.monotonic() + plan['deadline_seconds']

    def record(kind, value):
        with store.tx():
            store.fence(run['id'], run['epoch'])
            store.audit(run['id'], None, 'environment_' + kind, value)

    try:
        session = factory(plan['config'])
        record('opened', {'capabilities': asdict(session.capabilities)})
        if not session.capabilities.synchronous or session.capabilities.asynchronous:
            raise ContractError('this experiment driver requires synchronous settlement')
        cursor, actions = 0, 0
        while not session.status().done:
            if time.monotonic() >= deadline:
                raise TimeoutError('experiment deadline exceeded')
            if actions >= plan['max_actions']:
                raise ContractError('experiment action limit reached')
            store.dispatch_fence(run['id'], run['epoch'])
            frame = session.observe()
            if not frame.decisions or len({d.agent for d in frame.decisions}) != len(frame.decisions):
                raise ContractError('environment requires unique acting agents')
            record('observation', asdict(frame))
            intents = {}
            for decision in frame.decisions:
                if decision.agent not in plan['agents']:
                    raise ContractError('acting agent absent from experiment')
                intents[decision.agent] = policy(decision)
            operation = f'{run["id"]}:{actions}'
            record('intent', {'operation': operation, 'revision': frame.revision, 'actions': intents})
            reply = session.submit(intents, operation=operation, expected_revision=frame.revision)
            record('submission', asdict(reply))
            if reply.status != 'accepted':
                raise ContractError('environment rejected or deferred intent: ' + str(reply.reason))
            outcomes = session.poll(cursor)
            if len(outcomes) != 1 or tuple(reply.outcomes) != tuple(outcomes):
                raise ContractError('synchronous environment settlement missing or inconsistent')
            for outcome in outcomes:
                if outcome.cursor != cursor + 1 or outcome.operation != operation:
                    raise ContractError('environment outcome cursor/operation mismatch')
                record('resolution', asdict(outcome))
                cursor = outcome.cursor
            actions += 1
        record('terminal', asdict(session.status()))
        session.close()
        cleaned = True
        record('closed', {'confirmed': True})
        seal_terminal(store, run['id'], run['epoch'], 'success')
        return store.finish(run['id'], run['epoch'], task='success')
    except BaseException as error:
        primary = error
        record('failure', {'type': type(error).__name__, 'reason': str(error)})
        raise
    finally:
        if primary is not None:
            if session is not None and not cleaned:
                try:
                    session.close()
                    cleaned = True
                    record('closed', {'confirmed': True})
                except BaseException as cleanup:
                    primary.add_note('environment cleanup failed: ' + str(cleanup))
                    record('cleanup_failure', {'type': type(cleanup).__name__, 'reason': str(cleanup)})
            if session is None or cleaned:
                try:
                    store.finish(run['id'], run['epoch'], task='infrastructure_failure', reason=str(primary))
                except Exception as failure:
                    primary.add_note('finish failed: ' + str(failure))
            # Unconfirmed cleanup deliberately retains the lease for reconciliation.
