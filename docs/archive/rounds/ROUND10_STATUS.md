# Round 10 live evidence

Native8 disposable world DC_AITeammate_1061484436, NPC126. Exact isolated PID32680 stopped and managed job pwsh-35d2b5e56dd04374 collected (deliberate JVM -1).

## Actual pursuit verified
live-native8.log line1393 ordinary ISWalkToTimedAction requested player route. Lines1396-1438: player moves from11778.5,6749.5 toward11787.75,6750.673; NPC remains member=true/Follow and moves from11777.5,6747.5 via11781.319,6746.5 to11786.5,6748.5. This is actual physical pursuit, not just goal assignment. Player did not reach requested final tile11786,6753; no claim complete path traversal.

## Actual mailbox dispatch verified, simulated decision only
line1426 request=true; game wrote test-profile/Lua/dc_teammate_request.txt. Parent parsed via teammate_protocol and wrote atomic correlated ModelReply(action=wait,text='[transport test] Waiting here.'). Lines1475-1477 mailbox phase=complete, adapter waiting, actual sub=Stay, membership true. Rewrote SAME consumed session/seq1/NPC126 reply with action=follow and '[replay test] Must not execute.'. Lines1593-1611 remain complete and Stay, confirming no redispatch after consumption. No model was called.

## Remaining
Chinese Kahlua Unicode compatibility CONFIRMED broken in current deployed mailbox: actual jar executable probe shows byte('中')=20013, char(228,184,173) yields mojibake, emoji has UTF16 surrogates. Evidence tests/KahluaUnicodeProbe.evidence.txt. Child23bd15a7-3bd5-46ac-8abe-358c2a80bd3a now fixing source mailbox/tests with runtime UTF16-vs-UTF8 detection, scalar validation/byte counting, preserving native code units. Do not deploy until reviewed/tested. ASCII proven live.

Added source-only DC_AI_TeammateUI.lua: single-player opt-in right-click menu recruit/recover, follow, wait, message text box, status. test_teammate_ui.py passes mock callback wiring, gating, submit/cancel; UI NOT deployed or live-rendered yet.
Combat, real save/reload identity, player-facing controls/install package, actual configured model roundtrip remain. No model credential present in known config/environment as last checked. Goal remains active.
