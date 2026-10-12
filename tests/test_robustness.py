import copy
from concurrent.futures import ThreadPoolExecutor
import itertools
import json
from pathlib import Path
import unittest
import uuid
from actio.profiles import robustness_campaign as c
from actio.tasks import robustness as tasks
from actio.interfaces.cli.robustness import verify
from actio.application.robustness import reserve_live
from actio.evidence.campaigns.robustness_measurement import metric_cells
from actio.measurement.robustness_definitions import metric_definitions
from actio.evidence.campaigns.robustness_measurement import coverage
from actio.contracts.json import ContractError
from actio.contracts.json import digest
from actio.adapters.filesystem.common import file_hash
from actio.evidence.bundles.eval_contract import seal
from actio.tasks.registry import validate_task
from actio.tasks.registry import task_result
from actio.tasks.diagnostic import task
from actio.tasks.diagnostic import visible
from actio.tasks.controls import control
from actio.measurement.diagnostic import oracle_row
from actio.measurement.diagnostic import hand_examples
from actio.tasks.finite import get as old_get
from actio.tasks.finite import options
from actio.measurement.oracle import evaluate
from actio.interfaces.store import Store
from actio.interfaces.migration import snapshot_evaluation_copy
from actio.application import evaluation_store as lineage
from actio.evidence.lineage.evaluation_history import lineage as historical
from actio.evidence.lineage.evaluation_history import preserve

SOURCE=Path('D:/actio-c2c2-live-v1/candidates.sqlite')
BINDINGS={s:{'agent':'ACTOR_'+s,'spec_hash':'0'*64} for s in ('A','B')}


def empty(pre=None):
    pre=pre or c.preregistration()
    return seal({'schema':c.EVIDENCE,'preregistration':pre,'freeze':None,'phase_state':'local_validation',
                 'entries':[{'unit':u,'evidence':None,'reason':'offline nonexecution','episode_ms':None} for u in pre['body']['units']]})


