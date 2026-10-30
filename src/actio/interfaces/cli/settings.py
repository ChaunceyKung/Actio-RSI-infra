"""Inspect resolved project settings without resolving or printing credentials."""
import argparse
import json
from pathlib import Path
from actio.contracts.json import ContractError
from actio.profiles.settings import load_settings


def main(argv=None):
    parser = argparse.ArgumentParser(prog='actio config')
    parser.add_argument('command', choices=['show'])
    parser.add_argument('--settings', type=Path)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(load_settings(args.settings).view(), ensure_ascii=False, indent=2))
        return 0
    except ContractError as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False))
        return 2
