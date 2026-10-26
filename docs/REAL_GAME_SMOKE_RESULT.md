# Standalone smoke evidence

- Game build: Project Zomboid B42 `42.21.0 4a0e9546ec`.
- Profile: each run uses a fresh disposable profile under `standalone/runtime/build/runs/`.
- Runtime: own Java premain agent; no Knox or ZombieBuddy runtime dependency.
- Mod loading: **passed** after seeding `options.ini`; run `034429` reports `loading DC_AIStandalone`, `active mods=[DC_AIStandalone]`, `discovered=true`.
- Lua loading: **passed**; run `034429` reports `[DCStandaloneTest] bootstrap loaded`.
- World entry: **not passed**. Runs end after `Game booting` / `STATE: exit zombie.gameStates.TISLogoState`, with no `OnGameStateEnter`, `OnMainMenuEnter`, or world-start evidence. The latest test bootstrap now adds read-only state diagnostics; it does not accept terms or force transitions.
- Native profile parser: **passed** by `ModProfileProbe` against the actual game JAR.
- Offline transformer/FSM/source tests: **passed**.

The current evidence is initialization and mod/Lua loading only, not a playable teammate acceptance.