class RobustnessPure(unittest.TestCase):
    def test_01_schedule_mapping_and_closed_old_domains(self):
        pre=c.preregistration();p=pre['body'];units=p['units']
        self.assertEqual((len(units),len(p['seat_slots']),len({u['pair_hash'] for u in units})),(64,128,32))
        self.assertEqual(len({digest(visible(card,'A')) for card in tasks.cards()}),16)
        for family in ('scheduling','bargaining'):
            first=[u for u in units if u['family']==family and u['order']%2==0]
            self.assertEqual([sum(u['arm']==arm for u in first) for arm in ('baseline','candidate')],[8,8])
        self.assertTrue(all(units[i]['family']!=units[i+2]['family'] for i in range(0,60,2)))
        for card in tasks.cards():
            for version in (c.baseline(),c.candidate()):
                t=tasks.card(card['id'],BINDINGS,c.REHEARSAL,version['artifact'])
                self.assertEqual(validate_task(t),t['body'])
                pure=task(card)
                for field in ('public','action_specs','relationships','order'):self.assertEqual(t['body'][field],pure[field])
                for s in ('A','B'):self.assertEqual(t['body']['seats'][s]['private'],pure['seats'][s]['private'])
            with self.assertRaises(ContractError):old_get(card['id'])
        for mutation in (lambda p:p['units'].pop(),lambda p:p['units'][0].update(arm='candidate' if p['units'][0]['arm']=='baseline' else 'baseline'),
                         lambda p:p['units'][0].update(world='other'),lambda p:p.update(schema='unknown'),lambda p:p['seat_slots'].pop()):
            bad=copy.deepcopy(p);mutation(bad)
            with self.assertRaises(ContractError):c.validate_preregistration(seal(bad))
        self.evidence={'episodes':64,'seat_slots':128,'candidate_pairs':32,'A_views':16,'closed_old_domains':True}

    def test_02_exhaustive_independent_mapping_truth(self):
        legal=invalid=0
        for card in tasks.cards():
            full=tasks.card(card['id'],BINDINGS,c.REHEARSAL,c.baseline()['artifact'])['body']
            for a,b in itertools.product(options(card,'A'),options(card,'B')):
                row=oracle_row(card,a,b);legal+=1
                self.assertTrue(row['production_agrees'] and row['visible_reference_agrees'])
                self.assertEqual(task_result(full,[a,b]),row['production'])
            for a,b in [('INVALID','accept'),(options(card,'A')[0],'INVALID'),(None,None),(options(card,'A')[0],None)]:
                row=oracle_row(card,a,b);invalid+=1
                self.assertTrue(row['production_agrees'] and row['visible_reference_agrees'])
                self.assertEqual(task_result(full,[] if a is None else [a] if b is None else [a,b]),row['production'])
        self.assertEqual((legal,invalid),(416,128))
        examples=hand_examples(tasks.cards())
        self.assertTrue(all(x['matches'] for x in examples))
        self.evidence={'legal':legal,'invalid_missing':invalid,'hand_examples':examples}

    def test_03_metrics_missing_applicability_and_pair_denominators(self):
        r=verify(empty());self.assertTrue(r['valid'],r)
        report=r['report'];self.assertEqual(report['counts']['not_run'],128)
        for kind in ('hidden_world','presentation'):self.assertEqual(report['comparisons'][kind]['execution_coverage']['missing'],32)
        self.assertEqual(report['pair_coverage']['missing'],32)
        for name,den in report['metrics'].items():
            self.assertEqual(den['assigned'],den['eligible']+den['not_applicable'])
            self.assertEqual(den['eligible'],den['defined']+den['missing'])
            if metric_definitions()['metrics'][name]['type']=='boolean':self.assertEqual(den['defined'],den['true']+den['false'])
            else:self.assertNotIn('true',den)
        card=tasks.get('S-hidden-w0-normal')
        _,cells=metric_cells(card,{'A':'INVALID'},{'A':'observed','B':'not_run'})
        self.assertFalse(cells['format_A']['value']);self.assertEqual(cells['format_B']['state'],'not_applicable')
        _,cells=metric_cells(card,{'A':'propose:morning','B':'decline'},{'A':None,'B':None})
        self.assertFalse(cells['b_response_rule']['value']);self.assertTrue(cells['self_hard_B']['value'])
        self.evidence={'empty_report_hash':digest(report),'metric_count':len(report['metrics']),'decision':report['candidate_decision']}

    def test_04_consistent_copy_historical_dispatch_claims_and_decision(self):
        root=Path('D:/actio-c2c4-tests')/uuid.uuid4().hex[:12];root.mkdir(parents=True)
        self.evidence={'root':str(root),'external_provider_requests':0}
        before=file_hash(SOURCE);record=snapshot_evaluation_copy(SOURCE,root/'candidates.sqlite')
        s=Store(root/'candidates.sqlite');pre=c.preregistration();body=lineage.plan(pre,'local_fixture')
        try:
            self.assertEqual(s.evaluation_lineage(),historical())
            eid=s.evaluation(body);unchanged=s.evaluation_lineage()
            bad=copy.deepcopy(body);bad['candidate']='0'*64
            with self.assertRaises(ContractError):s.evaluation(bad)
            self.assertEqual(s.evaluation_lineage(),unchanged)
        finally:s.close()
        def claim(index):
            db=Store(root/'candidates.sqlite')
            try:
                db.claim_evaluation(eid,{'root':str(root/index),'namespace':body['claim_namespace']});return True
            except ContractError:return False
            finally:db.close()
        with ThreadPoolExecutor(2) as pool:winners=list(pool.map(claim,['one','two']))
        self.assertEqual(sum(winners),1)
        campaign=empty(pre);report=verify(campaign)['report'];s=Store(root/'candidates.sqlite')
        try:
            decision=s.decide_evaluation(eid,campaign,report);export=s.evaluation_lineage();preserve(export)
            self.assertEqual((lineage.verify(export)['evaluations'],lineage.verify(export)['evaluation_decisions']),(3,2))
            with self.assertRaises(ContractError):s.decide_evaluation(eid,campaign,report)
        finally:s.close()
        self.assertEqual(file_hash(SOURCE),before)
        self.evidence.update(snapshot=record,winners=winners,decision=decision['state'],historical_preserved=True)

    def test_05_once_claim_concurrent_roots_and_unknown_plan(self):
        root=Path('D:/actio-c2c4-tests')/uuid.uuid4().hex[:12];(root/'.local').mkdir(parents=True)
        def reserve(i):
            try:reserve_live(root,root/str(i),'evaluation',{});return True
            except FileExistsError:return False
        with ThreadPoolExecutor(2) as pool:winners=list(pool.map(reserve,range(2)))
        self.assertEqual(sum(winners),1);self.assertFalse(reserve(3))
        old=historical();body=next(json.loads(r['body']) for r in old['body']['tables']['evaluation'] if '"plan"' in r['body'])
        self.assertEqual(lineage.plan(body['plan'],body['evidence_kind']),body)
        bad=copy.deepcopy(body['plan']['body']);bad['implementation']['unknown']='0'*64
        with self.assertRaises(ContractError):lineage.plan(seal(bad),body['evidence_kind'])
        self.evidence={'root':str(root),'winners':winners,'source_changed_old_plan_rejected':True,'old_plan_exact':True,'sent':0}
