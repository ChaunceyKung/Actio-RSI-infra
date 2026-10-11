"""AST architecture census: includes function-local imports, never suppresses legacy cycles."""
import ast
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
PURE={'contracts':set(), 'domain':{'contracts'}, 'tasks':{'contracts','domain','tasks'}, 'measurement':{'contracts','domain','tasks','measurement'}}

def inspect(root=None):
    root=Path(root) if root else ROOT/'src/actio'
    source_root=root.parent
    files={'.'.join(p.relative_to(source_root).with_suffix('').parts).removesuffix('.__init__'):p for p in root.rglob('*.py')}
    edges={name:set() for name in files};violations=[];dynamic=[]
    shims={name for name,p in files.items() if p.parent==root and p.read_text(encoding='utf8').startswith('"""Compatibility')}
    for name,p in files.items():
        tree=ast.parse(p.read_text(encoding='utf8'));package=name if p.name=='__init__.py' else name.rsplit('.',1)[0]
        layer=name.split('.')[1] if '.' in name else ''
        for n in ast.walk(tree):
            targets=[]
            if isinstance(n,ast.Import):targets=[a.name for a in n.names]
            if isinstance(n,ast.ImportFrom):
                base='.'.join(package.split('.')[:len(package.split('.'))-n.level+1]) if n.level else ''
                base='.'.join(x for x in (base,n.module) if x)
                targets=[base+'.'+a.name if base+'.'+a.name in files else base for a in n.names]
            if isinstance(n,ast.Call) and (isinstance(n.func,ast.Name) and n.func.id in ('__import__','import_module') or isinstance(n.func,ast.Attribute) and n.func.attr=='import_module'):
                value=n.args[0].value if n.args and isinstance(n.args[0],ast.Constant) else None
                dynamic.append({'module':name,'line':n.lineno,'literal':value})
                if isinstance(value,str):targets.append(value)
            for target in targets:
                if target.startswith(('tests','scripts','test_','gateway_stub','chat_stub')):violations.append({'module':name,'line':n.lineno,'target':target,'reason':'product depends on tests/tools'})
                if target in files and target!=name:edges[name].add(target)
                if target in shims and name not in shims:violations.append({'module':name,'line':n.lineno,'target':target,'reason':'implementation depends on compatibility shim'})
                if layer in PURE and target.startswith('actio.') and target.split('.')[1] not in PURE[layer]:violations.append({'module':name,'line':n.lineno,'target':target,'reason':'pure layer dependency'})
    index={};low={};stack=[];on=set();components=[]
    def visit(v):
        index[v]=low[v]=len(index);stack.append(v);on.add(v)
        for w in sorted(edges[v]):
            if w not in index:visit(w);low[v]=min(low[v],low[w])
            elif w in on:low[v]=min(low[v],index[w])
        if low[v]==index[v]:
            c=[]
            while True:
                w=stack.pop();on.remove(w);c.append(w)
                if w==v:break
            if len(c)>1:components.append(sorted(c))
    for v in sorted(edges):
        if v not in index:visit(v)
    flat=[n for n,p in files.items() if p.parent==root and n not in shims and p.name not in ('__init__.py','__main__.py')]
    groups={'audit':{'stream_audit','channel_audit','transport_contract','accounting'},'bundles':{'task_evidence','terminal','verify','eval_contract','evaluation'},'campaigns':{'transport_campaign','pilot_measurement','suite_measurement','candidate_measurement','evaluation_measurement','robustness_measurement','campaign_registry','campaign','calibration'},'lineage':{'candidate_lineage','evaluation_history','evaluation_lineage','candidate','candidate_evaluation','robustness'},'diagnostics':{'failure_observation','failure_fixtures','future_schedule','task_diagnostics','transport_diagnostics'}}
    group_edges={g:set() for g in groups}
    for name,targets in edges.items():
        current=name.split('.')[2] if name.startswith('actio.evidence.') and len(name.split('.'))>3 else None
        if current:
            for target in targets:
                other=target.split('.')[2] if target.startswith('actio.evidence.') and len(target.split('.'))>3 else None
                if other and other!=current: group_edges[current].add(other)
    group_cycles=[]
    def walk(node, path):
        if node in path:
            group_cycles.append(path[path.index(node):]+[node]); return
        for nxt in group_edges[node]: walk(nxt, path+[node])
    for node in groups: walk(node, [])
    return {'status':'PASS' if not violations and not components and not flat and not group_cycles else 'INCOMPLETE', 'modules':len(files),'edges':sum(map(len,edges.values())),
            'violations':violations,'strong_components':sorted(components,key=lambda c:(-len(c),c)),'unmigrated_root_modules':sorted(flat),
            'shims':sorted(shims),'dynamic_imports':dynamic,'evidence_groups':{k:sorted(v) for k,v in group_edges.items()},'evidence_group_cycles':group_cycles,'dependencies':{n:sorted(v) for n,v in sorted(edges.items())},
            'scope':'all current Python including local imports; no ignored subgraph; package target DAG still required'}

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('output');ap.add_argument('--root',type=Path)
    args=ap.parse_args(); value=inspect(args.root);Path(args.output).write_text(json.dumps(value,indent=2),encoding='utf8');print(json.dumps({k:value[k] for k in ('status','modules','edges','strong_components')}))
    raise SystemExit(0 if value['status']=='PASS' else 1)
