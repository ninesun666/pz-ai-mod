import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('standalone_smoke', ROOT / 'standalone/runtime/smoke_game.py')
SMOKE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SMOKE)


class ExitedProcess:
    pid = 123456
    returncode = 7

    def poll(self):
        return self.returncode


class SmokeProfileTests(unittest.TestCase):
    def setup_root(self, root):
        for relative in ('standalone/common', 'standalone/42/media/lua/client', 'standalone/runtime/build'):
            (root / relative).mkdir(parents=True)
        (root / 'standalone/runtime/build/DC_AIStandaloneRuntime.jar').touch()
        (root / 'standalone/runtime/tests').mkdir()
        (root / 'standalone/runtime/tests/WorldBootstrap.lua').write_text('-- test bootstrap', encoding='utf-8')

    def run_smoke(self, root, args):
        with patch.object(SMOKE, 'ROOT', root), patch('sys.argv', ['smoke_game.py', *args]), \
                patch.object(SMOKE.subprocess, 'Popen', return_value=ExitedProcess()) as launch, \
                patch.object(SMOKE.time, 'strftime', return_value='test-run'), patch('builtins.print'):
            code = SMOKE.main()
        return code, launch

    def test_new_profile_loads_mod_with_authorized_tos_seed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.setup_root(root)
            code, launch = self.run_smoke(root, ['--world'])
            self.assertEqual(code, 1)  # Process exit cannot masquerade as game-thread success.
            profile = root / 'standalone/runtime/build/runs/test-run/profile'
            self.assertEqual((profile / '.dc-standalone-disposable').read_text(), 'DCStandalone disposable profile v1\n')
            options = (profile / 'options.ini').read_text()
            self.assertIn('termsOfServiceVersion=1', options)  # User-authorized automation seed.
            self.assertIn('mod = DC_AIStandalone', (profile / 'mods/default.txt').read_text())
            self.assertTrue((profile / 'mods/reset-mods-42_00.txt').exists())
            self.assertTrue((profile / 'mods/DC_AIStandalone/42/media/lua/client/DCStandaloneTestBootstrap.lua').exists())
            report = json.loads((profile.parent / 'report.json').read_text())
            self.assertFalse(report['passed'])
            self.assertFalse(report['terminatedByHarness'])
            self.assertEqual(launch.call_count, 1)

    def test_reuse_preserves_options_and_removes_only_world_bootstrap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.setup_root(root)
            profile = root / 'existing-disposable'
            profile.mkdir()
            (profile / '.dc-standalone-disposable').write_text('DCStandalone disposable profile v1\n')
            options = 'version=8\ntermsOfServiceVersion=1\nlanguage=ZH\n'
            (profile / 'options.ini').write_text(options)
            client = profile / 'mods/DC_AIStandalone/42/media/lua/client'
            client.mkdir(parents=True)
            (client / 'DCStandaloneTestBootstrap.lua').write_text('-- stale test world bootstrap')
            (client / 'keep.lua').write_text('-- retain')
            self.run_smoke(root, ['--profile', str(profile)])
            self.assertEqual((profile / 'options.ini').read_text(), options)
            self.assertFalse((client / 'DCStandaloneTestBootstrap.lua').exists())
            self.assertTrue((client / 'keep.lua').exists())

    def test_interactive_launch_does_not_start_click_thread(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.setup_root(root)
            with patch('threading.Thread') as thread:
                _, launch = self.run_smoke(root, ['--world', '--interactive', '--gate', 'follow'])
            thread.assert_not_called()
            self.assertEqual(launch.call_count, 1)
            self.assertNotIn('-Djava.awt.headless=true', launch.call_args.args[0])

    def test_timeout_reports_observed_stage(self):
        stages = (
            ('[DCStandaloneTest] world started', 'gameplay callback not observed'),
            ('[DCStandalone] first game-thread tick', 'after game-thread callback'),
            ('[DCStandalone] follow-probe round=1 dist=14.0', 'after game-thread probe started'),
        )
        for text, expected in stages:
            with self.subTest(stage=text), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.setup_root(root)
                def launch_game(*args, **kwargs):
                    kwargs['stdout'].write(text.encode('utf-8'))
                    kwargs['stdout'].flush()
                    return ExitedProcess()
                with patch.object(SMOKE, 'ROOT', root), \
                        patch('sys.argv', ['smoke_game.py', '--world', '--gate', 'follow', '--timeout', '0']), \
                        patch.object(SMOKE.subprocess, 'Popen', side_effect=launch_game), \
                        patch.object(SMOKE.time, 'strftime', return_value='test-run'), patch('builtins.print'):
                    self.assertEqual(SMOKE.main(), 1)
                report = json.loads((root / 'standalone/runtime/build/runs/test-run/report.json').read_text())
                self.assertFalse(report['passed'])
                self.assertIn(expected, report['reason'])

    def test_unmarked_profile_is_rejected_before_launch_or_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.setup_root(root)
            profile = root / 'user-profile'
            profile.mkdir()
            (profile / 'options.ini').write_text('untouched')
            with self.assertRaisesRegex(SystemExit, 'Refusing unmarked profile'):
                self.run_smoke(root, ['--profile', str(profile)])
            self.assertEqual(list(profile.iterdir()), [profile / 'options.ini'])
            self.assertEqual((profile / 'options.ini').read_text(), 'untouched')


if __name__ == '__main__':
    unittest.main()
