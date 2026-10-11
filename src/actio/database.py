"""One known legacy schema, explicit creation and copy-only migration. No runtime imports."""
import json
import os
from pathlib import Path
import sqlite3

from actio.contracts.json import ContractError
from actio.adapters.filesystem.common import file_hash, uid, write_json

VERSION = 2


def connect(path, *, readonly=False):
    path = Path(path).resolve()
    if not path.is_file():
        raise ContractError('database missing; use init explicitly')
    db = sqlite3.connect(path.as_uri() + ('?mode=ro' if readonly else '?mode=rw'),
                         uri=True, timeout=10, isolation_level=None)
    db.row_factory = sqlite3.Row
    return db


def structure(db):
    return [(r[0], r[1], ' '.join(r[2].split())) for r in db.execute(
        "SELECT type,name,sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' ORDER BY type,name")]


def inspect(db):
    version = db.execute('PRAGMA user_version').fetchone()[0]
    if version not in (0, VERSION, 3, 4):
        raise ContractError('unsupported database schema version: ' + str(version))
    with sqlite3.connect(':memory:') as expected:
        expected.executescript(Path(__file__).with_name('legacy_schema.sql' if version == 0 else 'schema.sql').read_text())
        if version in (3,4):
            expected.executescript(Path(__file__).with_name('candidate_schema.sql').read_text())
        if version == 4:
            expected.executescript(Path(__file__).with_name('evaluation_schema.sql').read_text())
        if structure(db) != structure(expected):
            raise ContractError('unknown or incomplete database structure')
    if not db.execute("SELECT value FROM meta WHERE key='store'").fetchone():
        raise ContractError('database store identity missing')
    return version


def migrate_evaluation_copy(source, destination):
    """Copy v3 facts and attach a historical evaluation; original is read-only."""
    import json
    from actio.contracts.json import canonical, digest
    from .store import Store
    from . import evaluation_store as evaluation
    from .evaluation_campaign import LEGACY_READER, baseline, candidate
    source,destination=Path(source).resolve(),Path(destination).resolve()
    backup=destination.with_name(destination.name+'.backup.sqlite')
    record=destination.with_name(destination.name+'.migration.json')
    stage=destination.with_name(destination.name+'.migrating-'+uid())
    if source==destination or any(p.exists() for p in (destination,backup,record)):
        raise ContractError('new evaluation migration destination required')
    src=Store(source,readonly=True)
    try:
        if src.version!=3 or src.db.execute('PRAGMA quick_check').fetchone()[0]!='ok':
            raise ContractError('evaluation migration requires intact v3')
        old=src.candidate_lineage();before=file_hash(source)
        with backup.open('xb'):pass
        saved=sqlite3.connect(backup)
        try:src.db.backup(saved);saved.execute('PRAGMA journal_mode=DELETE')
        finally:saved.close()
        target=sqlite3.connect(stage,isolation_level=None)
        saved=connect(backup,readonly=True)
        try:
            saved.backup(target)
            target.executescript('BEGIN IMMEDIATE;\n'+Path(__file__).with_name('evaluation_schema.sql').read_text()+'\nCOMMIT;')
            inspect(target)
        finally:target.close();saved.close()
        result={'from':3,'to':4,'source':str(source),'destination':str(destination),
            'source_sha256':before,'backup_sha256':file_hash(backup),'legacy_lineage_hash':old['sha256'],'reader':LEGACY_READER}
        target=Store(stage)
        try:
            with target.tx():
                target.db.execute('INSERT INTO evaluation_migration VALUES(1,?)',(canonical(result),))
                body={'schema':'historical-evaluation-reference.v1','id':evaluation.LEGACY_ID,'evidence_kind':'local_fixture','reader':LEGACY_READER,'lineage_hash':old['sha256']}
                target.db.execute('INSERT INTO evaluation VALUES(?,?)',(evaluation.LEGACY_ID,canonical(body)))
                for role,proposal in [('baseline',baseline()),('candidate',candidate())]:
                    cid=digest(proposal)
                    binding={'legacy_binding':target.row('SELECT * FROM campaign_binding WHERE candidate=?',(cid,)),
                             'legacy_decision':target.row('SELECT * FROM decision WHERE candidate=?',(cid,))}
                    if any(v is None for v in binding.values()):raise ContractError('old assessment missing')
                    target.db.execute('INSERT INTO evaluation_binding VALUES(?,?,?,?)',(evaluation.LEGACY_ID,cid,role,canonical(binding)))
                evaluation.event(target,evaluation.LEGACY_ID,'imported',{'legacy_lineage_hash':old['sha256']})
            evaluation.export(target)
            target.db.execute('PRAGMA wal_checkpoint(TRUNCATE)');target.db.execute('PRAGMA journal_mode=DELETE')
        finally:target.close()
        if file_hash(source)!=before or src.candidate_lineage()!=old:raise ContractError('source changed during migration')
        stage.rename(destination);write_json(record,{'status':'migrated',**result});return result
    except BaseException as error:
        if backup.exists():write_json(record,{'status':'failed','reason':str(error),'backup':str(backup),'retained_stage':str(stage)})
        raise
    finally:src.close()


