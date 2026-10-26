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
        self.lua.globals().ZombRand = lambda *_: 123456
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


if __name__ == "__main__":
    unittest.main()
