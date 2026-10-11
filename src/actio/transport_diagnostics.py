"""Compatibility entry point; implementation lives in actio.interfaces.transport_diagnostics."""
from actio.evidence.transport_diagnostics import *
from actio.interfaces.transport_diagnostics import main

if __name__ == '__main__':
    raise SystemExit(main())
