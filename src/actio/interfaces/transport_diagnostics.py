from actio.evidence.transport_diagnostics import analyze, plan, portable, read
import sys
from pathlib import Path
from actio.contracts.json import canonical
from actio.contracts.json import ContractError
from actio.contracts.json import require
PACKAGE='transport-diagnostic-package.v2-refactor'
SUITE='transport-diagnostic-suite.v1'

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
            from actio.application.diagnostic_runtime import run
            from actio.interfaces.store import Store
            from actio.interfaces.wiring import diagnostic_ports
            result=run(a.root,a.project,a.freeze,store_factory=Store,ports=diagnostic_ports())
        else:raise ContractError('unknown diagnostic command; no live mode')
        print(canonical(result));return 2 if result.get('status') in ('FAIL','INCOMPLETE') else 0
    except (ContractError,OSError,ValueError,KeyError,TypeError,IndexError,AttributeError):
        # Untrusted message text and filesystem contents never enter error output.
        print(canonical({'valid':False,'error':'diagnostic input or execution rejected; inspect controlled receipts'}));return 2
