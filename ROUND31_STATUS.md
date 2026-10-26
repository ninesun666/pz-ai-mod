# 第31轮：真实中文确定按钮与邮箱提交

在test-profile原生游戏通过真实右键/根菜单/与队友对话/确定按钮完成一次实际UI提交。观察器仅预填中文“请在这里等待”（不是真实键盘输入），不直接调用提交回调；实际确定按钮由守卫鼠标脚本点击。测试过程均先验证隔离PID及前台窗口。

live-chinese-submit.log 1402-1403：
- DC_DIALOG_CLICK: OK beforeSeq=0 beforePending=false
- DC_DIALOG_AFTER: seq=1 pending=true phase=pending error=nil

并读回test-profile/Lua/dc_teammate_request.txt：严格五字段，npc_id=131，seq=1，action=none，text=请在这里等待。证明原生确定按钮成功调用生产提交逻辑，并正确写出Unicode请求文本。

本轮没有启动模型桥接，不伪造模型响应；不证明模型回复或NPC说话。取消按钮、跟随点击、完整中文视觉仍待验收。PID25008已校验隔离命令行后终止；job pwsh-ad60a66e222e4510已收集，JVM -1为主动终止，无后台任务。
