# 开发核查历史证据（不随发行包分发）

## 一、实际发行范围

[`build_teammate_package.py:8–16`](<../tools/build_teammate_package.py#L8-L16>) 的白名单包括：

- [`DC_AI_Teammate.lua`](<../DC_AIVoice/42.0/media/lua/client/DC_AI_Teammate.lua>)、[`DC_AI_TeammateMailbox.lua`](<../DC_AIVoice/42.0/media/lua/client/DC_AI_TeammateMailbox.lua>)、[`DC_AI_TeammateUI.lua`](<../DC_AIVoice/42.0/media/lua/client/DC_AI_TeammateUI.lua>)；
- [`mod.info`](<../teammate-package/common/mod.info>)；
- [`teammate_bridge.py`](<../bridge/teammate_bridge.py>)、[`teammate_protocol.py`](<../bridge/teammate_protocol.py>)、示例配置及安装说明。

核验时的 [`build_workshop_package.py:11–16`](<../tools/build_workshop_package.py#L11-L16>) 只选取白名单中的 `mods/` 内容，再添加发布文档；**Workshop 草稿不包含 Python bridge，bridge 属于另行分发的独立预览包**。不能把“Workshop 订阅”写成自动安装或启动 bridge。白名单不包含第三方 JAR/DLL/源码、Python 解释器、模型、音频、安装器或私密配置。此结论来自构建代码，不是对未经重新核验的任意现存 ZIP 作保证。

## 二、没有第三方再分发，不等于已有自有代码许可

### 1. 第三方文件未入包

仅调用用户另行安装的依赖 API，不等于把依赖的软件副本分发出去。本方案不因外部依赖关系本身就需要附带 ZombieBuddy、Knox 或 ByteBuddy 的全部许可证，也不应把“尚未取得这些组件的再分发许可”误写成本方案的阻塞项。以后如果复制代码、素材、JAR、安装器或其他实质部分，必须重新审查对应许可与通知要求。

本地 ZombieBuddy [`LICENSE.txt:1–12`](<../fresh-package-profile/mods/ZombieBuddy/LICENSE.txt#L1-L12>) 是 MIT 文本，版权行是 `Copyright (c) 2025 Andrey "Zed" Zaikin`，要求在其软件副本或实质部分中保留版权与许可通知。这一已存在的许可不应说成完全没有授权，但它不自动覆盖 Knox、ByteBuddy、游戏本体或我们自己的代码，也不意味着所有上游素材均已审查。

### 2. 自有代码提交权与用户获得的权利

本次读到的三份 Lua、两份 Python 及本项目元数据中，未见明确适用于本项目的许可证或版权归属声明。不能据此编造作者、选 MIT/GPL/Apache-2.0，也不能认为公开可读就授予了任意修改、复制、再发布的权利。

[Steam Subscriber Agreement §6.A、§6.B、§6.D](https://store.steampowered.com/subscriber_agreement/#6) 规定上传产生的平台许可与订阅使用安排，并要求提交者拥有足够权利，含代表其他贡献者提交的权利。[Project Zomboid Modding Policy §3、§6](https://projectzomboid.com/blog/modding-policy/) 同样区分 Mod 原创内容的所有权、游戏方使用权和提交者保证。

因此：

- **真正必须确认的是提交权及贡献者授权**，包括说明文档、封面等一切实际发布内容。
- **没有独立开源 LICENSE 文件不自动阻止权利人发布自己的作品。** 选择开放源代码许可是权利人的选择，不是本次核验发现的 Steam 上传硬条件。
- Workshop 的平台/订阅许可不等于授予所有人一般性的源码再发布许可，也不自动覆盖站外单独分发的 Python bridge。站外 bridge 应由有权发布者说明收件人获准安装、运行及其他使用的范围；可以使用开源许可，也可以用明确的非开源使用条款。
- 本文只记录状态，不代作者作上述授权，也不擅自把“保留所有权利”作为已经选定的发行许可证。

## 三、致谢不能全部当成可选偏好

[Project Zomboid Modding Policy §1.1.2、§4.1–4.3](https://projectzomboid.com/blog/modding-policy/) 要求第三方材料取得必要许可，并规定署名；其中 §4.3 对与其他 Mod 存在实质独特或直接联系而未署名的情况，说明即使获得免署名许可，仍可能因作者投诉而下架直到补足署名。

本项目直接依赖 Knox 的 NPC API，Knox 又依赖 ZombieBuddy。因此发布页应明确致谢这些项目并链接来源，不能笼统声称“不捆绑所以无需任何致谢”。这与复制第三方许可证全文是两回事。可用不猜测个人身份的文案：

> 感谢 Knox Event Expanded NPC 项目及其贡献者提供 NPC 功能，感谢 ZombieBuddy 项目及其贡献者提供底层运行支持。本项目仅提供独立的队友控制与模型桥接，不包含上述项目文件，不代表这些项目的官方作品。

链接：

- [Knox Event Expanded NPC Workshop 项](https://steamcommunity.com/sharedfiles/filedetails/?id=3397396843)
- [ZombieBuddy Workshop 项](https://steamcommunity.com/sharedfiles/filedetails/?id=3619862853)
- [ZombieBuddy 上游仓库](https://github.com/zed-0xff/ZombieBuddy)

本次两个 Workshop 页面抓取失败：不声称在线核验了它们当前的作者列表、版本或许可。Knox 的 Workshop ID 来自现有 [`发布说明:13–14`](<发布说明.md#L13-L14>)；ZombieBuddy 的 Workshop URL 和仓库地址可由本地上游 [`README:109–113`](<../fresh-package-profile/mods/ZombieBuddy/README.md#L109-L113>) 佐证。正式发布前由发布者核对实际项目页面，避免指向失效/错误条目。

## 四、确切依赖 ID 与原生 require 语法

| 项目 | 可核验依据 | 结论 |
|---|---|---|
| 本项目 | [`mod.info:1–4`](<../teammate-package/common/mod.info#L1-L4>) | `id=DC_AITeammate`、`versionMin=42.21`；核验时无 `require=` |
| Knox | [`上游 mod.info:1–8`](<../fresh-package-profile/mods/KnoxEventExpanded/common/mod.info#L1-L8>) | `id=KnoxEventExpandedNpc`、`modversion=0.4.0-13`、`versionMin=42.21` |
| ZombieBuddy | [`上游 mod.info:1–10`](<../fresh-package-profile/mods/ZombieBuddy/42/mod.info#L1-L10>) | `id=ZombieBuddy`；此文件不证明 2.3.4 版本号 |
| 实际 NPC 调用 | [`队友适配器:28–31`](<../DC_AIVoice/42.0/media/lua/client/DC_AI_Teammate.lua#L28-L31>) | 调用 `KnoxEventLoader.getAPI("npc")`；不是可独立运行的 NPC 实现 |

**已直接证明的原文**是 Knox 元数据和 ZombieBuddy [`README:44–48`](<../fresh-package-profile/mods/ZombieBuddy/README.md#L44-L48>) 中的：

```text
require=\ZombieBuddy
```

上面实际文件中是 **一个反斜杠**。不是 JSON/Python 字符串里的转义形式，也不是 Lua 的 `require "module"`，更不是 Steam Workshop 的数字 item ID。旧 [`WORKSHOP_RELEASE_AUDIT:143–144`](<../WORKSHOP_RELEASE_AUDIT.md#L143-L144>) 双反斜杠展示不可直接照抄为两个字符。

本机游戏 [`ModSelectorModel:103–121`](<D:/SteamLibrary/steamapps/common/ProjectZomboid/media/lua/client/OptionScreens/ModSelector/ModSelectorModel.lua#L103-L121>) 使用 `modInfo:getRequire()` 建立依赖关系，[`:138–155`](<D:/SteamLibrary/steamapps/common/ProjectZomboid/media/lua/client/OptionScreens/ModSelector/ModSelectorModel.lua#L138-L155>) 用它调整加载顺序。这证明 `require` 是游戏依赖元数据，不只是说明文字。但本次未读取其底层字符串解析实现，**不声称已证明多依赖分隔符、重复键或本项目拟新增声明的原生解析结果**。

本项目应把已证实的 Mod ID 与“用户需单独安装并启用两项依赖”的说明写清。添加原生 `require` 可改善缺依赖检查/加载顺序，但不是许可证要求；当前缺少该字段是依赖元数据缺口，不等于已有手动安装必然不可运行。Workshop 的 Required Items 关系与游戏 `require` 是不同层次，不应假装在描述里写了名称就已经配置好两者。

## 五、Python 与网络说明应缩小到实际源码

[`teammate_bridge:12–33`](<../bridge/teammate_bridge.py#L12-L33>) 只导入 Python 标准库及自有协议模块；[`teammate_protocol:34–41`](<../bridge/teammate_protocol.py#L34-L41>) 也全为标准库。因此旧语音项目审计涉及的 `edge-tts`、`miniaudio`、`sounddevice`、`numpy`、`faster-whisper`、`zhconv`、模型下载和声音样例权利，**都不是本方案已经存在的运行/再分发依赖**。不需要凭空增加 pip 许可证清单或模型授权阻塞项；也不必打包 Python 解释器或其完整许可证，除非发行范围将来扩展为捆绑解释器。

[`发布说明:21`](<发布说明.md#L21>) 把 Python 3.10+ 作为用户要求；这是发布支持基线，不是本次从源码或运行测试证明的最低解释器版本。

[`teammate_bridge:133–152`](<../bridge/teammate_bridge.py#L133-L152>) 显示网络 payload 含配置的模型名、系统提示、`npc_id`、`action` 和玩家 `text`；请求头携带用户自己的 API key。不要沿用“发送全部游戏状态”或“下载 ASR 模型”等不适用表述。[`:87–120`](<../bridge/teammate_bridge.py#L87-L120>) 接受用户配置的 HTTP/HTTPS endpoint，应建议使用可信 HTTPS；[`:214–228`](<../bridge/teammate_bridge.py#L214-L228>) 明确离线模式不调用模型。不替服务商承诺数据保留期限、免费可用性或隐私政策；把服务费用和条款交由用户在实际选用服务时确认。

## 六、阻塞项与可选项

### 本方案真正需要解决的事项

1. **权利确认缺口**：有权提交者须确认自有内容与全部贡献者授权；未经确认不代其上传。仅凭文件名或“没有第三方 JAR”不能完成此项。
2. **站外 bridge 的授权说明**：缺少独立使用/再利用授权文本，不要宣称用户已有无限制改编、再分发权。由权利人明确希望授予的范围，不要求其必须开源。
3. **准确的依赖说明与致谢**：保留上述来源/致谢，注明外部安装，不宣称自身已有原生依赖声明。正式发布前核对依赖页面；不因“不捆绑”取消致谢。
4. **与发行方式一致的交付说明**：如承诺完整模型功能，需提供实际可获得的 bridge 发行渠道和网络说明；只有 Workshop Lua 包时明确 bridge 不随订阅提供。若尚无下载地址，它是交付缺口，不是第三方再分发许可缺口。
5. **维持白名单边界**：最终制品不得混入凭据、日志、存档、第三方代码/二进制、模型或音频。本次没有运行构建或验证最终上传物。

### 不是本次证明的硬性许可要求

- 选择某个开源许可证；自有代码的权利人可以不作一般开源授权。
- 虚构 `author=`、`license=`，或宣称这些字段是游戏必须字段；显示名称与提交权是不同问题。
- 给不存在于本包的第三方副本补齐一整套许可证，或先取得所有外部依赖的捆绑许可。
- 无意义的 pip 版本锁定/模型许可证清单；本 bridge 没有这些依赖。
- 额外署名排版、每个文件的重复版权头、独立 `NOTICE` 文件、发布编号或校验清单的具体格式；若最终所选许可有相应要求，则按该许可另行落实。

干净环境验证、封面合规、中文界面验收、最终标题与可见性属于其他发布质量/平台条件，不应与“必须选择开源许可证”混为一谈。本次没有启动游戏、上传、修改凭据或给任何代码授予许可证；只新增/整理本文。
