from actio.adapters.persistence.migration import MigrationStorage
"""Explicit copy-only migration assembly."""
from actio.application import migration
from actio.interfaces.store import Store

def migrate_evaluation_copy(source, destination):
    return migration.migrate_evaluation_copy(source, destination, store_factory=Store, storage=MigrationStorage)

def snapshot_evaluation_copy(source, destination):
    return migration.snapshot_evaluation_copy(source, destination, store_factory=Store, storage=MigrationStorage)
