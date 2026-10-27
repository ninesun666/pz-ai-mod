# 第40轮：离线中文跨语言链路回归

新增test_teammate_chinese_roundtrip.py，使用模拟HTTP响应验证三种模型动作：none/follow/wait。测试覆盖：
- Lua邮箱写出中文请求“请在这里等待，我去看看前面。”；
- Python bridge读取同一请求，发送中文系统提示和原文；
- 模拟模型返回简体中文及动作；
- Lua严格关联session/seq/npc_id，执行follow/wait或none；
- NPC Say收到中文回复，重复tick不重放；
- 明确禁止真实网络。

独立测试1项通过；全套unittest从45增至46项并全部通过。该测试证明中文协议/桥接/模拟Lua链路，不证明真实模型、原生游戏中文字形或屏幕显示。