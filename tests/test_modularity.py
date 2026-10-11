"""Boundary regressions introduced by the modular extraction."""
import ast
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

class Modularity(unittest.TestCase):
    def test_pure_layers_have_only_downward_dependencies(self):
        import actio
        root=Path(actio.__file__).parent
        allowed={'contracts':set(),'domain':{'contracts'},'tasks':{'contracts','domain','tasks'},'measurement':{'contracts','domain','tasks','measurement'}}
        forbidden={'sqlite3','subprocess','socket','os','deepseek_harness','concordia'}
        for layer,deps in allowed.items():
            for p in (root/layer).glob('*.py'):
                for n in ast.walk(ast.parse(p.read_text(encoding='utf8'))):
                    names=[a.name for a in n.names] if isinstance(n,ast.Import) else [n.module or ''] if isinstance(n,ast.ImportFrom) else []
                    for name in names:
                        self.assertNotIn(name.split('.')[0],forbidden,(p,n.lineno,name))
                        if name.startswith('actio.'):
                            self.assertIn(name.split('.')[1],deps,(p,n.lineno,name))
    def test_diagnostic_fixture_has_no_test_loader_or_global_patch(self):
        import actio.diagnostic_runtime as runtime
        text=Path(runtime.__file__).read_text(encoding='utf8')
        self.assertNotIn('sys.path',text)
        self.assertNotIn('gateway_stub',text)
        self.assertEqual(runtime.TOOLS,())
        from actio.adapters.transport.fixture import GatewayStub
        import inspect
        self.assertIn('response_policy',inspect.signature(GatewayStub).parameters)
    def test_legacy_stub_profile_and_unknown_reservation(self):
        from actio.budget import profile_for,totals
        from actio.transport_contract import config,PROFILE
        self.assertEqual(profile_for(config('http://127.0.0.1:19999')),PROFILE)
        charge={'calls':1,'input_tokens':None,'output_tokens':512,'cost_minor':None}
        self.assertEqual(totals([{'state':'unknown','reservation':charge,'usage':None}]),charge)
    def test_budget_ipc_implementation_has_no_runtime_import(self):
        code="import sys; import actio.interfaces.budget; assert not any(n in sys.modules for n in ('actio.runtime','actio.transport','deepseek_harness','concordia')); print('PASS')"
        p=subprocess.run([sys.executable,'-X','utf8','-I','-B','-c',code],capture_output=True,encoding='utf8',timeout=20)
        self.assertEqual(p.returncode,0,p.stderr)

if __name__=='__main__':unittest.main()
