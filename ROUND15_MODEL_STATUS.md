# Round 15 continuation: real model bridge verified

User supplied endpoint `192.168.1.3:8080` and a credential in chat; authorized for this test. Credential value omitted from this record and package. Model listing succeeded at `/v1/models`; selected `gpt-6-astra`.

Direct `call_model` through teammate_bridge returned strict valid decision: action=wait, text=`I'll wait here. Be careful out there.`

Actual `TeammateBridge(config=ModelConfig(...))` request/reply roundtrip then used test-profile/Lua private mailbox with fresh nonce, exact seq=1, npc_id=131. Parsed reply confirmed session_match=true, seq_match=true, npc_match=true, action=wait, same model text. This proves real endpoint -> bridge -> strict correlated wire, but NOT live game action because no game process was running; request/reply files are test mailbox artifacts.

Attempted UI live verification: UI source/deployed hash match. UI1 created disposable world due config then saved/quit; UI2 reload screenshot capture unavailable to model image reader; UI3 correctly refused unverified click because SetForegroundWindow handle check failed, no click sent. No real UI menu/glyph proof. No native game jobs remain.

Important: key appeared in user message and was used in-memory only. Do not include it in final response or artifacts. If user wants stronger end-to-end, need run bridge watch with real live game and verified foreground input; also avoid stale request artifacts. Goal remains active.
