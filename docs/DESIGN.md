# 大肥鱼独立队友（DC_AIStandalone）设计文档 v1 — 供评审

> 状态：**进行中**。本文档描述当前已实现架构与后续计划，供评审后调整方向。
> 基线：`rework/standalone-companion` @ `ea0fc72`，B42 `42.21.0 4a0e9546ec`。
> 验收红线：**不是可玩成品**。世界内可见渲染、移动、指令执行、存档恢复均未实机通过。

## 1. 目标与非目标

**目标**
- 游戏内可玩的自有 AI 队友“大肥鱼”：自有实体构造、更新、渲染，不套皮普通 NPC。
- 不依赖 Knox Event Expanded NPC；不要求用户安装 ZombieBuddy。ZombieBuddy 仅作已审查开源参考，若改造其代码须保留 MIT 版权/许可通知并记录固定提交 `7794d9f974b5…`。
- 无文字交互：原生上下文菜单 / 短按键；绝不弹聊天框、绝不全屏覆盖层、绝不吞鼠标。
- 确定性行为（跟随/停留/重新集合），模型调用只做可选高层建议，不参与逐帧控制。
- 身份持久化：存档→退出→重载恢复同一 UUID，不重复生成。

**非目标（当前阶段）**
- 不做战斗 AI、语音台词、自定义 3D 模型替换（外观现为 placeholder，文档明确标注）。
- 不做多机/服务端同步。

## 2. 总体架构：两条腿 + 一个桥

```
┌─ Lua 层（client）────────────────────────────┐
│ DC_AI_Standalone.lua    身份注册表 + 意图状态   │
│ DC_AI_StandaloneUI.lua  原生右键菜单（fail-closed）│
│ DC_AI_RuntimeProbe.lua  幂等运行探针（测试用）    │
└──────────────┬───────────────────────────────┘
               │ LuaManager 注入的 JavaFunction
┌─ Java 层（premain agent，own runtime）────────┐
│ CompanionBridge     ASM 注入 LuaManager.init() │
│ CompanionActor      自有 IsoLivingCharacter 实体 │
│ CompanionLifecycle  纯 FSM：DETACHED/ATTACHED/  │
│                     DISPOSED，线程绑定，不可复活 │
│ BehaviorController  纯确定性意图仲裁（未接线）    │
│ WorldActorProbe     仅测试开关的静止挂载探针      │
└──────────────────────────────────────────────┘
```

**设计原则**
1. **fail-closed**：任何前提不满足（无玩家、schema 不符、实体未就绪、非游戏线程）一律拒绝并留下明确错误，不伪造成功。
2. **分层证据**：源码检查 → 启动通过 → 遥测出现 → 实机可玩，四档分开记录，禁止拿低档冒充高档（见 `docs/REAL_GAME_SMOKE_RESULT.md`）。
3. **探针与生产隔离**：所有会生成实体的探针（`WorldActorProbe`、constructor probe）必须显式 JVM 属性或 `--gate` 开启；生产启动绝不生成实体。
4. **无第三方生产依赖**：agent jar 只打包自有类 + ASM（BSD-3）+ 许可证文本。

## 3. Java 注入层

### 3.1 CompanionBridge（agent 入口）
- own premain agent 用 ASM 9.9 在 `LuaManager.init()V` 的 `RETURN` 前注入**恰好一处** `CompanionBridge.install()`。
- `install()` 注册有界 `DCStandaloneTick` / `DCStandaloneClose` JavaFunction；可选属性开启 constructor/world 探针。
- 所有回调强制 `Thread.currentThread() == GameWindow.gameThread`，否则抛异常。

