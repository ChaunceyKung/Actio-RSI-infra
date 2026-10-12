"""Static migration identities, checker counterexamples and navigation audit."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
from architecture import inspect

ROOT=Path(__file__).resolve().parents[2]
BASE='205cf8b1c2551e4075054131b5ff8baa0aaaadfa'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def assertions(node):
 return [ast.dump(n,include_attributes=False) for n in ast.walk(node) if isinstance(n,ast.Assert) or
         isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr.startswith('assert')]
def methods(text):
 return {c.name+'.'+f.name:f for c in ast.parse(text).body if isinstance(c,ast.ClassDef)
         for f in c.body if isinstance(f,ast.FunctionDef) and f.name.startswith('test_')}
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 migration=json.loads((ROOT/'docs/validation/refactor_entrypoints/migration.json').read_bytes())
 mapping={};method_rows=[];assertion_changes=[]
 for name in migration['removed_modules']:
  path='src/'+name.replace('.','/')+'.py'
  old=git('show',BASE+':'+path).decode()
  mapping[name]={'old_path':path,'old_sha256':hashlib.sha256(old.encode()).hexdigest(),
    'former_targets':[n.module for n in ast.walk(ast.parse(old)) if isinstance(n,ast.ImportFrom)],
    'compatibility':'removed in 0.2.0; fixed old reader only'}
 for path in sorted((ROOT/'tests').glob('test_*.py')):
  before=methods(git('show',BASE+':tests/'+path.name).decode());after=methods(path.read_text(encoding='utf8'))
  assert before.keys()<=after.keys()
  for name,old in before.items():
   prior=assertions(old);current=assertions(after[name]);assert len(current)>=len(prior),(path.name,name)
   if prior!=current:assertion_changes.append({'method':path.stem+'.'+name,'before':prior,'after':current})
  method_rows.append({'suite':path.stem,'original':sorted(before),'added':sorted(after.keys()-before.keys()),'source_sha256':sha(path)})
 assert len(method_rows)==34 and sum(len(r['original']) for r in method_rows)==165
 counterexamples=[]
 with tempfile.TemporaryDirectory() as t:
  root=Path(t)/'actio'
  for group,other in [('audit','campaigns'),('campaigns','audit')]:
   d=root/'evidence'/group;d.mkdir(parents=True);(d/'__init__.py').write_text('import actio.evidence.'+other+'.leaf');(d/'leaf.py').write_text('')
  v=inspect(root);assert v['status']=='INCOMPLETE' and v['strong_components']==[] and v['evidence_group_cycles']==[['audit','campaigns']];counterexamples.append(v)
 for relative,code,reason in [
  ('contracts/nested.py',"from importlib import import_module\ndef f():return import_module('..application.impl',__package__)",'pure layer dependency'),
  ('evidence/unknown/__init__.py','','unknown evidence group'),
  ('legacy.py','"""Compatibility fake exemption."""','root file not allowed'),
  ('interfaces/old.py','from actio import budget','removed root API dependency')]:
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/'actio';target=root/relative;target.parent.mkdir(parents=True);target.write_text(code)
   v=inspect(root);assert v['status']=='INCOMPLETE' and any(x['reason']==reason for x in v['violations']);counterexamples.append(v)
 current=inspect();assert current['status']=='PASS'
 old_refs=[]
 pattern=re.compile(r'actio\.(?:'+ '|'.join(re.escape(n.removeprefix('actio.')) for n in migration['removed_modules'])+r')(?![\w.])')
 for path in sorted((ROOT/'src/actio').rglob('*')):
  if path.suffix not in {'.py','.mjs'}:continue
  text=path.read_text(encoding='utf8')
  for lineno,line in enumerate(text.splitlines(),1):
   if pattern.search(line):
    assert path.relative_to(ROOT).as_posix()=='src/actio/adapters/runtime/eval_worker.py' and ('denied=' in line or 'actio.host' in line),(path,lineno)
    old_refs.append({'file':path.relative_to(ROOT).as_posix(),'line':lineno,'reason':'retained security deny list','names':pattern.findall(line)})
  assert 'sys.modules[' not in text and 'sys.meta_path' not in text and 'sys.path.insert' not in text,path
 docs=[ROOT/'README.md',ROOT/'src/actio/README.md',*(ROOT/'docs/architecture'/n for n in ['README.md','MODULES.md','FLOWS.md','MIGRATION_0_2.md']),*(ROOT/'src/actio'/g/'README.md' for g in ['contracts','domain','tasks','profiles','application','adapters','evidence','measurement','interfaces'])]
 links=[]
 for path in docs:
  for href in re.findall(r'\[[^\]]*\]\(([^)]+)\)',path.read_text(encoding='utf8')):
   if '://' in href or href.startswith('#'):continue
   target=(path.parent/href.split('#')[0]).resolve();assert target.exists(),(path,href)
   links.append({'file':path.relative_to(ROOT).as_posix(),'target':href})
 out={'status':'PASS','base':BASE,'identity':'actio-entrypoints-r15-r18-20261012','removed_api_map':mapping,
      'methods':method_rows,'assertion_changes_requiring_review':assertion_changes,'counterexamples':counterexamples,
      'architecture':current,'allowed_old_references':old_refs,'documentation_links':links,
      'original_methods':165,'new_methods':sum(len(r['added']) for r in method_rows),
      'scope':'static checks only; installed execution and full method receipts are separate'}
 a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'status':'PASS','original_methods':165,'assertion_changes':len(assertion_changes),'links':len(links)}))
if __name__=='__main__':main()
