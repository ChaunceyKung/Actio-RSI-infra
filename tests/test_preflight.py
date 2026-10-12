import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from actio.contracts.json import canonical
from actio.contracts.json import ContractError
from actio.adapters.filesystem.common import clean_env
from actio.domain.roles import template
from actio.domain.roles import stub_config
from actio.interfaces.cli.preflight import preflight
from actio.domain.roles import parse_config
from actio.domain.roles import budget


class Preflight(unittest.TestCase):
    def test_role_modes_fix_c2r1_without_fake_disabled_quotes(self):
        c=stub_config('http://127.0.0.1:23456');result=preflight(c)
        self.assertTrue(result['configuration_valid'],result)
        for role in ('gm','judge','retries','other'):
            self.assertEqual(c['roles'][role]['budget'],budget())
            self.assertIsNone(c['roles'][role]['provider'])
        self.assertEqual(result['status'],'BLOCKED');self.assertFalse(result['live_ready']);self.assertFalse(result['transport_validated'])
        self.assertTrue(preflight(template('disabled'))['configuration_valid'])
        self.evidence={'config':c,'result':result,'real_requests':0}

    def test_strict_types_unknown_fields_duplicate_keys_and_money(self):
        c=stub_config('http://127.0.0.1:23456');failures={}
        for name,mutate in {
            'unknown':lambda x:x.update(secret='do-not-accept'),
            'unknown_role':lambda x:x['roles'].update(other_solver=x['roles']['solver']),
            'bool_calls':lambda x:x['roles']['solver']['budget'].update(calls=True),
            'float_cost':lambda x:x['roles']['solver']['budget'].update(cost_minor=1.5),
            'nan':lambda x:x['roles']['solver']['budget'].update(cost_minor=float('nan')),
            'too_large':lambda x:x['roles']['solver']['budget'].update(cost_minor=2**54),
            'negative':lambda x:x['roles']['solver']['budget'].update(input_tokens=-1),
            'float_tokens':lambda x:x['roles']['solver']['parameters'].update(max_tokens=1.0),
            'tools':lambda x:x['roles']['solver'].update(tools=['shell']),
            'missing':lambda x:x['roles']['solver'].pop('data_scope'),
            'unknown_parameter':lambda x:x['roles']['solver']['parameters'].update(auto_retry=True),
            'stop_string':lambda x:x.update(stop_conditions='none'),
        }.items():
            v=copy.deepcopy(c);mutate(v);r=preflight(v);self.assertFalse(r['configuration_valid'],name);failures[name]=r['reasons']
        for raw in ('{"schema":1,"schema":2}','{"x":1.0}','{"x":NaN}','{"x":Infinity}','{"x":{"a":1,"a":2}}'):
            with self.assertRaises(ContractError):parse_config(raw)
        self.evidence={'counterexamples':failures,'money':'integer minor units only; synthetic price not a real quotation'}

    def test_disabled_roles_cannot_request_budget_credentials_or_remote_mode(self):
        c=stub_config('http://127.0.0.1:23456');cases={}
        for role in ('gm','judge','retries','other'):
            for name,change in {'cost':lambda r:r['budget'].update(cost_minor=1),
                                'credential':lambda r:r.update(credential_ref='FAKE_REF'),
                                'provider':lambda r:r.update(provider='fake-provider'),
                                'live':lambda r:r.update(mode='future_live')}.items():
                v=copy.deepcopy(c);change(v['roles'][role]);result=preflight(v)
                self.assertFalse(result['configuration_valid']);cases[role+'-'+name]=result['reasons']
        self.evidence={'rejected':cases}

    def test_endpoint_and_approval_are_never_authorization(self):
        endpoints=['http://localhost:23456','http://127.0.0.1.evil.invalid:23456','https://api.deepseek.com',
                   'http://127.0.0.1:23456/v1','http://127.0.0.1:23456?redirect=1',
                   'http://u:p@127.0.0.1:23456','http://[::1]:23456','http://127.0.0.1:80']
        for endpoint in endpoints:self.assertFalse(preflight(stub_config(endpoint))['configuration_valid'],endpoint)
        zero=stub_config('http://127.0.0.1:23456',0);self.assertEqual(preflight(zero)['status'],'BLOCKED')
        c=stub_config('http://127.0.0.1:23456');c['authorization_ref']='FORGED APPROVAL';s=c['roles']['solver']
        s.update(mode='future_live',endpoint='https://provider.invalid',provider='future-provider',model='future-exact-version',credential_ref='FUTURE_ENV_REF')
        s['budget'].update(currency='TEST_ONLY',price_version='unverified-quote-fixture')
        valid=preflight(c);self.assertTrue(valid['configuration_valid'],valid)
        self.assertFalse(valid['live_authorized']);self.assertFalse(valid['transport_validated']);self.assertFalse(valid['live_ready'])
        c['authorization_ref']=None;self.assertFalse(preflight(c)['configuration_valid'])
        self.evidence={'positive_fields_still_blocked':valid,'endpoint_rejections':endpoints,'model_requests':0}

    def test_actual_readonly_cli_duplicate_key_and_side_effect_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);env=clean_env(root);p=root/'config.json'
            p.write_text('{"schema":"pilot-config.v2","schema":"pilot-config.v2"}',encoding='utf8')
            result=subprocess.run([sys.executable,'-X','utf8','-I','-B','-m','actio','preflight',str(p)],cwd=root,env=env,capture_output=True,text=True,encoding='utf8',timeout=15)
            self.assertEqual(result.returncode,2);self.assertIn('duplicate JSON key',result.stdout)
            script='''import os,sys,json
from actio.interfaces.cli.preflight import preflight
value=json.loads(sys.stdin.read())
'codec warmup'.encode('utf-16be')
def audit(event,args):
    if event.startswith('socket.') or event in ('open','subprocess.Popen','import'):raise AssertionError('preflight side effect '+event)
class NoEnv(dict):
    def get(self,*args):raise AssertionError('environment read')
    def __getitem__(self,*args):raise AssertionError('environment read')
    def __iter__(self):raise AssertionError('environment enumeration')
os.environ=NoEnv();sys.addaudithook(audit)
print(json.dumps(preflight(value)))
'''
            config=stub_config('http://127.0.0.1:23456');result=subprocess.run([sys.executable,'-X','utf8','-I','-B','-c',script],input=canonical(config),cwd=root,env=env,capture_output=True,text=True,encoding='utf8',timeout=15)
            self.assertEqual(result.returncode,0,result.stderr);self.assertTrue(json.loads(result.stdout)['configuration_valid'])
            self.evidence={'guarded_result':json.loads(result.stdout),'denied':'environment/open/socket/process/import after import; no real secrets read'}


if __name__=='__main__':unittest.main()