def snapshot_evaluation_copy(source, destination):
    """Consistent schema4 SQLite backup, preserving WAL-visible rows and old facts."""
    from actio.contracts.json import digest
    from .store import Store
    from .evaluation_history import lineage as historical
    source,destination=Path(source).resolve(),Path(destination).resolve()
    backup=destination.with_name(destination.name+'.backup.sqlite')
    record=destination.with_name(destination.name+'.snapshot.json')
    stage=destination.with_name(destination.name+'.copying-'+uid())
    if source==destination or any(p.exists() for p in (destination,backup,record)):
        raise ContractError('new snapshot destination required; previous attempts retained')
    src=Store(source,readonly=True)
    def files():
        return {p.name:file_hash(p) for p in (source,Path(str(source)+'-wal')) if p.exists()}
    try:
        if src.version!=4 or src.db.execute('PRAGMA quick_check').fetchone()[0]!='ok':
            raise ContractError('intact schema4 required')
        before=files();old=src.evaluation_lineage()
        if old!=historical():raise ContractError('source is not authenticated C2C2 authority')
        with backup.open('xb'):pass
        saved=sqlite3.connect(backup)
        try:src.db.backup(saved);saved.execute('PRAGMA journal_mode=DELETE')
        finally:saved.close()
        saved=connect(backup,readonly=True);target=sqlite3.connect(stage,isolation_level=None)
        try:
            saved.backup(target)
            if inspect(target)!=4 or list(saved.iterdump())!=list(target.iterdump()):
                raise ContractError('snapshot semantic mismatch')
            semantic=digest(list(saved.iterdump()))
        finally:target.close();saved.close()
        check=Store(stage,readonly=True)
        try:
            if check.evaluation_lineage()!=old:raise ContractError('snapshot lineage changed')
        finally:check.close()
        if files()!=before or src.evaluation_lineage()!=old:raise ContractError('source changed during backup')
        stage.rename(destination)
        result={'status':'copied','from':4,'to':4,'source':str(source),'destination':str(destination),
                'source_files_before':before,'source_files_after':files(),'backup_sha256':file_hash(backup),
                'snapshot_semantic_hash':semantic,'lineage_hash':old['sha256'],'all_rows_equal':True,'source_unchanged':True}
        write_json(record,result);return result
    except BaseException as error:
        if backup.exists():write_json(record,{'status':'failed','reason':str(error),'backup':str(backup),'retained_stage':str(stage)})
        raise
    finally:src.close()


def create(path, *, lineage=False):
    path = Path(path).resolve()
    # Exclusive reservation distinguishes initialization from accidental lookup.
    with path.open('xb'):
        pass
    db = sqlite3.connect(path, isolation_level=None)
    try:
        db.executescript(Path(__file__).with_name('schema.sql').read_text())
        if lineage:
            db.executescript(Path(__file__).with_name('candidate_schema.sql').read_text())
        db.execute("INSERT INTO meta VALUES('store',?)", (uid(),))
    finally:
        db.close()


