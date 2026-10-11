"""Test-only SDK host which hangs at the public close boundary."""
from pathlib import Path
import sys
import threading
from deepseek_harness import DeepSeekHarness
from actio.adapters.runtime.host import main

root=Path(sys.argv[1])
def hang(self):
    (root/'close-entered').write_text('public SDK close entered')
    threading.Event().wait()
DeepSeekHarness.close=hang
main(root)
