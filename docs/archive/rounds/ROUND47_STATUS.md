# 第47轮：MiniMax JSON 模式与原生前台限制

先对授权端点做了受控对比：普通模式和 `response_format=json_object` 都能返回可解析中文 JSON，返回的 MiniMax 实际模型名为 `MiniMax-M3.1-Flash`。随后启动隔离原生测试并等待加载，但当前 GUI 前台保护两次拒绝 `SetForegroundWindow` 后输入，无法进入世界/触发新请求；后台游戏与桥接 watcher 已取消并收集，确认没有遗留隔离 Java 进程。

没有把本轮当成原生成功，也没有改变严格校验来规避失败。完整自动回归49项通过。

发现 ai-mod/bridge/config.json 仍存在旧版配置文件，但 api_key 为空且不在发行白名单；独立包和工坊包均不包含它。后续发行审计需继续保证旧配置不进入制品。
