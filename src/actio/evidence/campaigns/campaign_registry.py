"""Trusted schema dispatch for campaign evidence readers."""
from actio.evidence.campaigns import candidate_measurement, evaluation_measurement, robustness_measurement

def analyzer(schema):
    return {'pilot-config.v8':candidate_measurement.analyze_pilot,
            'pilot-config.v9':evaluation_measurement.analyze_pilot,
            'pilot-config.v10':robustness_measurement.analyze_pilot}[schema]
