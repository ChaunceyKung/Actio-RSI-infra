import base64
import copy
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from actio.common import digest, ContractError, clean_env, file_hash
from actio.eval_contract import seal
from actio import candidate_campaign as campaign
from actio.candidate_contract import baseline, candidate, rejected_fixtures, validate_proposal, decide, POLICY_HASH
from actio.candidate import binding_plan, verify
from actio.candidate_store import verify as verify_lineage
from actio.candidate_measurement import classify
from actio.channel_audit import audit, verdict
from actio.stream_audit import verdict as old_verdict
from actio.store import Store
from actio.database import migrate_lineage_copy
from test_suite import GUARD

ROOT=Path(__file__).resolve().parents[1]


def response(text='accept',reasoning='Check.',*,interleaved=True):
    pieces=[{'role':'assistant','content':None,**({'reasoning_content':None} if reasoning else {})}]
    if reasoning:pieces.extend({'reasoning_content':x} for x in reasoning)
    pieces.extend({'content':x} for x in text)
    rows=[{'id':'fixture','model':'gpt-5.6','object':'chat.completion.chunk','choices':[{'index':0,'delta':d}]} for d in pieces]
    rows.append({'id':'fixture','model':'gpt-5.6','object':'chat.completion.chunk','choices':[{'index':0,'delta':{},'finish_reason':'stop'}],'usage':{'prompt_tokens':1,'completion_tokens':2,'total_tokens':3}})
    raw=''.join('data: '+json.dumps(r,ensure_ascii=False)+'\n\n' for r in rows)+'data: [DONE]\n\n'
    chunks=[];ends=[]
    for idx,typ,value in [(3,'reasoning',reasoning),(8 if reasoning else 0,'text',text)]:
        if not value:continue
        chunks.append({'type':'block-start','index':idx,'blockType':typ})
        chunks.extend({'type':typ+'-delta','index':idx,'text':x} for x in value)
        end={'type':'block-end','index':idx,'block':{'type':typ,'text':value}}
        if interleaved:ends.append(end)
        else:chunks.append(end)
    chunks+=ends+[{'type':'usage','usage':{}},{'type':'finish','reason':{'kind':'stop'}}]
    return {'status':200,'error':None,'raw':raw,'raw_base64':base64.b64encode(raw.encode()).decode(),'chunks_json':json.dumps(chunks),
            'timings':{'headers_ms':2,'first_token_ms':3,'total_ms':4},'deadlines':{'trigger':None}}


