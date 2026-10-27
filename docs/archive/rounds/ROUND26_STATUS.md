# 第26轮：真实中文“在这里等待”点击验证

添加仅限test-profile的回调观察器和安全点击脚本。点击脚本先验证PID命令行属于隔离test-profile，再验证前台窗口，按实际客户区853×480与游戏坐标1280×720换算，并等待hover稳定后发送真实鼠标点击。

live-chinese-ui4.log证据：NPC131恢复成功；真实右键构建中文子菜单且`submenu_chinese_options=true`；根/子菜单位置被日志记录。随后用观察到的坐标真实点击“在这里等待”，记录：
`DC_UI_CLICK: 在这里等待`
`DC_UI_AFTER: phase=waiting npc=131 error=nil`
这证明中文菜单点击实际触发生产wait回调，并将同一恢复NPC131置于waiting，未抛异常。观察器不在发行包。

仍缺：真实“跟随我”点击证据（生产状态由waiting回following）、中文对话框按钮及模型中文NPC说话显示；不可据此完成全部视觉验收。隔离进程PID31484经命令行校验后已停止，job pwsh-70902456fee246a4已收集；JVM -1为主动终止，无遗留后台任务。
