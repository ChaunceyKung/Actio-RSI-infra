import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from actio.contracts.json import canonical
from actio.contracts.json import digest
from actio.contracts.json import ContractError
from actio.evidence.bundles.eval_contract import seal
from actio.tasks.finite import get
from actio.tasks.finite import card
from actio.tasks.finite import validate
from actio.tasks.finite import cards
from actio.tasks.finite import options
from actio.measurement.oracle import fixture_policy
from actio.tasks.diagnostic import dataset
from actio.tasks.diagnostic import visible
from actio.tasks.diagnostic import validate_dataset
from actio.tasks.controls import a_reference
from actio.tasks.controls import b_reference
from actio.tasks.controls import diagnose_a
from actio.tasks.controls import control
from actio.tasks.controls import aggregate
from actio.tasks.controls import cell
from actio.measurement.diagnostic import synthetic_analysis
from actio.measurement.diagnostic import metric_cells
from actio.measurement.diagnostic import legacy_control
from actio.evidence.diagnostics import task_diagnostics as cli
from actio.application.task_diagnostics import analyze

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'docs/validation/phase1c2c2'
DOC = ROOT / 'docs/validation/phase1c2c3'


class TaskDiagnostics(unittest.TestCase):
    def test_visible_reference_ties_gap_and_absence(self):
        c = get('H5'); view = visible(c, 'A')
        ref = a_reference(view)
        self.assertEqual(ref['conditional_argmax_set'], ['apple for 1 coins', 'banana for 1 coins'])
        self.assertEqual(diagnose_a(view, 'apple for 2 coins')['conditional_offer_gap']['value'], 1)
        self.assertTrue(diagnose_a(view, 'apple for 2 coins')['own_hard']['value'])
        self.assertEqual(diagnose_a(view, 'INVALID')['conditional_offer_gap'], cell(reason='syntax_invalid', applicable=False))
        self.assertEqual(diagnose_a(view, None)['conditional_offer_gap']['state'], 'missing')
        self.assertEqual(diagnose_a(view, 'apple for 1 coins', trusted=False, missing_reason='technical_unknown')['conditional_offer_gap'], cell(reason='technical_unknown'))
        self.assertEqual(diagnose_a(view, 'apple for 5 coins')['conditional_offer_gap']['reason'], 'own_hard_violation')
        empty = copy.deepcopy(view); empty['public']['allowed'] = []
        self.assertEqual(a_reference(empty)['own_legal_set'], [])
        self.assertEqual(diagnose_a(empty, None)['conditional_offer_gap']['reason'], 'empty_own_legal_set')
        self.assertIsNone(control(empty, 'conditional_argmax_first'))
        bv = visible(c, 'B')
        self.assertEqual(b_reference(bv)['state'], 'missing')
        self.assertEqual(b_reference(visible(c, 'B', ['bad']))['reason'], 'predecessor_invalid')
        self.assertEqual(b_reference(visible(get('H4'), 'B', ['apple for 3 coins']))['actions'], ['accept'])
        self.assertEqual(b_reference(visible(get('S1'), 'B', ['propose:morning']))['actions'], ['decline'])

    def test_policy_only_visible_strict_fields_and_no_oracle(self):
        for c in dataset()['body']['cards']:
            for seat, acts in [('A', []), ('B', [options(c, 'A')[0]])]:
                view = visible(c, seat, acts)
                with (patch('actio.measurement.oracle.evaluate', side_effect=AssertionError('oracle unavailable')),
                      patch('actio.tasks.finite.result', side_effect=AssertionError('production unavailable'))):
                    self.assertIsNotNone(control(view, 'conditional_argmax_first'))
                for key in ('opponent_private', 'oracle', 'group', 'arm', 'candidate', 'card_hash'):
                    bad = copy.deepcopy(view); bad[key] = 'hidden'
                    with self.assertRaises(ContractError):
                        control(bad, 'conditional_argmax_first')
                bad = copy.deepcopy(view); bad['own']['opponent'] = {'hidden': True}
                with self.assertRaises(ContractError):
                    control(bad, 'conditional_argmax_first')

    def test_frozen_dataset_exhaustive_and_counterfactuals(self):
        data = dataset(); frozen = json.loads((DOC / 'frozen-design/dataset.json').read_bytes())
        self.assertEqual(data, frozen)
        self.assertEqual(cli.policies(), json.loads((DOC / 'frozen-design/policies.json').read_bytes())['body'])
        self.assertEqual(cli.metric_definitions(), json.loads((DOC / 'frozen-design/metrics.json').read_bytes())['body'])
        r = synthetic_analysis(data)
        self.assertEqual(r['counts'], {'groups': 8, 'worlds': 16, 'presentations': 32, 'legal_action_combinations': 416,
                         'invalid_missing_vectors': 128, 'policy_controls': 160, 'historical_live_pairs': 0, 'independent_research_units': 0})
        self.assertEqual(set(r['gates'].values()), {'PASS'})
        self.assertTrue(any(not row['oracle']['joint_feasible'] for row in r['truth_table']))
        self.assertTrue(any(row['oracle']['joint_achieved'] and row['oracle']['utilities'] == {'A': 0, 'B': 0} for row in r['truth_table']))
        for family in ('scheduling', 'bargaining'):
            self.assertTrue(any(g['family'] == family and g['nonempty_disjoint_witness'] for g in r['projections']['groups']))
        self.evidence = {'counts': r['counts'], 'gates': r['gates']}

    def test_independent_paths_and_explicit_denominators(self):
        from actio.measurement.oracle import evaluate
        from actio.tasks.finite import result
        from actio.tasks.diagnostic import task
        c = dataset()['body']['cards'][0]
        with patch('actio.tasks.finite.result', side_effect=AssertionError('forbidden')):
            self.assertFalse(evaluate(c, {'A': 'propose:morning', 'B': 'accept'})['a_own'])
        with patch('actio.measurement.oracle.evaluate', side_effect=AssertionError('forbidden')):
            self.assertFalse(result(task(c), ['propose:morning', 'accept'])['hard']['A'])
        rows = [metric_cells(c, acts) for acts in ({}, {'A': 'INVALID'}, {'A': 'propose:afternoon'},
                {'A': 'propose:afternoon', 'B': 'INVALID'}, {'A': 'propose:afternoon', 'B': 'decline'})]
        for name in rows[0]:
            boolean = cli.metric_definitions()['metrics'][name]['type'] == 'boolean'
            counts = aggregate([r[name] for r in rows], 'test_vector', boolean=boolean)
            self.assertEqual(counts['assigned'], counts['eligible'] + counts['not_applicable'])
            self.assertEqual(counts['eligible'], counts['defined'] + counts['missing'])
            if boolean:
                self.assertEqual(counts['defined'], counts['true'] + counts['false'])
            else:
                self.assertNotIn('true', counts)
        self.assertEqual(rows[1]['format_A']['value'], False)
        self.assertEqual(rows[1]['format_B']['reason'], 'task_predecessor_invalid')
        self.assertEqual(rows[3]['utility_A']['state'], 'not_applicable')
        self.assertIsNone(rows[3]['utility_A']['value'])
        self.assertFalse(rows[4]['b_response_rule']['value'])

    def test_historical_sidecar_and_old_contract_preserved(self):
        h = cli.load_history(OLD)
        r = cli.retrospective({**h, 'source_assurance': 'public_projection_only'})
        self.assertTrue(r['original_metrics_equal'])
        self.assertEqual(r['summary'], {'historical_live_pairs': 12, 'identical_A_B_actions': 12,
            'A_in_conditional_argmax': 12, 'matches_legacy_own_rule': 11, 'joint_feasible_cards': 10, 'joint_achieved_cards': 5,
            'feasible_but_not_agreed': ['S1', 'S3', 'H1', 'H3', 'H4'],
            'positive_omniscient_regret': ['S1', 'S3', 'S6', 'H1', 'H3']})
        self.assertEqual(r['original_decision']['state'], 'insufficient_evidence')
        self.assertFalse(r['original_decision']['eligible_for_activation'])
        for c in cards():
            old = fixture_policy(c, 'own_rule')
            a = legacy_control(visible(c, 'A'))
            self.assertEqual(old, {'A': a, 'B': b_reference(visible(c, 'B', [a]))['actions'][0]})
        with self.assertRaises(ContractError):
            get(dataset()['body']['cards'][0]['id'])
        bindings = {s: {'agent': 'ACTOR_' + s, 'spec_hash': '0' * 64} for s in ('A', 'B')}
        for c in cards():
            self.assertEqual(validate(card(c['id'], bindings, 'tokenkey_suite_rehearsal'))['parameters'], c)
        self.evidence = r['summary']

    def test_new_directory_portability_and_raw_scope(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); first = base / 'first'; moved = base / 'moved'
            before = {n: (OLD / n).read_bytes() for n in cli.trust()['historical_files']}
            analyze(OLD, first, receipt=DOC / 'historical-source.json')
            self.assertTrue(cli.verify(first)['valid'])
            self.assertFalse(cli.verify(first)['raw_authentication_repeated'])
            with self.assertRaises(ContractError):
                analyze(OLD, first)
            shutil.copytree(first, moved); shutil.rmtree(first)
            with patch('actio.evidence.diagnostics.task_diagnostics.load_history', side_effect=AssertionError('original source unavailable')):
                self.assertTrue(cli.verify(moved)['valid'])
            for path in moved.iterdir():
                text = path.read_text(encoding='utf8')
                self.assertNotIn('D:\\\\', text)
                self.assertNotIn('reasoning_content', text)
            self.assertEqual(before, {n: (OLD / n).read_bytes() for n in before})
            public = base / 'public'; analyze(OLD, public)
            self.assertEqual(cli.verify(public)['gates']['historical_source_assurance'], 'PARTIAL_PUBLIC_PROJECTION_ONLY')

    def test_resealed_bad_packages_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); original = base / 'original'; analyze(OLD, original)
            mutations = {
                'unknown_schema': ('dataset.json', lambda v: v.update(schema='unrecognized')),
                'missing_world': ('dataset.json', lambda v: v['cards'].__delitem__(slice(0, 2))),
                'duplicate_identity': ('dataset.json', lambda v: v['cards'].__setitem__(1, v['cards'][0])),
                'wrong_binding': ('historical-actions.json', lambda v: v['rows'][0]['binding'].update(card_hash='0' * 64)),
                'edited_action': ('historical-actions.json', lambda v: v['rows'][0]['actions'].update(A='INVALID')),
                'source_break': ('historical-actions.json', lambda v: v['source'].update(reader_commit='0' * 40)),
                'forged_authentication': ('source-assurance.json', lambda v: v.update(raw_verified_here=True)),
                'edited_metric': ('synthetic-report.json', lambda v: v['truth_table'][0]['oracle'].update(joint_achieved=True)),
            }
            for name, (file, mutate) in mutations.items():
                folder = base / name; shutil.copytree(original, folder)
                value = json.loads((folder / file).read_bytes())['body']; mutate(value)
                (folder / file).write_text(canonical(seal(value)), encoding='utf8')
                values = {n: json.loads((folder / n).read_bytes()) for n in cli.PACKAGE_FILES}
                # Even self-consistent rehashing of all references cannot grant source trust.
                (folder / 'manifest.json').write_text(canonical(cli.manifest(values)), encoding='utf8')
                self.assertFalse(cli.verify(folder)['valid'], name)
            folder = base / 'path'; shutil.copytree(original, folder)
            value = json.loads((folder / 'manifest.json').read_bytes())['body']
            value['files']['../outside.py'] = {'body_sha256': '0' * 64, 'file_sha256': '0' * 64}
            (folder / 'manifest.json').write_text(canonical(seal(value)), encoding='utf8')
            self.assertFalse(cli.verify(folder)['valid'])
            (folder / 'extra.py').write_text('raise RuntimeError("must not execute")', encoding='utf8')
            self.assertFalse(cli.verify(folder)['valid'])


if __name__ == '__main__':
    unittest.main()
