import argparse
import json
from pathlib import Path
import sys

from .common import ContractError
from .facts import Facts
from .memory import Memory,namespace
from .runtime import RuntimePort,synthetic_spec
from .scenarios import assistant,social
from .store import Store


def main(argv=None):
    p=argparse.ArgumentParser(prog='actio',description='Windows single-host synthetic fixture infrastructure; no live provider')
    p.add_argument('--db',type=Path,default=Path('actio.sqlite'))
    p.add_argument('--short-root',type=Path,default=Path('D:/actio-p1b'))
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('init'); sub.add_parser('capabilities')
    c=sub.add_parser('agent'); c.add_argument('id'); c.add_argument('--create',action='store_true')
    c=sub.add_parser('assistant'); c.add_argument('--agent',required=True); c.add_argument('--key',required=True)
    c=sub.add_parser('social'); c.add_argument('--a',required=True); c.add_argument('--b',required=True); c.add_argument('--key',required=True)
    c.add_argument('--memory-revision',type=int); c.add_argument('--replay'); c.add_argument('--illegal',action='store_true')
    c=sub.add_parser('query'); c.add_argument('run')
    c=sub.add_parser('reconcile'); c.add_argument('run'); c.add_argument('--recover-owner',action='store_true')
    c=sub.add_parser('memory'); c.add_argument('--agent',required=True); c.add_argument('--environment',choices=['assistant','social'],required=True)
    c.add_argument('--target',choices=['assistant','social']); c.add_argument('--revision',type=int)
    c=sub.add_parser('require'); c.add_argument('capability')
    args=p.parse_args(argv)
    store=None
    try:
        if args.command=='capabilities':
            result=RuntimePort.capabilities
        elif args.command=='require':
            RuntimePort.require(args.capability); result={'supported':True}
        else:
            store=Store(args.db)
            match args.command:
                case 'init': result={'store':str(store.path),'initialized':True}
                case 'agent': result=store.agent(args.id,synthetic_spec(args.id) if args.create else None)
                case 'assistant': result=assistant(store,args.key,args.agent,args.short_root)
                case 'social': result=social(store,args.key,args.a,args.b,args.short_root,as_of=args.memory_revision,replay=args.replay,illegal=args.illegal)
                case 'query':
                    run=store.run(args.run)
                    result={'run':run,'operations':store.rows('SELECT * FROM operation WHERE run=?',(run['id'],)),
                            'streams':store.rows('SELECT * FROM stream WHERE run=?',(run['id'],)),
                            'world':store.rows('SELECT * FROM world WHERE run=?',(run['id'],))}
                case 'reconcile':
                    recovery=store.recover() if args.recover_owner else []
                    result={'recovery':recovery,'facts':Facts(store).reconcile(store.run(args.run)['id']),'run':store.run(args.run)}
                case 'memory': result=Memory(store).retrieve(namespace(args.agent,args.environment),args.agent,target=args.target,as_of=args.revision)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (ContractError,TimeoutError) as e:
        print(json.dumps({'error':type(e).__name__,'reason':str(e)},ensure_ascii=False),file=sys.stderr)
        return 2
    finally:
        if store:
            store.close()


if __name__=='__main__':
    raise SystemExit(main())
