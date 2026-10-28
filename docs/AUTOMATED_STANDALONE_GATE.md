# Automated standalone gate

Run from `ai-mod`:

```powershell
./standalone/runtime/test.ps1 -Build
```

The gate runs all `test_standalone*.py` checks, `git diff --check`, and optionally the real B42 API ECJ build. It currently verifies source boundaries, stable identity persistence, fail-closed runtime probing, and Java compilation/packaging. It explicitly prints that this is **not gameplay acceptance**.

The gate does not launch a game, modify saves, or claim that a character is visible or controllable. Gameplay acceptance remains a separate manual/instrumented stage requiring a disposable profile.

## Unattended world entry (2026-10-28): the Click-to-Start blocker is gone

Why follow-gate runs stalled on 2026-10-28 while spawn passed: the spawn marker
fires during world load, but the follow gate needs gameplay ticks, and
`GameLoadingState.update()` holds the game at the post-load "Click to Start"
phase until `Mouse.isButtonDown(LMB)` or joypad A (verified by javap against
B42.21 projectzomboid.jar; the state's only exit sets private `forceDone`).
OS-level clicks needed desktop takeover, which is exactly what we do not have.

`AutoInputDriver` (`-Ddcai.autoGate=1`, passed by smoke_game.py for every
`--world` run) closes the loop inside the game JVM:

- `Mouse.isButtonDown(i)` is a direct read of the public static
  `Mouse.buttonDownStates` array — writing that array IS the game's input
  pipeline, no OS input involved.
- The driver holds LMB true only while `GameWindow.states.current` is
  `GameLoadingState`, and actively holds LMB false otherwise, so a synthetic
  press cannot leak into gameplay UI.
- Test-only, disposable-profile only; never run with a real profile.

Result: `smoke_game.py --world --gate follow` is now a fully unattended,
bounded (timeout + terminate/kill), evidence-writing loop — build, launch,
world entry, follow stimulus, verdict, report.json, cleanup. No human input at
any stage.
