# 第22轮：工坊目录草稿构建

新增 tools/build_workshop_package.py：复用独立包 FILES 白名单，只将4个模组文件放到 DC_AI_Teammate/Contents/mods/...；其余为 workshop.txt、中文说明、检查清单、更新记录和 SHA256。官方模板路径确认 Contents 大写。构建验证 private、无既有工坊ID、精确成员列表、CRC及所有哈希。未上传。

新增 publish-draft/README.md、发布说明.md、发布检查清单.md、更新记录.md。候选版本0.1.0-preview尚未正式发布，不擅自选择许可证/作者。构建产物 dist/DC_AI_Teammate-workshop-draft.zip 是待完成草稿，缺preview.png、作者许可确认、桥接下载地址和原生中文交互验收，不可称可直接发布。

执行工坊构建成功；完整unittest32通过；独立预览包重新构建且解压桥接测试通过。无游戏进程/模型请求/后台任务。下一步应优先真实中文UI点击显示，避免继续只做包装。目标未完成。
