# Standalone smoke evidence

- Game build: Project Zomboid B42 `42.21.0 4a0e9546ec`.
- Profile: each run uses a fresh disposable profile under `standalone/runtime/build/runs/`.
- Runtime: own Java premain agent; no Knox or ZombieBuddy runtime dependency.
- Mod loading: passed after seeding `options.ini`; run `034429` reports `loading DC_AIStandalone`, `active mods=[DC_AIStandalone]`, `discovered=true`.
- Lua loading: passed; run `034429` reports `[DCStandaloneTest] bootstrap loaded`.
- Detached entity construction: **passed after game-data initialization** in run `20261027-042731`, stdout line 171: `[DCStandaloneTest] detached constructor PASS on MainThread`. The probe constructed the own `CompanionActor`, checked it remained detached with no current square, and queried its HumanVisual/ItemVisuals. This does not prove world attachment or rendering.
- Terms gate: the corrected diagnostic in run `20261027-042731` reached `TermsOfServiceState` with `terms=true`, `main=false`, `termsVersion=-1`. No diagnostic exception occurred. Automated runs do not accept terms on the user's behalf; a human consent action in the disposable test window is required once before automated world entry can proceed.
- World entry: not yet passed. The 70-second run timed out awaiting the first game-thread OnTick callback and the harness terminated only its owned PID 20260. No world attachment/rendering evidence exists.
- Actor lifecycle: explicit attachAt/detach methods now normalize coordinates, reject foreign/unloaded cells and invalid positions, validate the game thread, and use a pure DETACHED/ATTACHED/DISPOSED owner-thread guard. Engine-facing attachment/teardown remains unexecuted; update/postupdate are deliberate empty safety hooks, not implemented movement or animation.
- Native profile parser: passed by `ModProfileProbe` against the actual game JAR.
- Offline transformer/FSM/source tests: passed.

The current evidence is initialization and mod/Lua loading only, not a playable teammate acceptance.
