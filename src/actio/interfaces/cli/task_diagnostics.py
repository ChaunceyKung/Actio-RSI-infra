from actio.evidence.diagnostics.task_diagnostics import plan, verify, ZERO
from actio.application.task_diagnostics import analyze
import sys
from actio.contracts.json import canonical
from actio.contracts.json import ContractError
from actio.contracts.json import seal
from actio.tasks.registry import require
SCHEMA = 'task-diagnostic-package.v1'
READER = '3bef7e15b0eb21beeb10888eb508056592b977b0'
PACKAGE_FILES = ['plan.json', 'dataset.json', 'policies.json', 'metrics.json', 'historical-actions.json',
                 'source-assurance.json', 'retrospective.json', 'synthetic-report.json', 'overlap.json']
ZERO = {'new_model_requests': 0, 'new_provider_requests': 0, 'new_catalog_get': 0,
        'new_mcp_calls': 0, 'new_dsh_workers': 0, 'credential_reads': 0}

def main(argv=None):
    # Explicit offline parsing avoids argparse/gettext's environment lookup.
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if args == ['plan']:
            out = {'valid': True, 'plan': seal(plan()), **ZERO}
        elif len(args) == 2 and args[0] == 'verify':
            out = verify(args[1])
        elif args and args[0] == 'analyze':
            allowed = {'--source', '--output', '--source-receipt', '--dataset'}
            require(len(args) % 2 == 1, 'analyze requires option/value pairs')
            pairs = list(zip(args[1::2], args[2::2]))
            require(all(k in allowed for k, _ in pairs) and len({k for k, _ in pairs}) == len(pairs), 'unknown or duplicate option')
            opts = dict(pairs); require({'--source', '--output'} <= set(opts), '--source and --output required')
            out = analyze(opts['--source'], opts['--output'], receipt=opts.get('--source-receipt'), data_path=opts.get('--dataset'))
        else:
            raise ContractError('usage: actio diagnostics task plan | analyze --source DIR --output NEW_DIR [--source-receipt FILE] [--dataset FILE] | verify DIR')
    except (OSError, ContractError, KeyError, TypeError, ValueError, IndexError) as exc:
        out = {'valid': False, 'reason': str(exc), **ZERO}
    print(canonical(out))
    return 0 if out['valid'] else 1

if __name__=='__main__':raise SystemExit(main())
