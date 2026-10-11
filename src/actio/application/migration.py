from pathlib import Path
from actio.contracts.json import ContractError
from actio.adapters.filesystem.common import file_hash
from actio.adapters.filesystem.common import uid
from actio.adapters.filesystem.common import write_json
VERSION = 2

def migrate_evaluation_copy(source, destination, *, store_factory, storage):
    """Copy v3 facts and attach a historical evaluation; original is read-only."""
    import json
    from actio.contracts.json import canonical
    from actio.contracts.json import digest
    from actio.application import evaluation_store as evaluation
    from actio.profiles.evaluation_campaign import LEGACY_READER
    from actio.profiles.evaluation_campaign import baseline
    from actio.profiles.evaluation_campaign import candidate
    source,destination=Path(source).resolve(),Path(destination).resolve()
    backup=destination.with_name(destination.name+'.backup.sqlite')
    record=destination.with_name(destination.name+'.migration.json')
    stage=destination.with_name(destination.name+'.migrating-'+uid())
    if source==destination or any(p.exists() for p in (destination,backup,record)):
        raise ContractError('new evaluation migration destination required')
    src=store_factory(source,readonly=True)
    try:
        if src.version!=3 or src.db.execute('PRAGMA quick_check').fetchone()[0]!='ok':
            raise ContractError('evaluation migration requires intact v3')
        old=src.candidate_lineage();before=file_hash(source)
        with backup.open('xb'):pass
        saved=storage.connect(backup)
        try:src.db.backup(saved);saved.execute('PRAGMA journal_mode=DELETE')
        finally:saved.close()
        target=storage.connect(stage,isolation_level=None)
        saved=storage.open_existing(backup,readonly=True)
        try:
            saved.backup(target)
            target.executescript('BEGIN IMMEDIATE;\n'+storage.schema('evaluation_schema.sql')+'\nCOMMIT;')
            storage.inspect(target)
        finally:target.close();saved.close()
        result={'from':3,'to':4,'source':str(source),'destination':str(destination),
            'source_sha256':before,'backup_sha256':file_hash(backup),'legacy_lineage_hash':old['sha256'],'reader':LEGACY_READER}
        target=store_factory(stage)
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


def snapshot_evaluation_copy(source, destination, *, store_factory, storage):
    """Consistent schema4 SQLite backup, preserving WAL-visible rows and old facts."""
    from actio.contracts.json import digest
    from actio.evidence.evaluation_history import lineage as historical
    source,destination=Path(source).resolve(),Path(destination).resolve()
    backup=destination.with_name(destination.name+'.backup.sqlite')
    record=destination.with_name(destination.name+'.snapshot.json')
    stage=destination.with_name(destination.name+'.copying-'+uid())
    if source==destination or any(p.exists() for p in (destination,backup,record)):
        raise ContractError('new snapshot destination required; previous attempts retained')
    src=store_factory(source,readonly=True)
    def files():
        return {p.name:file_hash(p) for p in (source,Path(str(source)+'-wal')) if p.exists()}
    try:
        if src.version!=4 or src.db.execute('PRAGMA quick_check').fetchone()[0]!='ok':
            raise ContractError('intact schema4 required')
        before=files();old=src.evaluation_lineage()
        if old!=historical():raise ContractError('source is not authenticated C2C2 authority')
        with backup.open('xb'):pass
        saved=storage.connect(backup)
        try:src.db.backup(saved);saved.execute('PRAGMA journal_mode=DELETE')
        finally:saved.close()
        saved=storage.open_existing(backup,readonly=True);target=storage.connect(stage,isolation_level=None)
        try:
            saved.backup(target)
            if storage.inspect(target)!=4 or list(saved.iterdump())!=list(target.iterdump()):
                raise ContractError('snapshot semantic mismatch')
            semantic=digest(list(saved.iterdump()))
        finally:target.close();saved.close()
        check=store_factory(stage,readonly=True)
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
