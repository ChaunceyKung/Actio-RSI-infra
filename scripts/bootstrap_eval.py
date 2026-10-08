"""Install only the offline eval closure in a clean venv; no runtime/Concordia required."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from actio.common import clean_env


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--venv',type=Path,required=True);p.add_argument('--offline',action='store_true');p.add_argument('--characterization',action='store_true')
    a=p.parse_args();target=a.venv.resolve();prep=ROOT/'.local/eval-prepare';prep.mkdir(exist_ok=True)
    env=clean_env(prep)
    if not target.exists():subprocess.run([sys.executable,'-m','venv',str(target)],env=env,check=True)
    python=target/'Scripts/python.exe'
    cmd=[str(python),'-m','pip','--isolated','install','--disable-pip-version-check','--no-cache-dir','--require-hashes','--only-binary=:all:',
         '-r',str(ROOT/'requirements-eval.lock'),'--find-links',str(ROOT/'.local/wheels'),'--find-links',str(ROOT/'.local/eval-wheels')]
    if a.characterization:cmd+=['-r',str(ROOT/'requirements-eval-test.lock')]
    if a.offline:cmd+=['--no-index']
    subprocess.run(cmd,env=env,check=True)
    subprocess.run([str(python),'-m','pip','--isolated','install','--disable-pip-version-check','--no-deps','--no-build-isolation',str(ROOT)],env=env,check=True)
    print('Offline eval closure installed; core runtime dependencies intentionally not installed in eval-only venv.')
