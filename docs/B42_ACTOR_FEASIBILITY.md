# B42 actor feasibility gate

## Result: blocked before entity implementation

The local B42 `projectzomboid.jar` is class-major 69 and the bundled runtime is Java 25. The available legacy `IsoSurvivor` signatures are not evidence of a usable modern human actor:

- `IsoSurvivor` is final and thin in the inspected build.
- `IsoGameCharacter.getVisual()` and no-argument `getItemVisuals()` throw `RuntimeException("subclasses must implement this")` in the inspected hierarchy.
- `IsoGameCharacter.save(ByteBuffer, boolean)` calls virtual visual methods, so an unmodified `IsoSurvivor` cannot safely be treated as a renderable/saveable companion.
- `IsoPlayer.invokeOnPlayerInstance(Runnable)` executes synchronously under a lock; it is not a main-thread scheduler.

Therefore the standalone slice does **not** create an `IsoSurvivor`, reanimate a zombie, disguise the player, or use a full-screen sprite. The actor/renderer gate is explicitly blocked until an owned Java integration supplies and validates the missing visual, update, path, damage, chunk, and save behavior.

The pinned ZombieBuddy checkout is reference/provenance only. The locally installed older ZombieBuddy JAR is not an authoritative compile target and must not be mixed with the pinned Java 25 source.

## Current verified scope

- Old Knox adapter/UI/mailbox/overlay/test bootstrap return before side effects.
- Standalone identity registry unit tests pass: one UUID is created, persisted, restored, and invalid commands do not mutate intent.
- No claim of in-game actor, appearance, mouse acceptance, follow, combat, or save/reload gameplay has been made.
