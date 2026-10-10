"""New standard-library-only environment; copy exact product text, never runtime binaries."""
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    if len(sys.argv)!=2:raise SystemExit('usage: install_failure_diagnostics.py NEW_VENV')
    dest=Path(sys.argv[1]).resolve()
    if dest.exists():raise SystemExit('new environment directory required')
    subprocess.run([sys.executable,'-m','venv','--without-pip',str(dest)],check=True)
    python=dest/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
    site=Path(subprocess.check_output([str(python),'-X','utf8','-I','-c','import sysconfig;print(sysconfig.get_path("purelib"))'],text=True,encoding='utf8').strip())
    shutil.copytree(ROOT/'src/actio',site/'actio',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    subprocess.run([str(python),'-X','utf8','-I','-B','-c',
        'import importlib.util;assert importlib.util.find_spec("deepseek_harness") is None;assert importlib.util.find_spec("concordia") is None;from actio.transport_diagnostics import plan;assert plan()["network_requests"]==0;print("stdlib diagnostics installation PASS")'],check=True)
    print(str(python))


if __name__=='__main__':main()
