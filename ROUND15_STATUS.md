# Round 15: UI verification attempt, not a pass

Goal active. No real DeepSeek config path supplied since user's selection of DeepSeek API; do not search secrets.

Verified production/deployed teammate UI SHA256 match269219F90040B4466FC608E8A2C1410A634A54A749E616CBA018F4675F5C4D26.

live-ui1 inadvertently ran existing create/save automation, exited normally0, disposable worldDC_AITeammate_9534980797/NPC131 (save request1444 and return1453). This is NOT a UI interaction test. Config changed to exact reload of that world, combat=false.

live-ui2 captured desktop to ui-screen.png, but read_image tool rejects model image input. Cannot visually inspect screenshot or claim glyph/menu rendering. Process3596 stopped, jobpwsh-758296d8629c4000 collected.

Added disposable-only DC_AI_UIObserve.lua: requires production UI, listens actual OnFillWorldObjectContextMenu after UI registration, logs root option names and AI teammate presence. No synthetic trigger or callback execution. Bootstrap now explicitly requires observer in create/reload paths; startup call restored and read-back verified after edit.

live-ui3 PID27616: SetForegroundWindow returned false, verified handle inequality threw before any clicks. Process responding; stopped only verified isolated PID. Jobpwsh-3930b3a043b14c57 collected. No DC_UI_LIVE or recovery records, only stock mannequin error. No claims of actual menu execution. Foreground denial is environmental, not a proven mod failure. Image-input unsupported and foreground unavailable prevent current interactive observation; later native event telemetry still possible after user foregrounds game.

All game jobs stopped/collected; ui1 jobpwsh-b5b9580cdbf449c9 also collected. Existing preview package unchanged and prior core movement/combat/reload proofs remain. UI actual clicks/speech glyphs and configured model roundtrip still unverified. Do not mark goal complete or blocked yet.
