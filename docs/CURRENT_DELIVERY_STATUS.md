# Current delivery gate status

## Verified (2026-10-27 spawn gate, run 20261027-221308)

- Live-world spawn probe passed: `CompanionActor extends IsoPlayer` constructed in-world near the player, log shows `instance=present anim=true mesh=true tex=true`, screenshot shows a second character standing next to the player. Evidence: `standalone/runtime/build/runs/20261027-221308/` (report.json, now.png, stdout.log).
- Old overlay, Knox adapter, mailbox and fixed legacy bootstrap are retired before side effects.
- ZombieBuddy source is pinned and license-reviewed; no runtime dependency is shipped.
- An opaque companion ID is persisted in player ModData and restored by unit test; it is not yet a standard UUID or world-bound lifecycle implementation.
- Own Java `CompanionActor` compiles against actual B42 JARs with Java 25 ECJ.
- Own agent transforms the actual B42 `LuaManager.init()` class bytes; real game smoke test observed installation on `MainThread`.
- Automated gate runs source tests, identity tests, real class transformation, deterministic behavior probe, compile and packaging.
- Deterministic follow/hold/retreat intent arbitration has hysteresis, cancellation, unavailable-actor fail-closed behavior and path request throttling.

## Not verified / not delivered

- Follow locomotion: `follow` 门禁已建立（2026-10-27，run 20261027-230750）但 **未通过**：传送玩家拉开 14 格后，FSM 发出 path requested，但伙伴 `pathing=false` 位置永不变化；`addToWorld()` 修复不解决。已固化结论（AGENTS.md 标准答案表）：Knox 路线 NPC 移动 = 自有行为树 + 模拟玩家输入驱动，非本地 IsoPlayer 不被引擎 update 循环驱动；下一步需反编译 IsoNpcPlayer/MetaNpcCharacter 的移动路径并回写 research/decompiled/。
- No follow/hold/retreat behavior acceptance in the live world (blocked on locomotion above).
- No `CompanionActor` save/reload identity acceptance (same UUID after save, exit, reload; no duplicate).
- No whale-girl visual assets or directional world animation have been approved or integrated.
- No keyboard/context command has been enabled; the UI entrypoint remains inert while actor capability is absent.
- No combat, obstacle, mouse-preservation, or long-session stability acceptance exists.

The project must not be called a finished playable whale-girl teammate until the second section is cleared by disposable-profile real-game evidence.
