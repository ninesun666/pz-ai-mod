import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class StandaloneSourceTests(unittest.TestCase):
    def test_runtime_has_no_third_party_teammate_dependency(self):
        files = list((ROOT / "standalone").rglob("*.java")) + list((ROOT / "standalone").rglob("*.lua"))
        text = "\n".join(path.read_text(encoding="utf-8") for path in files)
        for forbidden in ("KnoxEventLoader", "spawnNpc(", "me.zed_0xff.zombie_buddy", "tellNpcFollow(", "tellNpcStay("):
            self.assertNotIn(forbidden, text)

    def test_no_text_controls_use_native_key_event_only(self):
        ui = (ROOT / "standalone/42/media/lua/client/DC_AI_StandaloneUI.lua").read_text(encoding="utf-8")
        self.assertIn("Events.OnFillWorldObjectContextMenu.Add", ui)
        self.assertIn("大肥鱼：跟随", ui)
        self.assertIn("大肥鱼：停留", ui)
        self.assertIn("大肥鱼：重新集合", ui)
        self.assertNotIn("ISTextBox", ui)
        self.assertNotIn("ISPanel", ui)
        self.assertNotIn("OnKeyPressed", ui)

    def test_runtime_does_not_capture_mouse_or_open_textbox(self):
        files = list((ROOT / "standalone").rglob("*.lua"))
        text = "\n".join(path.read_text(encoding="utf-8") for path in files)
        self.assertNotIn("ISPanel", text)
        self.assertNotIn("ISTextBox", text)
        self.assertNotIn("onMouseDown", text)
        self.assertNotIn("onMouseRightDown", text)


if __name__ == "__main__":
    unittest.main()
