import base64
import copy
import json
import unittest
from actio.common import ContractError,canonical,digest
from actio.eval_contract import seal
from actio.failure_observation import observe,protocol,segmented_utf8,parse,LIMITS
from actio.failure_fixtures import vector,mutate,frame,error,chunk,portable_vectors
from actio.future_schedule import plan
from actio.transport_diagnostics import portable,analyze


class FailureObservation(unittest.TestCase):
    def test_fixture_expected_and_no_authority(self):
        for v in portable_vectors():
            r=observe(v['input']);self.assertEqual(r['classification'],v['expected']['classification'])
            self.assertFalse(r['admission']['actually_admitted']);self.assertFalse(r['accounting']['diagnosis_settles'])
            self.assertEqual(r['accounting']['original_state'],'unknown');self.assertFalse(r['retry_authorized'])

    def test_message_never_classifies_or_leaks(self):
        a=vector();b=mutate(a,lambda b:b['response'].update(raw=frame({'error':{'message':'timeout secret arbitrary bill free'}})))
        r=observe(b);self.assertEqual(r['classification'],'provider_error_observed')
        self.assertNotIn('timeout secret',canonical(r))
        c=mutate(a,lambda b:b['response'].update(raw=frame(error('unknown-private-type','unknown-private-code'))))
        r=observe(c);self.assertEqual(r['provider_declared_errors'][0]['type'],'unclassified')
        self.assertNotIn('unknown-private',canonical(r))

    def test_normal_error_text_comments_and_line_endings(self):
        a=vector('success',text='error 字符')
        for raw in (a['body']['response']['raw'],a['body']['response']['raw'].replace('\n','\r\n'),
                    ': error is only a comment\n\n\n'+a['body']['response']['raw']):
            r=observe(mutate(a,lambda b:b['response'].update(raw=raw)))
            self.assertEqual(r['provider_declared_errors'],[])
        r=observe(mutate(vector(),lambda b:b['response'].update(raw='data: {"error":\ndata: {"type":"api_error"}}\n\n')))
        self.assertEqual(r['classification'],'provider_error_observed')
        raw='中文😀'.encode();self.assertEqual(segmented_utf8([base64.b64encode(bytes([v])).decode() for v in raw]),'中文😀')
        with self.assertRaises(ContractError):segmented_utf8(['/w=='])

    def test_terminals_and_trailing_data(self):
        for suffix,signal in [('data: [DONE]\n\n','error_with_DONE'),(frame(chunk({},'stop')),'error_with_success_finish'),
                              (frame(error()),'multiple_provider_errors')]:
            r=observe(mutate(vector(),lambda b:b['response'].update(raw=b['response']['raw']+suffix)))
            self.assertIn(signal,r['signals'])
        for change in (lambda b:b['response'].update(raw=b['response']['raw']+'data: [DONE]\n\n'),
                       lambda b:b['response'].update(raw=b['response']['raw']+frame(error())),
                       lambda b:b['response'].update(raw=frame(chunk({},'stop'))+b['response']['raw'])):
            self.assertEqual(observe(mutate(vector('success'),change))['classification'],'contradictory_evidence')

    def test_adapter_native_conflicts_missing_and_prefix(self):
        a=vector()
        def success(b):
            c=json.loads(b['response']['chunks_json']);c[-1]['reason']={'kind':'stop'};b['response']['chunks_json']=canonical(c)
        self.assertEqual(observe(mutate(a,success))['classification'],'contradictory_evidence')
        self.assertEqual(observe(mutate(a,lambda b:b['native'].update(chunks=[]),sync_native=False))['classification'],'contradictory_evidence')
        self.assertEqual(observe(mutate(a,lambda b:b.update(native=None)))['classification'],'unclassified_evidence')
        r=observe(vector('prefix'));self.assertTrue(r['adapter_native']['content_prefix_present']);self.assertFalse(r['admission']['trusted_complete_text'])
        with self.assertRaises(ContractError):observe(mutate(vector('prefix'),lambda b:b['operation'].update(admitted=True)))

    def test_usage_is_separate_and_zero_not_trusted(self):
        r=observe(vector());self.assertIsNone(r['accounting']['verified_usage_preserved']);self.assertFalse(r['accounting']['adapter_zero_is_trusted_usage'])
        def raw_usage(b):b['response']['raw']+=frame({'usage':{'prompt_tokens':12,'completion_tokens':5,'total_tokens':17}})
        r=observe(mutate(vector(),raw_usage));self.assertIn('raw_adapter_usage_conflict',r['signals'])
        r=observe(vector('success'));self.assertTrue(r['accounting']['raw_adapter_usage_consistent'])
        def matching_error(b):
            raw_usage(b);c=json.loads(b['response']['chunks_json']);c[0]['usage']={'inputTokens':12,'outputTokens':5,'totalTokens':17}
            b['response']['chunks_json']=canonical(c);b['native']['usage']=c[0]['usage']
        r=observe(mutate(vector(),matching_error));self.assertTrue(r['accounting']['raw_adapter_usage_consistent']);self.assertEqual(r['accounting']['original_state'],'unknown')
        with self.assertRaises(ContractError):observe(mutate(vector(),lambda b:b['accounting'].update(trusted_usage={'input_tokens':0})))

    def test_binding_bytes_deadline_and_schema_rejection(self):
        mutations=[lambda b:b['identity'].update(attempt='different'),lambda b:b['identity'].update(request_hash='0'*64),
            lambda b:b['native'].update(stream='different'),lambda b:b['response'].update(raw_base64='%%%'),
            lambda b:b['response'].update(raw_base64='/w=='),lambda b:b['response'].update(raw_base64=''),
            lambda b:b['response'].update(deadlines={'trigger':'fetch_total','total_ms':90000,'headers_ms':60000},timings={'total_ms':1}),
            lambda b:b.update(schema='future-schema'),lambda b:b.update(origin='historical_c4'),
            lambda b:b['response'].update(raw=frame(chunk({'content':''})).replace('gpt-5.6','other-model'))]
        for fn in mutations:
            with self.assertRaises((ContractError,ValueError)):observe(mutate(vector(),fn,sync_bytes=False))
        a=vector();a['body']['identity']['attempt']='changed'
        with self.assertRaises(ContractError):observe(a)

    def test_duplicate_nonfinite_resource_limits(self):
        for raw in ('{"error":{},"error":{}}','{"a":NaN}','{"a":Infinity}','['*34+'0'+']'*34,
                    canonical({str(i):0 for i in range(129)}),canonical(['x']*4097)):
            with self.assertRaises((ContractError,ValueError)):parse(raw,2*1024*1024)
        cases=[': '+('x'*65537)+'\n\n',(': x\n\n'*1025),('data: \n'*9+'\n'), 'data: {}\r\r']
        for raw in cases:
            with self.assertRaises((ContractError,ValueError)):observe(mutate(vector(),lambda b:b['response'].update(raw=raw)))
        with self.assertRaises(ContractError):observe(mutate(vector(),lambda b:b['response'].update(raw='x'*262145)))

    def test_future_membership_adjacency_balance_and_curves(self):
        p=plan()['body'];units=[r['source_unit'] for r in p['units']]
        self.assertEqual(len({u['id'] for u in units}),64)
        for i in range(0,64,2):self.assertEqual(units[i]['card'],units[i+1]['card']);self.assertNotEqual(units[i]['arm'],units[i+1]['arm'])
        for family in ('scheduling','bargaining'):
            first=[units[i] for i in range(0,64,2) if units[i]['family']==family]
            self.assertEqual(sum(u['arm']=='baseline' for u in first),8)
            for group in {u['structural_group'] for u in first}:
                self.assertEqual(sum(u['arm']=='baseline' for u in first if u['structural_group']==group),2)
        old=p['curves']['old'];self.assertEqual([old[16][k] for k in ('candidate','hidden_world','presentation')],[8,0,0])
        self.assertEqual(next(i for i,r in enumerate(old) if r['hidden_world']),17)
        self.assertEqual(next(i for i,r in enumerate(old) if r['presentation']),21)
        self.assertEqual(len(p['curves']['proposed']),65);self.assertFalse(p['executable'])

    def test_portable_recomputation_and_tamper(self):
        p=portable();self.assertTrue(analyze(p)['valid']);self.assertFalse(analyze(p)['historical_raw_authenticated'])
        for field in ('sources','fixtures','observations','future'):
            b=copy.deepcopy(p['body']);b[field]={}
            with self.assertRaises((ContractError,ValueError)):analyze(seal(b))


if __name__=='__main__':unittest.main()