def migrate_copy(source, destination):
    """Never mutate the original DB, including its historical claims and pins."""
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if source == destination:
        raise ContractError('migration requires a new copy destination')
    src = connect(source, readonly=True)
    backup = destination.with_name(destination.name + '.backup.sqlite')
    record = destination.with_name(destination.name + '.migration.json')
    stage = destination.with_name(destination.name + '.migrating-' + uid())
    try:
        version = inspect(src)
        if version != 0:
            raise ContractError('migration only supports known Phase 1B version 0')
        if destination.exists():
            # Idempotency is for the same immutable snapshot, never overwrite a copy.
            old = connect(destination, readonly=True)
            try:
                inspect(old)
                row = old.execute('SELECT * FROM migration WHERE id=1').fetchone()
                if not row or not backup.is_file() or row['backup_hash'] != file_hash(backup):
                    raise ContractError('destination is not a verified migration copy')
                check = sqlite3.connect(':memory:')
                try:
                    src.backup(check)
                    saved = connect(backup, readonly=True)
                    try:
                        # Content comparison includes every old table and WAL-visible row.
                        if list(check.iterdump()) != list(saved.iterdump()):
                            raise ContractError('source changed since migration; choose new destination')
                    finally:
                        saved.close()
                finally:
                    check.close()
                return {'status': 'already_migrated', 'destination': str(destination), 'backup_sha256': row['backup_hash']}
            finally:
                old.close()
        if backup.exists() or record.exists():
            raise ContractError('prior migration attempt retained; choose new destination')
        with backup.open('xb'):
            pass
        copy = sqlite3.connect(backup)
        try:
            src.backup(copy, pages=256)
            copy.execute('PRAGMA journal_mode=DELETE')
        finally:
            copy.close()
        h = file_hash(backup)
        result = {'source': str(source), 'destination': str(destination), 'backup': str(backup),
                  'backup_sha256': h, 'from': 0, 'to': VERSION, 'status': 'backup_complete'}
        write_json(record, result)
        saved = connect(backup, readonly=True)
        target = sqlite3.connect(stage, isolation_level=None)
        try:
            saved.backup(target)
            target.execute('PRAGMA foreign_keys=ON')
            target.execute('BEGIN IMMEDIATE')
            for sql in Path(__file__).with_name('schema.sql').read_text().split(';'):
                if any(name in sql for name in ('request_identity', 'scenario_terminal', 'CREATE TABLE IF NOT EXISTS migration')):
                    target.execute(sql)
            target.execute('INSERT INTO migration VALUES(1,0,?,?,?)',
                           (VERSION, h, target.execute("SELECT value FROM meta WHERE key='store'").fetchone()[0]))
            target.execute('PRAGMA user_version=2')
            inspect(target)
            target.commit()
            target.execute('PRAGMA journal_mode=DELETE')
        except BaseException:
            target.rollback()
            raise
        finally:
            target.close()
            saved.close()
        # Windows rename refuses an existing destination; no replacement of user data.
        stage.rename(destination)
        result['status'] = 'migrated'
        write_json(record, result)
        return result
    except BaseException as error:
        if backup.exists() and not destination.exists():
            write_json(record, {'status': 'failed', 'reason': str(error), 'backup': str(backup),
                                'backup_sha256': file_hash(backup), 'retained_stage': str(stage)})
        raise
    finally:
        src.close()


def migrate_lineage_copy(source, destination):
    """Explicit v2 -> v3 snapshot with backup; never upgrade an old run in place."""
    source, destination = Path(source).resolve(), Path(destination).resolve()
    backup = destination.with_name(destination.name + '.backup.sqlite')
    record = destination.with_name(destination.name + '.migration.json')
    stage = destination.with_name(destination.name + '.migrating-' + uid())
    if source == destination or any(p.exists() for p in (destination,backup,record)):
        raise ContractError('new lineage migration destination required')
    src = connect(source, readonly=True)
    try:
        if inspect(src) != 2: raise ContractError('lineage migration requires v2')
        with backup.open('xb'): pass
        saved = sqlite3.connect(backup)
        try: src.backup(saved); saved.execute('PRAGMA journal_mode=DELETE')
        finally: saved.close()
        saved = connect(backup, readonly=True); target = sqlite3.connect(stage, isolation_level=None)
        try:
            saved.backup(target)
            target.executescript('BEGIN IMMEDIATE;\n' + Path(__file__).with_name('candidate_schema.sql').read_text() + '\nCOMMIT;')
            inspect(target); target.execute('PRAGMA journal_mode=DELETE')
        finally: target.close(); saved.close()
        stage.rename(destination)
        result={'status':'migrated','from':2,'to':3,'backup_sha256':file_hash(backup),'source':str(source),'destination':str(destination)}
        write_json(record,result); return result
    except BaseException as error:
        if backup.exists():
            write_json(record,{'status':'failed','reason':str(error),'backup':str(backup),
                               'backup_sha256':file_hash(backup),'retained_stage':str(stage)})
        raise
    finally: src.close()
