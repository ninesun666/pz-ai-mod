# DC AI Teammate 本地化清单与实施计划

> 本文件仅是盘点和计划；本轮不修改生产 Lua。目标是发布前将玩家可见内容完整汉化，同时保持协议字段、内部状态、API 名称和日志稳定。

## 一、生产 Lua 中的玩家可见英文

### `DC_AI_TeammateUI.lua`

| 位置/原文 | 建议中文 | 风险/处理 |
|---|---|---|
| `Teammate unavailable` | `队友不可用` | 错误回退提示；应使用运行时中文构造，不要写非 ASCII 源字面量。 |
| `Request failed` | `请求失败` | 邮箱请求失败回退提示。 |
| `Teammate request sent; waiting for model bridge.` | `队友请求已发送，正在等待模型桥接程序。` | 发送成功提示；长度适中。 |
| `AI teammate: message (model bridge required)` | `AI 队友：输入消息（需要运行模型桥接程序）` | `ISTextBox` 标题；中文可能改变宽度，需增大宽度或确认布局。 |
| `AI teammate` | `AI 队友` | 右键菜单根项。 |
| `Recruit / recover teammate` | `招募 / 恢复队友` | 子菜单；斜线可保留，也可改为 `招募或恢复队友`。 |
| `Follow me` | `跟随我` | 手动命令。 |
| `Wait here` | `在这里等待` | 手动命令。 |
| `Talk to teammate` | `与队友交谈` | 打开输入框。 |
| `Status` | `状态` | 状态菜单项。 |
| 状态拼接 `phase / mailboxPhase / error or OK` | 中文状态标签（见下表） | 不能直接把内部英文 phase 交给玩家；应通过映射函数展示。 |

状态值建议映射：

| 内部值（保持不变） | 玩家显示 |
|---|---|
| `idle` | `空闲` |
| `spawning` | `正在生成队友` |
| `following` | `正在跟随` |
| `waiting` | `正在等待` |
| `recovered` | `已恢复` |
| `pending` | `等待模型回复` |
| `complete` | `已完成` |
| `error` | `错误` |
| `OK` | `正常` |

建议状态格式：`队友：正在跟随 / 模型：空闲 / 正常`，避免直接暴露 `following / idle / OK`。

### `DC_AI_TeammateMailbox.lua`

该文件大部分错误字符串目前通过状态、日志或测试读取；其中 `M.status()` 本身不渲染文本，但 UI 会显示 `m.error`，因此以下均属于间接玩家可见内容，必须翻译或映射：

| 原文 | 建议中文 | 备注 |
|---|---|---|
| `adapter unavailable` | `队友模块不可用` | UI 状态错误。 |
| `teammate not ready` | `队友尚未准备好` | UI 状态错误。 |
| `adapter has an error` | `队友模块出现错误` | UI 状态错误。 |
| `remembered teammate identity mismatch` | `已记录的队友身份不匹配` | 安全校验失败。 |
| `npc API unavailable` | `NPC 接口不可用` | 依赖未加载。 |
| `teammate unavailable` | `队友不可用` | NPC 列表/目标不存在。 |
| `ambiguous teammate identity` | `队友身份不唯一` | 拒绝执行。 |
| `teammate not in group` | `队友不在玩家队伍中` | 拒绝执行。 |
| `teammate world not ready` | `队友所在区域尚未加载` | 拒绝执行。 |
| `reply too large` | `模型回复过大` | 协议错误。 |
| `invalid, duplicate or unknown field` | `回复字段无效、重复或未知` | 协议错误。 |
| `expected exactly five fields` | `回复必须包含五个字段` | 协议错误。 |
| `invalid identity` | `身份信息无效` | 协议错误。 |
| `invalid sequence` | `序号无效` | 协议错误。 |
| `action not allowed` | `模型返回了不允许的动作` | 协议错误。 |
| `invalid text` | `文本无效` | 协议错误。 |
| `reply does not match pending identity` | `回复与当前请求身份不匹配` | 拒绝过期/串线回复。 |
| `action completed; teammate speech unavailable` | `动作已完成，但队友语音气泡无法显示` | 当前实际为 NPC `Say`，建议称“说话提示”而非“语音”。 |
| 日志前缀 `[DC_AI_TeammateMailbox]` | 保留 | 日志不是玩家 UI；不要改变以免影响诊断。 |

`request already pending`、`invalid request text`、`sequence exhausted`、`request writer unavailable`、`request close failed`、`pending request timeout` 等也会通过 `status().error` 进入 UI，必须纳入映射：

- `request already pending` → `已有请求正在等待回复`
- `invalid request text` → `请求文本无效`
- `sequence exhausted` → `请求序号已耗尽，请重新启动游戏`
- `request writer unavailable` → `无法写入请求文件`
- `request close failed` → `请求文件关闭失败`
- `pending request timeout` → `模型回复超时`

