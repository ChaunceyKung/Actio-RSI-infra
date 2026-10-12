from actio.evidence.bundles.eval_contract import LIMITS
"""Bounded local child evaluation process; never a provider or plugin loader."""
import subprocess
import sys
import tempfile
from actio.contracts.json import canonical, parse, require
from actio.adapters.filesystem.common import clean_env

def execute_worker(payload,timeout):
    with tempfile.TemporaryDirectory(prefix='actio-eval-') as temp:
        env=clean_env(temp)
        command=[sys.executable,'-I','-B','-m','actio.interfaces.workers.eval_worker']
        try:
            p=subprocess.run(command,input=canonical(payload).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                             timeout=timeout,env=env,cwd=temp)
        except subprocess.TimeoutExpired as e:raise TimeoutError('local evaluator exceeded frozen deadline; child killed and waited') from e
        require(len(p.stdout)<=LIMITS['input_bytes'] and len(p.stderr)<=LIMITS['response_bytes'],'local evaluator output limit')
        if p.returncode:raise RuntimeError('local evaluator exit '+str(p.returncode)+': '+p.stderr.decode(errors='replace')[:256])
        return parse(p.stdout)
