"""Local official runtime composition. Called only at an execution boundary."""
def episode_ports():
    from actio.contracts.ports import EpisodePorts
    from actio.adapters.runtime.runtime import RuntimePort, pins
    from actio.adapters.runtime import supervisor
    from actio.adapters.runtime.facts import Facts
    from actio.adapters.transport.transport import TransportPort, transport_pins, transport_spec
    from actio.adapters.environment.concordia import run_engine, final_source
    from actio.adapters.persistence.ledger import Ledger
    return EpisodePorts(RuntimePort, TransportPort, run_engine, Facts, final_source,
                        supervisor, pins, transport_pins, transport_spec, Ledger)


def diagnostic_ports():
    from actio.contracts.ports import DiagnosticPorts
    from actio.adapters.runtime.runtime import verify_runtime
    from actio.adapters.runtime.cleanup import cleanup
    from actio.adapters.transport.fixture import GatewayStub, planned
    from actio.adapters.persistence.ledger import Ledger
    return DiagnosticPorts(verify_runtime, GatewayStub, planned, cleanup, Ledger)
