"""Mailbox integration tests; run with pytest or python -B."""
from pathlib import Path
from lupa import LuaRuntime

SRC = Path(__file__).resolve().parents[1] / "DC_AIVoice/42.0/media/lua/client/DC_AI_TeammateMailbox.lua"

class Reader:
    def __init__(self, data):
        raw = data.encode("utf-16-le", errors="surrogatepass")
        self.data = [int.from_bytes(raw[i:i + 2], "little") for i in range(0, len(raw), 2)]
        self.i = 0
        self.closed = False
    def read(self):
        if self.i >= len(self.data): return -1
        c = self.data[self.i]; self.i += 1; return c
    def close(self): self.closed = True

class Writer:
    def __init__(self, sink): self.sink = sink; self.closed = False
    def write(self, text): self.sink.append(text)
    def close(self): self.closed = True

class Obj:
    def __init__(self, ident): self.ident = str(ident); self.goal = None; self.say = []
    def getId(self): return self.ident
    def getWorldObject(self): return self
    def getSquare(self): return self
    def Say(self, text): self.say.append(text)
class List:
    def __init__(self, xs): self.xs = xs
    def size(self): return len(self.xs)
    def get(self, i): return self.xs[i]
class Group:
    def __init__(self, npc): self.npc = npc
    def inGroup(self, n): return n is self.npc
class API:
    def __init__(self, npc): self.npc = npc; self.group = Group(npc)
    def getNpcs(self): return List([self.npc])
    def getGroup(self, _): return self.group
class Player:
    def __init__(self): self.data = {"DC_AI_TeammateNpcId": "9007199254740993"}
    def getModData(self): return self.data

def boot(reply=None):
    lua = LuaRuntime(unpack_returned_tuples=True)
    sink, replies, ticks = [], [reply], []
    npc, player = Obj("9007199254740993"), Player()
    api = API(npc)
    now = [1000]
    lua.globals().getTimestampMs = lambda: now[0]
    lua.globals().getPlayer = lambda: player
    lua.globals().ZombRand = lambda n: 123456789
    lua.globals().KnoxEventLoader = type("Loader", (), {"getAPI": staticmethod(lambda _: api)})
    lua.globals().DC_AI_Teammate = lua.table_from({"state": lua.table_from({"phase":"following", "error":None, "npcId":"9007199254740993"}), "follow": lambda: True, "wait": lambda: True})
    lua.globals().getFileWriter = lambda *args: Writer(sink)
    lua.globals().getFileReader = lambda *args: Reader(replies.pop(0)) if replies else None
    lua.globals().Events = lua.table_from({"OnTick": lua.table_from({"Add": lambda f: ticks.append(f)})})
    lua.execute(SRC.read_text(encoding="utf-8"))
    return lua, sink, replies, ticks, now, npc

def test_valid_actions_and_exact_wire():
    for action in ("none", "follow", "wait"):
        lua, sink, _, ticks, now, npc = boot()
        M = lua.globals().DC_AI_TeammateMailbox
        calls = []
        def command(name):
            # Correlated reply is consumed before external command code executes.
            assert M.status()["pending"] is False
            calls.append(name)
            return True
        lua.globals().DC_AI_Teammate.follow = lambda: command("follow")
        lua.globals().DC_AI_Teammate.wait = lambda: command("wait")
        assert M.request("come = here") is True
        wire = sink[0]
        fields = dict(line.split("=", 1) for line in wire.rstrip("\n").split("\n"))
        assert list(line.split("=", 1)[0] for line in wire.rstrip("\n").split("\n")) == ["session", "seq", "npc_id", "action", "text"]
        reply = "session=%s\nseq=%s\nnpc_id=%s\naction=%s\ntext=你好🙂\n" % (fields["session"], fields["seq"], fields["npc_id"], action)
        # Replace the reader with the valid correlated reply.
        lua.globals().getFileReader = lambda *args, r=Reader(reply): r
        now[0] += 300
        ticks[0]()
        assert M.status()["phase"] == "complete"
        assert npc.say == ["你好🙂"]
        assert calls == ([] if action == "none" else [action])
        lua.globals().getFileReader = lambda *args: Reader(reply)
        now[0] += 300; ticks[0]()
        assert npc.say == ["你好🙂"]
        assert M.request("next") is True
        assert "\nseq=2\n" in sink[-1]
        now[0] += 300; ticks[0]()
        assert M.status()["phase"] == "error"  # old seq cannot serve new request
        assert npc.say == ["你好🙂"]

