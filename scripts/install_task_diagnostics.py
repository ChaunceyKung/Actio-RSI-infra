"""Install only the pure diagnostic reader into a new stdlib-only environment."""
from pathlib import Path
import shutil
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from actio.common import canonical
from actio.task_diagnostics import SOURCE_FILES, source_pins
import hashlib


def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: python scripts/install_task_diagnostics.py NEW_VENV')
    dest = Path(sys.argv[1]).resolve()
    if dest.exists():
        raise SystemExit('destination must not exist')
    if sys.version_info[:2] != (3, 12) or sys.platform != 'win32':
        raise SystemExit('this minimal installer is validated for Windows Python 3.12 only')
    venv.EnvBuilder(with_pip=False).create(dest)
    package = dest / 'Lib/site-packages/actio'; package.mkdir(parents=True)
    for name in SOURCE_FILES:
        shutil.copyfile(ROOT / 'src/actio' / name, package / name)
    installed = {n: hashlib.sha256((package / n).read_bytes().replace(b'\r\n', b'\n')).hexdigest() for n in SOURCE_FILES}
    assert installed == source_pins()
    print(canonical({'status': 'PASS', 'python': str(dest / 'Scripts/python.exe'), 'source_install_equal': installed,
                     'dependencies': 'standard library only; no pip, DSH, MCP or Concordia', 'network_requests': 0}))


if __name__ == '__main__':
    main()
