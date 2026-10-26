# NPC teammate integration — verified progress

## Objective
Build and test an actual AI teammate, not invulnerability or healing. Goal remains active; NOT complete.

## Verified 2026-10-25
- Game: 42.21.0. Actual NPC Workshop item 3397396843, KnoxEventExpandedNpc v0.4.0-13. Earlier 3594208822 was a collection, not NPC mod.
- Dependency ZombieBuddy item 3619862853, agent v2.3.4.
- Windows normal launcher corrected to `-agentlib:zbNative` in ProjectZomboid64.json vmArgs (no ` --` inside JSON argument). DLL/JAR in game directory. Official installer source confirms this argument. Main game PID 3548 launched at 01:36:56; not controlled or attached by our old agent in this process. Do not force-kill it.
- Original Rising/2026-10-24_20-11-39/mods.txt restored to backup content. No NPC added to original save. Original default.txt not changed.
- Isolated profile: ai-mod/test-profile. Contains only ZombieBuddy and KnoxEventExpanded copies. Correct mod ID is KnoxEventExpandedNpc (not folder name).
- Fresh profile first startup reset default.txt despite reset marker. Rewrote default.txt after initialization, second test recognized both mods.
- Startup test via bundled Java with classpath .;projectzomboid.jar, cwd game dir, -cachedir=<absolute test-profile>, -nosteam, -Dzomboid.steam=0. Agent options config_dir=<test-profile>/zb-config,policy=deny-new,exit_after_game_init. Explicit test-only hash-pinned approvals for just these two JARs, no global allow-all.
- startup-second.log: lines 214-223 recognized two mods, added Knox jar; 442-450 loaded both; exit code 0. Main-menu init only, NOT NPC behavior verified. Several optional/intra-mod Lua require warnings remain at 515-527. Font/vanilla fluid warnings also present.
- All managed jobs collected: pwsh-115a5ef32e404fc0 and pwsh-e09f54e43dbb4dfc exit 0. Agent fd305003-cd95-413b-9eeb-d52086f1e6d6 finished read-only API research.

## API evidence from installed Knox mod
KnoxEventLoader.getAPI('npc'), initialized OnGameTimeLoaded. Main-thread only.
- DebugMenu.lua spawn: api:spawnNpc('SurvivorNpc',x,y). Return type unknown; ground floor only (no z arg). Snapshot api:getNpcs() IDs before; on later bounded ticks identify newly created ID and world object. Do NOT choose nearest unrelated NPC.
- meta:getWorldObject(), worldNpc:getMetaCharacter(), meta:getId(). api:getWorldNpcs() lists live world entities.
- api:getGroup(player); group:joinGroup(meta,true); verify group:inGroup(meta); group:sendToGroup(meta); meta:switchDialogueTree('GroupDialogue'). Forced recruitment bypasses acceptance, not damage.
- Follow meta:setGoal('RoamingSubTree'); meta:setSubGoal('FollowSubTree').
- Wait helper tellNpcStay(meta,x,y,z): sets StaySubTree, sets MovementSubTreeTargetX/Y/Z on its MovementSubTree child.
- api:getSquad(player): setWeaponPreference(WeaponPreference.ANY), setWeaponReady(WeaponReady.READY), setFollowDistance(FollowDistance.BALANCED), setFightStance(FightStance.STAY/AGGRESSIVE/DISENGAGE).
- getGoalPretty/getSubGoalPretty and group:getGroupNpcMembers for telemetry.
- forceJoinGroup helper has wrong isNpcInGroup argument count: use direct API instead.
- leaveGroup doesn't undo spawning. Use disposable save and restore for rollback.

## Next
Create scoped main-thread companion adapter + test telemetry, in separate local mod/profile. Test game world startup safely without original save, actual spawn/recruit/follow/stay/combat, then model bridge integration. Existing bridge config has empty API key; real LLM connection not demonstrated. Do not claim end-to-end until tested. Can use ZombieBuddy startup exit flag for repeatable smoke tests, but remove for world behavior tests. No GUI control tool implicit; if automating Lua, use actual game main-thread event, never background RunLua.

## Round 4 additions
- Adapter created: ai-mod/DC_AIVoice/42.0/media/lua/client/DC_AI_Teammate.lua. Main-thread only, OnTick-driven spawn acknowledgment, timeout 30s, no heal/god. Uses verified API sequence and WeaponPreference.ANY etc. Squad currently AGGRESSIVE for first live verification.
- Unit test with lupa (Lua 5.4) passed 2026-10-25: ai-mod/tests/test_teammate_adapter.py prints {"status":"pass","phase":"following","npcId":"7",...}. This validates adapter control flow offline, NOT game behavior.
- Isolated mod installed: ai-mod/test-profile/mods/DC_AI_Teammate (id DC_AITeammate, versionMin 42.21), enabled in default.txt after ZombieBuddy/KnoxEventExpandedNpc.
- Subagent 4e348b2e-0eb9-498d-8ac2-3609a6d03ec7 researching automated disposable world creation from main menu; pending.

## Important prior errors
Earlier assistant claimed hp=1.0 was full and god flag guaranteed safety; these were unverified and user died. Do not reuse heal/guard agents. Current request explicitly rejects godmode. Existing guardagent.jar built but no evidence attached. Earlier code has health/timing/encoding bugs. Screenshot content was not actually inspected by earlier text-only model; font diagnosis was not established.
