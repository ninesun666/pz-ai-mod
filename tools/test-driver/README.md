# Isolated session test tools

`DCTestDriver.lua` in this directory is the authoritative test-only source. The
previous identical copies were discovered under `driver-profile` and
`test-profile`; they are ignored deployment artifacts, not independent sources.
From the ai-mod root, explicitly synchronize only these Lua files:

```powershell
./tools/sync-test-driver.ps1 -ProfileName driver-profile,test-profile
```

This never touches shared gameplay mods, mod lists, Java/IME code, or config.
An already-running game's loaded Lua is not changed by copying a file; this work
does not restart/reload any game.

## CLI transport

`pwsh -File` does not preserve PowerShell array syntax across its process
boundary. Do not pass `-Steps 'cmd=ping','cmd=snapshot'` there. Use one JSON
argument, or (best across differently quoting shells) a UTF-8 JSON file:

```powershell
pwsh -File ./tools/run-session.ps1 -StepsJson '["cmd=ping","cmd=snapshot"]' -ValidateOnly
pwsh -File ./tools/run-session.ps1 -StepsFile ./steps.json -ValidateOnly
```

The file contains `["cmd=ping","cmd=snapshot"]`. `-ValidateOnly` validates and
prints the exact array, then exits BEFORE process checks, logs, mailbox writes,
or game launch. In the same PowerShell process, `& ./tools/run-session.ps1
-Steps @('cmd=ping','cmd=snapshot') -ValidateOnly` is also supported. Mixed
input modes, non-array JSON, malformed commands, duplicate/reserved fields and
comma-joined legacy input fail early rather than being split heuristically.

**Without `-ValidateOnly`, the runner still launches its isolated game profile.**
Do not run it merely to test argument parsing. This change did not validate the
existing launcher JVM/agent arguments.

Defaults are ping and snapshot only. Save, teleport, speed and IME operations
remain explicit opt-in protocol commands, never appended automatically. Quit
is rejected by the runner and disabled in Lua; no save-before-quit,
Runtime.exit call, kill fallback or automatic shutdown exists. `-NoQuit` is a
compatibility no-op. Operators must manage the game lifecycle themselves.

## Protocol v2 and limitations

Requests/replies carry `session=<token>;seq=<positive integer>`. The runner
uses a new GUID and requires `protocol=2` in the ready marker. The driver binds
to the first valid session for its lifetime, rejects another session and
stale sequences, and catches execution errors while echoing the request
identity. Missing/invalid identity reports `session=invalid;seq=0` and fails
closed. Repeated identical mailbox content is not executed again. Mailbox
writer failures are logged, not reported as success. Sequence/session state
is not persisted across a game restart. The mailbox is not an authentication
boundary; do not use it with a shared or valuable world.

Offline verification: `python -m unittest discover -s tests -p test_session_tools.py -v`.
Tests run actual pwsh `-File` parsing in validation-only mode and Lua through
Lupa with mocked file/game APIs. They are not in-game acceptance evidence.
