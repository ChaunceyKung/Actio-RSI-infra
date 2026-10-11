"""Portable offline task diagnostics; no credentials, runtime, network or database.

Trusted registry is shipped with code. Bundle hashes are data references, never
permission to import an artifact-selected reader or execute bundled code.
"""
import hashlib
from pathlib import Path
import sys

from actio.contracts.json import canonical
from actio.contracts.json import digest
from actio.contracts.json import ContractError
from actio.contracts.json import seal
from actio.contracts.json import unseal
from actio.tasks.registry import require
from actio.contracts.json import parse
from actio.tasks.finite import cards
from actio.tasks.diagnostic import dataset
from actio.tasks.diagnostic import validate_dataset
from actio.tasks.diagnostic import CTA
from actio.tasks.controls import VERSION as POLICY
from actio.tasks.controls import CONTROLS
from actio.measurement.diagnostic import metric_definitions
from actio.measurement.diagnostic import synthetic_analysis
from actio.measurement.diagnostic import retrospective

SCHEMA = 'task-diagnostic-package.v1'
READER = '3bef7e15b0eb21beeb10888eb508056592b977b0'
PACKAGE_FILES = ['plan.json', 'dataset.json', 'policies.json', 'metrics.json', 'historical-actions.json',
                 'source-assurance.json', 'retrospective.json', 'synthetic-report.json', 'overlap.json']
ZERO = {'new_model_requests': 0, 'new_provider_requests': 0, 'new_catalog_get': 0,
        'new_mcp_calls': 0, 'new_dsh_workers': 0, 'credential_reads': 0}


def read_json(path, maximum=16 * 1024 * 1024):
    path = Path(path)
    require(not path.is_symlink() and not path.is_junction(), 'data link/junction not permitted')
    require(path.is_file() and path.stat().st_size <= maximum, 'missing or oversized data file')
    return parse(path.read_text(encoding='utf8'))


def trust():
    return read_json(Path(__file__).resolve().parents[2].joinpath('task_diagnostic_trust.json'))


def source_pins():
    root = Path(__file__).resolve().parents[2]
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest() for p in sorted(root.rglob('*')) if p.is_file() and (p.suffix in ('.py','.mjs','.sql','.json','.txt') or p.name=='SOTOPIA_LICENSE')}


def policies():
    return {'schema': POLICY, 'controls': CONTROLS,
            'demonstration_tie_break': 'first argmax in ActionSpec order; set membership remains normative',
            'legacy_comparison': 'scheduling first maximum; bargaining maximum (score, action string)',
            'authority': 'synthetic controls only; no candidate/solver/training labels'}


def plan():
    return {'schema': 'task-diagnostic-plan.v1', 'dataset_hash': dataset()['sha256'],
            'policy_hash': digest(policies()), 'metrics_hash': digest(metric_definitions()),
            'source': source_pins(), 'design': 'bc645c1', 'historical_reader': READER,
            'counts': {'groups': 8, 'worlds': 16, 'presentations': 32, 'legal_combinations': 416,
                       'policy_controls': 160, 'historical_live_pairs': 12},
            'scope': 'diagnostic_development; synthetic controls and retrospective public actions',
            'historical_real_generation_attempts': 139, 'historical_catalog_get': 1,
            'money_authorization': 'existing uncapped authorization unchanged; no calls in this phase',
            'human_labels': 0, 'independent_research_units': 0, 'activation': False, **ZERO}


def extract_history(report, pre, decision, lineage, registry):
    """Whitelist public actions/metrics; never copy raw HTTP/reasoning/session data."""
    p = unseal(pre)
    refs = {r['unit']['id']: r for r in report['execution_refs']}
    rows = []
    for r in report['rows']:
        u = r['unit']; ref = refs[u['id']]
        rows.append({'card': u['card'], 'arm': u['arm'], 'actions': {s['seat']: s['action'] for s in r['seats']},
            'original_metrics': r['metrics'], 'original_metric_cells': r['metric_cells'],
            'binding': {'episode': u['id'], 'pair_hash': u['pair_hash'], 'card_hash': u['pair']['card_hash'],
                        'task_hash': ref['dataset_hash'], 'candidate_hash': u['candidate_hash'],
                        'scaffold_hash': u['scaffold_hash'], 'report_row_hash': digest(r),
                        'text_verified': {s['seat']: s['text_verified'] for s in r['seats']}}})
    return {'schema': 'task-diagnostic-historical-actions.v1', 'tasks': p['cards'], 'rows': rows,
            'decision': decision, 'lineage_hash': lineage['sha256'],
            'source': {'reader_commit': READER, 'product_commit': '6466e2be6f31e0ac5861a379d761d2e7bf39c5eb',
                       'files': registry['historical_files'], 'report_hash': digest(report), 'plan_hash': pre['sha256'],
                       'source_hashes': registry['historical_source_hashes']},
            'persona': registry['persona'], 'checklist': p['versions']['candidate']['artifact']['scaffold']['checklist'],
            'original_counts': report['counts'], 'original_candidate_decision': report['candidate_decision'],
            'original_activation': report['activation']}


def load_history(folder):
    folder = Path(folder); registry = trust()
    values = {}
    for name, pin in registry['historical_files'].items():
        path = folder / name
        value = read_json(path)
        require(hashlib.sha256(path.read_bytes()).hexdigest() == pin, 'untrusted historical input: ' + name)
        values[name] = value
    history = extract_history(values['samples/report.json'], values['preregistration.json'],
                              values['samples/decision.json'], values['samples/lineage.json'], registry)
    require(digest(history) == registry['historical_excerpt_hash'], 'historical excerpt trust anchor mismatch')
    return history


