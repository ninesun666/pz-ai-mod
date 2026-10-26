# Real-game initialization smoke result

Run `20261027-021239`, isolated cachedir, PID 26012:

- Loaded the project-owned self-contained Java agent; launch command had no Knox/ZombieBuddy mod or `zbNative` argument.
- Actual game stdout reported `[DCStandalone] bridge installed on MainThread`.
- Harness observed the marker after 16.97 seconds and terminated its own process; exit code 1 reflects forced termination, not a clean normal game exit.
- Raw game stderr also reported missing font-page textures. Those errors are not resolved by the bridge result and healthy visible startup has not been established.
- An older separate test instance was already running. No operations were sent to it; this result is restricted to class/Lua initialization, not rendering or input acceptance.

Durable raw evidence is generated under `standalone/runtime/build/runs/20261027-021239/` (ignored runtime output): `report.json`, `stdout.log`, `stderr.log`.

**Pass scope:** real B42 Lua initialization invokes our own bridge on MainThread. **Not tested:** gameplay OnTick thread assertion, world actor, appearance, movement, mouse, or save/reload.
