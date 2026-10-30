"""Compose TOML settings with the existing bounded DSH/Concordia gateway use case."""
import json
from pathlib import Path
import uuid

from actio.contracts.json import ContractError, require
from actio.profiles.settings import load_settings, gateway_config
from actio.profiles.gateway_base import AUTH
from actio.adapters.filesystem.common import file_hash, write_json
from actio.adapters.filesystem.credentials import resolve_credential
from actio.interfaces.store import Store
from actio.adapters.persistence.ledger import Ledger
from actio.application.gateway import execute


def predecessors(paths):
    values = []
    for path in paths:
        path = Path(path).resolve()
        previous = json.loads(path.read_bytes())
        require(all(w['state'] == 'reaped' and json.loads(w['report']).get('after', json.loads(w['report'])).get('active') == 0
                    for ep in previous['episodes'] for w in ep['workers']), 'previous workers not reaped')
        values.append({'path': str(path), 'sha256': file_hash(path), 'reason': 'explicit diagnostic continuation'})
    return values


def run(settings_path=None, *, root=None, rehearsal=False, previous=()):
    settings = load_settings(settings_path)
    root = ((settings.source.parent / root).resolve() if root else
            settings.paths['runs'] / ('gw-' + uuid.uuid4().hex[:8]))
    require(not root.exists(), 'new run directory required; existing runs are never replayed')
    base_config = gateway_config(settings)
    secret = None
    try:
        if rehearsal:
            from actio.adapters.transport.fixture import GatewayStub
            fixture = root.with_name(root.name + '-fixture')
            require(not fixture.exists(), 'new fixture directory required')
            fixture.mkdir(parents=True)
            secret = 'ACTIO_FAKE_' + uuid.uuid4().hex
            responses = [p for variant in base_config['plan'] for p in (
                {'text': 'propose:morning', 'model': settings.llm['model']},
                {'text': 'accept' if variant == 'compatible' else 'decline', 'model': settings.llm['model']})]
            with GatewayStub(fixture, responses, secret) as service:
                config = gateway_config(settings, endpoint=service.endpoint, rehearsal=True)
                result = _execute(settings, root, config, secret, previous, service.receives)
        else:
            # Missing credentials fail before allocating any run, lease or authority.
            secret = resolve_credential(settings.source.parent, settings_path=settings.source)
            result = _execute(settings, root, base_config, secret, previous)
        return result
    except Exception as error:
        if secret:
            raise ContractError(str(error).replace(secret, '[credential omitted]')) from None
        raise
    finally:
        secret = None


def _execute(settings, root, config, secret, previous, receives=None):
    config['authority'] = {'id': uuid.uuid4().hex, 'root': str(settings.paths['authority'])}
    config['predecessors'] = predecessors(previous)
    result = execute(config, root, secret, operation_authorization=AUTH,
                     store_factory=Store, ledger_factory=Ledger, receives=receives)
    write_json(root / 'settings.json', settings.view())
    ledger = Ledger(root / 'budget.sqlite', readonly=True)
    try:
        snapshot = ledger.snapshot()
    finally:
        ledger.close()
    attempts = snapshot['attempts']
    summary = {'status': 'complete' if not result['not_run_episodes'] and all(
        ep['error'] is None and ep['bundle']['verification']['scenario_completeness'] == 'complete'
        for ep in result['episodes']) else 'incomplete',
        'mode': config['mode'], 'root': str(root), 'settings_hash': settings.sha256,
        'provider': settings.llm['provider'], 'model': settings.llm['model'],
        'episodes': [{'id': ep['run']['id'], 'state': ep['run']['state'], 'task': ep['run']['task'],
                      'error': ep['error'], 'evidence': ep['bundle']['verification']['scenario_completeness']}
                     for ep in result['episodes']],
        'attempts': len(attempts), 'settled': sum(a['state'] == 'settled' for a in attempts),
        'unknown': sum(a['state'] == 'unknown' for a in attempts), 'usage': snapshot['totals'],
        'spending_policy': settings.llm['spending_policy'], 'supplier_bill': 'unreconciled',
        'campaign_valid': result['campaign']['valid'], 'credential_scan': result['credential_scan']}
    write_json(root / 'summary.json', summary)
    return summary
