# Current delivery gate status

## Verified

- Old overlay, Knox adapter, mailbox and fixed legacy bootstrap are retired before side effects.
- ZombieBuddy source is pinned and license-reviewed; no runtime dependency is shipped.
- An opaque companion ID is persisted in player ModData and restored by unit test; it is not yet a standard UUID or world-bound lifecycle implementation.
- Own Java `CompanionActor` compiles against actual B42 JARs with Java 25 ECJ.
- Own agent transforms the actual B42 `LuaManager.init()` class bytes; real game smoke test observed installation on `MainThread`.
- Automated gate runs source tests, identity tests, real class transformation, deterministic behavior probe, compile and packaging.
- Deterministic follow/hold/retreat intent arbitration has hysteresis, cancellation, unavailable-actor fail-closed behavior and path request throttling.

## Not verified / not delivered

- No world actor has been inserted into a live world.
- No `CompanionActor` constructor/render/update/save lifecycle has been run in-game.
- No whale-girl visual assets or directional world animation have been approved or integrated.
- No keyboard/context command has been enabled; the UI entrypoint remains inert while actor capability is absent.
- No live follow, hold, retreat, combat, obstacle, mouse, or save/reload acceptance exists.

The project must not be called a finished playable whale-girl teammate until the second section is cleared by disposable-profile real-game evidence.
