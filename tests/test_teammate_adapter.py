import json
from pathlib import Path
from lupa import LuaRuntime

src = Path(__file__).resolve().parents[1] / 'DC_AIVoice' / '42.0' / 'media' / 'lua' / 'client' / 'DC_AI_Teammate.lua'

class List:
    def __init__(self, items): self.items = items
    def size(self): return len(self.items)
    def get(self, i): return self.items[i]

class Square:
    def __init__(self, x=100, y=200, z=0, free=True): self.x, self.y, self.z, self.free = x, y, z, free
    def getX(self): return self.x
    def getY(self): return self.y
    def getZ(self): return self.z
    def isFree(self, _): return self.free

class World:
    def __init__(self, square): self.square = square
    def getSquare(self): return self.square

class Meta:
    def __init__(self, ident):
        self.ident = ident; self.goal = None; self.sub = None; self.world = World(Square(101, 200, 0)); self.dialogue = None; self.tree_ready = True
    def getId(self): return self.ident
    def getWorldObject(self): return self.world
    def switchDialogueTree(self, x): self.dialogue = x
    def setGoal(self, x): self.goal = x
    def setSubGoal(self, x): self.sub = x
    def getGoalPretty(self): return self.goal
    def getSubGoalPretty(self): return self.sub

class Group:
    def __init__(self): self.members=[]; self.sent=[]
    def joinGroup(self, meta, force): self.members.append(meta)
    def inGroup(self, meta): return meta in self.members
    def sendToGroup(self, meta): self.sent.append(meta)

class Squad:
    def __init__(self): self.values={}
    def setWeaponPreference(self,x): self.values['weapon']=x
    def setWeaponReady(self,x): self.values['ready']=x
    def setFollowDistance(self,x): self.values['distance']=x
    def setFightStance(self,x): self.values['stance']=x

class Api:
    def __init__(self): self.npcs=[]; self.group=Group(); self.squad=Squad(); self.spawned=False; self.spawn_calls=0
    def getNpcs(self): return List(self.npcs)
    def getGroup(self,p): return self.group
    def getSquad(self,p): return self.squad
    def spawnNpc(self, kind, x, y):
        assert kind == 'SurvivorNpc' and isinstance(x,int) and isinstance(y,int)
        self.spawn_calls += 1; self.spawned=True
        meta = Meta(7)
        self.npcs.append(meta)
        return meta

class Player:
    def __init__(self): self.square=Square(); self.moddata={'DC_AI_TeammateNpcId': None}
    def getZ(self): return 0
    def getSquare(self): return self.square
    def getModData(self): return self.moddata

lua=LuaRuntime(unpack_returned_tuples=True)
state={'now':0,'api':Api(),'player':Player(),'grid':Square(101,200,0,True)}
lua.globals().getTimestampMs=lambda: state['now']
lua.globals().getPlayer=lambda: state['player']
lua.globals().getCell=lambda: type('C',(),{'getGridSquare':lambda s,x,y,z: state['grid']})()
lua.globals().KnoxEventLoader=type('L',(),{'getAPI':staticmethod(lambda name: state['api'])})
lua.globals().WeaponPreference=type('E',(),{'ANY':'ANY'})
lua.globals().WeaponReady=type('E',(),{'READY':'READY'})
lua.globals().FollowDistance=type('E',(),{'BALANCED':'BALANCED'})
lua.globals().FightStance=type('E',(),{'STAY':'STAY'})
lua.globals().tellNpcFollow=lambda world, npc: (npc.setGoal('RoamingSubTree'), npc.setSubGoal('FollowSubTree'))
lua.globals().tellNpcStay=lambda npc, x, y, z: (npc.setGoal('RoamingSubTree'), npc.setSubGoal('StaySubTree'))
lua.globals().print=lambda *x: None
lua.globals().Events = lua.table_from({
    'OnTick': lua.table_from({'Add': lambda fn: setattr(lua.globals(), '_tick', fn)}),
    'OnGameTimeLoaded': lua.table_from({'Add': lambda fn: setattr(lua.globals(), '_loaded', fn)}),
})
lua.execute(src.read_text(encoding='utf-8'))
M=lua.globals().DC_AI_Teammate
assert M.start is not None, 'adapter must export start'
assert M.follow is not None and M.wait is not None, 'adapter must export follow and wait'
assert M.start() is True
assert state['api'].spawned and state['api'].spawn_calls == 1
state['now']=100; lua.globals()._tick()
assert M.state['phase']=='following' and M.state['npcId']=='7'
assert state['player'].moddata['DC_AI_TeammateNpcId'] == '7'
assert len(state['api'].group.members)==1 and state['api'].group.sent[0].ident==7
assert state['api'].group.members[0].goal=='RoamingSubTree' and state['api'].group.members[0].sub=='FollowSubTree'
assert state['api'].squad.values == {'weapon':'ANY','ready':'READY','distance':'BALANCED','stance':'STAY'}
assert M.wait() is True and M.state['phase'] == 'waiting'
assert M.follow() is True and M.state['phase'] == 'following'
def reset():
    state.update(now=0, api=Api(), player=Player(), grid=Square(101,200,0,True))
    lua.globals().DC_AI_Teammate = None
    lua.execute(src.read_text(encoding='utf-8'))
    return lua.globals().DC_AI_Teammate

