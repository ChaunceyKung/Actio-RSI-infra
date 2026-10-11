"""Evidence export assembly."""
from actio.application.export import closure
from actio.application import export as use_case
from actio.interfaces.store import Store

def export_bundle(db_path, target, destination):
    return use_case.export_bundle(db_path, target, destination, store_factory=Store)
