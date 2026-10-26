# AI 队友预览包

这是仅包含队友功能的预览包，不是旧版无线电／语音代理。它不提供治疗、无敌、物品生成、传送或角色属性修改功能。正常使用**会改变所选世界**：招募会创建真实 NPC，并将其精确 id 写入玩家模组数据。请先使用全新的可丢弃世界；不要仅为测试就在原有存档中启用此预览版。

## 环境要求与兼容性

- 已检查／测试的版本为 **Windows 版 Project Zomboid 42.21.0**。元数据声明 `versionMin=42.21`；尚未确认后续游戏版本的兼容性。
- **Knox Event Expanded NPC 0.4.0-13**，创意工坊项目 **3397396843**，准确的模组 id 为 `KnoxEventExpandedNpc`（不是其目录名）。需要单独获取，本包不包含该依赖。
- **ZombieBuddy**，已检查的代理版本为 **2.3.4**，创意工坊项目 **3619862853**，准确的模组 id 为 `ZombieBuddy`。Knox 明确依赖它。仅订阅还不够：还必须安装其原生代理并启用模组。
- Windows 版 ZombieBuddy 需要将其自己的 `ZombieBuddy.jar` 和 `zbNative.dll` 放在游戏目录中。使用普通启动（Normal Launch）的 JSON 配置时，JVM 参数为 `-agentlib:zbNative`，JSON 参数内不加 ` --`。Steam 启动选项则为 `-agentlib:zbNative --`。备用启动（Alternate Launch）需要在批处理启动器的 `_JAVA_OPTIONS` 中添加该参数，或使用 ZombieBuddy 官方安装器安装。请遵循可信的依赖说明，并检查启动器改动。不要添加无关的 `dcaiv-agent.jar` 或防护代理。
- Java 模组具有不受限制的系统访问权限。仅批准预期且可信的 ZombieBuddy／Knox JAR 及其哈希；不要启用 `allow-all`，也不要复制测试用批准文件。此队友包不需要单独安装 JDK、Gradle、ByteBuddy，也不需要编译 Java；使用游戏自带运行时和单独分发的依赖即可。
- 仅支持**单人模式、玩家索引 0**。客户端／服务器多人模式下菜单被禁用。适配器要求在游戏主 Lua 线程运行，且 Knox NPC API 已初始化。
- **建议使用 Python 3.10+**；已检查的产物使用 Python 3.11。两个队友 Python 文件仅使用标准库，不需要安装 pip 包。TTS、ASR、麦克风访问、`edge-tts`、`miniaudio`、`sounddevice`、`faster-whisper`、`numpy`、`zhconv` 和 ffmpeg 均不是队友功能的依赖。
- 真实模型对话需要兼容 OpenAI 聊天补全接口的端点、模型、API 凭据和网络访问。手动跟随／等待不需要桥接程序。

## 包内容精确白名单

```text
mods/DC_AI_Teammate/common/mod.info
mods/DC_AI_Teammate/42/media/lua/client/DC_AI_Teammate.lua
mods/DC_AI_Teammate/42/media/lua/client/DC_AI_TeammateMailbox.lua
mods/DC_AI_Teammate/42/media/lua/client/DC_AI_TeammateUI.lua
bridge/teammate_bridge.py
bridge/teammate_protocol.py
bridge/teammate-config.example.json
README.md
SHA256.json
```

三个 Lua 文件仅取自正式源目录 `ai-mod/DC_AIVoice/42.0/media/lua/client/` 中的对应文件，不使用测试框架 Lua。当前 `ai-mod/tools/build_teammate_package.py` 从独立的中文元数据文件 `ai-mod/teammate-package/common/mod.info` 读取包元数据，不再复用隔离测试配置或混合源码模组的元数据：

```text
name=AI 队友（单人预览版）
id=DC_AITeammate
description=单人实体 NPC AI 队友：招募、跟随、等待、模型对话与正常战斗。
versionMin=42.21
```

