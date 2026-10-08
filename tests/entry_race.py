"""Two real control processes pause immediately before atomic begin; test-only gates."""
import json
import os
from pathlib import Path
import sys

from actio.common import ContractError
from actio.runtime import RuntimePort
from actio.scenarios import assistant,social
from actio.store import Store

root,scenario=Path(sys.argv[1]),sys.argv[2]
class GatedStore(Store):
    def begin(self,*args,**kwargs):
        (root/('ready-'+str(os.getpid()))).write_text('before atomic claim')
        assert sys.stdin.readline().strip()=='go'
        return super().begin(*args,**kwargs)

class CountedRuntime(RuntimePort):
    def start(self):
        with (root/'runtime-paths.jsonl').open('a') as out:
            out.write(json.dumps({'pid':os.getpid(),'run':self.run['id'],'agent':self.agent})+'\n')
        return super().start()

s=GatedStore(root/'ledger.sqlite')
try:
    if scenario=='assistant':run=assistant(s,'same','A',root,runtime_type=CountedRuntime)
    else:run=social(s,'same','A','B',root,runtime_type=CountedRuntime)
    denied=None
    if run['state'] in ('allocated','running'):
        try:s.finish(run['id'],run['epoch'],task='success')
        except ContractError as error:denied=str(error)
    print(json.dumps({'run':run['id'],'observed_state':run['state'],'finish_denied':denied}))
finally:s.close()