for bad_grid in (None, Square(free=False)):
    adapter = reset()
    state['grid'] = bad_grid
    assert adapter.start() is False
    assert adapter.state.phase == 'error' and state['api'].spawn_calls == 0

adapter = reset()
def broken_spawn(*args):
    state['api'].spawn_calls += 1
    raise RuntimeError('injected spawn failure')
state['api'].spawnNpc = broken_spawn
assert adapter.start() is False
assert 'injected spawn failure' in adapter.state.error
assert adapter.start() is False and state['api'].spawn_calls == 1

adapter = reset()
state['player'] = None
assert adapter.start() is False and adapter.state.phase == 'error'
adapter = reset()
state['api'] = None
assert adapter.start() is False and adapter.state.phase == 'error'

adapter = reset()
assert adapter.start() is True
state['now'] = 30001
lua.globals()._tick()
assert adapter.state.error == 'spawn timeout'

adapter = reset()
assert adapter.start() is True
assert adapter.start() is False and state['api'].spawn_calls == 1
state['api'].npcs.extend([Meta(8), Meta(9)])
lua.globals()._tick()
assert adapter.state.npcId == '7'
assert [n.ident for n in state['api'].group.members] == [7]

for missing in ('group', 'squad'):
    adapter = reset()
    setattr(state['api'], missing, None)
    assert adapter.start() is False
    assert state['api'].spawn_calls == 0

adapter = reset()
assert adapter.follow() is False
assert adapter.wait() is False
def reload_adapter():
    lua.globals().DC_AI_Teammate = None
    lua.execute(src.read_text(encoding='utf-8'))
    return lua.globals().DC_AI_Teammate

# Reload must recover only the saved member, never recruit a replacement.
for saved_state in ('member', 'missing', 'outsider', 'unloaded'):
    adapter = reset()
    exact, other = Meta(42), Meta(99)
    state['api'].npcs = [other] if saved_state == 'missing' else [other, exact]
    state['api'].group.members = [other]
    if saved_state in ('member', 'unloaded'):
        state['api'].group.members.append(exact)
    if saved_state == 'unloaded':
        exact.world = None
    state['player'].moddata['DC_AI_TeammateNpcId'] = '42'
    adapter = reload_adapter()
    assert adapter.start() is (saved_state == 'member')
    assert state['api'].spawn_calls == 0
    assert state['api'].group.sent == []
    assert other.goal is None and other.sub is None
    assert exact.goal is None and exact.sub is None
    assert state['player'].moddata['DC_AI_TeammateNpcId'] == '42'
    if saved_state == 'member':
        assert adapter.state.npcId == '42'
    else:
        assert adapter.state.phase == 'error'

# Both commands fail without mutating any NPC when prerequisites disappear.
for command in ('follow', 'wait'):
    for unavailable in ('player', 'api', 'group', 'membership', 'world', 'square', 'exception'):
        adapter = reset()
        assert adapter.start() is True
        lua.globals()._tick()
        exact = state['api'].npcs[0]
        other = Meta(99)
        state['api'].npcs.insert(0, other)
        exact.goal, exact.sub = 'sentinel', 'sentinel'
        if unavailable in ('player', 'api'):
            state[unavailable] = None
        elif unavailable == 'group':
            state['api'].group = None
        elif unavailable == 'membership':
            state['api'].group.members = [other]
        elif unavailable == 'world':
            exact.world = None
        elif unavailable == 'square':
            exact.world.square = None
        else:
            def broken_membership(meta):
                raise RuntimeError('membership lookup failed')
            state['api'].group.inGroup = broken_membership
        assert getattr(adapter, command)() is False
        assert adapter.state.phase == 'error'
        assert (exact.goal, exact.sub) == ('sentinel', 'sentinel')
        assert other.goal is None and other.sub is None

# Identity is persisted before setup fails, including pre-membership failures.
for failure in ('group', 'squad', 'dialogue'):
    adapter = reset()
    assert adapter.start() is True
    exact = state['api'].npcs[0]
    assert adapter.state.npcId == '7'
    assert state['player'].moddata['DC_AI_TeammateNpcId'] == '7'
    if failure in ('group', 'squad'):
        setattr(state['api'], failure, None)
    else:
        def broken_dialogue(tree):
            raise RuntimeError('dialogue setup failed')
        exact.switchDialogueTree = broken_dialogue
    lua.globals()._tick()
    assert adapter.state.phase == 'error'
    assert adapter.state.npcId == '7'
    assert state['player'].moddata['DC_AI_TeammateNpcId'] == '7'
    adapter = reload_adapter()
    adapter.start()
    assert state['api'].spawn_calls == 1

print(json.dumps({'status':'pass','coverage':'exact spawn return, spawn once, STAY, persistence, reload recovery/fail closed, command membership/world checks and exceptions, finish failure identity, follow/wait, unloaded/blocked tile, spawn exception, missing player/API/group/squad, timeout, unrelated NPCs, missing teammate'}))