该元数据没有声明自动依赖解析；必须手动启用两个依赖。不要复制无线电源码模组的元数据。当前三份中文 Lua 已通过原生菜单跟随、等待、打开对话、确定提交及取消测试；确定提交使用测试预填中文，不代表已验证中文输入法。第 34 轮已核对原生安装的三个 Lua 和中文元数据与当前 ZIP 逐字节一致，并完成加载；该轮前台保护拒绝输入，因此不作为新一轮世界内交互验收。中文字形和 NPC 中文说话显示仍未完成可视验证。

**必须排除**所有测试、测试模组／引导程序／战斗自动化、可丢弃配置目录／存档、批准文件、日志、凭据、字节码缓存及第三方依赖副本。还应排除旧版 `DC_AIVoice.lua`、`DC_AIVoice_UI.lua`、`bridge.py`、`voice.py`、`tts.py`、旧 CMD／PowerShell 安装器与启动器、声音槽位、语音样本及整个旧 `agent/` 目录树。旧代理暴露治疗／无敌／物品命令。旧安装器会递归复制混合源码目录树、删除已有目标，并在游戏目录创建 WAV 文件；它不是本包的安装器。本包不含可执行安装器。

## 开发者离线验收

在工作区根目录执行：

```bat
python -B ai-mod\tools\verify_teammate_release.py
```

该入口按顺序重建独立预览包、重建 private Workshop 草稿，再运行自动发现的离线回归；任一步失败都会停止。它不启动游戏、不访问模型、不检查中文字形，也不代表公开上传已经完成。


## 手动安装与启动

### 先确认拿到哪一种包

- **独立预览 ZIP**：根目录包含 `mods/`、`bridge/` 和 `README.md`；下方第 2、4 步按这个布局描述。
- **工坊草稿 ZIP**：先进入解压后的 `DC_AI_Teammate/`，模组位于 `Contents/mods/DC_AI_Teammate/`。手动测试时，第 2 步从此位置复制模组；不要把 `Contents` 整体复制到用户 mods 目录。**该包不包含 bridge**，第 4 步必须另取独立预览包中的 `bridge/`。尚未提供公开下载地址，不能把订阅理解为已经安装模型桥接。
- **准备上传的目录**：应从当前工坊 ZIP 全新解压生成，保留 `workshop.txt` 与 `Contents/` 同级结构。旧轮次 staging 目录是历史产物，不作为当前上传源。上传与公开可见性仍需单独确认。

### 安装步骤

1. 退出游戏。保留重要世界的备份，并为首次使用选择全新的可丢弃世界。不要盲目覆盖已有队友安装，也不要删除已保存的 NPC 数据来强制重新生成。
2. 仅将归档中的 `mods/DC_AI_Teammate` 文件夹复制到 `%USERPROFILE%\Zomboid\mods\DC_AI_Teammate`。这是**用户配置目录下的 mods 目录，不是 Steam 游戏安装目录下的 mods 目录**。如果明确使用独立的游戏 `-cachedir` 配置目录，请使用该配置目录下的 `mods`。保持 `common/mod.info` 和 `42/media/...` 的结构完整。
3. 确认单独安装的 ZombieBuddy 代理已加载；为可丢弃世界启用 `ZombieBuddy`、`KnoxEventExpandedNpc` 和 `DC_AITeammate`。不要同时启用混合源码模组 `DC_AIVoice`，否则会加载重复的队友全局变量和不需要的无线电行为。更改已安装模组后请重启游戏。
4. 将归档中的 bridge 目录复制到游戏安装目录之外的私有本地目录。在该目录中将 `teammate-config.example.json` 复制为 `teammate-config.json`，并仅在本机配置它。绝不要分发填写了配置的副本。
5. Lua 文件 API 使用所选游戏的 **Lua 缓存目录**。Windows 默认路径为 `%USERPROFILE%\Zomboid\Lua\dc_teammate_request.txt` 和 `%USERPROFILE%\Zomboid\Lua\dc_teammate_reply.txt`。使用自定义 `-cachedir` 时，路径为 `<selected-profile>\Lua\...`（其中 `<selected-profile>` 为所选配置目录）。不要误用配置目录根目录、旧版 `ai_state.txt`／`ai_reply.txt`、存档目录或仓库测试配置目录。父目录必须已存在；请让所选游戏配置自行初始化这些目录。请求、回复和配置文件的路径必须各不相同。
6. 在 CMD 中进入私有桥接目录，以**持续监视模式**启动；每对邮箱仅运行一个桥接进程：

