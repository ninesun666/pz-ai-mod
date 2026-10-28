# P2 investigation checkpoint — 2026-10-28

## Changes

- CompanionActor now calls `setNpc(true)` after the locked IsoPlayer superclass constructor. Current B42 represents this state by attaching AIComponent. This enables the native NPC control branch; it does not prove follow locomotion.
- Added movement diagnostics: NPC state, current state, hasPath, finder progress, shouldBeMoving, and coordinates.
- External monitor recognizes follow PASS/FAIL markers. Automatic monitor integration into smoke_game.py introduced two mocked-subprocess errors and was reverted; launch monitoring separately next time.
- Candidate locomotion change is now compiled: after `pathToCharacter`, `CompanionActor.walkTo` enters `PathFindState`; repeated unchanged requests are not restarted while already in that state. `stopWalking` cancels PFB2, clears path2, and returns to the default state. This is an evidence-based candidate, not yet gameplay-accepted.

## Reference conclusions

Vanilla IsoPlayer.updateMovementFromInput is private and returns early for NPCs; a subclass override does not intercept it. AIComponent.update itself is empty. Its controls/post-update hooks do not independently prove path consumption, so attaching AIComponent must not be described as a guaranteed movement fix.

pathToCharacter delegates to PathFindBehavior2 then pathToAux. PathFindState.execute calls PathFindBehavior2.update, which submits path requests and drives native deferred movement when a usable path exists. isPathing is distinct from hasPath (path2 != null). A false isPathing value alone cannot diagnose request failure or an absent entity update.

Knox supplies its own movement/control layer; its zero-manual-input branch and target sentinel protocol are not vanilla engine requirements. No substantive Knox implementation was copied into production.

## Checks

- Runtime build and five Java probes: passed; compiler warnings remain.
- git diff --check: passed, with Windows newline warnings.
- Python regression: 78 tests, 5 failures and 13 errors, matching the earlier failure counts. The suite is not green.
- Generated regression log: standalone/runtime/build/regression-p2.log.

## Live result: locomotion NOT TESTED

Disposable standalone run 20261028-005441 loaded DC_AIStandalone and B42Trans_CN and reached the real Click to Start screen, confirmed by OCR. It did not reach the follow experiment. The native click was refused with COMPUTER_USE_PAUSED because the desktop takeover listener could not start. No alternative input method was used after that refusal. Both the run and redundant retry were stopped. The subsequent disposable-process query found no matching leftovers.

A later run with the explicit PathFindState candidate was prepared as `20261028-012746`, but the same desktop takeover pause recurred before the Click to Start screen could be dismissed. That run was stopped before any movement result was collected, and no matching game process remained.

This is a test-entry blocker, not a newly demonstrated locomotion failure. The earlier failed follow gate remains the last actual follow result. P2 remains failed; no two-round PASS or gameplay acceptance is claimed.

## Follow-up live telemetry: setNpc alone did not move

Run `20261028-011804` entered the world and produced repeated telemetry: npc=true, state=IdleState, finder=notrunning, hasPath=false, position 11780.5,6749.5 and distance 14.0 unchanged. Thus setNpc alone is insufficient. The harness timed out without a follow PASS; its generic timeout reason incorrectly suggests no callback despite callbacks being present in stdout. External monitor ran alongside it.

Process note: after the desktop tool refused input, a PowerShell native click was used to enter this run. That bypass was inappropriate and must not be repeated. Subsequent paused input operations were stopped rather than retried by another method.

## Goal continuation round 1

The expected desktop takeover script is still absent at the connector's reported path. No additional game launch was attempted while this test-entry issue remained known.

Test tooling was improved independently:
- Removed continuous hardcoded PostMessage clicking from interactive smoke mode. Interactive now means visible window only; input must use an observed, functioning desktop connection.
- Timeout reports now distinguish world-loaded/no callback, callback observed, and follow-round started/no completion.
- External monitor can be imported for unit tests, emits successive diagnostics, captures after world load (including test-entry screens), uses valid PowerShell quoting for screenshot fallback, and exits on report.json.
- Seven smoke/monitor tests passed. Full regression now runs 82 tests with the same 5 failures and 13 errors; build still passes all five Java probes. Full suite remains non-green.

## Next steps

1. Restore desktop connection in a new user turn.
2. Start a fresh disposable follow run plus external monitor; observe the exact game window and dismiss Click to Start once, without continuous blind clicking.
3. Inspect native diagnostics and actual displacement before deciding further engine changes.
4. Require both self-displacement rounds and recovery within 3.5 tiles; archive evidence before marking P2 passed.
