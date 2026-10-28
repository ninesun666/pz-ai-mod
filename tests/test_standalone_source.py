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


class BehaviorTreeMirrorTests(unittest.TestCase):
    """1:1 structural replica of Knox's behavior-tree core, scoped to
    follow/stay/movement (decision 2026-10-28, see STANDALONE_COMPANION_REWORK.md)."""

    BT = "standalone/runtime/src/dcai/companion/bt"

    def test_core_and_subtree_files_exist(self):
        expected = [
            "core/BehaviorNode.java", "core/SequenceNode.java", "core/SelectorNode.java",
            "core/InverterNode.java", "core/BehaviorTreeBase.java",
            "CompanionBehaviorTree.java", "CompanionMotion.java",
            "conditions/IsFollowingCondition.java",
            "actions/SetFollowPointAction.java", "actions/StayAction.java",
            "actions/InterpolatePathAction.java", "actions/MoveToSquareAction.java",
            "subtrees/movement/MovementKeys.java", "subtrees/movement/MovementSubTree.java",
            "subtrees/follow/FollowSubTree.java", "subtrees/stay/StaySubTree.java",
        ]
        for rel in expected:
            self.assertTrue((ROOT / self.BT / rel).is_file(), rel)

    def test_knox_data_keys_mirror(self):
        movement = (ROOT / self.BT / "subtrees/movement/MovementKeys.java").read_text(encoding="utf-8")
        for key in ("MOVE_TARGET_X", "MOVE_TARGET_Y", "MOVE_TARGET_Z", "MOVE_PATH", "MOVE_NEEDS_RESTART"):
            self.assertIn(key, movement)
        follow = (ROOT / self.BT / "subtrees/follow/FollowSubTree.java").read_text(encoding="utf-8")
        self.assertIn("FOLLOW_DISTANCE", follow)
        self.assertIn("TICKS", follow)

    def test_gate_marker_contract_preserved(self):
        move = (ROOT / self.BT / "actions/MoveToSquareAction.java").read_text(encoding="utf-8")
        self.assertIn("[DCStandalone] path requested (locomotion arrival unverified)", move)

    def test_controller_dispatches_through_tree(self):
        controller = (ROOT / "standalone/runtime/src/dcai/companion/CompanionController.java").read_text(encoding="utf-8")
        self.assertIn("tree.setGoal(CompanionBehaviorTree.GOAL_FOLLOW)", controller)
        self.assertIn("tree.setGoal(CompanionBehaviorTree.GOAL_STAY)", controller)


class AutoInputDriverTests(unittest.TestCase):
    """Unattended world entry: synthetic LMB through the game's own input array."""

    def test_driver_only_touches_loading_state(self):
        src = (ROOT / "standalone/runtime/src/dcai/companion/AutoInputDriver.java").read_text(encoding="utf-8")
        self.assertIn("GameLoadingState", src)
        self.assertIn("Mouse.buttonDownStates", src)
        self.assertIn('Boolean.getBoolean("dcai.autoGate")', src)
        # outside the loading state the driver actively releases LMB
        self.assertIn("buttons[0] = loading", src)

    def test_smoke_passes_auto_gate_for_world_runs(self):
        src = (ROOT / "standalone/runtime/smoke_game.py").read_text(encoding="utf-8")
        self.assertIn("-Ddcai.autoGate=true", src)
        self.assertIn("args.world", src)
