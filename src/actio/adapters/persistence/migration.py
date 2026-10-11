"""Persistence operations for explicit copy-only schema migrations."""
import sqlite3
from pathlib import Path
from actio.adapters.persistence import database

class MigrationStorage:
    connect = staticmethod(sqlite3.connect)
    open_existing = staticmethod(database.connect)

    @staticmethod
    def inspect(connection):
        return database.inspect(connection)

    @staticmethod
    def schema(name):
        if name != 'evaluation_schema.sql':
            raise ValueError('unsupported migration resource')
        return Path(__file__).with_name(name).read_text()
