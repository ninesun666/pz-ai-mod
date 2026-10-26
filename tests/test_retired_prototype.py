"""Source-level retirement regression checks, NOT an in-game input test."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RetiredPrototypeTests(unittest.TestCase):
    def test_all_old_entrypoints_return_before_side_effects(self):
        names = ("DC_AI_Teammate.lua", "DC_AI_TeammateUI.lua",
                 "DC_AI_TeammateMailbox.lua", "DC_AI_PetOverlay.lua")
        roots = (ROOT / "DC_AIVoice/42.0/media/lua/client",
                 ROOT / "test-profile/mods/DC_AI_Teammate/42/media/lua/client")
        paths = [root / name for root in roots for name in names]
        paths.append(ROOT / "test-profile/mods/DC_AITeammateTest/42/media/lua/client/DC_AI_TeammateTest.lua")
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8")
                executable = [line.strip() for line in text.splitlines()
                              if line.strip() and not line.lstrip().startswith("--")]
                self.assertEqual(executable[0], "do return end")


if __name__ == "__main__":
    unittest.main()
