import unittest
from pathlib import Path
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "standalone/42/media/lua/client/DC_AI_Standalone.lua"


class Player:
    def __init__(self):
        self.data = {}

    def getModData(self):
        return self.data


class TestStandaloneRegistry(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.player = Player()
        self.player.data = self.lua.table()
        self.lua.globals().getPlayer = lambda: self.player
        self.random_value = 123455
        def next_random(*_):
            self.random_value += 1
            return self.random_value
        self.lua.globals().ZombRand = next_random
        self.lua.globals().print = lambda *_: None
        self.lua.globals().Events = self.lua.table_from({
            "OnTick": self.lua.table_from({"Add": lambda fn: setattr(self.lua.globals(), "tick", fn)})
        })
        self.lua.execute(SRC.read_text(encoding="utf-8"))
        self.mod = self.lua.globals().DC_AI_Standalone

    def test_identity_is_created_once_and_persisted(self):
        self.lua.globals().tick()
        first = self.mod.state.companionId
        self.assertTrue(first.startswith("dc-whale-"))
        self.assertEqual(self.player.data["DC_AI_Standalone"]["companionId"], first)
        self.mod.state.companionId = None
        self.assertTrue(self.mod.ensureIdentity())
        self.assertEqual(self.mod.state.companionId, first)
        self.lua.globals().tick()
        self.assertEqual(self.mod.state.intent, "hold")
        self.assertFalse(self.mod.command("follow"))
        self.assertEqual(self.mod.state.intent, "hold")
        self.assertEqual(self.mod.state.error, "actor unavailable")

    def test_player_switch_does_not_reuse_identity(self):
        self.lua.globals().tick()
        first = self.mod.state.companionId
        second_player = Player()
        second_player.data = self.lua.table()
        self.lua.globals().getPlayer = lambda: second_player
        self.lua.globals().tick()
        second = self.mod.state.companionId
        self.assertNotEqual(first, second)
        self.assertEqual(second_player.data["DC_AI_Standalone"]["companionId"], second)
        self.assertEqual(self.mod.state.intent, "hold")

    def test_player_switch_restores_second_identity_and_intent(self):
        second_player = Player()
        second_player.data = self.lua.table_from({"DC_AI_Standalone": self.lua.table_from({
            "schema": 1, "companionId": "dc-whale-second", "assetId": "deepseek_whale_girl", "intent": "follow"
        })})
        self.lua.globals().getPlayer = lambda: second_player
        self.lua.globals().tick()
        self.assertEqual(self.mod.state.companionId, "dc-whale-second")
        self.assertEqual(self.mod.state.intent, "follow")
        self.assertEqual(self.mod.state.phase, "identity-restored")


    def test_direct_ensure_switch_and_return_restore_original(self):
        self.assertTrue(self.mod.ensureIdentity())
        first = self.mod.state.companionId
        original = self.player
        second = Player()
        second.data = self.lua.table()
        self.lua.globals().getPlayer = lambda: second
        self.assertTrue(self.mod.ensureIdentity())
        self.assertNotEqual(first, self.mod.state.companionId)
        self.lua.globals().getPlayer = lambda: original
        self.assertTrue(self.mod.ensureIdentity())
        self.assertEqual(first, self.mod.state.companionId)
        self.assertEqual(original.data["DC_AI_Standalone"]["companionId"], first)

    def test_missing_player_does_not_write_old_player(self):
        self.assertTrue(self.mod.ensureIdentity())
        first = self.mod.state.companionId
        self.lua.globals().getPlayer = lambda: None
        self.assertFalse(self.mod.ensureIdentity())
        self.assertIsNone(self.mod.state.companionId)
        self.assertEqual(first, self.player.data["DC_AI_Standalone"]["companionId"])

    def test_corrupt_identity_is_preserved_and_can_be_repaired(self):
        saved = self.lua.table_from({"schema": 999, "companionId": "keep-me"})
        self.player.data["DC_AI_Standalone"] = saved
        self.lua.globals().tick()
        self.assertIsNone(self.mod.state.companionId)
        self.assertEqual(self.mod.state.error, "unsupported identity schema")
        self.assertEqual(saved.schema, 999)
        self.assertEqual(saved.companionId, "keep-me")
        saved.schema = 1
        self.lua.globals().tick()
        self.assertEqual(self.mod.state.companionId, "keep-me")
        self.assertEqual(self.mod.state.phase, "identity-restored")
        self.assertIsNone(self.mod.state.error)


    def test_native_menu_is_disabled_without_live_executor(self):
        self.lua.execute('''
            require = function() end
            getSpecificPlayer = function(index) return index == 0 and {} or nil end
            Events.OnFillWorldObjectContextMenu = {Add = function(fn) fillMenu = fn end}
            menuOptions = {}
            menu = {addOption = function(self, name, target, callback, intent)
                local option = {name=name, callback=callback, intent=intent}
                table.insert(menuOptions, option)
                return option
            end}
        ''')
        ui = ROOT / "standalone/42/media/lua/client/DC_AI_StandaloneUI.lua"
        self.lua.execute(ui.read_text(encoding="utf-8"))
        self.lua.execute('fillMenu(0, menu, {}, true); assert(#menuOptions == 0)')
        self.lua.execute('fillMenu(1, menu, {}, false); assert(#menuOptions == 0)')
        self.lua.execute('''
            fillMenu(0, menu, {}, false)
            assert(#menuOptions == 3)
            for _, option in ipairs(menuOptions) do
                assert(option.notAvailable == true)
                assert(string.find(option.name, "实体尚未就绪", 1, true))
                option.callback(nil, option.intent)
            end
        ''')
        self.assertIsNone(self.mod.state.companionId)
        self.assertEqual(self.mod.state.intent, "hold")
        self.assertFalse(self.mod.canCommand())


if __name__ == "__main__":
    unittest.main()
