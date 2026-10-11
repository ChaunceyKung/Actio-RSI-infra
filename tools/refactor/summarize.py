"""Inventory completed local regressions; publish counts/hashes, never raw captures."""
import argparse
import hashlib
import json
from pathlib import Path
from validate import hashes
from validate import SUITES

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recorded_roots(value):
    # Only test-owned top-level metadata, never paths embedded in an artifact.
    for row in value:
        item = row['evidence'].get('root')
        if isinstance(item, str) and Path(item).is_absolute():
            yield Path(item).resolve()


def collect(root, final_matrix='formal11'):
    reports, roots, errors, evidence_files = [], set(), [], []
    final_sources = hashes(ROOT/'src/actio')
    for folder in sorted(root.iterdir()):
        receipt = folder/'receipt.json'
        if receipt.is_file():
            value = json.loads(receipt.read_bytes())
            source = value.get('sources')
            changed = sorted(k for k in set(source or {}) | set(final_sources)
                             if (source or {}).get(k) != final_sources.get(k)) if source else None
            reports.append({'name': folder.name, 'receipt_sha256': sha(receipt),
                            'status': value['status'], 'rows': value.get('rows', []),
                            'source_differences_from_final': changed,
                            'source_manifest_sha256': hashlib.sha256(json.dumps(source, sort_keys=True).encode()).hexdigest() if source else None,
                            'scope': value.get('scope')})
        for path in sorted(folder.glob('*-controlled-evidence.json')):
            roots.update(recorded_roots(json.loads(path.read_bytes())))
            evidence_files.append({'path': str(path), 'sha256': sha(path)})
    # Paths come from this run's controlled test receipts, never an old phase scan.
    receives = {}
    for folder in sorted(roots):
        if not folder.is_dir():
            errors.append({'path': str(folder), 'type': 'missing_recorded_root'})
            continue
        for path in folder.rglob('receives.json'):
            path = path.resolve()
            if path in receives:
                continue
            try:
                value = json.loads(path.read_bytes())
                assert type(value) is list
                receives[path] = {'path': str(path), 'count': len(value), 'sha256': sha(path)}
            except (ValueError, AssertionError, OSError) as error:
                errors.append({'path': str(path), 'type': type(error).__name__})
    matrices = []
    for path in sorted(root.glob('formal*/report.json')):
        name = path.parent.name
        role = 'final installation matrix' if name == final_matrix else 'superseded installation additional matrix'
        value = json.loads(path.read_bytes())
        matrices.append({'name': name, 'role': role, 'report_sha256': sha(path), 'status': value['status'],
                         'totals': value['totals'], 'workers': len(value['cleanup']['jobs']),
                         'services': len(value['cleanup']['ports'])})
    latest = {}
    for report in reports:
        for row in report['rows']:
            old = latest.get(row['suite'])
            if old is None or row['started'] > old['started']:
                latest[row['suite']] = {**row, 'receipt': report['name'],
                                        'source_differences_from_final': report['source_differences_from_final']}
    development = sum(v['count'] for v in receives.values())
    return {'status': 'INCOMPLETE', 'regressions': reports, 'latest_suite_outcomes': latest,
            'missing_suites': sorted(set(sum(SUITES.values(), [])) - set(latest)),
            'latest_test_total': sum(row['tests'] for row in latest.values()),
            'latest_pass_test_total': sum(row['tests'] for row in latest.values() if row['status'] == 'PASS'),
            'development_loopback_receives': development,
            'development_receive_files': list(receives.values()), 'development_count_errors': errors,
            'development_count_scope': 'unique receives.json below roots in this run controlled test evidence; includes failed and repeated tests; excludes all formal matrices and in-process MJS emissions',
            'recorded_test_roots': [str(p) for p in sorted(roots)], 'controlled_evidence_hashes': evidence_files,
            'matrices': matrices,
            'observed_total_loopback_receives': development + sum(m['totals']['received'] for m in matrices),
            'external_requests': 0,
            'limitations': ['latest suite results retain installation differences; they do not assert all tests ran on final wheel',
                            'HTTP count is a receive-file census, not a packet trace; interrupted tests without evidence would not be covered']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--final-matrix', default='formal11')
    args = parser.parse_args()
    value = collect(args.root, args.final_matrix)
    if not any(m['name'] == args.final_matrix for m in value['matrices']):
        raise SystemExit('final matrix receipt missing')
    if any(r['status'] == 'RUNNING' for r in value['regressions']):
        raise SystemExit('regression still running; no final summary written')
    args.output.write_text(json.dumps(value, indent=2), encoding='utf8')
    print(json.dumps({'development_loopback_receives': value['development_loopback_receives'],
                      'total_loopback_receives': value['observed_total_loopback_receives'],
                      'receipts': len(value['regressions']), 'roots': len(value['recorded_test_roots']),
                      'errors': len(value['development_count_errors'])}))


if __name__ == '__main__':
    main()
