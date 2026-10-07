"""Experimental Phase 1A helpers. Synthetic inputs only; not a product API."""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOCAL = ROOT / '.local'
EVIDENCE = ROOT.parents[1] / 'docs' / 'validation' / 'phase1a' / 'evidence'

def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def digest(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()

def file_hash(path):
    return hashlib.file_digest(open(path, 'rb'), 'sha256').hexdigest()

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

def jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line] if Path(path).exists() else []

def clean_env(root):
    """No inherited provider credentials, proxy settings, PYTHONPATH or user HOME."""
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    temp = root / 'temp'
    temp.mkdir(exist_ok=True)
    system = os.environ.get('SystemRoot', r'C:\Windows')
    return {
        'SystemRoot': system, 'WINDIR': system, 'COMSPEC': str(Path(system) / 'System32/cmd.exe'),
        'PATH': str(Path(system) / 'System32'),
        'HOME': str(root), 'USERPROFILE': str(root),
        'APPDATA': str(root / 'appdata'), 'LOCALAPPDATA': str(root / 'localappdata'),
        'TEMP': str(temp), 'TMP': str(temp),
        'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8', 'PYTHONDONTWRITEBYTECODE': '1',
        'DSH_PRIMARY_RUNTIME': '', 'DSH_TELEMETRY_DISABLED': '1',
    }
