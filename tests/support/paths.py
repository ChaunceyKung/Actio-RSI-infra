"""Test storage and optional historical inputs use the same project TOML."""
from pathlib import Path
import unittest
from actio.profiles.settings import load_settings

ROOT = Path(__file__).resolve().parents[2]


def runtime_root():
    return load_settings(ROOT / 'actio.toml').paths['runs']


def history_path(name):
    path = load_settings(ROOT / 'actio.toml').history[name]
    if path is None:
        raise unittest.SkipTest('unconfigured optional input: history.' + name)
    return path
