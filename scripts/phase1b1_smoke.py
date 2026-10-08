"""Public CLI smoke in an already bootstrapped clean environment; synthetic only."""
import datetime
import argparse
import json
from pathlib import Path
import platform
import sqlite3
import subprocess
import sys

from actio.common import clean_env,file_hash,write_json
from actio.runtime import pins,verify_runtime
from actio.supervisor import owned_root

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/validation/phase1b1'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bootstrap-log',type=Path)
    args=parser.parse_args()
    root=owned_root(Path('D:/actio-p1b1-demo'),'phase1b1-public-cli-smoke')
    env=clean_env(root);db=root/'ledger.sqlite';commands=[]
    def cli(*args,code=0,database=db):
        command=[sys.executable,'-m','actio','--db',str(database),'--short-root',str(root),*map(str,args)]
        p=subprocess.run(command,capture_output=True,text=True,encoding='utf8',env=env,timeout=90)
        commands.append({'command':command,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        assert p.returncode==code,p.stderr
        return json.loads(p.stdout) if p.stdout else None
    status='FAIL'
    try:
        verify_runtime()
        cli('init')
        for who in ('A','B'):cli('agent',who,'--create')
        a=cli('assistant','--agent','A','--key','assistant-one')
        social=cli('social','--a','A','--b','B','--key','social-one','--memory-revision','1')
        replay=cli('social','--a','A','--b','B','--key','replay-one','--replay','social-one')
        rejected=cli('social','--a','A','--b','B','--key','rejected','--illegal')
        assert a['task']==social['task']==replay['task']=='success' and rejected['task']=='task_failure'
        before=cli('query','social-one')
        for extra in (['--illegal'],['--memory-revision','0']):
            cli('social','--a','A','--b','B','--key','bad-replay','--replay','social-one',*extra,code=2)
        assert before==cli('query','social-one')
        cli('reconcile','assistant-one')
        package=root/'social-bundle'
        exported=cli('export','social-one','--output',package)
        verified=cli('verify',package)
        assert verified==exported['verification'] and verified['scenario_completeness']=='complete'
        command=[sys.executable,'-m','actio.verify',str(package)]
        p=subprocess.run(command,capture_output=True,text=True,env=env,timeout=15)
        commands.append({'command':command,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        assert p.returncode==0 and json.loads(p.stdout)==verified
        absent=root/'absent.sqlite';cli('query','missing',code=2,database=absent);assert not absent.exists()
        legacy=root/'legacy.sqlite'
        src=sqlite3.connect(db);dest=sqlite3.connect(legacy);src.backup(dest);src.close()
        for table in ('request_identity','scenario_terminal','migration'):dest.execute('DROP TABLE '+table)
        dest.execute('PRAGMA user_version=0');dest.commit();dest.close()
        q=cli('query','social-one',database=legacy);assert q['current_verification']=='legacy_unverified'
        copy=root/'migrated.sqlite'
        cli('migrate','--output',copy,database=legacy)
        cli('migrate','--output',copy,database=legacy)
        legacy_export=cli('export','social-one','--output',root/'legacy-bundle',database=copy)
        assert legacy_export['verification']['scenario_completeness']=='legacy_unverified'
        p=subprocess.run([sys.executable,'-m','pip','--isolated','check'],capture_output=True,text=True,env=env)
        commands.append({'command':[sys.executable,'-m','pip','--isolated','check'],'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        assert p.returncode==0
        status='PASS'
    finally:
        workers=[]
        if db.exists():
            conn=sqlite3.connect(db);conn.row_factory=sqlite3.Row
            workers=[dict(w) for w in conn.execute('SELECT * FROM worker')];conn.close()
        if status=='PASS':assert all(json.loads(w['report'])['after']['active']==0 for w in workers)
        stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        data={'status':status,'exit_code':0 if status=='PASS' else 1,'mode':'CLEAN_INSTALL_PUBLIC_CLI_REAL_ENGINE_DSH_FIXTURE',
              'platform':platform.platform(),'python':sys.version,'root':str(root),'pins':pins(),'commands':commands,'workers':workers,
              'bootstrap_log':str(args.bootstrap_log.resolve()) if args.bootstrap_log else None,
              'bootstrap_log_sha256':file_hash(args.bootstrap_log) if args.bootstrap_log else None,
              'bootstrap_command':'.local/venv/Scripts/python.exe -X utf8 scripts/bootstrap.py --venv '+Path(sys.executable).parents[1].relative_to(ROOT).as_posix()+' --offline-wheels --concordia-source ../../codebase/15_concordia/repo',
              'network':'No index/network used in this preparation; 41 cached locked wheels and read-only fixed local Git archive',
              'source_hashes':{p.relative_to(ROOT).as_posix():file_hash(p) for folder in ('src','scripts') for p in (ROOT/folder).rglob('*') if p.suffix in ('.py','.mjs','.sql','.json')}}
        path=DOC/'evidence'/('smoke-'+stamp+'.json');path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
        print(status,path)


if __name__=='__main__':main()
