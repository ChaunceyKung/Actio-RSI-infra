"""Seal the bounded authored dataset and policy/evaluator source before formal validation."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from actio.common import canonical, file_hash
from actio.eval_contract import seal
from actio.task_diagnostic_data import dataset
from actio.task_diagnostic_policy import VERSION, CONTROLS
from actio.task_diagnostic_analysis import metric_definitions


def main():
    folder = ROOT / 'docs/validation/phase1c2c3/frozen-design'
    folder.mkdir(exist_ok=False)
    artifacts = {'dataset.json': dataset(), 'policies.json': seal({'schema': VERSION, 'controls': CONTROLS,
        'demonstration_tie_break': 'first argmax in ActionSpec order; set membership remains normative',
        'legacy_comparison': 'scheduling first maximum; bargaining maximum (score, action string)',
        'authority': 'synthetic controls only; no candidate/solver/training labels'}),
        'metrics.json': seal(metric_definitions())}
    for name, value in artifacts.items():
        (folder / name).write_text(canonical(value), encoding='utf8')
    source = {p.name: file_hash(p) for p in sorted((ROOT / 'src/actio').glob('task_diagnostic_*.py'))}
    record = {'schema': 'task-diagnostic-design-freeze.v1', 'design_commit': 'bc645c1',
              'artifacts': {n: file_hash(folder / n) for n in artifacts}, 'source': source,
              'argv': sys.argv, 'scope': 'before formal acceptance; initial development probe explicitly retained',
              'development_attempts': [
                  {'argv': '.local/phase1c2c2-runtime-venv/Scripts/python.exe -I -B -c <import new modules; synthetic_analysis>',
                   'result': 'ModuleNotFoundError: actio.task_diagnostic_data', 'cause': '-I ignores PYTHONPATH; old installed package'},
                  {'argv': 'PYTHONPATH=src .local/phase1c2c2-runtime-venv/Scripts/python.exe -B -c <dataset; validate_dataset; synthetic_analysis>',
                   'result': {'groups': 8, 'worlds': 16, 'presentations': 32, 'legal_combinations': 416, 'four_synthetic_gates': 'PASS'},
                   'limitation': 'development probe preceded this machine-readable source freeze; not final-source acceptance'}],
              'new_model_requests': 0, 'data_or_policy_tuned_after_probe': False}
    (folder / 'freeze.json').write_text(canonical(seal(record)), encoding='utf8')
    print(json.dumps({'dataset_sha256': artifacts['dataset.json']['sha256'], 'frozen_files': list(artifacts)}))


if __name__ == '__main__':
    main()
