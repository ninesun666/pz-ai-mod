# 编码参考清单 — 大肥鱼独立队友 v1

> 用途：按模块列出编码时可参考的工程、mod、逆向文件与游戏内数据，**只列已核实存在的本地路径**和已固定的上游提交。
> 使用纪律：
> - **生产代码不复制进项目**，除非已读许可证并保留通知（目前唯一允许改造的是 ZombieBuddy 的 MIT 部分，须记录来源与修改）。
> - 反编译结果只用来理解 API 语义，**不得把反编译签名当作可用功能**——一切以编译/运行探针为准。
> - 引用游戏 JAR 内容属于合理研究；但**不得把游戏 JAR/资源打包进发布物**。

## 0. 环境事实（编码前提）

| 项 | 值 |
|---|---|
| 游戏版本 | B42 `42.21.0 4a0e9546ec` |
| 游戏目录 | `D:\SteamLibrary\steamapps\common\ProjectZomboid` |
| 主 JAR | `projectzomboid.jar`（编译 classpath 用，含混淆前类名如 `zombie.characters.IsoLivingCharacter`） |
| 游戏自带 JRE | `jre64\`（Java 25 运行时；**无 javac/jartool**，用 ECJ 3.43.0 `-17` 编译） |
| 本仓库 | `ai-mod` @ `rework/standalone-companion` |
| 反编译方法 | 用 IDE/CFR/Vineflower 反编译 `projectzomboid.jar` 到本地只读目录（不提交仓库） |

## 0.5 既有逆向资料总库（先查这里，再反编译）

之前各阶段沉淀的逆向资料都在仓库内，**大部分问题不需要重新反编译**：

### research\pz-reverse\ — PZ 逆向笔记库（带索引）
- `index\` + `build_doc.py` + `cat-*.md` 分类文档：`cat-ai.md`（AI 状态机）、`cat-characters.md`（角色类）、`cat-lua.md`、`cat-native-dlls.md`（原生 DLL）、`cat-input-ime.md`（输入法）、`cat-mod-design.md`、`cat-network.md`、`cat-audio-ui.md`、`cat-game-design.md`、`cat-mods-fonts.md`、`cat-dc-toolkit.md`。

### research\decompiled\ — Knox 逆向类笔记（Knox Event Expanded NPC 反编译）
- `KnoxEventNpcAPI.txt`、`NpcBehaviorTree.txt`、`NpcBehaviorTreeManager.txt`、`BehaviorNode.txt`、`BehaviorTreeBase.txt`、`SelectorNode.txt`、`FollowSubTree.txt`、`AttackAction.txt`、`MetaCharacterManager.txt`、`MetaNpcCharacter-sig.txt` — Knox 的行为树/角色管理实现笔记，M3 移动与行为接线时的对照实现（只读参考，生产代码不依赖 Knox）。

### research\*.txt — 游戏类 javap 签名库（已核实存在的 API 清单）
- `javap-zombie_characters_IsoGameCharacter.txt` / `IsoLivingCharacter.txt` / `IsoPlayer.txt` / `IsoSurvivor.txt` / `IsoZombie.txt`
- `javap-zombie_characters_action_ActionContext.txt`、`javap-zombie_characters_component_StateMachineComponent.txt`
- `javap-zombie_core_skinnedmodel_advancedanimation_AdvancedAnimator.txt`、`javap-zombie_core_skinnedmodel_ModelManager.txt`、`javap-zombie_core_skinnedmodel_visual_HumanVisual/IHumanVisual/ItemVisuals.txt`
- `javap-zombie_iso_IsoCell.txt` / `IsoMovingObject.txt` / `IsoObject.txt`、`javap-zombie_MovingObjectUpdateScheduler.txt`
- `javap-zombie_ai_states_GenericDefaultState.txt`、`generated-companion-javap.txt`
- 写代码前先 grep 这里确认方法签名，避免再跑 javap。

### research\*.md — 阶段逆向笔记
- `逆向笔记-knox核心.md`、`knox-design.md` — Knox 核心机制逆向结论。
- `game-zombiebuddy-design.md` — ZombieBuddy 设计逆向。
- `字体与汉化模组解剖.md`、`架构与重做路线.md` — 字体/汉化与整体架构演进。

### 仓库根目录 — 输入法与原生层逆向
- `ime-api.txt` / `ime-native-api.txt` / `ime-signatures.txt` / `ime-textbox.txt` / `ime-display-bc.txt` — 原型阶段对游戏输入框/IME 的逆向记录（交互层需要输入相关参考时查这里）。
- `bridge\`、`agent\`、`dctoolkit\` — 旧原型工程（含 zbNative 原生代理逆向产物），仅作历史参考，生产禁用。
- `knox-i18n\` — Knox 汉化资料。

### upstream\ZombieBuddy\doc\ — ZombieBuddy 官方文档（固定提交 7794d9f9）
- `LuaAPI.md`、`ModdingGuide.md`、`CommandLine.md`、`DevDebugFunctions.md`、`ModSigning.md`、`Installation.md`、`Migrating2xTo3x.md` — 改造其代码时对照的原始语义文档。

## 1. 实体与渲染（M1–M2：挂载、可见性）

**逆向/源（projectzomboid.jar 内类，反编译阅读）**
- `zombie.characters.IsoLivingCharacter` — 我们的基类；注意 `IsoSurvivor` 是 final。
- `zombie.characters.IsoGameCharacter` — attach/detach、moving object 注册、action 状态机。
- `zombie.iso.IsoCell / IsoMovingObject` — `getGridSquare`、movingObjects 成员管理。
- `zombie.iso.objects.IsoPlayer`-相邻渲染路径 — **重点看渲染管线如何收集可见角色**（scene cull → model slot），验证 `updateForServerGui()` 是否等价于可见更新。
- `zombie.ai.State` + `zombie.ai.states.*` — 玩家/幸存者状态实现，M3 移动接 `player` action group 时参考其进入/退出语义（不要整拷，挑 walk/idle）。
- `zombie.scripting.objects.ModelScript` / `model_X` 脚本 — 模型槽定义。

**游戏数据目录（只读参考）**
- `media\actiongroups\` — `player` 动作组 XML，动作→动画集映射；确认 idle 初始状态。
- `media\AnimSets\`、`media\animstates\`、`media\animscript\` — 动画集/状态机定义，M3 播放移动动画时对照。
- `media\models_X\`（B42 新模型目录）+ `media\clothing\` — placeholder 外观与最终贴图方案的素材形态参考。

**已有探针（本仓库，优先复用）**
- `standalone/runtime/src/dcai/companion/CompanionActor.java` — 已解决的坑全在注释里：分离构造 `super(null,0,0,0)`、`getVisual()` 必须重写、`postupdate()` 安全门禁。
- `standalone/runtime/src/dcai/companion/WorldActorProbe.java` + `smoke_game.py --gate world-actor` — 挂载验证入口。

## 2. 寻路与移动（M3）

**逆向/源**
- `zombie.ai.spath.*`（A*/路径状态）、`IsoGameCharacter.getPathTo…` 系列 — 候选寻路 API，**先探针验证 IsoLivingCharacter 可见性**（部分是 IsoPlayer 专属）。
- `zombie.characters.IsoZombie` — 引擎内最完整的非玩家移动实现（转向、障碍处理），语义参考。

**参考 mod（观察行为，不抄运行时）**
- `upstream\ZombieBuddy`（固定提交 `7794d9f974b509f9f800b266f76c15cd9eb6bfa6`）— 其 Java 侧 teammate 移动指令如何翻译成游戏调用，是现成对照。改造其代码时按 AGENTS.md 保留 MIT 通知。
- Knox 相关本地资料 `knox-i18n\`（仅 i18n）；Knox 本体在 Workshop 目录可对照其 NPC 移动的 Lua 层用法。

## 3. 交互与 UI（M4）

**逆向/源**
- `zombie.Lua.LuaManager` — 注入点与 JavaFunction 注册形态（`CompanionBridge` 已有完整实现）。
- `zombie.ui.ContextMenu / ISContextMenu`（Lua 侧 `ISContextMenu`）— 右键菜单 API；本仓库 `DC_AI_StandaloneUI.lua` 已有可运行骨架。
- `media\lua\client\ISUI\Hutch\ISHutchMenu.lua`、`ISVehicleMenu.lua`、`AdminContextMenu.lua`（游戏目录）— 官方 `OnFillWorldObjectContextMenu` 用法范本（addOption/addSubMenu/notAvailable）。
- `media\lua\shared\` — `Events`、`Keyboard`、工具函数定义。

**参考 mod**
- `upstream\ZombieBuddy` 的 Lua 交互层 — 它的菜单/快捷键形态可对照，但注意 AGENTS.md 红线：不引入其自更新、原生代理、硬编码 jar 路径。

## 4. 身份与存档（M5）

**逆向/源**
- `zombie.characters.IsoPlayer.getModData` / `KahluaTable` 序列化 — ModData 持久化语义（哪些类型能存）。
- `zombie.gameStates.*` 存档加载顺序 — 决定 Lua 何时能安全恢复实体（`OnGameStart` vs 首个 OnTick）。

**本仓库**
- `standalone/42/media/lua/client/DC_AI_Standalone.lua` — schema 1 注册表：玩家绑定、fail-closed、损坏修复语义已定稿（测试 `tests/test_standalone_registry.py` 8 用例）。
- `tests/test_standalone_smoke.py` — disposable profile 纪律（`.dc-standalone-disposable` 标记）。

## 5. 外观（M6）

**游戏数据目录（只读）**
- `media\clothing\`、`media\items\`（clothing script）、`media\textures\` — 贴图方案 A 的全部素材形态。
- `media\models_X\` — B42 模型格式；若走方案 B（自定义模型），先研究此处 + `fileGuidTable.xml` 的引用方式。
- `media\XUI\`（若存在）/ `media\fonts`、`zombienewtext*.fnt` — 头顶名字与字幕渲染参考。

**参考 mod**
- Workshop 内任意"自定义服装/模型"mod 的 `media\` 结构（本地 `Workshop\` 目录可挑一个结构最简的做形态参考；只看文件组织，不复制美术资源）。

## 6. 工具链

| 工具 | 用途 | 位置 |
|---|---|---|
| ECJ 3.43.0 | Java `-17` 编译（游戏 JRE 无 javac） | `.local-tools\`（build.ps1 已接好） |
| ASM 9.9 | 字节码注入（随 agent 打包，BSD-3） | `standalone\runtime` |
| lupa | Lua 单测宿主 | Python 包（tests 已用） |
| build/test 脚本 | 构建 + 全部门禁 | `standalone/runtime/build.ps1` / `test.ps1` |
| smoke_game.py | 隔离实机冒烟（tick/visual-setup/world-actor 三档 gate） | `standalone/runtime/` |

## 7. 反编译工作区约定

1. 反编译输出放 `ai-mod\parking\decompile\`（已 gitignore 区域），**不提交**。
2. 只反编译 `projectzomboid.jar`；Workshop 第三方 mod 二进制不逆向进仓库。
3. 每个关键类读完在 PR/commit message 里注明"依据：反编译 IsoXxx@42.21，已用探针 yy 验证"。
