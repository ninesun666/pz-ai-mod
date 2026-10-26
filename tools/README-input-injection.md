# 输入注入辅助脚本（诊断用，已知局限）

- send-scans.ps1：扫描码级 SendInput（修正过 INPUT=40 字节结构体，返回值已校验）
- send-click.ps1：客户区坐标点击（SetCursorPos+mouse_event，坐标换算已验证正确）
- send-keys.ps1：SendKeys 路线（GLFW 游戏不消费 WM_CHAR，仅实验用）

已知结论（2026-10-27，活实例主菜单实测）：三类注入 OS 层均成功，
但 PZ/GLFW 不消费——键盘、鼠标、相对移动皆无反应；无法用于驱动游戏 UI。
IME 验收类操作只能由真人在游戏窗口完成。