def assurance(receipt=None):
    registry = trust()
    if receipt is None:
        return {'schema': 'task-diagnostic-assurance.v1', 'source_assurance': 'public_projection_only',
                'raw_verified_here': False, 'receipt_hash': None, 'reader_commit': READER,
                'portable_scope': 'pinned public excerpt and synthetic consistency; raw protocol not authenticated'}
    raw = Path(receipt).read_bytes(); value = read_json(receipt)
    require(hashlib.sha256(raw).hexdigest() == registry['source_receipt_file_hash'], 'untrusted source receipt')
    require(value['reader_commit'] == READER and value['exit_code'] == 0 and value['result']['report_exact'], 'failed old-reader certification')
    return dict(registry['certified_assurance'])


def overlap(history):
    persona = history['persona']
    pairs = [
        ('Follow the public rules and your own hard constraints.', CTA, 'format and own/public hard metrics already at observed ceiling'),
        ('Use only your own context and actual public actions.', None, 'visible-input boundary requirement, not a measured hidden belief'),
        ('Return exactly one action_spec option as plain text without quotes, JSON, explanation or private details.', CTA, 'exact-option formatting requirement'),
    ]
    return {'schema': 'task-diagnostic-overlap.v1', 'persona': persona, 'call_to_action': CTA,
            'comparisons': [{'checklist': item, 'persona_excerpt': p, 'action_spec_overlap': c, 'observation': o}
                            for item, (p, c, o) in zip(history['checklist'], pairs)],
            'interpretation': 'authored content-overlap comparison; not proof of prompt equivalence or duplication ineffectiveness',
            'baseline_and_candidate_observed_violations': {'baseline': 0, 'candidate': 0}}


def build(history, source_assurance, data):
    registry = trust()
    require(digest(history) == registry['historical_excerpt_hash'], 'untrusted or altered historical public actions')
    validate_dataset(data)
    require(history['tasks'] == cards(), 'old task outputs changed')
    require(source_assurance in (assurance(), registry['certified_assurance']), 'unknown historical assurance')
    sidecar = retrospective({**history, 'source_assurance': source_assurance['source_assurance']})
    return {'plan.json': seal(plan()), 'dataset.json': data, 'policies.json': seal(policies()),
            'metrics.json': seal(metric_definitions()), 'historical-actions.json': seal(history),
            'source-assurance.json': seal(source_assurance), 'retrospective.json': seal(sidecar),
            'synthetic-report.json': seal(synthetic_analysis(data)), 'overlap.json': seal(overlap(history))}


def gates(values):
    synthetic = unseal(values['synthetic-report.json']); retro = unseal(values['retrospective.json'])
    source = unseal(values['source-assurance.json'])
    return {**synthetic['gates'], 'historical_source_assurance': 'PASS_LOCAL_FIXED_READER' if source['source_assurance'] == 'fixed_reader_local_attested' else 'PARTIAL_PUBLIC_PROJECTION_ONLY',
            'retrospective_diagnostic_reproducibility': 'PASS' if retro['original_metrics_equal'] else 'NO_GO',
            'offline_portability': 'PASS_INTERNAL_RECOMPUTATION', 'live_solver_discrimination': 'NOT_RUN',
            'research_validity': 'UNESTABLISHED', 'capability_admission': 'insufficient_evidence',
            'production_activation': 'BLOCKED_FALSE', 'billing_upstream_identity': 'UNVERIFIED',
            'binary_source_mapping': 'unproven', 'full_controller_recovery': 'unsupported'}


def manifest(values):
    return seal({'schema': SCHEMA, 'files': {n: {'body_sha256': v['sha256'],
                    'file_sha256': hashlib.sha256(canonical(v).encode()).hexdigest()} for n, v in values.items()},
                 'source': source_pins(), 'gates': gates(values), 'reader_dispatch': 'installed trusted task_diagnostics only',
                 'trust_scope': 'code-anchored public excerpt + internal recomputation; raw authentication requires fixed old reader and controlled original',
                 **ZERO})





def verify(folder):
    try:
        folder = Path(folder)
        require(folder.is_dir() and not folder.is_symlink() and not folder.is_junction(), 'regular package directory required')
        require({p.name for p in folder.iterdir()} == set(PACKAGE_FILES + ['manifest.json']), 'package file whitelist/completeness')
        values = {n: read_json(folder / n) for n in PACKAGE_FILES}
        expected = build(unseal(values['historical-actions.json']), unseal(values['source-assurance.json']), values['dataset.json'])
        require(values == expected, 'diagnostic report/contract recomputation mismatch')
        actual_manifest = read_json(folder / 'manifest.json')
        require(actual_manifest == manifest(values), 'manifest/version/source/reference mismatch')
        for n, pin in unseal(actual_manifest)['files'].items():
            require(hashlib.sha256((folder / n).read_bytes()).hexdigest() == pin['file_sha256'], 'file bytes mismatch: ' + n)
        return {'valid': True, 'manifest_hash': actual_manifest['sha256'], 'gates': gates(values),
                'counts': unseal(values['synthetic-report.json'])['counts'],
                'retrospective': unseal(values['retrospective.json'])['summary'],
                'source_assurance': unseal(values['source-assurance.json']), 'raw_authentication_repeated': False, **ZERO}
    except (OSError, ContractError, KeyError, TypeError, ValueError, IndexError) as exc:
        return {'valid': False, 'reason': str(exc), **ZERO}
