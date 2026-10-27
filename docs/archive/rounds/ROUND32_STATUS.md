# 第32轮：真实跟随与取消按钮验收

隔离原生游戏通过守卫鼠标脚本完成：
1. 真实右键打开“AI 队友”中文根菜单；
2. 真实点击“跟随我”；
3. 观察器记录 `DC_UI_CLICK: 跟随我` 和 `DC_UI_AFTER: phase=following npc=131 error=nil`（日志1377-1378）；
4. 再次真实打开菜单，进入“与队友对话”；
5. 真实点击中文“取消”；
6. 观察器记录 `DC_DIALOG_CLICK: CANCEL beforeSeq=0 beforePending=false` 和 `DC_DIALOG_AFTER: seq=0 pending=false phase=idle error=nil`（日志1407-1408）。

这证明同一恢复NPC131可由中文菜单切回following，取消不会写邮箱或改变序号。原生对话框按钮日志也确认中文“确定／取消”与内部OK/CANCEL。PID13028经隔离命令行校验后停止，后台job已收集。

仍未完成真实桥接模型中文响应及NPC中文Say渲染；也未声称视觉字形验收。