```bat
python teammate_bridge.py --config "teammate-config.json" --request "%USERPROFILE%\Zomboid\Lua\dc_teammate_request.txt" --reply "%USERPROFILE%\Zomboid\Lua\dc_teammate_reply.txt"
```

对于隔离配置目录，请将两个邮箱路径都替换为其准确的 `Lua` 绝对路径。本包未提供队友 CMD 启动器。`--once` 仅用于可选诊断：尝试处理一次后就退出；若没有请求则报错。

7. 在可丢弃世界中，站在地面层 `z=0`，确保向东一格的相邻地块已加载且空闲。右键点击世界，选择 **AI 队友 → 招募／恢复队友**（菜单文字已在原生菜单日志中核对；中文字形仍待可视验收）。首次使用会生成／招募一个 `SurvivorNpc`，验证队伍成员资格，并设置武器就绪、均衡跟随距离和防御性的 `FightStance.STAY`。它不会赋予无敌状态。正常保存／重新加载后，选择同一菜单项可恢复精确匹配的已保存 NPC；恢复时不会自动重新执行跟随。若已保存 NPC 缺失、不在队伍中或尚未加载，程序会安全拒绝操作，而不是生成替代 NPC。
8. **跟随我**和**在这里等待**直接调用本地命令。**与队友对话**发送键入的文本；模型动作仅限 `none`、`follow` 和 `wait`。**状态**显示阶段／错误。启动时不会自动招募；没有 F7 语音功能。
9. 按 Ctrl+C 停止桥接程序。停用时，先退出游戏，再禁用独立模组。移除模组不会撤销已招募 NPC 或已保存的模组数据。不要把删除 NPC id 或从现有世界移除 Knox 当作回滚办法；安全的回滚边界是使用前备份／可丢弃世界。

## 实际 API 密钥与端点配置

专用示例有意使用以下内容：

```json
{
  "api_key": "",
  "base_url": "https://api.deepseek.com",
  "model": "deepseek-chat",
  "timeout_sec": 30
}
```

请私下提供你自己的凭据。此前检查的旧版 `bridge/config.json` 中密钥也为空，并不代表已配置真实集成。队友桥接程序**仅**读取通过 `--config` 明确指定的 JSON；它不会使用 `DEEPSEEK_API_KEY`／`OPENAI_API_KEY`，不会查找工具环境凭据，不会隐式读取旧配置，也不会静默回退到离线模式。这些行为与旧版无线电桥接程序不同。

请使用不带 BOM 的 UTF-8 JSON。`api_key` 必须是非空 ASCII 字符串，且不得含空白或控制字符。`base_url` 和 `model` 必须是非空字符串。对于 `https://api.deepseek.com` 或 `https://host/v1` 这样的 API 根地址，程序会追加 `/chat/completions`；也可直接使用以 `/chat/completions` 结尾的完整 URL。程序拒绝含凭据、查询字符串、片段、空白、非 HTTP(S) 协议的 URL，并拒绝重定向。优先使用 HTTPS；代码允许明文 HTTP，但应仅限可信的本地端点。即便本地端点无需鉴权，也需要非空占位密钥，因为桥接程序始终发送 Bearer 请求头。超时默认 30 秒，必须是 `(0,300]` 范围内的有限数值；请将其保持在 Lua 邮箱 60 秒的待处理超时以内。

