"""Architecture rules v3: recursive modules, root allowlist and evidence package DAG."""
import ast
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION = 'entrypoints-boundaries.v3'
PURE = {'contracts': set(), 'domain': {'contracts'}, 'tasks': {'contracts','domain','tasks'},
        'measurement': {'contracts','domain','tasks','measurement'}}
GROUPS = {'audit','bundles','campaigns','lineage','diagnostics'}
ROOT_FILES = {'__init__.py','__main__.py','README.md'}
ROOT_DIRS = set(PURE) | {'profiles','application','adapters','evidence','interfaces','resources','_vendor'}
REMOVED = {'budget','candidate','candidate_evaluation','cli','common','evaluation','eval_worker',
           'gateway','host','mcp_server','pilot','preflight','readiness','robustness','suite',
           'task_diagnostics','transport_campaign','transport_diagnostics','verify'}


def components(edges):
    index={};low={};stack=[];active=set();result=[]
    def visit(v):
        index[v]=low[v]=len(index);stack.append(v);active.add(v)
        for w in sorted(edges[v]):
            if w not in index:visit(w);low[v]=min(low[v],low[w])
            elif w in active:low[v]=min(low[v],index[w])
        if low[v]==index[v]:
            group=[]
            while True:
                w=stack.pop();active.remove(w);group.append(w)
                if w==v:break
            if len(group)>1:result.append(sorted(group))
    for v in sorted(edges):
        if v not in index:visit(v)
    return sorted(result)


def inspect(root=None):
    root=Path(root) if root else ROOT/'src/actio'
    files={'.'.join(p.relative_to(root.parent).with_suffix('').parts).removesuffix('.__init__'):p
           for p in root.rglob('*.py')}
    edges={n:set() for n in files};violations=[];dynamic=[];groups={g:set() for g in GROUPS}
    def reject(name,line,target,reason):
        violations.append(dict(module=name,line=line,target=target,reason=reason))
    def group(name):
        parts=name.split('.')
        return parts[2] if len(parts)>=3 and parts[:2]==['actio','evidence'] else None
    extras=sorted(p.name for p in root.iterdir() if p.is_file() and p.name not in ROOT_FILES and p.suffix!='.pyc')
    for n in extras:reject('actio',0,n,'root file not allowed')
    for p in root.iterdir():
        if p.is_dir() and p.name not in ROOT_DIRS|{'__pycache__'}:reject('actio',0,p.name,'root directory not allowed')
    for name,p in files.items():
        tree=ast.parse(p.read_text(encoding='utf8'));package=name if p.name=='__init__.py' else name.rsplit('.',1)[0]
        layer=name.split('.')[1] if '.' in name else ''
        g=group(name)
        if g and g not in GROUPS:reject(name,0,g,'unknown evidence group')
        aliases={'__import__':'__import__','import_module':'import_module'}
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom) and node.module=='importlib':
                aliases.update({a.asname or a.name:a.name for a in node.names if a.name=='import_module'})
        for n in ast.walk(tree):
            targets=[]
            if isinstance(n,ast.Import):targets=[a.name for a in n.names]
            elif isinstance(n,ast.ImportFrom):
                try:base=importlib.util.resolve_name('.'*n.level+(n.module or ''),package) if n.level else n.module or ''
                except ImportError:reject(name,n.lineno,n.module,'invalid relative import');continue
                targets=[base]
                targets.extend(base+'.'+a.name for a in n.names if base+'.'+a.name in files)
                if base=='actio':targets.extend(base+'.'+a.name for a in n.names if a.name in REMOVED)
            elif isinstance(n,ast.Call) and ((isinstance(n.func,ast.Name) and n.func.id in aliases) or isinstance(n.func,ast.Attribute) and n.func.attr=='import_module'):
                value=n.args[0].value if n.args and isinstance(n.args[0],ast.Constant) else None
                resolved=value if isinstance(value,str) and not value.startswith('.') else None
                if isinstance(value,str) and value.startswith('.'):
                    arg=n.args[1] if len(n.args)>1 else next((k.value for k in n.keywords if k.arg=='package'),None)
                    pkg=package if isinstance(arg,ast.Name) and arg.id=='__package__' else arg.value if isinstance(arg,ast.Constant) else None
                    if isinstance(pkg,str):
                        try:resolved=importlib.util.resolve_name(value,pkg)
                        except ImportError:pass
                dynamic.append(dict(module=name,line=n.lineno,literal=value,resolved=resolved))
                if resolved:targets=[resolved]
            for target in set(targets):
                top=target.split('.')[0]
                if target.startswith('actio.') and target.split('.')[1] in REMOVED:
                    reject(name,n.lineno,target,'removed root API dependency')
                if top in {'tests','tools','scripts','gateway_stub','chat_stub','readiness_stub','support'} or top.startswith('test_'):reject(name,n.lineno,target,'product depends on tests/tools')
                if target in files and target!=name:edges[name].add(target)
                if layer in PURE:
                    if target.startswith('actio.') and target.split('.')[1] not in PURE[layer]:reject(name,n.lineno,target,'pure layer dependency')
                    if top in {'sqlite3','subprocess','socket','os','deepseek_harness','concordia','importlib'} and not (top=='importlib' and isinstance(n,ast.ImportFrom) and n.module=='importlib' and all(a.name=='import_module' for a in n.names)):reject(name,n.lineno,target,'pure layer external I/O dependency')
                if layer in {'application','evidence'}:
                    if top in {'subprocess','sqlite3','deepseek_harness','concordia','mcp'} or target.startswith(('actio.adapters.runtime','actio.adapters.environment','actio.adapters.transport','actio.adapters.persistence','actio.interfaces')):reject(name,n.lineno,target,'use case/reader concrete runtime or persistence dependency')
                    if layer=='evidence' and target.startswith('actio.application'):reject(name,n.lineno,target,'reader depends on writer')
                if name=='actio.profiles.validation' and target.startswith('actio.') and target.split('.')[1] not in {'contracts','domain','tasks'}:reject(name,n.lineno,target,'profile validator dependency')
                if layer=='tasks' and name!='actio.tasks.registry' and target=='actio.tasks.registry':reject(name,n.lineno,target,'task leaf imports registry')
                other=group(target)
                if g in GROUPS and other in GROUPS and g!=other:groups[g].add(other)
    cycles=components(edges);group_cycles=components(groups)
    unresolved=[d for d in dynamic if d['resolved'] is None]
    return dict(rule_version=VERSION,status='PASS' if not (violations or cycles or group_cycles or unresolved) else 'INCOMPLETE',
        modules=len(files),edges=sum(map(len,edges.values())),strong_components=cycles,violations=violations,
        unmigrated_root_modules=extras,shims=[],dynamic_imports=dynamic,unresolved_dynamic_imports=unresolved,
        evidence_groups={k:sorted(v) for k,v in sorted(groups.items())},evidence_group_cycles=group_cycles,
        dependencies={k:sorted(v) for k,v in sorted(edges.items())},
        scope='All Python recursively including package init/local imports; unresolved dynamic imports require explicit review. Only evidence group projection is required acyclic; other parent projections are not claimed acyclic.')


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--root',type=Path);a=p.parse_args()
    value=inspect(a.root);a.output.write_text(json.dumps(value,indent=2),encoding='utf8')
    print(json.dumps({k:value[k] for k in ('status','modules','edges','strong_components','evidence_group_cycles','violations')}))
    raise SystemExit(0 if value['status']=='PASS' else 1)
