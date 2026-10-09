"""Published local matrix entrypoint; same service, pilot, DSH and Concordia.

The literal loopback server and fake credential are created here, never supplied
by a proposal. No real credential resolver is imported or called.
"""
import argparse
import json
from pathlib import Path
import sys
import uuid
from actio import candidate_campaign as contract
from actio.common import canonical, digest
from actio.eval_contract import seal
from actio.pilot import frozen_publication, execute, create
from actio.store import Store
from actio.candidate import binding_plan, decision_for, verify
from actio.candidate_contract import baseline,candidate,rejected_fixtures,decide

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    a=p.parse_args();pre=json.loads((ROOT/'docs/validation/phase1c2c1/preregistration.json').read_bytes())
    freeze=frozen_publication(ROOT,pre,contract)
    root=a.root.resolve();root.mkdir(parents=True,exist_ok=False)
    s=Store(root/'candidates.sqlite',create=True,lineage=True)
    try:
        for proposal in (baseline(),candidate(),*rejected_fixtures()):
            cid=s.candidate(proposal)
            if proposal['source']['kind']=='synthetic_fixture':
                s.decide_candidate(cid,decide(static_valid=False,complete=False,evidence_kind='static_fixture',diagnostics={'fixture':proposal['name']}))
        binding=binding_plan(pre)
        for cid in binding['candidate_hashes']:s.bind_candidate(cid,binding)
        create(root/'lineage-before.json',s.candidate_lineage())
    finally:s.close()
    sys.path.insert(0,str(ROOT/'tests'))
    from gateway_stub import GatewayStub,scan_secret
    secret='ACTIO_FAKE_'+uuid.uuid4().hex
    with GatewayStub(root,contract.fixture_plans(),secret) as service:
        report=execute(root/'matrix',pre,secret,freeze=freeze,endpoint=service.endpoint,
            authority_root=ROOT/'.local/phase1c2c1-claims',operation_authorization=contract.AUTH,receives=service.receives,contract=contract)
    campaign=json.loads((root/'matrix/pilot.json').read_bytes())
    s=Store(root/'candidates.sqlite')
    try:
        for cid in binding['candidate_hashes']:s.decide_candidate(cid,decision_for(campaign,report))
        lineage=s.candidate_lineage();create(root/'lineage.json',lineage)
    finally:s.close()
    s=Store(root/'candidates.sqlite',readonly=True)
    try:assert s.candidate_lineage()==lineage
    finally:s.close()
    delivery=seal({'schema':'candidate-delivery.v1','campaign':campaign,'lineage':lineage})
    result=verify(delivery);assert result['valid'],result
    create(root/'delivery.json',delivery);create(root/'verification.json',result)
    create(root/'secret-scan.json',scan_secret(root,secret))
    print(canonical({'root':str(root),'counts':report['counts'],'decision':report['decision']['state'],
                     'lineage':result['lineage'],'reopen_equal':True,'external_provider_requests':0}))


if __name__=='__main__':main()