可选配置 `"json_mode": true` 会发送 `response_format={"type":"json_object"}`，仅适用于支持该选项的端点；默认关闭，必须填写 JSON 布尔值。它不放宽动作、文本或响应校验，不自动重试，也不保证服务端始终返回有效结果。MiniMax 3.1 实测曾返回有效中文及三种动作，但也出现无效响应，尚未完成稳定性或游戏内验收。

模型输入是固定提示词下的 NPC id、请求动作（UI 发出的是 `none`）和玩家键入文本，不是麦克风音频或旧版生命值／状态载荷。文本中不要包含秘密信息。响应必须严格为包含 `text` 和 `action` 的 JSON；其他动作、额外字段、代码／工具调用均会被拒绝。桥接程序的帮助文本和固定提示现已改为中文；固定诊断信息避免输出凭据／服务器响应正文。模型失败时会退出持续监视模式，不会重试。

若要进行不联网检查，请将 `--config ...` 替换为 `--offline`。它输出 `[offline] 离线模式：未执行动作。`，动作是 `none`；这既不能证明已访问真实模型，也不能证明模型驱动的跟随／等待。另在第 16 轮（round16），已通过获授权的本地 OpenAI 兼容端点和 `gpt-6-astra` 模型完成真实游戏链路验证：真实游戏请求收到模型的 `wait` 回复，同一个精确恢复的 NPC 随后进入 Stay 状态。尚未测试 DeepSeek 专用端点的兼容性。

## 安全、重启与验证边界

- 这些说明不要求修改原有生命值、存档文件、游戏 JAR 或声音槽位。依赖安装会另行更改所选启动器／添加自身文件。使用模组游玩**会在所选世界持久化 NPC／世界／队伍数据**；正常运行并非不写存档。
- 分派动作前会检查会话、序号、精确十进制 NPC id、成员资格、世界就绪状态、文本限制和允许的动作。桥接回复采用原子写入。邮箱是控制输入，不是经过身份认证的消息：请保持私有，并确保每个邮箱只有一个写入者。
- Lua 请求写入不是原子的。读取到部分写入／格式错误的请求可能使桥接程序安全拒绝处理并退出。Lua 会保留格式错误／身份不匹配的待处理回复，直到收到有效的关联回复或达到 60 秒超时。请查看“状态”，不要快速重复发送。
- 桥接程序的防重放最高序号记录仅保存在内存中，重启即重置。不要反复重启并对着旧的待处理请求期待无代价重试。优先使用新的游戏 Lua 会话，并有意发起新请求；不要伪造邮箱内容。
- 已检查的测试覆盖模拟 HTTP、严格协议、适配器恢复／失败路径、邮箱动作／Unicode 及 UI 连接逻辑。Lupa 是开发测试依赖，不是运行时依赖。邮箱测试既可直接运行，也已通过 `load_tests` 接入 unittest 自动发现，七组邮箱用例不会再被普通发现流程遗漏。
- 隔离配置记录已验证真实跟随移动、等待、Unicode 传输、正常保存／进程重启后的精确 id 恢复、原生 NPC 战斗，以及第 16 轮中真实模型驱动同一恢复 NPC 等待。此前还测试了全新归档解压、桥接程序执行、空密钥失败且不替换回复、白名单内容和清单哈希。
- 第 17 轮（round17）已验证从解压后的分发包进行原生游戏加载，但该环境沿用了已安装的依赖，**不是无既有依赖的全新安装验证**。中文菜单跟随、等待、对话打开、确定提交和取消已在后续隔离测试中通过真实鼠标点击；中文字形渲染、中文输入法和 NPC 中文说话显示尚未完成可视验收。中文源码、桥接提示、元数据和说明已纳入重建预览包，并通过解压后的桥接运行及自动化回归测试；这些测试不能替代原生可视验收。这仍是预览版，不能宣称端到端发布验收已完成。
