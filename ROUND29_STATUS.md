# 第29轮：工坊发行包独立验收

新增 tests/test_workshop_package.py，直接读取已构建 `dist/DC_AI_Teammate-workshop-draft.zip`，不依赖构建脚本内部断言，校验：

- 12个文件精确白名单、无额外文件、ZIP可读；
- SHA256.json逐文件摘要与内容一致；
- 路径无绝对路径、`..`或反斜杠；
- `version=1`、`visibility=private`、没有Workshop `id=`；
- 依赖致谢与Workshop ID 3397396843/3619862853；
- `DC_AITeammate`、`versionMin=42.21`；
- 解压后源码、mod.info和文档与当前工作区逐字节一致。

构建后独立测试通过，完整unittest由此前32增至35项，全部通过。另创建全新 `dist/workshop-staging-round29/`，从ZIP解压并再次逐文件hash和精确文件集验证通过；该目录仍是private staging，未上传。

工坊构建脚本仍明确提示：封面、提交权/授权、bridge下载地址和原生中文验收待完成。此轮未运行游戏，未修改原存档。
