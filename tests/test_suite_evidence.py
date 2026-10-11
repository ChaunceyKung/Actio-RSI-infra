"""Counterexamples use actual matrix copies; never mutate stored samples."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from actio.common import canonical
from actio.evidence.bundles.eval_contract import seal
from actio.evidence.campaigns.suite_measurement import verify
from actio.evidence.audit.stream_audit import verdict

class SuiteEvidence(unittest.TestCase):
    def test_rehashed_raw_contradiction_and_partial_plan(self):
        path=Path(sys.argv[3]);value=json.loads(path.read_bytes());self.assertTrue(verify(value)['valid'])
        for mutation in ('raw','remove','duplicate','route','drop-partial'):
            b=copy.deepcopy(value['body'])
            if mutation=='remove':b['entries'].pop()
            elif mutation=='duplicate':b['entries'][-1]=b['entries'][0]
            elif mutation=='route':b['entries'][0]['unit']['model']='other'
            elif mutation=='drop-partial':b['entries'][0]['evidence']['ledger']['attempts'].pop()
            else:
                e=next(x for x in b['entries'] if x['evidence']);ledger=e['evidence']['ledger'];a=next(x for x in ledger['attempts'] if x['scope']['seat']=='A')
                lines=a['response']['raw'].splitlines(keepends=True);changed=False
                for i,line in enumerate(lines):
                    if not line.startswith('data: {'):continue
                    row=json.loads(line[6:])
                    if row.get('choices') and row['choices'][0].get('delta',{}).get('content'):
                        row['choices'][0]['delta']['content']='WRONG';lines[i]='data: '+json.dumps(row)+'\n';changed=True;break
                self.assertTrue(changed);a['response']['raw']=''.join(lines);a['response']['raw_base64']=base64.b64encode(a['response']['raw'].encode()).decode();a['text_integrity']=verdict(a['response'])
                for event in ledger['events']:
                    if event['attempt']==a['id'] and event['kind']=='settled':event['body'].update(response=a['response'],text_integrity=a['text_integrity'])
                source=next(iter(e['evidence']['dataset']['body']['sources'].values()));data=json.loads(source['files']['evidence.json'])
                for row in data['audit']:
                    if row['kind']=='transport_attempt' and row['op']==a['id']:row['body']=canonical(a)
                source['files']['evidence.json']=canonical(data);source['files'].pop('verification.json')
                manifest=json.loads(source['files']['manifest.json']);manifest['files']=[f for f in manifest['files'] if f['path']!='verification.json']
                for f in manifest['files']:
                    if f['path']=='evidence.json':f.update(bytes=len(source['files']['evidence.json'].encode()),sha256=hashlib.sha256(source['files']['evidence.json'].encode()).hexdigest())
                source['files']['manifest.json']=canonical(manifest);e['evidence']['dataset']=seal(e['evidence']['dataset']['body'])
                for rec in e['evidence']['receives']:
                    if rec['attempt']==a['id']:rec['response'].update(raw=a['response']['raw'],sha256=hashlib.sha256(a['response']['raw'].encode()).hexdigest())
            r=verify(seal(b));self.assertFalse(r['valid'],mutation)
        self.evidence={'input':str(path),'mutations_rejected':5,'historical_writes':0,'model_calls':0}

if __name__=='__main__':unittest.main()
