# 第27轮：真实中文对话框创建

隔离原生运行live-chinese-dialog.log，真实右键及坐标点击“与队友对话”，记录1383-1385：
- DC_UI_CLICK: 与队友对话
- DC_UI_AFTER: phase=recovered npc=131 error=nil
- DC_DIALOG: text=与 AI 队友对话（需要模型桥接程序） ok=确定 cancel=取消 okInternal=OK cancelInternal=CANCEL

证明原生实际鼠标打开生产对话框，按钮中文与内部标识正确。并非视觉字形验收，也未实际提交/取消或验证新中文模型回复。观察器用ISTextBox.new包装捕获实例（原生无instance单例），转发所有参数，不直接触发对话功能。UI单测通过。

PID9020经隔离命令行验证后停止，job pwsh-83100beeb50a4587已收集，JVM -1为主动终止。无后台任务。

另生成publish-draft/preview.png临时256方形文字封面；最初系统Python缺PIL，使用load_workspace_dependencies返回的Python成功生成。尚未加入工坊构建白名单，英文封面不满足中文最终设计，应替换或重新设计；不能认定封面已验收。

剩余真实跟随菜单点击、提交/取消、模型中文跟随和说话显示、完整视觉验证及许可发布材料。
