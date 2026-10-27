# Round 12 evidence

## Complete local verification
`python -m unittest discover -s ai-mod/tests -p test_*.py`: 30 unittest cases passed (bridge13+protocol17), adapter and UI import-time checks passed. Mailbox plain-function groups require direct script execution; last separately verified 6 groups in round11.

## Real native Unicode
Native10 exact request was generated using ASCII-source `string.char` UTF16 units (compiler corrupts non-ASCII Lua literals). Python parsed exact Chinese+emoji request and wrote correlated Chinese+emoji wait reply. Native mailbox reached phase=complete and adapter waiting/Stay at lines1456-1477 of live-native10.log. This proves actual file transport and action dispatch, but not glyph rendering.

## Real save/load attempt
Create test `live-save1.log`: disposable world DC_AITeammate_6020122841, NPC116; save manifest ai-mod/test-profile/Lua/dc_teammate_persistence.txt; log lines1429/1438 show save(true) and normal quitToDesktop request. GameWindow save start/end lines875-881.
Reload test used exact name and expected NPC116; log line504 RELOAD and lines654-655 load complete. However no RECOVER log appeared after load, so the test harness's OnPlayerUpdate recovery branch did not execute (likely reload startup event/loaded player callback issue). Therefore saved NPC identity recovery is NOT proven. The test failed closed/no replacement and process was stopped. Do not claim recovery.

## Follow-up diagnosis and correction
The reload1 failure root cause is concrete: its saved mods.txt was empty (read verified). Bootstrap bypassed the stock new-game step that copies default mods to currentGame; reload therefore legitimately disabled Knox and teammate Lua. Not a proven NPC persistence failure. Added stock `ActiveMods.getById("currentGame"):copyFrom(ActiveMods.getById("default"))` before createWorld. Redundant reload2 stopped, job pwsh-f2152e05f0ff4193 collected.

Corrected create run live-save2.log completed normally (job pwsh-54a0fdbf6dc047ab JVM exit0). Manifest now DC_AITeammate_1811762178 / NPC146. Lines1459-1468 save request+return/normal quit; actual saved mods.txt read verified ZombieBuddy, KnoxEventExpandedNpc, DC_AITeammate, DC_AITeammateTest all persisted. Test config now reload exact corrected world/NPC146. NEXT run live-reload3 completed: lines1365-1368 saved id146==expected146, adapter recovered npc146, result=true phase=recovered, member=true goalRoaming subFollow, NPC11786.5,6748.5 / player11787.749,6750.673. This proves same-ID live recovery after full normal save+process restart, without replacement spawn. PID32764 stopped after proof; job pwsh-a93f3d8f9cab4957 collected. All jobs collected, no test process left.

## Remaining work
No combat live test; no visual UI click/render test; no real model API key/roundtrip; no proven save/reload recovery. UI source-only current menu may have attachment/loading issues and needs live test. Source mailbox newest runtime ASCII-safe probe deployed only isolated test profile, production source not packaged. Goal remains active.
