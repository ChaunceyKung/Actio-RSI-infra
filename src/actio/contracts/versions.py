"""Stable protocol identities, independent of runtime source layout."""
INPUT_CONTRACT = 'fixture-input.v2'
VERIFIER = {'implementation':'actio-verifier.3', 'contract':INPUT_CONTRACT,
            'task_contract':'scheduling-input.v1',
            'transport_contract':'scheduling-transport.v1',
            'stored_report_policy':'hash-checked historical report; current result independently recomputed'}
