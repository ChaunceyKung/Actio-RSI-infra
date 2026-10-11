"""Compatibility entry point; implementation lives in actio.interfaces.budget."""
from actio.profiles.registry import *
from actio.interfaces.budget import main
from actio.adapters.persistence.ledger import Ledger
from actio.evidence.audit.accounting import verify_snapshot
from actio.evidence.audit.accounting import verify_run_attempts

if __name__ == '__main__':
    raise SystemExit(main())
