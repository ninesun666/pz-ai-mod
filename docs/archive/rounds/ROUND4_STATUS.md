
## Live world attempt, round 4
- Added test-only mod DC_AITeammateTest under isolated profile. Auto-launch main menu via DebugScenarios stock sequence with unique checked name, no original saves.
- Managed job pwsh-813266e808bb40a6 collected. Test Java process 19532 was stopped after log remained at TISLogoState exit; JVM exit -1 is deliberate termination, not passing test. No evidence OnMainMenuEnter / world startup executed. Need diagnose before repeating (thread dump or window inspection).
- live-first.log loads both DC_AITeammate and DC_AITeammateTest at 451-452; no world-start evidence. Test runner currently does NOT auto-call adapter.start after world loading; add bounded OnGameStart/OnTick sequence and telemetry before next run.
- Duplicate accidental folder test-profile/mods/DC_AITeammate contains only copied Lua, NO mod.info; actual enabled folder is DC_AI_Teammate. Do not confuse the two. No files deleted to clean this yet.
- Adapter now rejects multiple newly discovered NPC candidates, latches spawnAttempted, and catches OnTick errors. Still needs: safe candidate attribution beyond global new ID, loaded/clear spawn tile check, safe STAY initial stance, follow/wait command API, persistence, tests of failures. Not production-ready.
- Unit test last passed before final spawn latch/pcall changes; rerun before claiming current version tested. Lua runtime used is lupa default (not Kahlua); live verification required.
- Subagent 4e348b2e-0eb9-498d-8ac2-3609a6d03ec7 complete. Direct DebugScenarios launch doesn't require -debug. MainScreen initializes characters first if require before handler. Original main menu routinely deletes Tutorial/LastStand saves: use isolated cachedir always. MainScreen:setDefaultSandboxVars called before scenario settings now.
