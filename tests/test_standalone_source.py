import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class StandaloneSourceTests(unittest.TestCase):
    def test_runtime_has_no_third_party_teammate_dependency(self):
        files = list((ROOT / "standalone").rglob("*.java")) + list((ROOT / "standalone").rglob("*.lua"))
        text = "\n".join(path.read_text(encoding="utf-8") for path in files)
        for forbidden in ("KnoxEventLoader", "spawnNpc", "ZombieBuddy", "tellNpcFollow", "tellNpcStay"):
            self.assertNotIn(forbidden, text)

    def test_runtime_does_not_capture_mouse_or_open_textbox(self):
        files = list((ROOT / "standalone").rglob("*.lua"))
        text = "\n".join(path.read_text(encoding="utf-8") for path in files)
        self.assertNotIn("ISPanel", text)
        self.assertNotIn("ISTextBox", text)
        self.assertNotIn("onMouseDown", text)
        self.assertNotIn("onMouseRightDown", text)


if __name__ == "__main__":
    unittest.main()
