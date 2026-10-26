# AI 队友（单人预览版）发布目录

此说明随私密工坊草稿分发，不代表已公开发布。工作区中的 `publish-draft` 只是发布文档和元数据源目录，不是可直接上传的目录；不能将它或整个开发工作区交给上传器。

请先运行开发者离线验收入口，再将生成的 `DC_AI_Teammate-workshop-draft.zip` 解压到新的空目录。解压得到的 `DC_AI_Teammate` 才包含以下结构；最终封面、验收及提交权未确认前仍不可视为上传就绪。

## 目录
- `Contents/mods/DC_AI_Teammate/`：正式模组 Lua、`common/mod.info`、`common/poster.png`（256×256 自绘封面）。
- `Contents/mods/DC_AI_Teammate/42/media/fonts/CN/`：内置简体中文字体修复（Noto Sans SC 自烘焙 BMFont 图集，OFL 1.1；随附 `FONT-CREDITS.txt` 与 `LICENSE-OFL-1.1.txt`）。Knox 与 ZombieBuddy 本体**不捆绑**（Knox 无再分发许可），保持外部依赖。
- `Contents/mods/DC_AI_Teammate/42/media/lua/shared/Translate/CN/`：内置 Knox Event Expanded 简体汉化（本项目自译，非第三方译文）。
- `workshop.txt`：按 Project Zomboid 官方模板生成，当前 `visibility=private`。
- `发布说明.md`：中文功能、依赖、安装和限制说明。
- `更新记录.md`：版本与测试记录。
- `发布检查清单.md`：上传前人工确认项。

## 明确排除
不含 API 密钥、邮箱文件、测试存档、日志、测试脚本、第三方 JAR/DLL、第三方源码、旧 DC_AIVoice 代理或任何自动安装器。

## 上传前必须确认
1. 作者/发布者名称及许可证归属。
2. 工坊封面 PNG（官方界面要求的 256×256 预览图）。
3. 最终标题、标签、可见性及 Project Zomboid 版本策略。
4. ZombieBuddy、Knox Event Expanded NPC 的独立安装和许可证说明。
5. 外部桥接程序的分发地址与 API 网络/隐私说明。
6. 用全新配置目录复测依赖安装，再由用户确认是否上传。
