import json
from pathlib import Path
import shutil
import sysconfig

from actio.adapters.filesystem.common import file_hash
from actio.adapters.filesystem.common import write_json
from actio.adapters.runtime.runtime import RuntimePort

FIXTURES=Path(__file__).parent.parent/'fixtures'


class FaultRuntime(RuntimePort):
    mode=None
    script=None
    policy_changes={}
    limits_override={}

    def __init__(self,*args,**kwargs):
        super().__init__(*args,deadlines={'ready':4,'result':4,'drained':1,'closed':1},limits=self.limits_override,**kwargs)

    def prepare(self):
        super().prepare()
        config=json.loads((self.root/'profile.patch.yml').read_text(encoding='utf8'))
        plugins=config[-1]['insert']
        if self.mode in {'init','drain','rewrite','registry'}:
            plugins.append({'id':'test-fault','name':(FIXTURES/'faults.mjs').as_uri(),
                'config':{'mode':self.mode,'called':str(self.root/'late-called')}})
        if self.mode in {'run','exit','oversize'} or self.script is not None:
            plugins[-1 if plugins[-1]['id']=='actio-fixture' else 2]={'id':'actio-fixture','name':(FIXTURES/'provider.mjs').as_uri(),
                'config':{'mode':self.mode,'script':self.script,'log':str(self.root/'test-provider.jsonl')}}
        if self.mode=='mcp-hold':
            plugins[0]['config']['args']=[str(FIXTURES/'mcp_hold.py'),str(self.root)]
            plugins[1]['config']['tool']=str(FIXTURES/'mcp_hold.py')
            self.policy['toolHash']=file_hash(FIXTURES/'mcp_hold.py')
        self.policy.update(self.policy_changes)
        write_json(self.root/'policy.json',self.policy)
        write_json(self.root/'profile.patch.yml',config)
        if self.mode=='close':
            target=Path(sysconfig.get_path('purelib'))/'actio_test_close_host.py'
            shutil.copyfile(FIXTURES/'close_host.py',target)
            self.supervisor.module='actio_test_close_host'


def fault_type(mode=None,script=None,policy=None,limits=None):
    return type('ConfiguredFaultRuntime',(FaultRuntime,),{'mode':mode,'script':script,'policy_changes':policy or {},'limits_override':limits or {}})
