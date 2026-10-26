# 【历史文档】Workshop 发布审计清单（ai-mod）

> **已被当前 AI 队友发行流程取代。** 本文保留旧版审计证据，不是当前上传说明，也不描述 `DC_AI_Teammate` 的最终目录、版本或权限状态。当前发行源以 `tools/build_workshop_package.py`、`publish-draft/README.md` 和最新构建的私有 ZIP 为准。

> 审计范围：仅检查本地已安装的 Project Zomboid Workshop 示例、`ai-mod` 源码/目录与已存在的安装脚本；本次**不上传、不复制第三方二进制、不读取或修改凭据、不修改现有源代码**。
>
> 审计结论：当前目录可作为开发/测试工作区，但还不是可直接发布的 Workshop staging tree。发布前必须重新建立“只含自有文件”的干净包，并完成权利、依赖和运行验证。

## 1. 已核验的官方 Workshop 示例

### 1.1 `workshop.txt` 的精确格式

已读取游戏安装目录中的官方模板：

`D:\SteamLibrary\steamapps\common\ProjectZomboid\Workshop\ModTemplate\workshop.txt`

文件的逐行格式为（示例原文）：

```text
version=1
title=Mod Template
description=This is an example mod with two worlds.  You can use this as a template for your own map mods.
description=
description=The first world has a single 300x300-tile cell.
description=The second world adds cells all around the first world.
tags=
visibility=public
```

已在 `ai-mod/fresh-package-profile/Workshop/ModTemplate/workshop.txt` 和 `ai-mod/test-profile/Workshop/ModTemplate/workshop.txt` 交叉核对，内容一致。

**可据此确认的格式约束：**

- 第一行是 `version=1`。
- 元数据使用 `key=value`，不是 JSON，也不是 SteamCMD 的 VDF。
- 标题字段是单行 `title=`。
- 描述可以重复多行，每一行都使用 `description=`；空描述行也以 `description=` 保留。
- 标签使用 `tags=`，示例为空；实际标签必须来自游戏允许列表。
- 可见性使用 `visibility=public`（游戏 UI 还支持 `friendsOnly`、`private`、`unlisted`，源码中的对应字符串已核验）。
- 本地官方模板没有 `publishedfileid`、Steam 登录令牌或上传凭据字段。
- 描述内容应避免未经验证的换行/编码假设；最终发布包应使用 UTF-8 并进行一次干净读取验证。

### 1.2 Workshop 内容目录层级

已读取官方模板目录：

```text
Workshop/
└─ ModTemplate/
   ├─ workshop.txt
   └─ Contents/
      └─ mods/
         └─ ModTemplate/
            ├─ mod.info
            ├─ poster.png
            └─ media/
               └─ maps/
                  ├─ ModTemplateWorld1/
                  │  ├─ map.info
                  │  └─ spawnpoints.lua
                  │  └─ thumb.png
                  └─ ModTemplateWorld2/
                     ├─ map.info
                     ├─ spawnpoints.lua
                     └─ thumb.png
   └─ preview.png
```

注意：`preview.png` 位于 Workshop item 根目录；模板的 `poster.png` 位于 `Contents/mods/<ModId>/` 内。两者不是同一位置，不能仅凭文件名替换层级。

对 `ai-mod` 这类普通脚本模组，建议发布 staging tree 明确采用：

```text
<StagingRoot>/
├─ workshop.txt
├─ preview.png                 # 待发布者提供/确认，建议 256×256；不要从第三方素材直接复制
└─ Contents/
   └─ mods/
      └─ DC_AIVoice/
         └─ 42.0/
            ├─ mod.info
            └─ media/
               └─ lua/
                  └─ client/
                     ├─ DC_AIVoice.lua
                     ├─ DC_AIVoice_UI.lua
                     ├─ DC_AI_Teammate.lua
                     ├─ DC_AI_TeammateMailbox.lua
                     └─ DC_AI_TeammateUI.lua
```

这里的 `42.0` 层级来自现有模组目录和 README 中对 B42 的静态检查结论；`mod.info` 的 `id` 必须保持 `DC_AIVoice`。Workshop 根部的 `Contents/mods` 与游戏用户目录安装用的 `Zomboid\mods` 是不同概念，不能把开发目录原样上传。

### 1.3 官方 UI 的进一步证据

已读取游戏源码 `media/lua/client/OptionScreens/WorkshopSubmitScreen.lua`：

- UI 预览区域按 `256×256` 绘制（第 287–289 行）。这支持将 256×256 作为预览图的兼容性基线，但仍需以当前游戏/Steam 实际校验结果为准。
- UI 保存标题、描述、标签、可见性后调用 `item:writeWorkshopTxt()`（第 346–351 行）。
- 可见性字符串包括 `public`、`friendsOnly`、`private`、`unlisted`（第 300–309 行）。
- 标签来自 `SteamWorkshopItem.getAllowedTags()`（第 312–314 行）。已读取官方 `media/WorkshopTags.txt`，当前允许值包括 `Build 42`、`Audio`、`Framework`、`Interface`、`Language/Translation`、`Multiplayer`、`QoL` 等；发布时只能选择实际适用标签，不应臆造标签。

