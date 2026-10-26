import unittest
from pathlib import Path
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]


class StandaloneAcceptanceTests(unittest.TestCase):
    def test_runtime_probe_is_idempotent_and_fail_closed(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        calls = []
        lua.globals().print = lambda *args: calls.append(args)
        lua.globals().Events = lua.table_from({
            "OnTick": lua.table_from({"Add": lambda fn: setattr(lua.globals(), "tick", fn)})
        })
        lua.execute((ROOT / "standalone/42/media/lua/client/DC_AI_RuntimeProbe.lua").read_text(encoding="utf-8"))
        lua.globals().tick()
        lua.globals().tick()
        self.assertEqual(len(calls), 1)
        self.assertIn("runtime missing", calls[0][0])

    def test_active_sources_are_not_legacy_bootstrap(self):
        standalone = ROOT / "standalone"
        text = "\n".join(p.read_text(encoding="utf-8") for p in standalone.rglob("*.lua"))
        self.assertNotIn("KnoxEventLoader", text)
        self.assertNotIn("ISPanel", text)
        self.assertNotIn("ISTextBox", text)
        self.assertNotIn("DC_AI_TeammateMailbox", text)


if __name__ == "__main__":
    unittest.main()
