"""Independent acceptance checks for the actual Workshop ZIP, not builder inputs."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import tempfile
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'dist/DC_AI_Teammate-workshop-draft.zip'
PREFIX = 'DC_AI_Teammate/'
MOD = 'Contents/mods/DC_AI_Teammate/'
DOCS = {'workshop.txt', 'README.md', '更新记录.md', '发布说明.md',
        '发布检查清单.md', '依赖与许可说明.md', '安装说明.md'}
LUA = {'DC_AI_Teammate.lua', 'DC_AI_TeammateMailbox.lua', 'DC_AI_TeammateUI.lua'}
PAYLOAD = DOCS | {MOD + 'common/mod.info'} | {
    MOD + '42/media/lua/client/' + name for name in LUA}
EXPECTED = {PREFIX + name for name in PAYLOAD | {'SHA256.json'}}


class WorkshopArchiveTests(unittest.TestCase):
    def test_exact_allowlist_and_integrity(self):
        with ZipFile(ARCHIVE) as z:
            self.assertEqual(set(z.namelist()), EXPECTED)
            self.assertEqual(len(z.namelist()), len(EXPECTED))
            self.assertIsNone(z.testzip())
            manifest = json.loads(z.read(PREFIX + 'SHA256.json'))
            self.assertEqual(set(manifest), EXPECTED - {PREFIX + 'SHA256.json'})
            for name, digest in manifest.items():
                path = PurePosixPath(name)
                self.assertFalse(path.is_absolute())
                self.assertNotIn('..', path.parts)
                self.assertNotIn('\\', name)
                self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(), digest)

    def test_metadata_remains_private_and_credits_dependencies(self):
        with ZipFile(ARCHIVE) as z:
            metadata = z.read(PREFIX + 'workshop.txt').decode('utf-8').splitlines()
            self.assertEqual([v for v in metadata if v.startswith('visibility=')], ['visibility=private'])
            self.assertEqual([v for v in metadata if v.startswith('version=')], ['version=1'])
            self.assertFalse(any(v.startswith('id=') for v in metadata))
            text = '\n'.join(metadata)
            for item in ('3397396843', '3619862853', 'Knox', 'ZombieBuddy'):
                self.assertIn(item, text)
            mod = z.read(PREFIX + MOD + 'common/mod.info').decode('utf-8').splitlines()
            self.assertIn('id=DC_AITeammate', mod)
            self.assertIn('versionMin=42.21', mod)

    def test_archive_entries_are_reproducible_and_workshop_only(self):
        with ZipFile(ARCHIVE) as z:
            for info in z.infolist():
                self.assertEqual(info.date_time, (2026, 1, 1, 0, 0, 0))
                self.assertEqual(info.create_system, 3)
                self.assertEqual(info.external_attr >> 16, 0o100644)
                self.assertNotIn('/bridge/', info.filename)
                self.assertNotIn('/test-', info.filename)
                self.assertNotIn('.log', info.filename)
                self.assertNotIn('preview.png', info.filename)

    def test_fresh_extraction_matches_current_production(self):
        with tempfile.TemporaryDirectory(prefix='workshop-acceptance-') as temp:
            with ZipFile(ARCHIVE) as z:
                self.assertEqual(set(z.namelist()), EXPECTED)
                z.extractall(temp)
            folder = Path(temp) / 'DC_AI_Teammate'
            files = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
            self.assertEqual(files, PAYLOAD | {'SHA256.json'})
            for name in LUA:
                self.assertEqual((folder / MOD / '42/media/lua/client' / name).read_bytes(),
                                 (ROOT / 'DC_AIVoice/42.0/media/lua/client' / name).read_bytes())
            self.assertEqual((folder / MOD / 'common/mod.info').read_bytes(),
                             (ROOT / 'teammate-package/common/mod.info').read_bytes())
            for name in DOCS - {'安装说明.md'}:
                self.assertEqual((folder / name).read_bytes(), (ROOT / 'publish-draft' / name).read_bytes())
            self.assertEqual((folder / '安装说明.md').read_bytes(), (ROOT / 'TEAMMATE_INSTALL_DRAFT.md').read_bytes())


if __name__ == '__main__':
    unittest.main()