## 2. 当前 ai-mod 源码/包结构审计

已读取 `ai-mod/README.md`、`DC_AIVoice/42.0/mod.info`、Lua 文件、bridge Python 文件、构建/安装脚本。当前自有模组主体为：

```text
ai-mod/DC_AIVoice/42.0/
├─ mod.info
└─ media/lua/client/
   ├─ DC_AIVoice.lua
   ├─ DC_AIVoice_UI.lua
   ├─ DC_AI_Teammate.lua
   ├─ DC_AI_TeammateMailbox.lua
   └─ DC_AI_TeammateUI.lua
```

现有 `mod.info` 精确内容包含：

```text
name=无线电里的阿D·AI
id=DC_AIVoice
description=把游戏状态交给外部 bridge 调大模型，让阿D 根据你的处境实时说话。需要配合 bridge.py 使用；没开 bridge 时用本地兜底台词。
```

当前已发现的**不可直接纳入 Workshop 包**内容：

- `ai-mod/agent/dcaiv-agent.jar`、`guardagent.jar`、`*.class`：已编译 Java/agent 二进制，来源与构建可复现性、第三方依赖、运行时安全边界均需单独审查；本审计不复制它们。
- `ai-mod/fresh-package-profile/`、`ai-mod/test-profile/`：包含 `ZombieBuddy`、`KnoxEventExpanded` 等第三方/测试内容，不能整体上传。
- `ai-mod/voice-samples/*.mp3`：音频权利、生成服务条款、声音模型/人物标识授权未核验；不要直接打包。
- `ai-mod/bridge/config.json`：可能含 API key 或其他私密配置；不要读取、复制或发布。只可发布不含秘密的 `config.example.json`。
- `ai-mod/bridge/bridge.log`、临时目录、测试输出、凭据/缓存和构建产物：均应排除。
- `install-ai.ps1` 会把模组复制到用户 `Zomboid\mods`，并可能在游戏安装目录生成语音槽位；它是本地安装器，不是 Workshop 内容清单，不能把安装脚本行为误写成 Workshop 必需层级。

## 3. 许可证与第三方依赖风险

### 3.1 ZombieBuddy / Knox 依赖

已读到测试 profile 中的 `ZombieBuddy/LICENSE.txt`：它是 MIT 许可文本，版权声明为 Andrey “Zed” Zaikin；MIT 的版权与许可通知必须保留在其被再分发的软件副本或实质部分中。许可证只覆盖该项目在许可证范围内的代码，**不自动授予**其依赖库、素材、Workshop 内容、商标或服务的权利。

已读取 `ZombieBuddy/README.md`：

- ZombieBuddy 基于 ByteBuddy。
- README 要求 Java 17、Project Zomboid Build 42+，并警告 Java mod 具有不受限的系统访问能力。
- 示例说明 Java mod 通过 `require=\\ZombieBuddy`、`javaJarFile`、`javaPkgName` 接入。
- 测试中的 Knox `common/mod.info` 明确写有 `require=\\ZombieBuddy`、`javaJarFile=media/java/KnoxEventExpanded.jar`、`javaPkgName=knox.event.patches`，且 `versionMin=42.21`。

因此发布 DC_AIVoice 时必须选择并明确写入以下之一：

- **独立发布**：只发布 `DC_AIVoice` 的 Lua/自有说明，不把 Knox、ZombieBuddy、ByteBuddy 或其 JAR 塞进包内；README 明确说明哪些功能需要用户另行安装，并核对兼容版本。
- **依赖发布**：先取得 ZombieBuddy、ByteBuddy、Knox 的再分发许可和版本信息，并在包内按许可证要求附带通知；没有这些权利文件不得捆绑。

当前证据不足以证明可以再分发 `ZombieBuddy`、`KnoxEventExpanded`、ByteBuddy、Steam Workshop 内容或其二进制。审计结论按“不可捆绑、需外部依赖”处理。

### 3.2 Python 运行依赖

已从源码/脚本核验到的可选或必需依赖：

- Python 3（脚本由 `python bridge.py` 启动）。
- LLM 侧使用 Python 标准库 `urllib`，没有看到必须随包复制的 HTTP 二进制。
- TTS 安装脚本执行 `python -m pip install --upgrade edge-tts miniaudio`。
- 语音输入源码按需导入 `sounddevice`、`numpy`、`faster_whisper`，并可选导入 `zhconv`。
- faster-whisper 首次运行会下载模型；模型权利、模型仓库许可证和网络下载行为需在发布说明中单独披露，不能把未核验模型当作本项目资产。
- Windows SAPI 路线使用系统组件，可作为不安装 edge-tts 的降级方案，但应在干净机器上验证。

发布说明必须列出：Python 版本、pip 包及其版本锁定策略、模型下载位置/许可证、网络访问目的、API 数据处理和失败回退；不要把用户的 API key 写入示例或 Workshop 内容。

