
## Round 8 final evidence
- Native6 was the first successful end-to-end gameplay run after closing Knox procgen setup and advancing game speed.
- live-native6.log lines1356-1365: real NPC Sharron id121 phased in, exact `spawnNpc` return true, group accepted, `following npc=121`, and procgen setup closed without export.
- Lines1366-1378: `speed=1`, player updates active, `member=true`, initial `goal=Roaming sub=Follow`; live `WAIT result=true` changes goal to `Stay`; live `FOLLOW result=true` changes back to `Follow`.
- Lines1391 onward repeatedly show stable following state and membership. This verifies real in-game follow/wait/follow command dispatch and persistence during active updates. We did not force player displacement successfully; coordinates remained fixed during attempted keyboard input, so physical pursuit movement is not proven. No combat test.
- Native6 process was stopped after evidence and managed job collected with deliberate JVM -1.
- Offline tests pass: adapter expanded regression coverage; teammate_protocol 17 unittest tests; bridge clock Lua regression. Protocol module is standalone and not yet wired into bridge/adapter. Existing bridge remains radio state/reply only; no real API key configured and no model roundtrip.
- Therefore objective is substantially implemented but not fully complete as a model-driven teammate: real model command integration, combat, physical movement, and save/reload live test remain. Keep goal active.
