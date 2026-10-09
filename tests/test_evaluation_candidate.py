import copy
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch
from actio import evaluation_campaign as c
from actio import evaluation_store as es
from actio.candidate_contract import baseline,candidate
from actio.common import ContractError,digest,file_hash,write_json
from actio.database import migrate_evaluation_copy
from actio.eval_contract import seal
from actio.evaluation_measurement import metric_cells,decision_state
from actio.candidate_evaluation import verify
from actio.store import Store
from actio.suite_tasks import get

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('D:/actio-c2c1-main-v1/candidates.sqlite')


def empty(pre):
    return seal({'schema':c.EVIDENCE,'preregistration':pre,'freeze':None,'phase_state':'local_validation',
        'entries':[{'unit':u,'evidence':None,'reason':'local subset','episode_ms':None} for u in pre['body']['units']]})


class EvaluationPure(unittest.TestCase):
    def test_public_offline_commands_under_guard(self):
        from test_suite import GUARD
        records=[]
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'empty.json';write_json(path,empty(c.preregistration()))
            for args in (['plan'],['preflight'],['verify',str(path)]):
                code=GUARD+"\nfrom actio.candidate_evaluation import main\nsys.argv=['actio-candidate-evaluation',*sys.argv[1:]]\nraise SystemExit(main())"
                argv=[sys.executable,'-X','utf8','-I','-B','-c',code,*args]
                proc=subprocess.run(argv,capture_output=True,text=True,encoding='utf8',timeout=60)
                self.assertEqual(proc.returncode,0,proc.stderr)
                value=json.loads(proc.stdout);self.assertEqual(value['credential_reads'],0);self.assertEqual(value['network_requests'],0)
                records.append({'command':args[0],'argv':argv,'exit_code':0,'stdout_hash':digest(proc.stdout)})
        self.evidence={'guard':'no key/env/network/process/runtime import/write','commands':records}

    def test_versions_identities_denominators_policy(self):
        published=json.loads((ROOT/'docs/validation/phase1c2c1/proposals.json').read_bytes())
        self.assertEqual(published['baseline'],baseline());self.assertEqual(published['candidate'],candidate())
        self.assertEqual(digest(baseline()),'84e9ab99465ada9c47cc17334c305a5f493524f042a218d4be4732c054462fe5')
        self.assertEqual(digest(candidate()),'e381eb3dd58494dde035b7c301331bdc3f5cde8af18c644bf6e7301087a130b2')
        for family in ('scheduling','bargaining'):
            first=[u['arm'] for u in c.preregistration()['body']['units'] if u['family']==family and u['order']%2==0]
            self.assertEqual(first.count('baseline'),3)
        from actio import candidate_campaign as old
        with self.assertRaises(ContractError):old.validate(old.config('ep-00',endpoint=c.ENDPOINT))
        c.validate(c.config('ep-00'))
        with self.assertRaises(ContractError):c.validate(c.config('ep-00',endpoint='https://example.com/v1'))
        reasons={'A':'unobserved','B':'task_predecessor_invalid'}
        m,cs=metric_cells(get('S1'),{'A':'INVALID','B':None},reasons)
        self.assertIs(cs['format_A']['value'],False);self.assertEqual(cs['format_B']['state'],'not_applicable')
        self.assertEqual(cs['joint']['state'],'not_applicable');self.assertIsNone(cs['utility_A']['value'])
        m,cs=metric_cells(get('S1'),{'A':'propose:morning','B':'decline'},reasons)
        self.assertTrue(m['local_hard']['B']);self.assertTrue(m['b_local']);self.assertEqual(m['utilities'],{'A':0,'B':0})
        m,_=metric_cells(get('S2'),{'A':'propose:morning','B':'decline'},reasons)
        self.assertFalse(m['local_hard']['B'])
        cases=[(False,False,[], 'reject'),(True,False,[1],'infrastructure_failure'),(True,True,[1],'reject'),(True,True,[],'insufficient_evidence')]
        for static,technical,v,expected in cases:self.assertEqual(decision_state(static,technical,v),expected)
        r=verify(empty(c.preregistration()));self.assertTrue(r['valid'],r);self.assertEqual(r['report']['counts']['not_run'],48)
        self.evidence={'identities_unchanged':True,'balanced_arm_order':True,'old_v8_provider_rejected':True,'empty_counts':r['report']['counts'],'no_capability_pass':True}

    def test_copy_history_atomic_claim_decision_reopen_corruption(self):
        root=Path('D:/actio-c2c2-tests')/uuid.uuid4().hex[:12];root.mkdir(parents=True)
        self.evidence={'root':str(root)};before=file_hash(SOURCE)
        src=Store(SOURCE,readonly=True)
        try:old=src.candidate_lineage()
        finally:src.close()
        migration=migrate_evaluation_copy(SOURCE,root/'copy.sqlite');self.assertEqual(file_hash(SOURCE),before)
        s=Store(root/'copy.sqlite');initial=s.evaluation_lineage();pre=c.preregistration();body=es.plan(pre,'local_fixture')
        def deny(table):return lambda action,arg1,arg2,db,trigger:sqlite3.SQLITE_DENY if action==sqlite3.SQLITE_INSERT and arg1==table else sqlite3.SQLITE_OK
        for table in ('evaluation','evaluation_binding','evaluation_event'):
            s.db.set_authorizer(deny(table))
            with self.assertRaises(sqlite3.DatabaseError):s.evaluation(body)
            s.db.set_authorizer(None);self.assertEqual(s.evaluation_lineage(),initial)
        eid=s.evaluation(body);registered=s.evaluation_lineage();self.assertEqual(s.evaluation(body),eid);self.assertEqual(registered,s.evaluation_lineage())
        self.assertEqual(s.candidate(candidate()),body['candidate']);self.assertEqual(s.candidate_lineage(),old)
        with self.assertRaises(ContractError):s.bind_candidate(body['candidate'],{})
        s.claim_evaluation(eid,{'root':str(root),'namespace':body['claim_namespace']})
        with self.assertRaises(ContractError):s.claim_evaluation(eid,{'root':str(root),'namespace':body['claim_namespace']})
        campaign=empty(pre);report=verify(campaign)['report'];claimed=s.evaluation_lineage()
        for table in ('evaluation_decision','evaluation_event'):
            s.db.set_authorizer(deny(table))
            with self.assertRaises(sqlite3.DatabaseError):s.decide_evaluation(eid,campaign,report)
            s.db.set_authorizer(None);self.assertEqual(s.evaluation_lineage(),claimed)
        s.decide_evaluation(eid,campaign,report);saved=s.evaluation_lineage();self.assertEqual(saved['body']['legacy'],old)
        self.assertEqual(len(saved['body']['tables']['evaluation']),2);s.close()
        s=Store(root/'copy.sqlite',readonly=True);self.assertEqual(s.evaluation_lineage(),saved);s.close()
        delivery=seal({'schema':'candidate-delivery.v2','campaign':campaign,'lineage':saved});self.assertTrue(verify(delivery)['valid'])
        bad=copy.deepcopy(delivery['body']);bad['lineage']['body']['tables']['evaluation_decision'][0]['candidate']=digest(baseline());bad['lineage']=seal(bad['lineage']['body'])
        self.assertFalse(verify(seal(bad))['valid'])
        db=sqlite3.connect(root/'bad.sqlite');db.execute('PRAGMA user_version=4');db.close()
        with self.assertRaises(ContractError):Store(root/'bad.sqlite')
        self.assertEqual(file_hash(SOURCE),before)
        write_json(root/'delivery.json',delivery)
        self.evidence.update(migration=migration,source_unchanged=True,old_decisions_unchanged=True,reopen_equal=True,transaction_rollbacks=5,duplicate_claim_rejected=True)
