"""Public local-only two-seat smoke; all plans remain inside the test service process."""
import argparse
import json
from pathlib import Path
import sys
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from chat_stub import ChatStub
from actio.common import canonical,write_json
from actio.store import Store
from actio.transport import transport_spec,scheduling_transport
from actio.transport_contract import config
from actio.task_contract import task_card
from actio.budget import Ledger,verify_snapshot
from actio.evidence import export_bundle
from actio.transport_campaign import export_campaign


def run(root,endpoint,ledger_path,cfg,variant='compatible',runtime_type=None):
    s=Store(root/'ledger.sqlite',create=True)
    try:
        for a in ('ACTOR_A','ACTOR_B'):s.agent(a,transport_spec(a))
        bindings={seat:{'agent':a,'spec_hash':s.agent(a)['spec_hash']} for seat,a in [('A','ACTOR_A'),('B','ACTOR_B')]}
        task=task_card(variant,bindings,'transport_stub');error=None
        try:scheduling_transport(s,'episode',root,task=task,config=cfg,ledger_path=ledger_path,**({'runtime_type':runtime_type} if runtime_type else {}))
        except Exception as e:error={'type':type(e).__name__,'reason':str(e)}
        result=s.run('episode')
        exported=export_bundle(s.path,'episode',root/'bundle')
        return {'run':result,'error':error,'export':exported}
    finally:s.close()


def main():
    p=argparse.ArgumentParser();p.add_argument('--case',default='attached');p.add_argument('--variant',default='compatible');a=p.parse_args()
    root=Path('D:/actio-c2a1-smoke')/uuid.uuid4().hex[:12];root.mkdir(parents=True)
    with ChatStub(root,[{'text':'propose:morning','case':a.case},{'text':'accept','case':'trailing'}]) as service:
        cfg=config(service.endpoint);ledger=Ledger(root/'budget.sqlite',config=cfg);ledger.close()
        result=run(root,service.endpoint,root/'budget.sqlite',cfg,a.variant)
    ledger=Ledger(root/'budget.sqlite',readonly=True)
    try:snapshot=ledger.snapshot();verify_snapshot(snapshot)
    finally:ledger.close()
    campaign=export_campaign(root/'budget.sqlite',[root/'bundle'],service.receives,root/'campaign')
    write_json(root/'result.json',{**result,'budget':snapshot,'receives':service.receives,'campaign':campaign})
    print(canonical({'root':str(root),'error':result['error'],'verification':result['export']['verification'],
                     'states':[x['state'] for x in snapshot['attempts']],'local_http_requests':len(service.receives)}))
    return 0 if result['error'] is None else 1


if __name__=='__main__':raise SystemExit(main())