def test_stale_identity_duplicate_unknown_and_malicious_action_rejected():
    lua, sink, _, ticks, now, _ = boot()
    M = lua.globals().DC_AI_TeammateMailbox; assert M.request("x")
    fields = dict(line.split("=", 1) for line in sink[0].rstrip().split("\n"))
    base = "session=%s\nseq=%s\nnpc_id=%s\naction=none\ntext=x\n" % (fields["session"], fields["seq"], fields["npc_id"])
    for bad in (base.replace(fields["session"], "stale_nonce_123456789"), base.replace("seq=1", "seq=2"), base.replace("npc_id=" + fields["npc_id"], "npc_id=7"), base + "evil=x\n", base.replace("action=none", "action=eval"), base.replace("text=x", "text=x\naction=none")):
        lua.globals().getFileReader = lambda *args, r=Reader(bad): r
        now[0] += 300; ticks[0]()
        assert M.status()["phase"] == "error"
        # Every malformed reply must be rejected without consuming or dispatching.
        assert M.status()["pending"] is True

def test_bounds_and_timeout():
    lua, sink, _, ticks, now, _ = boot()
    M = lua.globals().DC_AI_TeammateMailbox
    assert M.request("x")
    lua.globals().getFileReader = lambda *args: Reader("a" * 4097)
    now[0] += 300; ticks[0]()
    assert M.status()["phase"] == "error"
    lua, _, _, ticks, now, _ = boot()
    M = lua.globals().DC_AI_TeammateMailbox; assert M.request("x")
    now[0] += 60001; ticks[0]()
    assert M.status()["phase"] == "error" and "timeout" in M.status()["error"]


def test_request_limits_readiness_and_errors():
    for text in ("x" * 513, "你" * 171, "bad\ntext", "bad\x00", "bad\u202e"):
        lua, sink, _, _, _, _ = boot()
        assert lua.globals().DC_AI_TeammateMailbox.request(text) is False
        assert sink == []
    for phase in ("idle", "spawning", "error"):
        lua, sink, _, _, _, _ = boot()
        lua.globals().DC_AI_Teammate.state.phase = phase
        assert lua.globals().DC_AI_TeammateMailbox.request("x") is False
        assert sink == []
    lua, sink, _, _, _, _ = boot()
    lua.globals().DC_AI_Teammate.state.npcId = "7"
    assert lua.globals().DC_AI_TeammateMailbox.request("x") is False
    assert sink == []
    lua, sink, _, _, _, _ = boot()
    mailbox = lua.globals().DC_AI_TeammateMailbox
    lua.globals().getFileWriter = lambda *args: None
    assert mailbox.request("x") is False
    assert mailbox.status()["pending"] is False
    assert mailbox.status()["seq"] == 1
    lua.globals().getFileWriter = lambda *args: Writer(sink)
    assert mailbox.request("x") is True
    assert "\nseq=2\n" in sink[0]


def test_file_sizes_and_read_bound():
    for size in (4095, 4096, 4097, 100000):
        lua, _, _, ticks, now, _ = boot()
        mailbox = lua.globals().DC_AI_TeammateMailbox
        assert mailbox.request("x")
        reader = Reader("x" * size)
        lua.globals().getFileReader = lambda *args: reader
        now[0] += 300; ticks[0]()
        assert reader.closed
        assert reader.i <= 4096
        assert mailbox.status()["phase"] == "error"


