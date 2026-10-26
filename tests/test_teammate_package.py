"""Verify the distributed archive in a fresh temporary install, not source imports."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

ARCHIVE = Path(__file__).resolve().parents[1] / 'dist/DC_AI_Teammate-preview.zip'
EXPECTED = {
    'mods/DC_AI_Teammate/common/mod.info',
    *('mods/DC_AI_Teammate/42/media/lua/client/' + n for n in (
        'DC_AI_Teammate.lua', 'DC_AI_TeammateMailbox.lua', 'DC_AI_TeammateUI.lua')),
    'bridge/teammate_bridge.py', 'bridge/teammate_protocol.py',
    'bridge/teammate-config.example.json', 'README.md', 'SHA256.json',
}

class PackagedInstallTests(unittest.TestCase):
    def test_payload_matches_current_sources(self):
        root = Path(__file__).resolve().parents[1]
        sources = {
            'README.md': root / 'TEAMMATE_INSTALL_DRAFT.md',
            'mods/DC_AI_Teammate/common/mod.info': root / 'teammate-package/common/mod.info',
        }
        for name in ('DC_AI_Teammate.lua', 'DC_AI_TeammateMailbox.lua', 'DC_AI_TeammateUI.lua'):
            sources['mods/DC_AI_Teammate/42/media/lua/client/' + name] = root / 'DC_AIVoice/42.0/media/lua/client' / name
        for name in ('teammate_bridge.py', 'teammate_protocol.py', 'teammate-config.example.json'):
            sources['bridge/' + name] = root / 'bridge' / name
        self.assertEqual(set(sources), EXPECTED - {'SHA256.json'})
        with ZipFile(ARCHIVE) as archive:
            for name, source in sources.items():
                with self.subTest(payload=name):
                    self.assertEqual(archive.read(name), source.read_bytes())

    def test_archive_metadata_is_reproducible(self):
        with ZipFile(ARCHIVE) as archive:
            for info in archive.infolist():
                self.assertEqual(info.date_time, (2026, 1, 1, 0, 0, 0))
                self.assertEqual(info.create_system, 3)
                self.assertEqual(info.external_attr >> 16, 0o100644)


    def test_archive_and_fresh_bridge_install(self):
        with tempfile.TemporaryDirectory(prefix='teammate-install-') as d:
            root = Path(d)
            with ZipFile(ARCHIVE) as z:
                self.assertEqual(set(z.namelist()), EXPECTED)
                self.assertEqual(len(z.namelist()), len(EXPECTED))
                self.assertIsNone(z.testzip())
                manifest = json.loads(z.read('SHA256.json'))
                self.assertEqual(set(manifest), EXPECTED - {'SHA256.json'})
                for name, digest in manifest.items():
                    self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(), digest)
                z.extractall(root)
            example = json.loads((root/'bridge/teammate-config.example.json').read_text())
            self.assertEqual(example['api_key'], '')
            lua = list((root/'mods').rglob('*.lua'))
            self.assertEqual(len(lua), 3)
            request = root/'request.txt'
            reply = root/'reply.txt'
            request.write_bytes(b'session=packagedinstalltest\nseq=1\nnpc_id=131\naction=none\ntext=Hello\n')
            cmd = [sys.executable, '-B', str(root/'bridge/teammate_bridge.py'),
                   '--request', str(request), '--reply', str(reply), '--once']
            # Inherit stdout/stderr: Windows confined programs cannot capture pipes.
            run = subprocess.run(cmd + ['--offline'], cwd=root)
            self.assertEqual(run.returncode, 0)
            wire = reply.read_text(encoding='utf-8')
            self.assertIn('npc_id=131\n', wire)
            self.assertIn('action=none\n', wire)
            previous = reply.read_bytes()
            run = subprocess.run(cmd + ['--config', str(root/'bridge/teammate-config.example.json')], cwd=root)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(reply.read_bytes(), previous)

if __name__ == '__main__':
    unittest.main()