### 3.2 CompanionActor（自有实体）
- `extends IsoLivingCharacter implements IHumanVisual`（`IsoSurvivor` 是 final，不能继承）。
- **分离构造**：`super(null, 0f, 0f, 0f)` —— 非零坐标会经全局 cell 自动注册；全零构造保证可控注册时机。
- 自有惰性 `HumanVisual` / `ItemVisuals`；重写 `getVisual()`、`getItemVisuals(out)`（out 参数路径做 null 安全）。
- `initializePlaceholderVisuals()`：自建 `SurvivorDesc`（女、名“大肥鱼 [placeholder]”）、`initSpritePartsEmpty()`、加载 **`player` action group**（`ActionGroup.getActionGroup("player")`，要求存在初始状态；`Base` 是动画集名不是动作组，禁止使用）。
- `attachAt(cell,x,y,z)`：校验游戏线程/生命周期/current cell/坐标合法/方块已加载，归一化位置后注册 moving object；`detach()` 反注册并关闭生命周期。
- **更新策略（关键安全决策）**：
  - `update()` 保持 no-op：继承路径会碰 `bodyDamage`/moodles/XP，其中多处强转 `IsoPlayer`，对本实体必炸。
  - `postupdate()` 为受就绪条件门禁的受控路径：挂载 + 模型活跃 + 动作组就绪时调用 `ActionContext.update()` + 公开包装 `updateForServerGui()`（动画器/动画播放器/模型槽/光照），**不含**生理更新。
  - `render()`/`renderlast()` 仅在显式请求过模型且模型活跃时走继承渲染。
  - ⚠️ 该路径**已编译但未实机验证**；不声称像素级渲染通过。

### 3.3 CompanionLifecycle
- 纯 FSM：`DETACHED → ATTACHED → DISPOSED`；owner 线程绑定；同步状态迁移；幂等 close；**不允许复活**。便于在无游戏 JAR 的纯 JVM 测试中验证全部迁移语义。

### 3.4 BehaviorController（已实现、未接线）
- 纯确定性：FOLLOW/HOLD/RETREAT 仲裁，进入/退出阈值滞回（stop 2.0 / start 4.0，RETREAT 1.5/2.5）、750ms 重寻路节流、单调时间校验、非法距离拒绝。
- **取消不丢失**：连续指令切换时 pending 的 `CANCEL_PATH` 保留到被消费（修复过 HOLD→RETREAT 丢取消的缺陷）。
- 输出动作枚举 `PATH_TO_OWNER / CANCEL_PATH / NONE`，未来由实体层翻译为游戏寻路调用。

## 4. Lua 层

### 4.1 身份注册表（DC_AI_Standalone.lua）
- schema 1；`companionId = "dc-whale-xxxxxxxx-xxxxxxxx"`（ZombRand）；`assetId = "deepseek_whale_girl"`；意图 ∈ {follow, hold, retreat}。
- 存储：`player:getModData().DC_AI_Standalone`（随存档持久化）。
- **玩家绑定**：每次身份操作前 `bindPlayer(p)` —— 切换玩家对象时重置瞬态并按新玩家的 ModData 恢复，绝不把旧 UUID 写进新玩家；玩家缺失时拒绝且不碰旧数据。
- **损坏数据 fail-closed**：schema 不符 → 记录错误、拒绝启动、不覆盖存档数据；修复后可恢复并清除陈旧错误。

### 4.2 交互入口（DC_AI_StandaloneUI.lua）
- **原生 `OnFillWorldObjectContextMenu`**：右键菜单加“大肥鱼：跟随/停留/重新集合”。
- 不注册任何 ISPanel/ISTextBox/鼠标处理器/键盘钩子；原版右键行为不受影响。
- `canCommand()` 目前**硬编码 false**：实体执行器未接线，菜单项显示“实体尚未就绪”并禁用；点击回调在执行时**再次校验**就绪。这是诚实的交互壳，不是已生效的控制。

### 4.3 运行探针（DC_AI_RuntimeProbe.lua，测试用）
- 幂等；只在 test bootstrap 环境被调用；调用 `DCStandaloneTick`，避免 UI/鼠标/文本输入。

## 5. 测试与验收体系