### `DC_AI_Teammate.lua`

该文件的 `log()` 和 `fail()` 字符串主要是日志，但 UI 的 `state.error` 会直接显示，因此全部错误也属于间接玩家可见：

- `no player` → `找不到玩家`
- `player must be on ground floor z=0` → `玩家必须位于地面层（z=0）`
- `npc API unavailable` → `NPC 接口不可用`
- `group unavailable before spawn` → `生成前无法获取玩家队伍`
- `squad unavailable before spawn` → `生成前无法获取小队`
- `saved teammate unavailable` → `已保存的队友不可用`
- `saved teammate is not in player group` → `已保存的队友不在玩家队伍中`
- `teammate world not ready` → `队友所在区域尚未加载`
- `squad unavailable` → `小队不可用`
- `group unavailable` → `玩家队伍不可用`
- `joinGroup did not establish membership` → `加入队伍失败`
- `adjacent spawn square not loaded` → `相邻生成位置尚未加载`
- `adjacent spawn square is not free` → `相邻生成位置不可用`
- `spawn failed: ...` → `生成队友失败：...`（外部异常文本需谨慎截断/隐藏）
- `spawn timeout` → `生成队友超时`
- `player/API disappeared` → `玩家或 NPC 接口已不可用`
- `tellNpcFollow unavailable` → `跟随接口不可用`
- `tellNpcStay unavailable` → `等待接口不可用`
- `teammate square unavailable` → `无法获取队友所在位置`
- `ambiguous spawn: multiple new NPCs; refusing recruitment` → `检测到多个新 NPC，已取消招募`

以下是内部/日志文本，不建议翻译：`following npc=... goal=... sub=...`、`recovered npc=...`、`spawn requested at...`、`loaded; call...`。如发布版本需要日志中文化，应另设稳定日志代码，不把内部状态字段改成中文。

## 二、桥接程序与文档中的用户可见英文

### 桥接 CLI/诊断

`teammate_bridge.py` 的固定 stderr 文本也会被普通用户看到：

- `teammate bridge: missing or stale request` → `队友桥接：请求不存在或已过期`
- `teammate bridge: request failed; no reply written` → `队友桥接：请求处理失败，未写入回复`
- `teammate bridge: invalid configuration or mailbox paths` → `队友桥接：配置或邮箱路径无效`

CLI `--help` 的参数说明、配置错误（如 `missing API credential`、`invalid base_url`、`missing model`）建议发布中文启动脚本/中文 README 包装；协议内部异常可保留英文以便开发诊断，但不应直接显示为游戏提示。

### `TEAMMATE_INSTALL_DRAFT.md`

当前文档几乎全部为英文，发布版应另建/改为 `README.zh-CN.md`（或直接中文化 README），至少翻译这些章节：

- 标题 `DC AI Teammate preview package` → `DC AI Teammate（AI 队友）预览版`
- Requirements and compatibility → `运行要求与兼容性`
- Exact package allow-list → `发行包文件清单`
- Manual installation and startup → `手动安装与启动`
- Actual API key and endpoint configuration → `API 密钥与接口配置`
- Safety, restarts, and verification limits → `安全、重启与验证范围`
- 所有依赖、路径、命令、警告、能力限制、回滚说明均需完整翻译，不翻译代码、命令、路径、JSON 键和协议字段。

建议保留英文原版作为开发者文档，发布包提供中文主文档；中英文版本必须共享版本号和更新记录。

## 三、LuaCompiler Unicode 风险与实施规则

历史实验证明：Kahlua 的 `LuaCompiler` 会破坏 Lua 源码中的非 ASCII 字面量（`LexState.save(int)` 截断到低 8 位）。因此**不能直接把中文写进 Lua 源字符串**，即使文件保存为 UTF-8 也可能出现乱码。

安全规则：

1. 生产 Lua 源码保持 ASCII-only。
2. 中文运行时文本用 `string.char(...)` 数值构造。例如 `队友` 可由 UTF-16 code unit 构造：`string.char(38431,21451)`；完整句子逐字符转换。
3. 不能对 emoji/辅助平面字符直接用一个 `string.char`；必须使用 UTF-16 代理对（如工具函数按 code point 生成高/低代理），并在运行时测试 `world:Say`。
4. 不把 `\u0000`、换行、控制符放入协议文本；继续使用现有 UTF-8/UTF-16 验证和 512 字节限制。
5. 通过 ASCII-only 的 `pcall(string.char, 20013)` 探测运行时字符串语义；不要在源文件中写 `"中"` 作为探针。
6. 推荐增加一个小型 `DC_AI_Text.lua` ASCII 源模块，集中提供 `char/cp/concat` 和中文常量，避免散落数字难以维护；它必须保持生产包 allow-list 可控，并补充真实引擎测试。
7. UI 尺寸要针对中文调整：输入框标题 `420x180` 及菜单文本需实测，避免截断；长错误应在日志保留详细原因、UI 显示短提示。

