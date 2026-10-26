# Standalone smoke evidence

- Game build: Project Zomboid B42 `42.21.0 4a0e9546ec`.
- Profile: each run uses a fresh disposable profile under `standalone/runtime/build/runs/`.
- Runtime: own Java premain agent; no Knox or ZombieBuddy runtime dependency.
- Mod loading: passed after seeding `options.ini`; run `034429` reports `loading DC_AIStandalone`, `active mods=[DC_AIStandalone]`, `discovered=true`.
- Lua loading: passed; run `034429` reports `[DCStandaloneTest] bootstrap loaded`.
- Placeholder visual setup: **passed after game-data initialization** in run `20261027-043706`, stdout lines 171-172: `[DCStandaloneTest] placeholder visual setup PASS (not rendered)` and detached constructor PASS. The own actor created its own `SurvivorDesc` identity (`大肥鱼 [placeholder]`), initialized Human/attached item groups, sprite parts and visual interfaces. This is a placeholder precondition probe, not screen rendering acceptance.
- World entry and rendering: not yet passed. The same run reached `TermsOfServiceState` (`terms=true`, `main=false`, `termsVersion=-1`) and was terminated by the harness after the visual gate. No world attachment, model-manager membership, on-screen character, collision, or input evidence exists.
- Actor lifecycle: explicit attachAt/detach methods normalize coordinates, reject foreign/unloaded cells and invalid positions, validate the game thread, and use a pure DETACHED/ATTACHED/DISPOSED owner-thread guard. Engine-facing attachment/teardown remains unexecuted.
- Action setup: actor loads the B42 `player` action group and requires its initial state. `Base` is the animation-set name, not the action group. This setup passed the real detached visual gate again in run `20261027-044525`.
- Stationary model pipeline: an explicit model request and readiness-gated rendering/postupdate path have been added. Postupdate calls ActionContext.update() and public updateForServerGui(), without inherited physiology update. This path is compiled but world execution/pixel visibility is untested; locomotion remains unimplemented.
- World actor probe: explicit `--world --gate world-actor` attaches a stationary placeholder near a loaded player and checks active model membership. It is disabled in production by default and has not passed a real-world run. A human terms action is still needed for world entry.
- Full repository regression: 68 tests run; 5 failures and 13 errors remain in retired adapter/mailbox/UI/package tests. The focused independent gate passes 8 Python tests and 5 JVM probes; the legacy failures are not hidden or treated as independent-runtime acceptance.
- Registry isolation: the Lua registry now binds state to the current player object before every identity operation. Player switches reset transient state, restore that player's saved UUID/intent, and never write to the previous player's ModData. Unsupported schemas remain fail-closed; successful later repair clears the stale error. Focused registry coverage is now 6 tests.
- Deterministic behavior: consecutive command changes preserve a pending path cancellation, so HOLD immediately followed by RETREAT cannot lose the cancellation. The JVM behavior probe covers this sequence plus throttling, hysteresis, unavailable readiness and invalid perception.

- Offline transformer/FSM/source tests: passed.

The current evidence is initialization and mod/Lua loading only, not a playable teammate acceptance.