| 层 | 工具 | 覆盖 |
|---|---|---|
| 纯 JVM | BehaviorProbe / CompanionLifecycleProbe / ModProfileProbe / bytecode 探针 | FSM 语义、确定性仲裁、原生 ActiveModsFile 解析、分离构造字节码 |
| Lua（lupa） | `tests/test_standalone_registry.py`（8 用例） | 身份创建/恢复、玩家切换隔离、损坏 schema、菜单禁用与 fail-closed |
| 源码静态 | `tests/test_standalone_source.py` | 无 Knox/ZombieBuddy 依赖、无鼠标捕获/文本框、菜单入口形态 |
| 实机冒烟 | `smoke_game.py` + `test.ps1` | 一次性可丢弃 profile（带 `.dc-standalone-disposable` 标记，未标记 profile 直接拒launch）；gate: tick / visual-setup / world-actor |

**实机证据现状**（详见 `docs/REAL_GAME_SMOKE_RESULT.md`）：
- ✅ mod 加载、Lua 加载、detached placeholder 视觉准备（runs `034429` / `043706` / `044525`，真实 B42）。
- ⛔ 世界进入被 **TermsOfServiceState** 阻断 —— 按红线**从不**替用户接受条款，需要用户在隔离窗口手动操作一次。
- ⛔ world-actor 挂载/模型成员探针已写好但**从未跑到通过**。
- ⛔ 渲染像素、移动、碰撞、指令实机执行、存档重载恢复：全部未验证。

## 6. 里程碑路线（评审重点）

1. **M1 世界挂载打通**（下一步）：用户在隔离窗口通过条款 → 跑 `--world --gate world-actor` → 验证 attachAt + 模型成员。
2. **M2 可见性验收**：截图证据确认屏幕上出现 placeholder 角色（区分于日志）。
3. **M3 移动闭环**：BehaviorController 接线到实体寻路（`PATH_TO_OWNER` → 游戏 pathfind API，需先探针验证 IsoLivingCharacter 可用接口）；卡住恢复。
4. **M4 指令生效**：`canCommand()` 接到真实执行器；菜单→意图→实体动作全链路实机验收。
5. **M5 存档恢复**：ModData UUID ↔ 实体重绑、防重复生成、死亡处理、保存/重载同一伙伴。
6. **M6 观感与反馈**：替换 placeholder 外观、事件短反馈（带冷却）。

## 7. 已知风险与开放问题（请评审）

1. **`updateForServerGui()` 等价性**：它暴露动画器/模型/光照更新，但未证明与玩家可见渲染路径等价；可能仍需补 `AdvancedAnimator` 相关调用或接受部分功能缺失。备选：进一步审计 `postupdate()` 的完整原版路径并逐段开放。
2. **寻路接口可用性**：IsoLivingCharacter 是否暴露可用的 pathfind/接口未验证，M3 有可能需要自写简化移动 + 方块碰撞。
3. **渲染裁剪**：`setSceneCulled(false)` 在模型初始化前可能静默无效；模型成员状态已纳入就绪条件，但首帧可见性仍需实测。
4. **外观方向**：placeholder 使用游戏内 survivor 贴图。最终“鲸鱼娘”外观走自定义模型还是贴图方案，需要你定夺（影响 M6 工作量估计）。
5. **条款门槛**：每次全新 profile 需人工过一次条款；是否可接受为一次性成本？
6. **指令形态**：目前是右键菜单。是否还需要短按键（会占用键位，需挑选不冲突键）或指向指令？

## 8. 提交记录（本设计对应）

- `718d1b4` 隔离可丢弃 profile 与条款门诊断
- `6f5edbd` 强化分离构造
- `3fe03e1` 受保护的生命周期探针
- `d0fa393` placeholder 视觉前置
- `83cfabb` 受保护的世界实体模型探针
- `57e5ead` 身份隔离 + 取消保留
- `ea0fc72` fail-closed 原生指令入口
