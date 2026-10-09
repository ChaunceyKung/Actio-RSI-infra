import copy
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock

from actio.common import ContractError,clean_env,digest
from actio.readiness_contract import template,validate,plan,execute,amount,reservation,quote_current,QUOTE
from actio.transport_contract import config as old_config,validate_config


class ReadinessConfig(unittest.TestCase):
    def test_default_blocked_approval_binding_and_no_secret_resolution(self):
        c=template();result=plan(c);self.assertEqual(result['status'],'BLOCKED')
        self.assertTrue(all(v==0 for v in c['budget'].values()));self.assertIsNone(c['approval'])
        resolver=Mock(side_effect=AssertionError('secret resolver must not run'))
        for change in (None,'budget','flag','mismatch','expired','matching'):
            value=copy.deepcopy(c)
            if change:value['budget']={k:v*2 for k,v in reservation(c).items()}
            if change=='flag':value['approval']={'approved':True}
            if change in ('mismatch','expired','matching'):
                value['approval']={'contract_hash':digest(value) if change!='mismatch' else '0'*64,
                                   'budget':value['budget'],'expires':'2020-01-01T00:00:00+00:00' if change=='expired' else '2099-01-01T00:00:00+00:00','reference':'not-an-authorization'}
            with self.assertRaises(ContractError):execute(value,operation_approval='push authorized',credential_resolver=resolver)
            self.assertEqual(plan(value)['status'],'BLOCKED')
        resolver.assert_not_called();self.evidence={'proposal':result,'credential_reads':0,'network_requests':0,'workers_started':0}

    def test_integer_pricing_upper_envelope_and_quote_or_alias_change(self):
        self.assertEqual(amount(4,8,5),8424)
        self.assertEqual(amount(0,12,5),9600)
        tiny={**QUOTE,'input_hit_minor':1};self.assertEqual(amount(1,0,0,tiny),1)
        c=template();self.assertEqual(reservation(c)['cost_minor'],314649600)
        self.assertFalse(c['bounds']['input_bound_verified'])
        self.assertTrue(any('insufficient' in b for b in plan(c)['blockers']))
        with self.assertRaises(ContractError):quote_current(c,datetime(2030,1,1,tzinfo=timezone.utc))
        for field,value in [('model','deepseek-v4-flash'),('endpoint','http://127.0.0.1:19999'),('profile','actio-fixture')]:
            altered=copy.deepcopy(c);altered[field]=value
            with self.assertRaises(ContractError):validate(altered)
        altered=copy.deepcopy(c);altered['quote']['input_miss_minor']+=1
        self.assertNotEqual(digest(c),digest(altered))
        with self.assertRaises(ContractError):validate(altered)
        altered=copy.deepcopy(c);altered['bounds']['input_bound_verified']=True
        with self.assertRaises(ContractError):validate(altered)
        self.assertEqual(validate_config(old_config('http://127.0.0.1:19999'))['schema'],'pilot-config.v3')

    def test_plan_cli_under_no_network_process_or_credential_access_guard(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name)
            code="""import sys,os,json
def audit(e,a):
 if e.startswith('socket.') or e=='subprocess.Popen':raise RuntimeError('side effects forbidden')
sys.addaudithook(audit)
class NoEnvironment(dict):
 def get(self,*a):raise RuntimeError('environment access forbidden')
 def __getitem__(self,k):raise RuntimeError('environment access forbidden')
os.environ=NoEnvironment()
from actio.readiness_contract import plan,template,execute
r=plan(template());assert r['credential_reads']==0
try:execute(template(),credential_resolver=lambda r:1/0)
except ValueError:pass
print(json.dumps(r))
"""
            p=subprocess.run([sys.executable,'-I','-B','-c',code],cwd=root,env=clean_env(root),capture_output=True,text=True,encoding='utf8',timeout=20)
            self.assertEqual(p.returncode,0,p.stderr);self.evidence={'guarded_plan':json.loads(p.stdout)}


if __name__=='__main__':unittest.main()
