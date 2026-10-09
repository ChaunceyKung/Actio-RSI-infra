"""Public fake-key loopback rehearsal of the genuine pi-ai/Concordia path."""
import json
from pathlib import Path
import sys
import uuid
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from gateway_stub import GatewayStub
from actio.gateway_contract import template,AUTH
from actio.gateway import execute,scan
from actio.common import canonical,write_json

def main():
    root=Path('D:/actio-c2b1-smoke')/uuid.uuid4().hex[:12];root.mkdir(parents=True)
    secret='ACTIO_FAKE_'+uuid.uuid4().hex
    with GatewayStub(root,[{'text':'propose:morning','case':'gateway-cost'},{'text':'accept'}],secret) as service:
        c=template(mode='tokenkey_rehearsal',endpoint=service.endpoint);c['plan']=['compatible']
        c['authority']={'id':uuid.uuid4().hex,'root':str(root/'authority')}
        result=execute(c,root/'run',secret,operation_authorization=AUTH,receives=service.receives)
    result['credential_scan']=scan(root,secret);write_json(root/'result.json',result)
    print(canonical({'root':str(root),'counts':result['campaign']['report']['counts'],'credential_scan':result['credential_scan'],'valid':result['campaign']['valid']}))
    return 0 if all(ep['error'] is None for ep in result['episodes']) else 2

if __name__=='__main__':raise SystemExit(main())
