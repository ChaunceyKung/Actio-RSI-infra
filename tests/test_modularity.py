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
        # The application invokes injected ports, never concrete runtime/DB adapters.
        for folder in ('application','evidence'):
            for p in (root/folder).glob('*.py'):
                for n in ast.walk(ast.parse(p.read_text(encoding='utf8'))):
                    names=[a.name for a in n.names] if isinstance(n,ast.Import) else [n.module or ''] if isinstance(n,ast.ImportFrom) else []
                    if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='__import__' and n.args and isinstance(n.args[0],ast.Constant):names.append(n.args[0].value)
                    for name in names:
                        self.assertNotIn(name.split('.')[0],{'subprocess','sqlite3','deepseek_harness','concordia'},(p,name))
                        self.assertFalse(name.startswith(('actio.adapters.runtime','actio.adapters.environment','actio.adapters.transport','actio.adapters.persistence','actio.interfaces')),(p,name))
                        if folder=='evidence':self.assertFalse(name.startswith('actio.application'),(p,name))
        p=root/'profiles/validation.py'
        for n in ast.walk(ast.parse(p.read_text(encoding='utf8'))):
            if isinstance(n,ast.ImportFrom) and (n.module or '').startswith('actio.'):
                self.assertIn(n.module.split('.')[1],{'contracts','domain','tasks'})
        for p in (root/'tasks').glob('*.py'):
            if p.stem=='registry':continue
            self.assertNotIn('actio.tasks.registry',p.read_text(encoding='utf8'),p)

    def test_diagnostic_fixture_has_no_test_loader_or_global_patch(self):
        import actio.application.diagnostic_runtime as runtime
        text=Path(runtime.__file__).read_text(encoding='utf8')
        self.assertNotIn('sys.path',text)
        self.assertNotIn('gateway_stub',text)
        self.assertEqual(runtime.TOOLS,())
        from actio.adapters.transport.fixture import GatewayStub
        import inspect
        self.assertIn('response_policy',inspect.signature(GatewayStub).parameters)
    def test_legacy_stub_profile_and_unknown_reservation(self):
        from actio.profiles.registry import profile_for
        from actio.profiles.registry import totals
        from actio.profiles.transport import config
        from actio.contracts.transport import PROFILE
        self.assertEqual(profile_for(config('http://127.0.0.1:19999')),PROFILE)
        charge={'calls':1,'input_tokens':None,'output_tokens':512,'cost_minor':None}
        self.assertEqual(totals([{'state':'unknown','reservation':charge,'usage':None}]),charge)
    def test_budget_ipc_implementation_has_no_runtime_import(self):
        code="import sys; import actio.interfaces.budget; assert not any(n in sys.modules for n in ('actio.adapters.runtime.runtime','actio.adapters.transport.transport','deepseek_harness','concordia')); print('PASS')"
        p=subprocess.run([sys.executable,'-X','utf8','-I','-B','-c',code],capture_output=True,encoding='utf8',timeout=20)
        self.assertEqual(p.returncode,0,p.stderr)

if __name__=='__main__':unittest.main()
