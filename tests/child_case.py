"""Isolated process fault driver, synthetic data and task-owned processes only."""
import json
import os
from pathlib import Path
import sys

from actio.common import ContractError,write_json
from actio.memory import Memory
from actio.runtime import RuntimePort,synthetic_spec
from actio.scenarios import assistant
from actio.store import Store
from support import fault_type

mode,root=sys.argv[1],Path(sys.argv[2])
s=Store(root/'ledger.sqlite',create=True)
if mode=='race':
    (root/('ready-'+str(os.getpid()))).write_text('ready')
    assert sys.stdin.readline().strip()=='go'
    try:
        run,fresh=s.begin('race-'+str(os.getpid()),{'scenario':'assistant'})
        print(json.dumps({'winner':True,'run':run['id']}))
    except ContractError as e:
        print(json.dumps({'winner':False,'reason':str(e)}))
    s.close();raise SystemExit(0)
s.agent('A',synthetic_spec('A'))

if mode=='A':
    class AtAccepted(RuntimePort):
        def record(self,record):
            if record['kind']=='accepted':
                write_json(root/'crash-marker.json',{'window':'A','receipt':record['receipt'],'job':self.job_name,
                    'sdk_pid':self.supervisor.proc.pid,'job_before':self.supervisor.job.snapshot()})
                os._exit(81)
            return super().record(record)
    assistant(s,'crash-A','A',root,runtime_type=AtAccepted)
elif mode=='owner':
    run,_=s.begin('owner',{'scenario':'assistant','agents':{'A':s.agent('A')['spec_hash']}})
    port=RuntimePort(s,run,'A',root).start()
    write_json(root/'crash-marker.json',{'window':'owner','job':port.job_name,'sdk_pid':port.supervisor.proc.pid,
        'job_before':port.supervisor.job.snapshot()})
    os._exit(83)
elif mode=='B':
    class AtTool(fault_type(mode='mcp-hold')):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs);self.deadlines['result']=20
    try:
        assistant(s,'crash-B','A',root,runtime_type=AtTool)
    except Exception as e:
        write_json(root/'crash-marker.json',{'window':'B','error':str(e)})
        s.close();raise SystemExit(82)
elif mode=='D':
    class BeforeAck(Memory):
        def write(self,*args,**kwargs):
            receipt=super().write(*args,**kwargs)
            write_json(root/'crash-marker.json',{'window':'D','effect':receipt})
            os._exit(84)  # The domain caller never receives the memory acknowledgement.
    import actio.scenarios as scenarios
    scenarios.Memory=BeforeAck
    scenarios.assistant(s,'crash-D','A',root)
else:
    raise ValueError(mode)
