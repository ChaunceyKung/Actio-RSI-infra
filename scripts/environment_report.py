"""Publish compact receipts; leave raw logs, DBs and journals in .local."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('receipt', type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    raw = args.receipt.read_bytes()
    original = json.loads(raw)
    rows = [{k: row[k] for k in ('suite', 'tests', 'failures', 'errors', 'skipped', 'status',
                                 'collection_execution_match', 'failed_ids', 'error_ids', 'log_sha256')}
            for row in original['rows']]
    result = {'status': original['status'], 'group': original.get('group'),
              'raw_receipt_sha256': hashlib.sha256(raw).hexdigest(),
              'tests': sum(r['tests'] for r in rows), 'rows': rows,
              'source_tree_sha256': hashlib.sha256(json.dumps(original['sources'], sort_keys=True).encode()).hexdigest(),
              'scope': original.get('scope'),
              'raw_artifacts': 'local only; rerun maintained validation command to reproduce'}
    if 'not_run' in original:
        result['not_run'] = original['not_run']
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8', newline='\n')


if __name__ == '__main__':
    main()
