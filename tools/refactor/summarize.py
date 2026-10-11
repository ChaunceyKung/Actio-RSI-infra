"""Summarize local regression receipts without publishing raw evidence or logs."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    reports=[];roots=set();receives={};errors=[]
    for folder in sorted(a.root.iterdir()):
        receipt=folder/'receipt.json'
        if receipt.is_file():
            v=json.loads(receipt.read_bytes());reports.append({'name':folder.name,'receipt_sha256':hashlib.sha256(receipt.read_bytes()).hexdigest(),'status':v['status'],'rows':v.get('rows',[]),'sources':v.get('sources'), 'scope':v.get('scope')})
        for evidence in folder.glob('*-controlled-evidence.json'):
            for row in json.loads(evidence.read_bytes()):
                value=row['evidence'].get('root')
                if value:roots.add(Path(value).resolve())
    # Each test root is a fresh UUID namespace. Deduplicate files across shared class roots.
    for root in sorted(roots):
        for path in root.rglob('receives.json'):
            if path in receives:continue
            try:
                value=json.loads(path.read_bytes());assert type(value) is list
                receives[path]={'path':str(path),'count':len(value),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            except Exception as e:errors.append({'path':str(path),'type':type(e).__name__})
    formal=json.loads((a.root/'formal09/report.json').read_bytes())
    result={'status':'INCOMPLETE','regressions':reports,'development_loopback_receives':sum(v['count'] for v in receives.values()),
            'development_receive_files':list(receives.values()),'development_count_scope':'unique receives.json under roots recorded by completed tests; in-process MJS fixture emissions are not HTTP sends; no formal matrix included',
            'development_count_errors':errors,'recorded_test_roots':[str(p) for p in sorted(roots)],
            'formal_matrix':{'status':formal['status'],'totals':formal['totals'],'workers':len(formal['cleanup']['jobs']),'services':len(formal['cleanup']['ports'])},
            'external_requests':0,'limitation':'tests lacking a recorded root are outside HTTP census; inspect suite evidence before treating count as exhaustive'}
    a.output.write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps({'development_loopback_receives':result['development_loopback_receives'],'receipts':len(reports),'roots':len(roots),'errors':len(errors)}))
if __name__=='__main__':main()
