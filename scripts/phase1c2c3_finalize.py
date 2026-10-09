"""Validate delivery provenance, preserve history, and scan only publication files."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/validation/phase1c2c3'
START = '217af1bcb106884fd4c164fc370f00cbaecffcc3'
sys.path.insert(0, str(ROOT / 'src'))
from actio.common import canonical, file_hash
from actio.task_diagnostics import source_pins, trust, verify


def write_new(name, body):
    with (DOC / name).open('x', encoding='utf8', newline='\n') as f:
        f.write(canonical(body))


def changed_files():
    names = subprocess.check_output(['git', '-c', 'core.quotepath=false', 'diff', '--name-only', START], cwd=ROOT, text=True, encoding='utf8').splitlines()
    names += subprocess.check_output(['git', '-c', 'core.quotepath=false', 'ls-files', '--others', '--exclude-standard'], cwd=ROOT, text=True, encoding='utf8').splitlines()
    return [ROOT / n for n in sorted(set(names)) if (ROOT / n).is_file()]


def scan():
    paths = changed_files(); raw = [p.read_bytes() for p in paths]
    # Explicit publication-only credential comparison; never log value/length/hash.
    secret = (ROOT / '.local/credentials/token_key.txt').read_text(encoding='utf-8-sig').strip().encode()
    assert secret and not any(secret in value for value in raw), 'credential publication blocked'
    assert not any(re.search(rb'\bsk-[A-Za-z0-9_-]{16,}|Bearer [A-Za-z0-9_-]{24,}', value) for value in raw), 'secret pattern blocked'
    historical = json.loads((ROOT / 'docs/validation/phase1c2c0/samples/pilot.json').read_bytes())
    attempt = historical['body']['entries'][7]['evidence']['ledger']['attempts'][0]
    texts = [''.join(x['text'] for x in json.loads(attempt['response']['chunks_json']) if x['type'] == 'reasoning-delta')]
    campaign = json.loads(Path('D:/actio-c2c2-live-v1/matrix/pilot.json').read_bytes())
    for entry in campaign['body']['entries']:
        if entry['evidence']:
            for attempt in entry['evidence']['ledger']['attempts']:
                if attempt['response']:
                    texts.append(''.join(x['text'] for x in json.loads(attempt['response']['chunks_json']) if x['type'] == 'reasoning-delta'))
    assert not any(t.encode() in value for t in texts if t for value in raw), 'historical reasoning publication blocked'
    assert not any(p.suffix in ('.sqlite', '.db', '.zip', '.exe', '.pyc') or '.local' in p.relative_to(ROOT).parts for p in paths)
    subprocess.run(['git', 'check-ignore', '--quiet', '.local/credentials/token_key.txt'], cwd=ROOT, check=True)
    assert not subprocess.check_output(['git', 'ls-files', '.local/credentials/token_key.txt'], cwd=ROOT)
    return {'status': 'PASS', 'files_scanned': len(paths), 'exact_credential': 'PASS',
            'credential_read_scope': 'publication scanner only; not diagnostic functions or provider use',
            'reasoning_body_copies': 0, 'database_cache_binary_publications': 0,
            'account_data': 'new package restricted to synthetic inputs, public actions, bindings, decisions and provenance',
            'credential_ignored_untracked': True}


def main():
    if sys.argv[1:] == ['scan']:
        print(canonical(scan())); return
    package = verify(DOC / 'package'); assert package['valid'], package
    sources = source_pins()
    evidence = [json.loads(p.read_bytes()) for p in (DOC / 'evidence').glob('*.json')]
    tests = [v for v in evidence if v.get('schema') == 'task-diagnostic-acceptance.v1' and v['status'] == 'PASS']
    cli = [v for v in evidence if v.get('schema') == 'task-diagnostic-cli-acceptance.v1' and v['status'] == 'PASS']
    literal = [v for v in evidence if v.get('schema') == 'task-diagnostic-literal-cli.v1' and v['status'] == 'PASS']
    assert len(tests) == len(cli) == len(literal) == 1
    assert all(v['source'] == sources for v in tests + cli + literal)
    freeze = json.loads((DOC / 'frozen-design/freeze.json').read_bytes())['body']
    probe = "from actio.task_diagnostic_data import dataset,validate_dataset; from actio.task_diagnostic_analysis import synthetic_analysis; d=dataset(); print(d['sha256'],len(d['body']['cards'])); validate_dataset(d); r=synthetic_analysis(d); print(r['counts']); print(r['gates'])"
    write_new('evidence/development-probes.json', {
        'schema': 'task-diagnostic-development-probes.v1', 'source': freeze['source'],
        'recording': 'transcribed from actual development tool outputs; not final-source acceptance',
        'attempts': [
            {'argv': ['.local/phase1c2c2-runtime-venv/Scripts/python.exe', '-m', 'py_compile', 'src/actio/task_diagnostic_data.py', 'src/actio/task_diagnostic_policy.py', 'src/actio/task_diagnostic_analysis.py', 'scripts/phase1c2c3_history.py'], 'exit_code': 0},
            {'environment_assignment': "PYTHONPATH='src'", 'argv': ['.local/phase1c2c2-runtime-venv/Scripts/python.exe', '-I', '-B', '-c', probe],
             'exit_code': 1, 'error': "ModuleNotFoundError: No module named 'actio.task_diagnostic_data'"},
            {'environment_assignment': "PYTHONPATH='src'", 'argv': ['.local/phase1c2c2-runtime-venv/Scripts/python.exe', '-B', '-c', probe],
             'exit_code': 0, 'result': {'dataset_hash': '3e37ca1cb71a90f3bef100a1ec4bff4721d584c19c3442ae04de42207630a02a', 'cards': 32, 'legal_combinations': 416, 'four_synthetic_gates': 'PASS'},
             'ordering_deviation': 'before machine-readable freeze; fixed design text already committed; data/policy not tuned'}],
        'tooling_note': 'One rg scripts/*scan* Windows glob search returned invalid filename; replaced by reading exact known scanner file. No product/test result inferred from that failed search.'})
    old = ROOT / 'docs/validation/phase1c2c2'
    assert all(file_hash(old / n) == expected for n, expected in trust()['historical_files'].items())
    claims = json.loads((old / 'execution-claims.json').read_bytes())
    assert all(file_hash(Path(claims['namespace']) / n) == row['sha256'] for n, row in claims['files'].items())
    assert file_hash(Path('D:/actio-c2c2-live-v1/delivery.json')) == trust()['certified_assurance']['certification_result']['delivery_file_sha256']
    changed = [p.relative_to(ROOT).as_posix() for p in changed_files()]
    assert not any(n.startswith('docs/validation/phase1c2c2/') for n in changed)
    assert not any(n.startswith('src/actio/') and not n.startswith('src/actio/task_diagnostic') for n in changed)
    ancestors = {}
    for pin in ['6466e2be6f31e0ac5861a379d761d2e7bf39c5eb', '3bef7e15b0eb21beeb10888eb508056592b977b0', START]:
        proc = subprocess.run(['git', 'merge-base', '--is-ancestor', pin, 'HEAD'], cwd=ROOT)
        assert proc.returncode == 0; ancestors[pin] = True
    write_new('preservation.json', {'schema': 'task-diagnostic-preservation.v1', 'start_head': START, 'start_remote_main': START,
        'start_worktree': 'clean', 'ancestors': ancestors, 'remote': 'https://github.com/ChaunceyKung/Actio-RSI-infra',
        'old_public_hashes_equal': trust()['historical_files'], 'old_controlled_delivery_unchanged': True,
        'immutable_claims_unchanged': len(claims['files']), 'old_product_files_changed': [], 'old_decisions_written': 0,
        'new_workers_jobs_services_ports': 'not created in this phase', 'new_model_provider_catalog_mcp_calls': 0,
        'historical_real_generation_attempts': 139, 'historical_catalog_get': 1})
    write_new('evidence/publication-scan.json', scan())
    artifacts = {p.relative_to(DOC).as_posix(): file_hash(p) for p in sorted(DOC.rglob('*')) if p.is_file()}
    write_new('evidence_manifest.json', {'schema': 'phase1c2c3-evidence-manifest.v1',
        'design_commit': 'bc645c1a81b77a7390cdcdecdde7c7b85572afd8',
        'implementation_commit': '0a66334d61a0de302bbf8f5e15ee1db1b9d2e8fb',
        'package_manifest_hash': package['manifest_hash'], 'source': sources, 'gates': package['gates'],
        'counts': package['counts'], 'retrospective': package['retrospective'], 'artifacts': artifacts,
        'tests': {'pure_tests': tests[0]['tests_run'], 'guarded_cli_commands': cli[0]['actual_commands'],
                  'literal_commands_including_install': len(literal[0]['commands']), 'source_bound': True},
        'entry_files': {n: file_hash(ROOT / n) for n in ('README.md', 'MILESTONES.md', 'AGENTS.md', '.gitattributes', 'pyproject.toml')},
        'tooling': {p.relative_to(ROOT).as_posix(): file_hash(p) for folder in ('scripts', 'tests') for p in sorted((ROOT / folder).glob('*'))
                    if p.is_file() and ('task_diagnostics' in p.name or 'phase1c2c3' in p.name)},
        'new_model_provider_catalog_mcp_workers': 0, 'historical_real_generation_attempts': 139, 'historical_catalog_get': 1,
        'process_limitation': 'initial finite development probe preceded machine-readable freeze; design text precommitted; formal acceptance after immutable data/source snapshot',
        'candidate_decision_mutations': 0, 'activation': False})
    # Check newly written manifest and all local markdown links, then scan final bytes.
    manifest = json.loads((DOC / 'evidence_manifest.json').read_bytes())
    assert all(file_hash(DOC / n) == h for n, h in manifest['artifacts'].items())
    links = 0
    for path in [ROOT / 'README.md', ROOT / 'MILESTONES.md', *DOC.glob('*.md')]:
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf8')):
            if '://' in target or target.startswith('#'):
                continue
            assert (path.parent / target.split('#')[0]).exists(), f'missing link: {path.name}: {target}'
            links += 1
    subprocess.run(['git', 'diff', '--check'], cwd=ROOT, check=True)
    result = scan()
    print(canonical({'status': 'PASS', 'artifacts': len(artifacts), 'links_checked': links, 'scan': result,
                     'counts': package['counts'], 'gates': package['gates']}))


if __name__ == '__main__':
    main()
