"""One known legacy schema, explicit creation and copy-only migration. No runtime imports."""
import json
import os
from pathlib import Path
import sqlite3

from .common import ContractError, file_hash, uid, write_json

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
    if version not in (0, VERSION):
        raise ContractError('unsupported database schema version: ' + str(version))
    with sqlite3.connect(':memory:') as expected:
        expected.executescript(Path(__file__).with_name('legacy_schema.sql' if version == 0 else 'schema.sql').read_text())
        if structure(db) != structure(expected):
            raise ContractError('unknown or incomplete database structure')
    if not db.execute("SELECT value FROM meta WHERE key='store'").fetchone():
        raise ContractError('database store identity missing')
    return version


def create(path):
    path = Path(path).resolve()
    # Exclusive reservation distinguishes initialization from accidental lookup.
    with path.open('xb'):
        pass
    db = sqlite3.connect(path, isolation_level=None)
    try:
        db.executescript(Path(__file__).with_name('schema.sql').read_text())
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
