"""Campaign export assembly using the original Ledger authority."""
from actio.adapters.persistence.ledger import Ledger
from actio.application import transport_export

def export_campaign(ledger_path, bundles, receives, destination):
    return transport_export.export_campaign(ledger_path, bundles, receives, destination, ledger_factory=Ledger)
