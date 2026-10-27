# Round 16: actual model-to-game action verified

Native live-model1.log lines1370-1386: exact saved NPC131 recovered in group, Follow. Test-only Lua issued fresh request at tick180 using production mailbox. A bounded Python watcher ignored previous session, invoked actual authorized local endpoint /v1/chat/completions model gpt-6-astra through TeammateBridge, and atomically wrote correlated reply. Returned action wait, text 'Got it. I’ll hold this position.' Session/NPC/seq matched.

At tick480 native mailbox complete error=nil; adapter waiting npc131; engine goalRoaming/subStay member=true. Thus actual game request -> real remote model -> correlated mailbox -> exact physical NPC wait is proven. Initial stale reply was rejected (ticks240-420) before valid reply arrived; no stale action executed. Speech method completed without error, but visible glyph rendering still unverified.

Game PID10828 stopped only after test-profile commandline validation, no save. Jobpwsh-9caf1ee5613f439d collected; bounded watcher jobpwsh-c9c136852e384f76 completed and collected. Credentials used in test command only, not in package/config/status. No original save modified.

New disposable DC_AI_ModelLiveTest.lua currently auto-loads and will issue request on recovery: must add explicit opt-in before future UI testing. No production source changes. UI actual clicks and visual speech still need verification; package native clean install not yet independently proven. Keep goal active.
