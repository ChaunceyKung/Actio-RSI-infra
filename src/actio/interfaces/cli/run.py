import argparse
import json
from pathlib import Path
import sys

from actio.contracts.json import ContractError
from actio.contracts.scenarios import UNSET


def main(argv=None):
    p=argparse.ArgumentParser(prog='actio',description='Single-host experiment and fixture infrastructure')
    p.add_argument('--settings',type=Path)
    p.add_argument('--db',type=Path)
    p.add_argument('--short-root',type=Path)
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('init'); sub.add_parser('capabilities')
    c=sub.add_parser('migrate'); c.add_argument('--output',required=True,type=Path)
    c=sub.add_parser('export'); c.add_argument('run'); c.add_argument('--output',required=True,type=Path)
    c=sub.add_parser('verify'); c.add_argument('bundle',type=Path)
    c=sub.add_parser('agent'); c.add_argument('id'); c.add_argument('--create',action='store_true')
    c=sub.add_parser('assistant'); c.add_argument('--agent',required=True); c.add_argument('--key',required=True)
    c=sub.add_parser('experiment'); c.add_argument('--key',required=True); c.add_argument('--config',type=Path,required=True)
    c=sub.add_parser('social'); c.add_argument('--a',required=True); c.add_argument('--b',required=True); c.add_argument('--key',required=True)
    c.add_argument('--memory-revision',type=int,default=UNSET); c.add_argument('--replay'); c.add_argument('--illegal',action='store_true',default=UNSET)
    c=sub.add_parser('task-card');c.add_argument('--variant',choices=['compatible','conflict'],required=True);c.add_argument('--a',required=True);c.add_argument('--b',required=True);c.add_argument('--output',required=True,type=Path)
    c=sub.add_parser('schedule');c.add_argument('--key',required=True);c.add_argument('--task',type=Path);c.add_argument('--script',type=Path);c.add_argument('--replay')
    c=sub.add_parser('query'); c.add_argument('run')
    c=sub.add_parser('reconcile'); c.add_argument('run'); c.add_argument('--recover-owner',action='store_true')
    c=sub.add_parser('memory'); c.add_argument('--agent',required=True); c.add_argument('--environment',choices=['assistant','social'],required=True)
    c.add_argument('--target',choices=['assistant','social']); c.add_argument('--revision',type=int)
    c=sub.add_parser('require'); c.add_argument('capability')
    args=p.parse_args(argv)
    store=None
    try:
        if args.command not in ('capabilities','require','verify') and (
                args.db is None or args.command in ('assistant','social','schedule') and args.short_root is None):
            from actio.profiles.settings import load_settings
            settings=load_settings(args.settings)
            args.db=args.db or settings.paths['database']
            args.short_root=args.short_root or settings.paths['runs']
            args.db.parent.mkdir(parents=True,exist_ok=True) if args.command=='init' else None
        if args.command in ('capabilities','require'):
            from actio.adapters.runtime.runtime import RuntimePort
        if args.command=='capabilities':
            result=RuntimePort.capabilities
        elif args.command=='require':
            RuntimePort.require(args.capability); result={'supported':True}
        elif args.command=='migrate':
            from actio.adapters.persistence.database import migrate_copy
            result=migrate_copy(args.db,args.output)
        elif args.command=='export':
            from actio.interfaces.export import export_bundle
            result=export_bundle(args.db,args.run,args.output)
        elif args.command=='verify':
            from actio.evidence.bundles.verify import verify_bundle
            result=verify_bundle(args.bundle)
            print(json.dumps(result,ensure_ascii=False,indent=2))
            return 2 if result['bundle_integrity']!='valid' or result['facts_consistency']=='invalid' else 0
        else:
            from actio.interfaces.store import Store
            if args.command in ('assistant','social','schedule'):
                from actio.application.scenarios import assistant
                from actio.application.scenarios import social
                from actio.application.scenarios import scheduling
            if args.command=='agent' and args.create:
                from actio.adapters.runtime.runtime import synthetic_spec
            readonly=args.command in ('query','task-card') or args.command=='agent' and not args.create
            store=Store(args.db,create=args.command=='init',readonly=readonly)
            match args.command:
                case 'init': result={'store':str(store.path),'initialized':True}
                case 'agent': result=store.agent(args.id,synthetic_spec(args.id) if args.create else None)
                case 'assistant': result=assistant(store,args.key,args.agent,args.short_root)
                case 'experiment':
                    from actio.application.experiment import experiment, validate_plan
                    from actio.interfaces.environments import resolve
                    from actio.contracts.json import parse
                    plan=validate_plan(parse(args.config.read_bytes()))
                    factory,identity=resolve(plan['environment'])
                    result=experiment(store,args.key,plan,environment_factory=factory,environment_identity=identity)
                case 'social': result=social(store,args.key,args.a,args.b,args.short_root,as_of=args.memory_revision,replay=args.replay,illegal=args.illegal)
                case 'task-card':
                    from actio.tasks.registry import task_card
                    from actio.adapters.filesystem.artifacts import publish
                    task=task_card(args.variant,{s:{'agent':a,'spec_hash':store.agent(a)['spec_hash']} for s,a in [('A',args.a),('B',args.b)]})
                    result={'task':str(publish(args.output,task)),'task_hash':task['sha256']}
                case 'schedule':
                    from actio.evidence.bundles.evaluation import read_json
                    result=scheduling(store,args.key,args.short_root,task=read_json(args.task) if args.task else UNSET,
                                      script=read_json(args.script) if args.script else UNSET,replay=args.replay)
                case 'query':
                    run=store.run(args.run)
                    result={'run':run,'operations':store.rows('SELECT * FROM operation WHERE run=?',(run['id'],)),
                            'streams':store.rows('SELECT * FROM stream WHERE run=?',(run['id'],)),
                            'world':store.rows('SELECT * FROM world WHERE run=?',(run['id'],)),
                            'schema_version':store.version,
                            'terminal':store.row('SELECT * FROM scenario_terminal WHERE run=?',(run['id'],)) if store.version else None,
                            'current_verification':'legacy_unverified' if not store.version else 'use offline verify; historical state is not a current certificate'}
                case 'reconcile':
                    from actio.adapters.runtime.facts import Facts
                    target=store.run(args.run)
                    recovery=store.recover(target['id']) if args.recover_owner else []
                    result={'recovery':recovery,'facts':Facts(store).reconcile(target['id']),'run':store.run(target['id'])}
                case 'memory':
                    from actio.application.memory import Memory
                    from actio.application.memory import namespace
                    result=Memory(store).retrieve(namespace(args.agent,args.environment),args.agent,target=args.target,as_of=args.revision)
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