### 3.3 语音与外部服务

- `edge-tts` 使用在线语音服务；具体服务条款、可发布音频的权利、商用/再分发限制需要发布者确认。
- `voice-samples/*.mp3` 的来源、生成参数、是否含第三方声音模仿或人物标识目前没有授权证据；发布前应删除，或补齐逐文件来源与许可记录。
- LLM API key、语音 API key、ASR key 都属于凭据，不能进入 Workshop 包、截图、日志或 README 示例。
- 默认配置中的 DeepSeek URL、模型名只是配置示例；不代表本项目拥有该服务的商标/服务授权，也不应承诺服务可用性。

## 4. 发布前 checklist

### A. 包内容

- [ ] 建立全新的临时 staging 目录，不从 `ai-mod` 根目录整体复制。
- [ ] 仅放入 `workshop.txt`、发布者自有 `preview.png`、`Contents/mods/DC_AIVoice/42.0/...`。
- [ ] 确认 `mod.info` 的 `id=DC_AIVoice` 与目录名一致。
- [ ] 不包含 `config.json`、日志、临时目录、`.class`、JAR、测试 profile、第三方模组、第三方 MP3 或凭据。
- [ ] 对 staging tree 做文件清单和 SHA-256 记录，确保上传前后没有未审查文件。

### B. workshop.txt

- [ ] 第一行严格为 `version=1`。
- [ ] 有非空 `title=` 和非空 `description=`；官方 UI 也会拒绝空标题/描述。
- [ ] `tags=` 只使用官方允许标签，建议至少评估 `Build 42`、`Audio`、`Interface`、`QoL` 是否真实适用。
- [ ] 按发布意图设置 `visibility=`；首次验证建议 `private` 或 `unlisted`，确认无误后再公开。
- [ ] 用 UTF-8 读取回写并检查换行、中文标题、重复 `description=` 行。

### C. 功能/安全

- [ ] 在未安装第三方 profile 的干净 B42.21+ 环境验证模组能加载。
- [ ] 分别验证 bridge 离线模式、无 API key 模式、真实 API 模式；真实 API 测试必须使用发布者本地环境变量或本地未纳入包的配置。
- [ ] 验证 bridge 发送的数据范围、日志脱敏、网络失败和超时行为。
- [ ] 若保留 Java agent，单独发布、单独签名/哈希和安全警告；不能把它伪装成普通 Lua Workshop 内容。
- [ ] 核对安装器对游戏目录、用户目录和 `ProjectZomboid64.json` 的写入行为；发布说明要明确它不是 Workshop 自动安装步骤。

### D. 权利/依赖

- [ ] 为自有 Lua、Python、文档、图标和预览图提供许可证/版权声明。
- [ ] 为每个第三方包记录名称、版本、来源 URL、许可证、是否允许再分发；无法证明的组件不打包。
- [ ] 明确 ZombieBuddy/ByteBuddy/Knox 是否为外部依赖；不要复制其 JAR 或 Workshop 内容。
- [ ] 记录 edge-tts、faster-whisper、模型、SAPI、LLM 服务和音频样例的条款/授权状态。
- [ ] 在 Workshop 描述中写出外部依赖、网络访问、API key 不随包提供、以及 Java agent 的高权限风险。

## 5. 实际发布仍缺少的输入

在真正创建 Workshop item 或上传前，仍需发布者提供/确认：

1. **发布身份与目标**：Steam 账号/发布者本人在交互式 Steam 客户端中完成登录；本审计不接触凭据，也不代为上传。
2. **最终 Workshop 标题、长描述、标签和可见性**：当前只有开发 README 和官方模板示例，尚无最终文案。
3. **自有预览图**：`preview.png` 的最终文件、版权来源、尺寸和是否允许发布；当前未发现可确认属于本项目的 Workshop 预览图。
4. **版本策略**：目标 PZ Build（例如 42.21.x）、模组版本号、更新说明以及是否支持旧版本。
5. **依赖策略**：决定 DC_AIVoice 是否仅 Lua 独立运行，还是正式支持/要求 ZombieBuddy、Knox 或 Java agent；若捆绑，必须提供完整许可证和再分发授权。
6. **第三方清单**：edge-tts、miniaudio、sounddevice、numpy、faster-whisper、zhconv、模型、音频样例及任何 JAR 的确切版本、来源和许可证。
7. **网络/隐私文案**：哪些游戏状态会发送到哪个 API、是否保存日志、数据保留期限、用户如何禁用联网/语音。
8. **干净环境验证结果**：在不含当前测试 profile、凭据和开发缓存的机器上加载、运行、卸载和更新测试记录。
9. **上传方式与回滚方案**：由发布者决定使用游戏 Workshop UI 还是其他受支持方式；需要保留 item ID、更新权限和私有测试回滚计划。

**本次未执行的动作：** Workshop 登录、创建 item、上传/更新、Steam API 调用、复制第三方二进制、读取 `config.json` 内容、修改现有源代码或安装文件。
