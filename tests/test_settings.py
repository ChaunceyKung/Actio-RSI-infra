"""TOML relocation, credential selection and the actual configured gateway path."""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from actio.contracts.json import ContractError
from actio.profiles.settings import load_settings, gateway_config
from actio.adapters.filesystem.credentials import resolve_credential
from actio.interfaces.cli.settings import main as settings_cli
from actio.interfaces.cli.run import main as run_cli
from actio.interfaces.gateway_settings import run

ROOT = Path(__file__).resolve().parents[1]


class SettingsTests(unittest.TestCase):
    def setUp(self):
        temporary = load_settings(ROOT / 'actio.toml').paths['temp']
        temporary.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=temporary)
        self.base = Path(self.temp.name)
        self.file = self.base / 'custom.toml'
        self.file.write_text((ROOT / 'actio.toml').read_text(encoding='utf8'), encoding='utf8')

    def tearDown(self):
        self.temp.cleanup()

    def change(self, old, new):
        self.file.write_text(self.file.read_text(encoding='utf8').replace(old, new), encoding='utf8')

    def test_relative_paths_follow_config_not_cwd_and_llm_selection(self):
        settings = load_settings(self.file)
        self.assertEqual(settings.paths['database'], self.base / '.local/actio.sqlite')
        self.assertEqual(settings.paths['runs'], self.base.parent / 't')
        self.change('gpt-5.6', 'claude-sonnet-4-6')
        self.assertEqual(gateway_config(load_settings(self.file))['model'], 'claude-sonnet-4-6')
        with patch('pathlib.Path.cwd', return_value=Path('C:/unrelated')):
            self.assertEqual(load_settings(self.file).paths['database'], self.base / '.local/actio.sqlite')

    def test_missing_or_invalid_config_has_no_historical_fallback(self):
        with self.assertRaisesRegex(ContractError, 'settings file missing'):
            load_settings(self.base / 'absent.toml')
        self.file.write_text('schema = "SYNTHETIC_SECRET_BAD_LINE"\n[', encoding='utf8')
        with self.assertRaises(ContractError) as caught:
            load_settings(self.file)
        self.assertNotIn('SYNTHETIC_SECRET', str(caught.exception))

    def test_unknown_secret_fields_and_unsupported_llm_fail_closed(self):
        self.change('provider = "tokenkey"', 'provider = "other"')
        with patch('actio.interfaces.gateway_settings.resolve_credential') as resolver:
            with self.assertRaisesRegex(ContractError, 'provider'):
                run(self.file)
            resolver.assert_not_called()
        self.change('provider = "other"', 'provider = "tokenkey"')
        self.change('https://api.tokenkey.dev/v1', 'https://example.invalid/v1')
        with self.assertRaisesRegex(ContractError, 'TokenKey origin'):
            gateway_config(load_settings(self.file))
        self.change('https://example.invalid/v1', 'https://api.tokenkey.dev/v1')
        self.file.write_text(self.file.read_text() + '\napi_key = "SYNTHETIC_SECRET"\n')
        with self.assertRaises(ContractError) as caught:
            load_settings(self.file)
        self.assertNotIn('SYNTHETIC_SECRET', str(caught.exception))

    def test_only_configured_credential_is_read_and_missing_file_is_not_copied(self):
        self.change('.local/credentials/token_key.txt', 'private/selected.txt')
        selected = self.base / 'private/selected.txt'
        with self.assertRaisesRegex(ContractError, 'configured credential file missing'):
            resolve_credential(ROOT, settings_path=self.file)
        self.assertFalse(selected.parent.exists())
        selected.parent.mkdir()
        selected.write_text('SYNTHETIC_SELECTED_KEY\n')
        with patch.dict(os.environ, {'ACTIO_SOLVER_KEY': 'SYNTHETIC_WRONG_AMBIENT_KEY'}):
            self.assertEqual(resolve_credential(ROOT, settings_path=self.file), 'SYNTHETIC_SELECTED_KEY')
        selected.write_text('two\nlines')
        with self.assertRaisesRegex(ContractError, 'format invalid'):
            resolve_credential(ROOT, settings_path=self.file)

    def test_show_does_not_resolve_key_and_default_db_comes_from_toml(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(settings_cli(['show', '--settings', str(self.file)]), 0)
        self.assertEqual(json.loads(output.getvalue())['paths']['database'], str(self.base / '.local/actio.sqlite'))
        self.assertFalse((self.base / '.local').exists())
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(run_cli(['--settings', str(self.file), 'init']), 0)
        self.assertTrue((self.base / '.local/actio.sqlite').is_file())

    def test_live_missing_key_does_not_allocate_run_or_authority(self):
        settings = load_settings(self.file)
        target = self.base / 'live-run'
        with self.assertRaisesRegex(ContractError, 'configured credential file missing'):
            run(self.file, root=target)
        self.assertFalse(target.exists())
        self.assertFalse(settings.paths['authority'].exists())

    def test_actual_toml_gateway_rehearsal_and_no_existing_run_replay(self):
        # Use the configured short run root; no private machine-specific path.
        runs = load_settings(ROOT / 'actio.toml').paths['runs'].as_posix()
        self.change('runs = "../t"', 'runs = ' + json.dumps(runs))
        result = run(self.file, rehearsal=True)
        self.assertEqual(result['status'], 'complete', result)
        self.assertEqual((result['attempts'], result['settled'], result['unknown']), (2, 2, 0))
        self.assertEqual(result['episodes'][0]['state'], 'execution_complete')
        self.assertTrue(result['campaign_valid'])
        self.assertFalse(result['credential_scan']['credential_found'])
        self.assertFalse(load_settings(self.file).paths['credential_file'].exists())
        self.evidence = {'root': result['root'], 'summary': result}
        with self.assertRaisesRegex(ContractError, 'never replayed'):
            run(self.file, root=result['root'], rehearsal=True)


if __name__ == '__main__':
    unittest.main()
