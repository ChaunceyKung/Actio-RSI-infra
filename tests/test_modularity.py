"""Boundary regressions introduced by the modular extraction."""
import ast
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest
import tempfile

class Modularity(unittest.TestCase):
    def test_recursive_checker_rejects_nested_shim_dependency_and_records_dynamic_import(self):
        spec=importlib.util.spec_from_file_location("architecture_checker",Path(__file__).resolve().parents[1]/"tools/refactor/architecture.py")
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);inspect=module.inspect
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'actio'; (root/'nested').mkdir(parents=True)
            (root/'__init__.py').write_text('')
            (root/'legacy.py').write_text('"""Compatibility shim."""\nfrom actio.nested.impl import value\n')
            (root/'nested/__init__.py').write_text('')
            (root/'nested/impl.py').write_text("from importlib import import_module\nvalue=import_module('actio.legacy')\n")
            result=inspect(root)
            self.assertEqual(result['status'],'INCOMPLETE')
            self.assertTrue(result['dynamic_imports'])
            self.assertTrue(any(v['target']=='legacy.py' and v['reason']=='root file not allowed' for v in result['violations']))
    def test_pure_layers_have_only_downward_dependencies(self):
        import actio
        root=Path(actio.__file__).parent
        allowed={'contracts':set(),'domain':{'contracts'},'tasks':{'contracts','domain','tasks'},'measurement':{'contracts','domain','tasks','measurement'}}
        forbidden={'sqlite3','subprocess','socket','os','deepseek_harness','concordia'}
        for layer,deps in allowed.items():
            for p in (root/layer).rglob('*.py'):
                for n in ast.walk(ast.parse(p.read_text(encoding='utf8'))):
                    names=[a.name for a in n.names] if isinstance(n,ast.Import) else [n.module or ''] if isinstance(n,ast.ImportFrom) else []
                    for name in names:
                        self.assertNotIn(name.split('.')[0],forbidden,(p,n.lineno,name))
                        if name.startswith('actio.'):
                            self.assertIn(name.split('.')[1],deps,(p,n.lineno,name))
        # The application invokes injected ports, never concrete runtime/DB adapters.
        for folder in ('application','evidence'):
            for p in (root/folder).rglob('*.py'):
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
        for p in (root/'tasks').rglob('*.py'):
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
        code="import sys; import actio.interfaces.ipc.budget; assert not any(n in sys.modules for n in ('actio.adapters.runtime.runtime','actio.adapters.transport.transport','deepseek_harness','concordia')); print('PASS')"
        p=subprocess.run([sys.executable,'-X','utf8','-I','-B','-c',code],capture_output=True,encoding='utf8',timeout=20)
        self.assertEqual(p.returncode,0,p.stderr)


    def checker(self):
        spec=importlib.util.spec_from_file_location('checker',Path(__file__).resolve().parents[1]/'tools/refactor/architecture.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module.inspect

    def test_package_init_group_cycle_without_module_cycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'actio'
            for group,other in [('audit','campaigns'),('campaigns','audit')]:
                p=root/'evidence'/group;p.mkdir(parents=True)
                (p/'__init__.py').write_text('import actio.evidence.'+other+'.leaf')
                (p/'leaf.py').write_text('')
            value=self.checker()(root)
            self.assertEqual(value['strong_components'],[])
            self.assertEqual(value['evidence_group_cycles'],[['audit','campaigns']])
            self.assertEqual(value['status'],'INCOMPLETE')

    def test_relative_dynamic_local_import_and_unknown_group(self):
        cases=[('contracts/nested.py',"from importlib import import_module\ndef f(): return import_module('..application.impl', __package__)",'pure layer dependency'),
               ('application/nested/impl.py','from ...adapters.persistence import ledger','use case/reader concrete runtime or persistence dependency'),
               ('evidence/extra/__init__.py','','unknown evidence group'),
               ('contracts/nested/__init__.py','from ...application import impl','pure layer dependency'),
               ('evidence/audit/reader.py',"def f(): return __import__('actio.application.writer')",'reader depends on writer'),
               ('interfaces/old.py','from actio import budget','removed root API dependency')]
        for name,code,reason in cases:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)/'actio';p=root/name;p.parent.mkdir(parents=True);p.write_text(code)
                value=self.checker()(root)
                self.assertTrue(any(v['reason']==reason for v in value['violations']),value)
                self.assertEqual(value['status'],'INCOMPLETE')

    def test_current_installed_boundaries_and_unresolved_import_review(self):
        import actio
        value=self.checker()(Path(actio.__file__).parent)
        self.assertEqual(value['status'],'PASS',value['violations'])
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'actio';(root/'domain').mkdir(parents=True)
            (root/'domain/unknown.py').write_text('def f(name): return __import__(name)')
            value=self.checker()(root)
            self.assertEqual(len(value['unresolved_dynamic_imports']),1)
            self.assertEqual(value['status'],'INCOMPLETE')

    def test_unified_cli_explicit_args_and_offline_guard(self):
        code="import sys; from actio.interfaces.cli.main import main; old=sys.argv[:]; assert main(['--help'])==0; assert main(['diagnostics','transport','plan'])==0; assert sys.argv==old; assert not any(m in sys.modules for m in ('deepseek_harness','concordia','mcp','sqlite3')); assert main(['unknown'])==2"
        p=subprocess.run([sys.executable,'-X','utf8','-I','-B','-c',code],capture_output=True,text=True,encoding='utf8',timeout=30)
        self.assertEqual(p.returncode,0,p.stderr)

if __name__=='__main__':unittest.main()
