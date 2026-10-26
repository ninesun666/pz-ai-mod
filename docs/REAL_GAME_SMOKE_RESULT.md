# Standalone smoke evidence

- Game build: Project Zomboid B42 `42.21.0 4a0e9546ec`.
- Profile: each run uses a fresh disposable profile under `standalone/runtime/build/runs/`.
- Runtime: own Java premain agent; no Knox or ZombieBuddy runtime dependency.
- Mod loading: passed after seeding `options.ini`; run `034429` reports `loading DC_AIStandalone`, `active mods=[DC_AIStandalone]`, `discovered=true`.
- Lua loading: passed; run `034429` reports `[DCStandaloneTest] bootstrap loaded`.
- Terms gate: the diagnostic run `035731` reached `TermsOfServiceState`; the first diagnostic implementation threw because a Java state object was incorrectly accessed as a Lua table. The diagnostic was corrected. Automated runs do not accept terms on the user's behalf; a human consent action in the disposable test window is required once before automated world entry can proceed.
- World entry: not yet passed. Prior runs stop before MainScreen; rerun after the terms-gate correction is required. No real entity construction/rendering evidence exists.
- Native profile parser: passed by `ModProfileProbe` against the actual game JAR.
- Offline transformer/FSM/source tests: passed.

The current evidence is initialization and mod/Lua loading only, not a playable teammate acceptance.