class CandidatePure(unittest.TestCase):
    def test_channels_fsm_and_fail_closed(self):
        cases=[]
        for text,reasoning in [('accept',''),('accept','Check.'),('行動','短句')]:
            for overlap in (False,True):
                r=response(text,reasoning,interleaved=overlap)
                native=([{'type':'reasoning','text':reasoning}] if reasoning else [])+[{'type':'text','text':text}]
                v=audit(r,text,require_bytes=True,native_blocks=native)
                self.assertTrue(v['native_reasoning_checked']);self.assertNotIn('reasoning',v);cases.append(v)
        self.assertEqual(old_verdict(response(reasoning=''))['status'],'verified')
        self.assertEqual(old_verdict(response())['status'],'rejected')
        malformed=[]
        for kind in ('no-content','length','raw-mismatch','block-mismatch','unknown-channel','duplicate-key','no-DONE','wrong-identity','type','extra-block','unfinished','bytes'):
            r=response(text='' if kind=='no-content' else 'accept');chunks=json.loads(r['chunks_json'])
            if kind=='length':r['raw']=r['raw'].replace('"stop"','"length"');chunks[-1]['reason']['kind']='max-tokens'
            if kind=='raw-mismatch':r['raw']=r['raw'].replace('"content": "a"','"content": "X"')
            if kind=='block-mismatch':next(c for c in chunks if c['type']=='block-end')['block']['text']='wrong'
            if kind=='unknown-channel':r['raw']=r['raw'].replace('"reasoning_content": null','"audio": null')
            if kind=='duplicate-key':r['raw']=r['raw'].replace('"id": "fixture"','"id":"fixture","id":"fixture"',1)
            if kind=='no-DONE':r['raw']=r['raw'].replace('data: [DONE]\n\n','')
            if kind=='wrong-identity':r['raw']=r['raw'].replace('"id": "fixture"','"id": "other"',1)
            if kind=='type':r['raw']=r['raw'].replace('"content": null','"content": 3',1)
            if kind=='extra-block':chunks.insert(1,{'type':'block-start','index':9,'blockType':'audio'})
            if kind=='unfinished':chunks=[c for c in chunks if c['type']!='block-end']
            r['raw_base64']=base64.b64encode(r['raw'].encode()).decode()
            if kind=='bytes':r['raw_base64']=base64.b64encode(b'other').decode()
            r['chunks_json']=json.dumps(chunks);v=verdict(r);self.assertEqual(v['status'],'rejected',kind);malformed.append({'case':kind,'verdict':v})
        with self.assertRaises(ContractError):audit(response(),'decline')
        with self.assertRaises(ContractError):audit(response(),'accept',native_blocks=[{'type':'text','text':'accept'}])
        self.evidence={'accepted':cases,'rejected':malformed,'native_mismatch_rejected':True,'old_v1_unchanged':True}

    def test_historical_channel_compatibility_and_clock_semantics(self):
        from actio.channel_audit import native_content
        path=ROOT/'docs/validation/phase1c2c0/samples/pilot.json';p=json.loads(path.read_bytes());e=p['body']['entries'][7]
        a=e['evidence']['ledger']['attempts'][0];d=json.loads(next(iter(e['evidence']['dataset']['body']['sources'].values()))['files']['evidence.json']);op=d['operations'][0]
        self.assertEqual(old_verdict(a['response']),a['text_integrity'])
        new=audit(a['response'],op['answer'],require_bytes=True,native_blocks=native_content(d,op['stream']))
        self.assertTrue(new['native_reasoning_checked']);self.assertEqual(len(new['blocks']),2)
        metadata={k:v for k,v in new.items() if k!='text'}
        oldclass=classify({**a,'text_integrity':{'status':'rejected','category':'unsupported_protocol/channel'}},op)
        self.assertEqual(oldclass['clocks']['total_ms']['state'],'observed')
        self.assertEqual(oldclass['finish'],'stop')
        r=response();r.update(error='anything',deadlines={'trigger':'fetch_total'});v=classify({'response':r,'state':'unknown'},op)
        self.assertEqual(v['category'],'timeout');self.assertEqual(v['clocks']['total_ms']['state'],'right-censored')
        self.assertEqual(classify({'response':{'error':'timeout is merely arbitrary text'},'state':'unknown'})['category'],'accounting_unknown')
        self.evidence={'historical_source_hash':file_hash(path),'old_reader':'e2e6691ef9bae5f61bccaaa97528e0478bd9a666',
            'old_verdict':a['text_integrity'],'new_verdict':metadata,'latency':oldclass,'no_reasoning_body_copied':True,
            'old_admitted':14,'old_sent':15,'old_not_run':33,'old_unknown':0,'new_provider_calls':0}

    def test_candidate_policy_and_complete_denominators(self):
        b=baseline();c=candidate();self.assertTrue(validate_proposal(b)['valid']);self.assertTrue(validate_proposal(c,b)['valid'])
        for p in rejected_fixtures():self.assertFalse(validate_proposal(p,b)['valid'])
        for field in ('policy_hash','mutation_seat','actor_slot','diff'):
            p=copy.deepcopy(c);p[field]='wrong';self.assertFalse(validate_proposal(p,b)['valid'])
        fixtures=[]
        for name,valid,complete,kind,gain,diagnostics,expected in [
            ('static',False,False,'static_fixture',None,{},'reject'),('missing',True,False,'local_fixture',None,{},'infrastructure_failure'),
            ('local-positive',True,True,'local_fixture',9,{},'insufficient_evidence'),
            ('positive',True,True,'policy_fixture',1,{},'pass'),('negative',True,True,'policy_fixture',-1,{},'reject'),
            ('missing-gain',True,True,'policy_fixture',None,{},'insufficient_evidence'),('zero-variance',True,True,'policy_fixture',0,{},'insufficient_evidence'),
            ('format',True,True,'policy_fixture',1,{'format_failure':True},'reject'),('hard',True,True,'policy_fixture',1,{'hard_failure':True},'reject'),
            ('protocol',True,False,'policy_fixture',1,{'protocol_failure':True},'infrastructure_failure')]:
            d=decide(static_valid=valid,complete=complete,evidence_kind=kind,diagnostics=diagnostics,synthetic_gain=gain)
            self.assertEqual(d['state'],expected);self.assertFalse(d['eligible_for_activation']);fixtures.append({'name':name,'decision':d})
        pre=campaign.preregistration();value=seal({'schema':campaign.EVIDENCE,'preregistration':pre,'freeze':None,'phase_state':'local_validation',
            'entries':[{'unit':u,'evidence':None,'reason':'not_started','episode_ms':None} for u in pre['body']['units']]})
        r=verify(value);self.assertTrue(r['valid'],r);self.assertEqual(r['report']['counts']['not_run'],48);self.assertEqual(r['report']['pair_coverage']['missing'],12)
        c=campaign.config('ep-00',endpoint='https://api.tokenkey.dev/v1')
        with self.assertRaises(ContractError):campaign.validate(c)
        self.evidence={'policy_fixtures':fixtures,'empty_plan_counts':r['report']['counts'],'pair_coverage':r['report']['pair_coverage'],'provider_origin_rejected':True}

    def test_store_atomicity_persistence_migration_and_corruption(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);s=Store(root/'lineage.sqlite',create=True,lineage=True);b=baseline();c=candidate();bid=s.candidate(b)
            initial=s.candidate_lineage();self.assertEqual(s.candidate(b),bid);self.assertEqual(s.candidate_lineage(),initial)
            failures=[]
            def deny(table):
                return lambda action,arg1,arg2,db,trigger: sqlite3.SQLITE_DENY if action==sqlite3.SQLITE_INSERT and arg1==table else sqlite3.SQLITE_OK
            for table in ('candidate','candidate_event','lineage_edge'):
                s.db.set_authorizer(deny(table))
                with self.assertRaises(sqlite3.DatabaseError):s.candidate(c)
                s.db.set_authorizer(None);self.assertEqual(initial,s.candidate_lineage());failures.append(table)
            cid=s.candidate(c)
            for p in rejected_fixtures():
                rid=s.candidate(p);s.decide_candidate(rid,decide(static_valid=False,complete=False,evidence_kind='static_fixture',diagnostics={'fixture':p['name']}))
            plan=binding_plan(campaign.preregistration());s.bind_candidate(cid,plan)
            with self.assertRaises(ContractError):s.bind_candidate(cid,plan)
            decision=decide(static_valid=True,complete=False,evidence_kind='local_fixture',diagnostics={'reason':'test interruption'})
            before=s.candidate_lineage()
            for table in ('decision','candidate_event'):
                s.db.set_authorizer(deny(table))
                with self.assertRaises(sqlite3.DatabaseError):s.decide_candidate(cid,decision)
                s.db.set_authorizer(None);self.assertEqual(before,s.candidate_lineage());failures.append('decision/'+table)
            s.decide_candidate(cid,decision);saved=s.candidate_lineage();s.close()
            s=Store(root/'lineage.sqlite',readonly=True);self.assertEqual(s.candidate_lineage(),saved);s.close()
            bad=copy.deepcopy(saved['body']);bad['tables']['lineage_edge'][0]['parent']=cid
            with self.assertRaises(ContractError):verify_lineage(seal(bad))
            old=Store(root/'old.sqlite',create=True);old.agent('A',{'immutable':True});old.close();h=file_hash(root/'old.sqlite')
            migration=migrate_lineage_copy(root/'old.sqlite',root/'copy.sqlite');self.assertEqual(file_hash(root/'old.sqlite'),h)
            newer=Store(root/'copy.sqlite');self.assertEqual(newer.agent('A')['spec'],{'immutable':True});newer.close()
            (root/'broken.sqlite').write_bytes(b'broken sqlite')
            with self.assertRaises(sqlite3.DatabaseError):Store(root/'broken.sqlite')
            self.evidence={'injected_rollback_points':failures,'reopen_equal':True,'corruption_rejected':True,'cycle_rejected':True,'migration':{k:v for k,v in migration.items() if k not in ('source','destination')},'lineage':verify_lineage(saved)}

    def test_portable_guarded_cli(self):
        code=GUARD+"\nfrom actio.candidate_campaign import plan\nfrom actio.candidate import verify\nfrom actio.candidate_contract import baseline\nprint(json.dumps({'units':len(plan()['preregistration']['body']['units']),'invalid':verify({'body':{},'sha256':'bad'})['valid']}))"
        p=subprocess.run([sys.executable,'-I','-B','-c',code],capture_output=True,text=True,timeout=45,env=clean_env(ROOT/'.local'))
        self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout),{'units':24,'invalid':False})
        self.evidence={'guard':'network/env/key/subprocess/runtime/writes denied','result':json.loads(p.stdout)}


if __name__=='__main__':unittest.main()
