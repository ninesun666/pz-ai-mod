# 第23轮：真实右键中文菜单事件验证

将当前生产中文UI部署到test-profile隔离副本，SHA256=219CE1E856C8EF4A35BAF878D52A6DE2D4DD0C1AB8EED29851B81CE0624A2248。精确reload世界9534980797/NPC131，combat=false且modelTest未启用。

真实原生游戏运行，先校验前台窗口句柄再单击进入世界；NPC131成功恢复、成员true。随后再次校验前台窗口，发送真实右键按下/释放。live-chinese-ui1.log 1369-1370实际OnFillWorldObjectContextMenu事件记录根选项包括AI 队友、teammate_root_present=true。这不是手动触发Lua事件或调用菜单回调，证明真实右键创建中文根菜单。未证明子菜单点击/屏幕字形/说话显示。

捕获chinese-menu.png后read_image拒绝：当前模型不支持图像输入。不能声称已看到截图。为避免盲点选未发送子菜单点击。可以后续添加只读坐标/回调日志或由支持图像的会话检查，但不可把日志当视觉验收。

只在检查命令行匹配隔离profile后停止PID10712，未保存。后台job pwsh-e3d854fd21d64171已收集（强制结束JVM -1非未解释故障）。无活动游戏作业。未修改原存档。

工坊可发布条件仍未满足，目标继续active。