## 四、实施顺序与验收

1. 建立 ASCII-only 文本构造工具和中文常量表；先写单元测试验证 UTF-16 Kahlua、UTF-8 字节限制、emoji/代理对。
2. 替换 UI 菜单、输入框、提示和状态映射；保留内部 phase/action 字段英文。
3. 将 adapter/mailbox 错误改为错误代码 + 中文显示映射，避免外部异常污染 UI。
4. 增加中文模型默认系统提示/中文请求上下文（不改变严格 JSON 输出协议）；真实模型回复文本由模型决定，不能强制声称中文，配置文档建议中文模型。
5. 翻译 README、发布说明、更新日志、配置示例注释；代码块/路径/JSON 键保持原样。
6. 在隔离存档验证：中文菜单、中文输入、中文模型回复、NPC `Say` 显示、follow/wait、超时/错配提示、打包运行。
7. 打包前扫描生产 Lua 的非 ASCII 源字节，扫描发行包排除密钥、测试存档、旧作弊/语音代码，并重算 SHA256。

## 五、不可翻译或必须保留原样

`DC_AI_Teammate`、`DC_AITeammate`、`DC_AI_TeammateNpcId`、`DC_AI_TeammateMailbox`、`session/seq/npc_id/action/text`、`none/follow/wait`、`DC_AI_Teammate.lua` 文件名、Knox/ZombieBuddy/API 方法名、Workshop ID、路径、JSON 键、CLI 参数和日志稳定前缀必须保持原样，以确保兼容性。

## 六、补充盘点与并行工作状态

底层异常同样可能经 `pcall` → `fail` → 状态 UI 出现，补充如下：

| 英文原文 | 中文显示 |
|---|---|
| `valid timestamp unavailable` | `无法获取有效时间戳` |
| `ZombRand unavailable` | `随机数接口不可用` |
| `invalid ZombRand result` | `随机数接口返回无效结果` |
| `invalid session token` | `会话标识无效` |
| `unpaired UTF-16 surrogate` | `回复包含不完整的 Unicode 字符` |
| `invalid reader character` | `回复文件包含无效字符` |
| `reply close failed` | `回复文件关闭失败` |
| `adapter command failed` | `队友动作执行失败` |
| `player square unavailable` | `无法获取玩家所在位置` |
| 未知 Java/Lua 异常正文 | `发生内部错误，请查看日志` |

未知异常保留原始日志，只在 UI 显示通用中文。`pcall` 异常可能带文件/行号前缀，错误映射宜用稳定错误代码，不能假定字符串总是裸消息。

原生 `ISTextBox` 确认/取消按钮也应检查显示为 `确定` / `取消`；内部 `button.internal == "OK"` 不可翻译。需要检查原生按钮是否依赖游戏当前语言，或在模组内安全设置标题。

桥接固定帮助文本补充：

| 英文原文 | 建议中文 |
|---|---|
| `standalone NPC teammate bridge` | `独立 NPC 队友模型桥接程序` |
| `explicit JSON model config (required in real mode)` | `显式指定 JSON 模型配置（真实模型模式必填）` |
| `explicit request mailbox` | `请求邮箱文件的完整路径` |
| `explicit reply mailbox` | `回复邮箱文件的完整路径` |
| `explicit offline no-op; no HTTP` | `离线检查模式：不调用网络、不执行动作` |
| `[offline] No action taken.` | `[离线检查] 未执行任何动作。` |

argparse 自带 usage/error/help/options 仍是英文，需中文帮助/错误入口才能称启动提示完整中文。Python 中文字面量不受 LuaCompiler 缺陷影响，Windows 控制台编码仍需测试。

发行 `mod.info`：名称建议 `DC AI Teammate（AI 队友）`；描述建议 `基于 Knox Event Expanded NPC 的实体 AI 队友：支持对话、跟随与等待。`。元数据不是 Lua，不能用 string.char，必须单独验证文本编码。

父代理报告已用数字 U(...) 翻译菜单/对话标题，并修改系统提示默认简体中文；这属于父代理的并行改动，本清单原文是初次检查快照。仍需状态/错误/原生按钮/CLI/文档/元数据。测试 observer 当前英文菜单查找必须同步，否则会误报菜单不存在。

## 七、当前结论

本轮只完成库存和设计，不修改生产代码。已确认玩家可见英文分布于 UI 直接文本、状态错误、adapter 错误和英文安装文档；Lua 中文字面量存在已证实的编译器风险。发布前必须按上述 numeric `string.char` 方案完成汉化并在原生游戏中验证，不能仅靠 Python/Lupa 测试宣称完成。
