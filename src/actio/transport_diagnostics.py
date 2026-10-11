"""C5 read-only diagnostics and explicit local-only validation entry points."""
import json
import sys
from pathlib import Path
from actio.contracts.json import canonical, digest, ContractError
from actio.adapters.filesystem.common import file_hash
from actio.contracts.json import seal, unseal
from actio.contracts.json import require
from .failure_observation import observe,from_entry,parse,LIMITS
from .failure_fixtures import CASES,portable_vectors
from .future_schedule import plan as schedule

PACKAGE='transport-diagnostic-package.v1'
SUITE='transport-diagnostic-suite.v1'


def sources():
    root=Path(__file__).parent
    return {p.relative_to(root).as_posix():file_hash(p) for p in sorted(root.rglob('*')) if p.suffix in ('.py','.mjs','.sql','.json')}


def plan():
    return {'schema':'transport-diagnostic-plan.v1','cases':CASES,'maximum_loopback_sends':12,
        'new_external_requests':0,'limits':LIMITS,'future':schedule(),'sources':sources(),
        'credential_reads':0,'network_requests':0,'workers_started':0}


def portable(history=None,runtime=None):
    vectors=portable_vectors()
    return seal({'schema':PACKAGE,'scope':'synthetic recomputation and public projections; no historical/raw runtime authentication',
        'sources':sources(),'fixtures':vectors,'observations':[observe(v['input']) for v in vectors],
        'future':schedule(),'historical_projection':history,'runtime_projection':runtime,
        'projection_authentication':'hash integrity only; controlled originals require separate verification'})


def analyze(value):
    b=unseal(value)
    if b['schema']=='transport-failure-evidence.v1':return observe(value)
    if b['schema']=='transport-diagnostic-controlled-entry.v1':
        require(set(b)=={'schema','origin','entry'},'controlled entry fields')
        return {'observations':from_entry(b['entry'],b['origin']),'scope':'controlled source authentication'}
    require(b['schema']==PACKAGE,'unknown diagnostic schema')
    expected=portable(b.get('historical_projection'),b.get('runtime_projection'))
    require(value==expected,'portable package/fixture/source/result mismatch')
    return {'valid':True,'scope':b['scope'],'synthetic_vectors':len(b['fixtures']),
        'historical_raw_authenticated':False,'runtime_raw_authenticated':False,'future_hash':b['future']['sha256'],
        'credential_reads':0,'network_requests':0,'workers_started':0}


def read(path):
    p=Path(path);require(p.stat().st_size<=64*1024*1024,'package byte bound')
    return parse(p.read_text(encoding='utf8'),64*1024*1024)


def main():
    args=sys.argv[1:]
    try:
        require(bool(args),'command required')
        if args[0]=='plan':require(len(args)==1,'plan arguments');result=plan()
        elif args[0] in ('analyze','verify'):
            require(len(args)==2,'reader arguments');result=analyze(read(args[1]))
        elif args[0]=='export':
            require(len(args) in (2,3),'export NEW_DIRECTORY [CONTROLLED_ENTRY]')
            history=analyze(read(args[2])) if len(args)==3 else None
            value=portable(history);root=Path(args[1]);root.mkdir(parents=True,exist_ok=False)
            with (root/'package.json').open('x',encoding='utf8',newline='\n') as f:f.write(canonical(value))
            result={'valid':True,'package':str(root/'package.json'),'sha256':value['sha256']}
        elif args[0]=='run-local':
            import argparse
            p=argparse.ArgumentParser();p.add_argument('command');p.add_argument('--root',required=True,type=Path)
            p.add_argument('--project',type=Path);p.add_argument('--freeze',required=True,type=Path)
            a=p.parse_args(args)
            from .diagnostic_runtime import run
            result=run(a.root,a.project,a.freeze)
        else:raise ContractError('unknown diagnostic command; no live mode')
        print(canonical(result));return 2 if result.get('status') in ('FAIL','INCOMPLETE') else 0
    except (ContractError,OSError,ValueError,KeyError,TypeError,IndexError,AttributeError):
        # Untrusted message text and filesystem contents never enter error output.
        print(canonical({'valid':False,'error':'diagnostic input or execution rejected; inspect controlled receipts'}));return 2


if __name__=='__main__':raise SystemExit(main())
