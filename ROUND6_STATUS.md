# Round 6 — verified live recruitment, not end-to-end completion

## Actual live evidence
- Managed job pwsh-8a4754b855b940f9 collected: JVM -1 from deliberate termination. Test process PID 29104 stopped. No live test left running.
- `test-profile/live-native3.log:1381-1389`: exact live NPC Cori id 146 phased in; adapter requested spawn; group accepted (chance to refuse 0); adapter logged `following npc=146 goal=Roaming sub=Follow`. The adapter only logs this after group:inGroup(meta) succeeds and squad configuration is applied. This verifies live spawn/world object/recruitment/goal setting, NOT observed following movement.
- Moving startup to first OnPlayerUpdate instead of OnGameTimeLoaded fixed the earlier startup timing issue. Previous runs spawned during loading before Knox initialized player metadata.
- Test options now focusloss=false, windowed 1280x720, welcome/survival guide disabled. However no periodic status lines were observed after first frame before termination; inspect pause state before assuming lack of ticks is an adapter issue.
- Test runner now contains future WAIT/FOLLOW staged commands plus position/membership telemetry (60/180 player updates). These changes were made after launch and have NOT run in the live game yet.

## Source/API correction
- Read-only child eb4517de-bf62-48c7-b6d6-a0c3e5009dc5 completed. Installed Java API confirms spawnNpc(String,int,int) synchronously returns MetaNpcCharacter; getNpcs holds MetaNpcCharacter. Dumps in tests/knox-javap-*.txt.
- Adapter now retains exact returned spawn meta, prefers it over global list differences, and checks group and squad before spawning. These latest fixes are OFFLINE-tested but not yet live-tested.
- Latest direct test passed: `python ai-mod/tests/test_teammate_adapter.py` covers exact spawn return, unrelated NPCs, spawn once, missing player/API/group/squad, blocked/unloaded tile, timeout, follow/wait, modData write. Follow/wait helpers remain mocks, not real behavior-tree coverage.
- IMPORTANT deployment folder mismatch: actual enabled mod with mod.info is `test-profile/mods/DC_AI_Teammate`, NOT `DC_AITeammate`. Several copy commands wrote to latter unused folder. Next run must read actual enabled Lua then sync newest adapter to DC_AI_Teammate. live-native3 used an earlier adapter that did successfully recruit. Do not silently assume latest source was live-tested.
- New test modifications have not addressed safe respawn after Lua reload, membership validation for commands, full actual save/reload, controlled follow displacement, waiting position, combat, or model integration.

## Next steps
1. Sync actual enabled adapter folder, verify hash; inspect/test runner before next launch.
2. Run native4 with staged wait/follow telemetry. Diagnose post-first-frame pause (do not use off-thread Lua or unsafe attach agents). Need observed movement, not merely goals.
3. Add validated command protocol and model bridge; config currently lacks configured API credential. Do not claim a real model roundtrip from offline canned responses.
4. Keep original Rising save and normal ProjectZomboid64 process untouched.
