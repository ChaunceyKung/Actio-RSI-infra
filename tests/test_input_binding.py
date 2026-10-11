import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from actio.common import canonical
from actio.common import digest
from actio.common import ContractError
from actio.evidence.terminal import terminal_body
from actio.evidence.verify import verify_bundle
from actio.evidence.verify import sha
from actio.evidence.verify import VERIFIER

SAMPLES=Path(__file__).resolve().parents[1]/'docs/validation/phase1b1/samples'


def mutate_bundle(target, edit, key='social'):
    shutil.copytree(SAMPLES/key,target)
    data=json.loads((target/'evidence.json').read_bytes())
    original=copy.deepcopy(data['occurrences'])
    edit(data)
    assert data['occurrences']==original, 'counterexample must preserve native raw'
    raw=canonical(data).encode(); (target/'evidence.json').write_bytes(raw)
    m=json.loads((target/'manifest.json').read_bytes())
    m['files']=[e for e in m['files'] if e['path']!='verification.json']
    for e in m['files']:
        if e['path']=='evidence.json': e.update(bytes=len(raw),sha256=sha(raw))
    (target/'verification.json').unlink()
    (target/'manifest.json').write_text(canonical(m),encoding='utf8')
    return data


def frozen_edit(data, change):
    m=json.loads(data['run']['input']); change(m)
    data['run']['input']=canonical(m); data['run']['input_hash']=digest(m)
    body=json.loads(data['terminal']['body']); body['manifest_hash']=digest(m)
    data['terminal']['body']=canonical(body)


class InputBinding(unittest.TestCase):
    def test_original_five_and_historical_reports(self):
        expected={'assistant':('complete','success'),'social':('complete','success'),
                  'rejected':('complete','task_failure'),'partial':('partial','infrastructure_failure'),
                  'unknown':('partial','infrastructure_failure')}
        results={}
        for name,axes in expected.items():
            v=verify_bundle(SAMPLES/name);results[name]=v
            self.assertEqual(v['bundle_integrity'],'valid',v)
            self.assertEqual((v['scenario_completeness'],v['task_outcome']),axes,v)
            self.assertEqual(v['verifier'],VERIFIER)
        self.evidence={'fresh_conclusions':results}

    def test_rehashed_frozen_contradictions_shared_with_seal(self):
        edits={
            'review_observation_A':lambda m:m['observations'].update(A='CHANGED'),
            'review_call_to_action':lambda m:m['action_spec'].update(call_to_action='CHANGED'),
            'missing_observations':lambda m:m.pop('observations'),
            'missing_options':lambda m:m['action_spec'].pop('options'),
            'missing_memory':lambda m:m.pop('memory'),
            'options':lambda m:m['action_spec'].update(options=['wait','cooperate']),
            'type':lambda m:m['action_spec'].update(output_type='free'),
            'tag':lambda m:m['action_spec'].update(tag='privileged'),
            'role':lambda m:m['entities'].update(A='B',B='A'),
            'observation_other':lambda m:m['observations'].update(A=m['observations']['B']),
            'observation_gm':lambda m:m['observations'].update(A=m['gm_private']),
            'policy':lambda m:m.update(observation_policy='all'),
        }
        results={}
        with tempfile.TemporaryDirectory() as tmp:
            for name,change in edits.items():
                p=Path(tmp)/name;d=mutate_bundle(p,lambda d:frozen_edit(d,change))
                v=verify_bundle(p);results[name]=v
                self.assertEqual(v['bundle_integrity'],'valid',v)
                self.assertEqual(v['facts_consistency'],'invalid',v)
                with self.assertRaises((ContractError,KeyError)):
                    terminal_body(d['run'],d['streams'],d['operations'],d['domain_receipts'],d['world'],d['audit'],'success')
        self.evidence={'counterexamples':results,'native_raw':'unchanged in every case','stored_report':'omitted to test semantics'}

    def test_real_inventory_corruption_still_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'bad';shutil.copytree(SAMPLES/'social',p)
            (p/'verification.json').write_bytes(b'{}')
            self.assertEqual(verify_bundle(p)['bundle_integrity'],'invalid')


if __name__=='__main__':unittest.main()
