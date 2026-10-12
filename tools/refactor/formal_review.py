"""Independently read closed final C5 databases and recompute, without new sends."""
import argparse
import json
from pathlib import Path
from actio.adapters.filesystem.common import file_hash
from actio.adapters.persistence.ledger import Ledger
from actio.application.diagnostic_runtime import review_entry
from actio.contracts.json import digest
from actio.evidence.diagnostics.failure_fixtures import CASES
from actio.evidence.diagnostics.transport_diagnostics import sources
from actio.adapters.runtime.cleanup import cleanup

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--wheel',type=Path,required=True);p.add_argument('--freeze',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 frozen=json.loads(a.freeze.read_bytes());assert frozen['sources']==sources() and frozen['wheel_sha256']==file_hash(a.wheel)
 report=json.loads((a.root/'report.json').read_bytes());assert report['status']=='PASS' and report['sources']==sources()
 rows=[];totals=dict(sent=0,settled=0,unknown=0,not_run=0,received=0,active=0)
 for case in CASES:
  path=a.root/case['id']/'entry.json';entry=json.loads(path.read_bytes())['body']['entry'];db=path.parent/'episode/budget.sqlite'
  before={str(p):file_hash(p) for p in [path,db]};ledger=Ledger(db,readonly=True)
  try:snapshot=ledger.snapshot()
  finally:ledger.close()
  assert snapshot==entry['evidence']['ledger']
  attempts=snapshot['attempts'];receives=entry['evidence']['receives']
  for attempt in attempts:
   matching=[r for r in receives if r['attempt']==attempt['id']];assert len(matching)==1
   assert matching[0]['response']['raw']==attempt['response']['raw'] and matching[0]['response']['status']==attempt['response']['status']
  counts={'sent':sum(e['kind']=='sending' for e in snapshot['events']),'settled':sum(t['state']=='settled' for t in attempts),
          'unknown':sum(t['state']=='unknown' for t in attempts),'not_run':2-len(attempts),'received':len(receives),
          'active':sum(t['state'] in ('authorized','reserved','sending') for t in attempts)}
  recomputed=review_entry(entry,case);assert recomputed['status']=='PASS'
  assert all(counts[k]==recomputed['observed'][k] for k in counts)
  for k in totals:totals[k]+=counts[k]
  assert all(file_hash(Path(p))==h for p,h in before.items())
  rows.append({'case':case['id'],'entry_hash':digest(entry),'file_hashes':before,'counts':counts,'checks':recomputed['checks'],'database_unchanged':True})
 assert totals=={'sent':12,'settled':5,'unknown':7,'not_run':6,'received':12,'active':0},totals
 assert all(report['totals'][k]==v for k,v in totals.items())
 stop=json.loads((a.root/'suite-stop.json').read_bytes());clean=cleanup(stop['workers'],stop['endpoints']);assert clean['status']=='PASS'
 scan=json.loads((a.root/'scan.json').read_bytes());assert scan['status']=='PASS' and not scan['credential_found']
 result={'status':'PASS','wheel_sha256':file_hash(a.wheel),'freeze_sha256':file_hash(a.freeze),'report_sha256':file_hash(a.root/'report.json'),
         'totals':totals,'rows':rows,'cleanup':clean,'scan':scan,'source_identity':sources(),
         'additional_loopback_sends':0,'external_requests':0,'credential_reads':0,
         'scope':'separate process: closed Ledger equals sealed entry; raw receive bindings, independent arithmetic and diagnostic recomputation; no runtime replay'}
 a.output.write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps({'status':'PASS','totals':totals,'workers':len(clean['jobs']),'ports':len(clean['ports'])}))
if __name__=='__main__':main()