def test_unicode_byte_limits_and_broken_surrogates():
    for text, accepted in (("你" * 170, True), ("你" * 171, False), ("🙂" * 128, True), ("🙂" * 129, False), ("a" * 508 + "🙂", True), ("a" * 509 + "🙂", False)):
        lua, sink, _, _, _, _ = boot()
        assert lua.globals().DC_AI_TeammateMailbox.request(text) is accepted
        if accepted:
            assert "text=" + text + "\n" in sink[0]
    for broken in ("\ud800", "\udc00", "\ud800x", "\ud800\ud800"):
        lua, sink, _, ticks, now, npc = boot()
        mailbox = lua.globals().DC_AI_TeammateMailbox
        assert mailbox.request("x")
        reply = sink[0].replace("text=x", "text=" + broken)
        reader = Reader(reply)
        lua.globals().getFileReader = lambda *args: reader
        now[0] += 300; ticks[0]()
        assert mailbox.status()["phase"] == "error"
        assert reader.closed and npc.say == []


def test_speech_uses_npc_and_failure_does_not_replay():
    for broken in (False, True):
        lua, sink, _, ticks, now, npc = boot()
        mailbox = lua.globals().DC_AI_TeammateMailbox
        calls = []
        def forbidden_halo(*args):
            raise AssertionError('player-only Halo API must not be used')
        lua.globals().HaloTextHelper = lua.table_from({'addText': forbidden_halo})
        lua.globals().DC_AI_Teammate.wait = lambda: calls.append('wait') or True
        if broken:
            def broken_speech(text):
                raise RuntimeError('speech unavailable')
            npc.Say = broken_speech
        assert mailbox.request('hello')
        wire = sink[0].replace('action=none', 'action=wait').replace('text=hello', 'text=你好')
        lua.globals().getFileReader = lambda *args: Reader(wire)
        now[0] += 300
        ticks[0]()
        assert mailbox.status()['phase'] == 'complete'
        assert mailbox.status()['pending'] is False
        assert calls == ['wait']
        if broken:
            assert mailbox.status()['error'] == 'action completed; teammate speech unavailable'
        else:
            assert mailbox.status()['error'] is None
            assert npc.say == ['你好']
        now[0] += 300
        ticks[0]()
        assert calls == ['wait']


def test_speech_target_unloads_after_action_reports_warning_without_replay():
    lua, sink, _, ticks, now, npc = boot()
    mailbox = lua.globals().DC_AI_TeammateMailbox
    calls = []
    def wait_and_unload():
        calls.append('wait')
        npc.getSquare = lambda *args: None
        return True
    lua.globals().DC_AI_Teammate.wait = wait_and_unload
    assert mailbox.request('hello')
    wire = sink[0].replace('action=none', 'action=wait').replace('text=hello', 'text=你好')
    lua.globals().getFileReader = lambda *args: Reader(wire)
    now[0] += 300
    ticks[0]()
    assert mailbox.status()['phase'] == 'complete'
    assert mailbox.status()['pending'] is False
    assert mailbox.status()['error'] == 'action completed; teammate speech unavailable'
    assert npc.say == [] and calls == ['wait']
    npc.getSquare = lambda *args: npc
    now[0] += 300
    ticks[0]()
    assert npc.say == [] and calls == ['wait']


def load_tests(loader, tests, pattern):
    import unittest
    return unittest.TestSuite(
        unittest.FunctionTestCase(fn, description=name)
        for name, fn in sorted(globals().copy().items())
        if name.startswith('test_') and callable(fn)
    )


if __name__ == "__main__":
    tests = [(name, fn) for name, fn in globals().copy().items() if name.startswith("test_")]
    for name, fn in tests:
        fn()
        print("PASS", name)
    print("Passed", len(tests), "mailbox test groups")
