"""Public local rehearsal: official adapter, USD quote estimates, fake memory-only key."""
import argparse
import json
from pathlib import Path
import sys
import uuid
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from readiness_stub import ReadyStub,scan_secret
from actio.common import canonical,write_json
from actio.store import Store
from actio.transport import transport_spec,scheduling_transport
from actio.task_contract import task_card
from actio.readiness_contract import rehearsal
from actio.budget import Ledger,verify_snapshot
from actio.evidence import export_bundle
from actio.transport_campaign import export_campaign


def run(root,cfg,ledger_path,secret,variant='compatible',runtime_type=None):
    root.mkdir(parents=True,exist_ok=True);s=Store(root/'ledger.sqlite',create=True)
    try:
        for a in ('ACTOR_A','ACTOR_B'):s.agent(a,transport_spec(a,cfg))
        bindings={seat:{'agent':a,'spec_hash':s.agent(a)['spec_hash']} for seat,a in [('A','ACTOR_A'),('B','ACTOR_B')]}
        task=task_card(variant,bindings,'priced_rehearsal');error=None
        try:scheduling_transport(s,'episode',root,task=task,config=cfg,ledger_path=ledger_path,credential=secret,**({'runtime_type':runtime_type} if runtime_type else {}))
        except Exception as e:error={'type':type(e).__name__,'reason':str(e)}
        result=s.run('episode');exported=export_bundle(s.path,'episode',root/'bundle')
        return {'run':result,'error':error,'export':exported}
    finally:s.close()


def main():
    p=argparse.ArgumentParser();p.add_argument('--case',default='attached');a=p.parse_args()
    root=Path('D:/actio-c2b0-smoke')/uuid.uuid4().hex[:12];root.mkdir(parents=True)
    secret='ACTIO_FAKE_'+uuid.uuid4().hex
    with ReadyStub(root,[{'text':'propose:morning','case':a.case},{'text':'accept'}],secret) as service:
        cfg=rehearsal(service.endpoint,root/'authority',uuid.uuid4().hex)
        l=Ledger(root/'budget.sqlite',config=cfg);l.close()
        result=run(root,cfg,root/'budget.sqlite',secret)
    l=Ledger(root/'budget.sqlite',readonly=True)
    try:snapshot=l.snapshot();verify_snapshot(snapshot)
    finally:l.close()
    campaign=export_campaign(root/'budget.sqlite',[root/'bundle'],service.receives,root/'campaign')
    scan=scan_secret(root,secret)
    write_json(root/'result.json',{**result,'budget':snapshot,'receives':service.receives,'campaign':campaign,'credential_scan':scan})
    print(canonical({'root':str(root),'error':result['error'],'verification':result['export']['verification'],
                     'states':[a['state'] for a in snapshot['attempts']],'local_http_requests':len(service.receives),'credential_scan':scan}))
    return 0 if result['error'] is None else 1


if __name__=='__main__':raise SystemExit(main())
