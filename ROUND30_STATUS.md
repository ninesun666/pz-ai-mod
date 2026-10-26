# 第30轮：可重复工坊发行包

改进build_workshop_package.py：固定ZIP时间戳为2026-01-01 00:00:00、Unix创建系统、0644文件权限、按路径排序写入，并让SHA256.json按键排序。两次连续构建得到相同包SHA256：20C756CA9B154667DF4EAC6995E5D8DC7D7E3587F89C2FDD41BE90BDF15692ED。

扩展test_workshop_package.py，检查归档元数据可复现且不存在bridge、test、log或preview.png；独立工坊验收4项通过。全套测试由35增至36项，全部通过。

工坊归档仍仅private staging，不含bridge和临时封面，未上传。中文原生UI的菜单、等待、对话框已有日志证据；跟随、按钮提交/取消、中文模型回复和字体视觉仍待原生验证。提交权、bridge下载地址和封面仍是发布阻塞项。
