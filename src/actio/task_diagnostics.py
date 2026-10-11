"""Compatibility task diagnostic module and reader entrypoint."""
from actio.evidence.diagnostics.task_diagnostics import *
from actio.application.task_diagnostics import analyze
from actio.interfaces.task_diagnostics import main
if __name__ == '__main__':raise SystemExit(main())
