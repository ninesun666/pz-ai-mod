# 第55轮：本地可用简体中文字库候选

发现本机已有 C:/Windows/Fonts/NotoSansSC-VF.ttf；只读解析 TTF name/cmap 元数据，不联网下载、不复制字体、不修改游戏文件。

内嵌声明：Noto Sans SC，Version 2.04;241114210130;non-release；© 2014-2021 Adobe，Reserved Font Name 'Source'；SIL Open Font License 1.1，链接 http://scripts.sil.org/OFL。

新增 tools/audit_teammate_ttf.py。实测 format12 Unicode cmap 覆盖当前 UI 所需178个字符，无缺字。这仅证明索引覆盖，不证明游戏能直接加载 TTF、字体贴图生成正确、屏幕效果或发行许可材料完整。字体未进入发行包。下一步应在隔离测试模组生成 BMFont 并确认游戏字体覆盖机制；先保留完整许可材料，再考虑分发。

Google Fonts 页面也被 web_fetch 域名非公网解析检查拒绝，未绕过。
