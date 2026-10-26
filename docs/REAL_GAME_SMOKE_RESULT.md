# Standalone smoke evidence

- Game build: Project Zomboid B42 `42.21.0 4a0e9546ec`.
- Profile: each run uses a fresh disposable profile under `standalone/runtime/build/runs/`.
- Runtime: own Java premain agent; no Knox or ZombieBuddy runtime dependency.
- Mod loading: passed after seeding `options.ini`; run `034429` reports `loading DC_AIStandalone`, `active mods=[DC_AIStandalone]`, `discovered=true`.
- Lua loading: passed; run `034429` reports `[DCStandaloneTest] bootstrap loaded`.
- Placeholder visual setup: **passed after game-data initialization** in run `20261027-043706`, stdout lines 171-172: `[DCStandaloneTest] placeholder visual setup PASS (not rendered)` and detached constructor PASS. The own actor created its own `SurvivorDesc` identity (`大肥鱼 [placeholder]`), initialized Human/attached item groups, sprite parts and visual interfaces. This is a placeholder precondition probe, not screen rendering acceptance.
- World entry and rendering: not yet passed. The same run reached `TermsOfServiceState` (`terms=true`, `main=false`, `termsVersion=-1`) and was terminated by the harness after the visual gate. No world attachment, model-manager membership, on-screen character, collision, or input evidence exists.
- Actor lifecycle: explicit attachAt/detach methods now normalize coordinates, reject foreign/unloaded cells and invalid positions, validate the game thread, and use a pure DETACHED/ATTACHED/DISPOSED owner-thread guard. Engine-facing attachment/teardown remains unexecuted; update/postupdate are deliberate empty safety hooks, not implemented movement or animation.
- Native profile parser: passed by `ModProfileProbe` against the actual game JAR.
- Offline transformer/FSM/source tests: passed.

The current evidence is initialization and mod/Lua loading only, not a playable teammate acceptance.
