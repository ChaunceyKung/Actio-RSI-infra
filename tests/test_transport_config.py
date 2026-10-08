import copy
import json
import unittest
from pathlib import Path
import subprocess
import sys
import tempfile
from actio.common import clean_env
from actio.common import ContractError
from actio.preflight import preflight,parse_config,stub_config
from actio.transport_contract import config,validate_config


class TransportConfig(unittest.TestCase):
    def test_windows_architecture_fallback_in_sanitized_child(self):
        with tempfile.TemporaryDirectory() as tmp:
            env=clean_env(Path(tmp))
            code="import platform; platform._wmi_query=lambda *a: (_ for _ in ()).throw(OSError('controlled WMI failure')); print(platform.machine())"
            p=subprocess.run([sys.executable,'-I','-S','-B','-c',code],cwd=tmp,env=env,capture_output=True,text=True,timeout=15)
            self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(p.stdout.strip(),'AMD64')
            self.evidence={'controlled_wmi_failure':True,'child_machine':p.stdout.strip(),'provider_environment':'not inherited'}

    def test_explicit_protocol_version_and_zero_inactive_roles(self):
        c=config('http://127.0.0.1:23456');self.assertTrue(preflight(c)['configuration_valid'])
        old=stub_config('http://127.0.0.1:23456');self.assertTrue(preflight(old)['configuration_valid'])
        self.assertEqual(old['roles']['solver']['protocol'],'messages.v1')
        with self.assertRaises(ContractError):validate_config(old)
        for role in ('gm','judge','retries','other'):
            self.assertEqual(c['roles'][role]['budget']['calls'],0);self.assertIsNone(c['roles'][role]['credential_ref'])
        self.evidence={'v3':preflight(c),'v2_remains_messages':old['roles']['solver']['protocol']}

    def test_forged_live_endpoints_types_and_credentials_fail_closed(self):
        outcomes={}
        for name,change in {'live':lambda c:c['roles']['solver'].update(mode='future_live'),
                           'dns':lambda c:c['roles']['solver'].update(endpoint='http://localhost:23456'),
                           'external':lambda c:c['roles']['solver'].update(endpoint='https://provider.invalid'),
                           'key':lambda c:c['roles']['solver'].update(credential_ref='FAKE_OTHER_REFERENCE'),
                           'bool':lambda c:c['roles']['solver']['budget'].update(calls=True),
                           'protocol':lambda c:c['roles']['solver'].update(protocol='messages.v1')}.items():
            c=config('http://127.0.0.1:23456');change(c);r=preflight(c);self.assertFalse(r['configuration_valid']);outcomes[name]=r
        c=config('http://127.0.0.1:23456');c['authorization_ref']='FORGED APPROVAL'
        r=preflight(c);self.assertTrue(r['configuration_valid']);self.assertFalse(r['live_ready']);self.assertFalse(r['live_authorized'])
        with self.assertRaises(ContractError):parse_config('{"schema":"pilot-config.v3","schema":"pilot-config.v3"}')
        self.evidence={'blocked':outcomes,'forged_reference':r,'model_requests':0}
