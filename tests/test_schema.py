import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import unittest
from unittest.mock import patch
import uuid

from actio.contracts.json import ContractError
from actio.adapters.filesystem.common import file_hash
from actio.adapters.filesystem.common import write_json
from actio.adapters.filesystem.common import clean_env
from actio.contracts.json import canonical
from actio.contracts.json import digest
from actio.adapters.persistence import database as database
from actio.interfaces.store import Store


class Schema(unittest.TestCase):
    def setUp(self):
        self.root=(Path(__file__).resolve().parents[2]/'t')/uuid.uuid4().hex[:12]
        self.root.mkdir(parents=True)
        write_json(self.root/'owner.json',{'test':self.id()})
        self.evidence={'root':str(self.root),'mode':'SQLITE_MIGRATION_CONTRACT'}

    def legacy(self):
        path=self.root/'legacy.sqlite'
        db=sqlite3.connect(path,isolation_level=None)
        db.executescript(Path(database.__file__).with_name('legacy_schema.sql').read_text())
        db.execute("INSERT INTO meta VALUES('store','legacy-synthetic')")
        db.execute("PRAGMA wal_autocheckpoint=0")
        db.execute("INSERT INTO agent VALUES('OLD','original-pin','original-spec')")
        db.execute("INSERT INTO run VALUES('legacy','key','old-input-hash','{}',1,'execution_complete','success','complete',NULL,0,123,'birth',1)")
        return path,db

    def test_process_interruption_before_version_commit_retains_backup(self):
        path,db=self.legacy();out=self.root/'interrupted.sqlite'
        code='''import os,sys
from actio.adapters.persistence import database
original=database.inspect
def crash(db):
    if db.execute('PRAGMA user_version').fetchone()[0]==2:os._exit(85)
    return original(db)
database.inspect=crash
database.migrate_copy(sys.argv[1],sys.argv[2])
'''
        try:
            command=[sys.executable,'-c',code,str(path),str(out)]
            p=subprocess.run(command,env=clean_env(self.root),capture_output=True,text=True,timeout=20)
            self.assertEqual(p.returncode,85,p.stderr);self.assertFalse(out.exists())
            backup=out.with_name(out.name+'.backup.sqlite')
            with sqlite3.connect(backup) as conn:
                self.assertEqual(conn.execute('SELECT spec FROM agent').fetchone()[0],'original-spec')
                self.assertEqual(conn.execute('PRAGMA user_version').fetchone()[0],0)
            stage=next(p for p in self.root.glob('interrupted.sqlite.migrating-*') if p.suffix!='.sqlite-journal' and not p.name.endswith('-journal'))
            with sqlite3.connect(stage) as conn:
                self.assertEqual(conn.execute('PRAGMA user_version').fetchone()[0],0)
            self.evidence['crash']={'exit_code':p.returncode,'command':command,'backup_sha256':file_hash(backup),'mode':'REAL_MIGRATION_PROCESS_EXIT_BEFORE_COMMIT'}
        finally:db.close()

    def test_migration_preserves_incompatible_spec_and_execution_refuses_it(self):
        from actio.adapters.runtime.runtime import synthetic_spec
        from actio.application.scenarios import assistant
        path,db=self.legacy();out=self.root/'old-spec.sqlite'
        spec=synthetic_spec('OLD');spec['pins']['code']={'historic.py':'old-source-pin'}
        db.execute('UPDATE agent SET spec=?,spec_hash=?',(canonical(spec),digest(spec)));db.close()
        database.migrate_copy(path,out)
        s=Store(out)
        try:
            before=s.agent('OLD')
            with self.assertRaisesRegex(ContractError,'pins changed'):
                assistant(s,'new-attempt','OLD',self.root)
            self.assertEqual(s.agent('OLD'),before)
            self.assertEqual(s.rows('SELECT * FROM worker'),[])
        finally:s.close()

    def test_wal_backup_copy_preserves_all_old_rows_and_repeated_migration(self):
        path,db=self.legacy()
        try:
            self.assertTrue(Path(str(path)+'-wal').is_file())
            old_tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            old={t:db.execute('SELECT * FROM '+t).fetchall() for t in old_tables}
            out=self.root/'copy.sqlite';r=database.migrate_copy(path,out)
            with sqlite3.connect(out) as copy:
                self.assertEqual(copy.execute('PRAGMA user_version').fetchone()[0],2)
                self.assertEqual({t:copy.execute('SELECT * FROM '+t).fetchall() for t in old_tables},old)
                self.assertEqual(copy.execute('SELECT * FROM scenario_terminal').fetchall(),[])
            with sqlite3.connect(r['backup']) as backup:
                self.assertEqual({t:backup.execute('SELECT * FROM '+t).fetchall() for t in old_tables},old)
                self.assertEqual(backup.execute('PRAGMA user_version').fetchone()[0],0)
            h=file_hash(out)
            again=database.migrate_copy(path,out)
            self.assertEqual(again['status'],'already_migrated');self.assertEqual(h,file_hash(out))
            with self.assertRaisesRegex(ContractError,'legacy'):
                Store(path)
            s=Store(path,readonly=True)
            self.assertEqual(s.run('legacy')['trajectory'],'complete');s.close()
            self.evidence['migration']=r
        finally:db.close()

    def test_failure_rolls_back_copy_and_preserves_recoverable_backup(self):
        path,db=self.legacy();out=self.root/'failed.sqlite'
        real=database.inspect
        def reject_new(conn):
            if conn.execute('PRAGMA user_version').fetchone()[0]==2:
                raise RuntimeError('injected after DDL before commit')
            return real(conn)
        try:
            with patch('actio.adapters.persistence.database.inspect',side_effect=reject_new):
                with self.assertRaisesRegex(RuntimeError,'injected'):
                    database.migrate_copy(path,out)
            self.assertFalse(out.exists())
            report=json.loads(out.with_name(out.name+'.migration.json').read_text())
            self.assertEqual(report['status'],'failed')
            with sqlite3.connect(report['backup']) as b:
                self.assertEqual(b.execute('SELECT spec FROM agent').fetchone()[0],'original-spec')
            with sqlite3.connect(report['retained_stage']) as b:
                self.assertEqual(b.execute('PRAGMA user_version').fetchone()[0],0)
                self.assertFalse(b.execute("SELECT name FROM sqlite_master WHERE name='scenario_terminal'").fetchone())
            self.evidence['failure']=report
        finally:db.close()

    def test_future_incomplete_missing_queries_never_create_or_write(self):
        missing=self.root/'absent.sqlite'
        with self.assertRaisesRegex(ContractError,'missing'):
            Store(missing,readonly=True)
        self.assertFalse(missing.exists())
        path,db=self.legacy();db.execute('PRAGMA user_version=99');db.close()
        h=file_hash(path)
        for readonly in (True,False):
            with self.assertRaisesRegex(ContractError,'unsupported'):
                Store(path,readonly=readonly)
        self.assertEqual(h,file_hash(path))
        with sqlite3.connect(path) as db:
            db.execute('PRAGMA user_version=0');db.execute('DROP TABLE world')
        h=file_hash(path)
        with self.assertRaisesRegex(ContractError,'incomplete'):
            Store(path,readonly=True)
        self.assertEqual(h,file_hash(path))
