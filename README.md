# 当前入口：单人实体 AI 队友

> **本文下方是旧无线电／语音原型的历史记录，不是实体队友安装指南。**
> 请使用[队友安装说明](<TEAMMATE_INSTALL_DRAFT.md>)和[中文发行更新记录](<publish-draft/更新记录.md>)。
> 不要按下方历史步骤运行旧安装器、旧 bridge 启动器或旧 agent；不要递归复制整个源码目录。
> 实体队友仅从独立白名单发行包安装，不提供治疗、无敌等旧代理功能。当前仍是待完成验收的预览版。

---

# 给僵尸毁灭工程接大模型：逆向结论 + 能跑的原型

你要的是“接入 AI 大模型的 mod”。我先把游戏拆开看了，结论如下（B42.21.0，Java 25，`projectzomboid.jar`）。

---

## 一、逆向结果：为什么不能“纯 Lua 发 HTTP”

| 查了什么 | 结果 |
|---|---|
| Lua 运行时 | `se/krka/kahlua/*`、`org/luaj/kahluafork/*` → **Kahlua**（Lua 5.1 fork），不是原生 Lua |
| Java 桥 | `se/krka/kahlua/integration/expose/LuaJavaClassExposer` → 只暴露**白名单**里的类，mod 不能自己注册新类 |
| `luajava` | jar 里没有；`media/lua` 里也没有任何 `java.net` / `luajava` 用法 |
| 网络/线程 | Lua 侧**没有** socket / http / thread。jar 里的 HTTP 库（Javacord、OkHttp、Prometheus）都只在 Java 侧用 |
| 文件 IO | ✅ `getFileReader(name, create)` / `getFileWriter(name, create, append)`，路径相对 `%USERPROFILE%\Zomboid\` |

**结论：模组自己的 Lua 发不出网络请求。** 想联网只有三条路：

| 路线 | 做法 | 代价 | 我选它吗 |
|---|---|---|---|
| A. 文件桥 | Lua 写状态文件，外部进程调模型，写回结果 | 需要一个常驻进程，延迟 1~2 秒 | ✅ 已经做了 |
| B. Java Agent | 用 ZombieBuddy/ByteBuddy 注入 HTTP 类，再暴露给 Lua | 要 JDK 21/25（你机器上只有 JDK 8）、跟版本绑定、每次更新重做 | 以后想做“零外部进程”再上 |
| C. 改 jar | 直接往 `projectzomboid.jar` 里塞类 | 校验/更新就炸，联机反作弊也不允许 | 不推荐 |

---

## 二、A 路线长这样

```
游戏 (Lua)                      bridge.py (Python)              大模型 API
    │                                  │                            │
    │ 写 Zomboid\ai_state.txt          │                            │
    │ ────────────────────────────────>│  POST /chat/completions    │
    │                                  │ ──────────────────────────>│
    │ 读 Zomboid\ai_reply.txt          │<────────────────────────── │
    │<──────────────────────────────── │ 写 reply (seq + text)      │
    │                                  │                            │
    └─ 屏幕上方显示「【无线电】阿D：…」                              │
```

- 游戏这边只做两件事：**写状态**、**读回信**，都是纯文本，不碰网络
- 模型的人设、API key 全在 Python 那侧，改 prompt 不用动 Lua

---

## 三、声音：小智是怎么发声的，我们怎么对齐

### 小智（xiaozhi-esp32）的做法

看了一圈它的服务端（`xiaozhi-esp32-server` 系）：**设备本身不会说话**，它只负责“播”。

```
文字 -> 服务端 TTS 合成 -> opus 音频流 -> WebSocket 推给 ESP32 -> 设备解码播放
```

所以“调音色”从来不是改固件，是改**服务端 TTS 的配置**：

| TTS 服务 | 配的是哪个字段 | 例子 |
|---|---|---|
| EdgeTTS（小智默认、免费） | `voice` | `zh-CN-XiaoxiaoNeural`、`zh-CN-YunjianNeural` |
| 火山引擎 | `voice_type` | `BV700_streaming` 之类 |
| CosyVoice / ChatTTS（本地） | `spk_id` / 参考音频 | 还能做**声音克隆** |

### 我们的对应做法（已改成游戏内播放）

逆向之后找到了一个**能绕过“必须启动时注册”的口子**，现在语音是真的在游戏里响的：

```
Lua 写状态 -> bridge 调模型 -> 拿到台词 -> TTS 渲成 wav
    -> 覆盖一个预置槽位 media/sound/dcav_0123.wav
    -> 回复里带 sound=dcav_0123
    -> Lua: getSoundManager():PlayWorldSoundWav("dcav_0123", 玩家脚下, ...)
```

关键证据（CFR 反编译 `projectzomboid.jar` 得到）：

| 位置 | 行为 |
|---|---|
| `ZomboidFileSystem.init()` | 启动时只扫 `./media`，建 `activeFileMap`；`getAbsolutePath()` 只是查表 → **运行期新放的文件查不到** |
| `FMODManager.loadSound()` | 按绝对路径缓存 sample（`fileToSoundMap`）→ 同一路径只解码一次 |
| `SoundManager.PlaySoundWav` / `CacheSound` | B42 里是空实现（`return null` / 空函数），老 API 废弃了 |
| `GameSounds.getOrCreateSound(name)` | 遇到未知名字会去找 `media/sound/<name>.ogg` 或 `.wav`，找到就 `FMODManager.loadSound()` 加载 —— **这就是入口** |

所以方案是「**预置槽位 + 覆盖内容**」：

1. 安装时在游戏目录生成 300 个占位 wav（`dcav_0000.wav … dcav_0299.wav`），启动时被索引
2. 运行期 bridge 把新的语音写进还没用过的槽位（写的是完整 wav，不是空文件）
3. Lua 按名字播 —— 因为该槽位**第一次播放**才解码，所以听到的一定是刚写进去的内容
4. 一个槽位一局只用一次；300 个槽位够说一整晚，重启游戏自动重新可用

两套 TTS 引擎，配置里 `tts.provider` 切换：

| provider | 说明 | 依赖 |
|---|---|---|
| `edge`（默认） | 和小智同一套神经语音，自然 | `pip install edge-tts miniaudio` |
| `sapi` | Windows 自带，机械但立刻能用 | 无 |

edge 没装/没网时会**自动退回 sapi**，不会不出声。
`tts.output`：`game`（默认，游戏内 3D 音源）／`desktop`（桌面扬声器）／`both`。

### Java Agent（更彻底，已装好）

槽位方案有个天花板：一局 300 句。要真正无限，就得进 JVM 里加接口 —— `ai-mod/agent/`：

```
Agent.premain  -> 等 LuaManager.env 出现
               -> 往 Lua 全局塞两个函数：
                    DCAgentPing()            探活
                    DCAgentPlay("C:/x.wav")  直接 FMOD 播任意 wav
```

它用 `javafmod.FMOD_System_CreateSound(path, 8)`（8 = FMOD_2D）+ `FMOD_System_PlaySound`，
**完全绕过 `ZomboidFileSystem` 的文件索引和 FMOD 的路径缓存**，所以想播哪句播哪句，没有次数限制。

- 编译：双击 `agent/build.cmd`（用机器上的 JDK 8 就行，agent 全走反射，Java 25 能跑）
- 安装：双击 `agent/install-agent.cmd`（往 `ProjectZomboid64.json` 的 `vmArgs` 加 `-javaagent:dcaiv-agent.jar`，原文件备份为 `ProjectZomboid64.json.bak-dcaiv`）
- 卸载：`agent/uninstall-agent.cmd`
- 验证：重启游戏后看 `%USERPROFILE%\Zomboid\dcagent.log`，应有 `registered DCAgentPing / DCAgentPlay`

有 agent 时，bridge 会额外写一份 wav 到 `Zomboid\dcaiv\line_<seq>.wav` 并在回信里带 `wav=`；
Lua 优先走 `DCAgentPlay`，没有 agent 或调用失败就退回槽位方案 —— 两条路互为备份。

### 音色（试听样例在 `voice-samples/`）

| 文件 | 音色 | 感觉 |
|---|---|---|
| `yunjian.mp3` | `zh-CN-YunjianNeural` | 男声，沉稳，适合阿D（默认） |
| `yunxi.mp3` | `zh-CN-YunxiNeural` | 男声，年轻、阳光 |
| `yunyang.mp3` | `zh-CN-YunyangNeural` | 男声，播音腔、靠谱 |
| `xiaoxiao.mp3` | `zh-CN-XiaoxiaoNeural` | 女声，温暖 |
| `xiaobei.mp3` | `zh-CN-liaoning-XiaobeiNeural` | 女声，东北话，搞笑 |

```json
"tts": {
  "enabled": true,
  "output": "game",
  "provider": "edge",
  "edge_voice": "zh-CN-YunjianNeural",
  "rate": 0,
  "volume": 100,
  "only_when_foreground": true,
  "max_chars": 80,
  "slot_count": 300
}
```

- **换音色**：改 `edge_voice`（或 sapi 的 `sapi_voice`），重启 bridge
- **语速/音量**：`rate` -10~10，`volume` 0~100
- **只在游戏窗口在前台时说**：`only_when_foreground`（默认 `true`，切出去就不念了）
- 看全部音色：`python tts.py --list`；单独试一句：`python tts.py --say "你好" --voice zh-CN-YunxiNeural`

---

### 语音输入 + 左上角面板

游戏里按 **F7** → 面板显示「正在听…」→ 说一句话（最长 6 秒，说完停一下）→ 本地 whisper 识别 → 阿D 回你，并且念出来。

```
F7 ──▶ 写 Zomboid\aiv_voice.txt "rec"
        bridge 录音 6 秒 → faster-whisper 识别（中文，自动转简体）
        → 带上当前处境问模型 → 回信写 aiv_ui.txt / ai_reply.txt + wav
        → 面板滚动显示对话，语音走 agent 或槽位
```

- 面板：`media/lua/client/DC_AIVoice_UI.lua`，左上角，显示最近 4 句 + 状态（待机 / 正在听 / 在想 / 在说话）
- 依赖：`pip install sounddevice faster-whisper`（已装），首次识别会自动下模型（`base` 约 145MB）
- 换模型：`config.json` 的 `asr.model_size` 改 `tiny`（快、糙）或 `small`（准、慢）
- 不想用语音：不按 F7 就行，原来的自动播报照旧
## 四、10 分钟跑通

### 1. 装模组

双击 **`install-ai.cmd`** → **重启游戏** → 主菜单 →「模组」→ 勾选「无线电里的阿D·AI」。

> B42 的两个坑（都踩过了）：
> 1. 只认 `%USERPROFILE%\Zomboid\mods`，**不认**游戏安装目录下的 `mods`
> 2. 必须带版本子目录：`DC_AIVoice\42.0\mod.info` + `42.0\media\...`，根目录放 `mod.info` 会被静默跳过

> 先把 `DC_RadioVoice`（本地台词版）取消勾选，两个一起开会有两个阿D抢话。

### 2. 先不花钱，测链路

双击 **`bridge\test-bridge-offline.cmd`**（不联网、不用 key）。
进游戏后，只要游戏里状态一变，控制台就会打印：

```
seq=1 -> （离线测试）收到 seq=1，链路通了。
```

游戏里屏幕上方同时出现这句话，说明整条链路通了。

### 3. 装语音（可选但强烈建议）

双击 **`bridge\setup-tts.cmd`**（`pip install edge-tts miniaudio`），装完会列出音色。
不装也能跑：会自动退回 Windows 自带的 sapi 声音。

### 4. 接真模型

1. 把 `bridge\config.example.json` 复制成 `bridge\config.json`
2. 填 `api_key`（DeepSeek 控制台拿；也支持任何 OpenAI 兼容接口，改 `base_url` + `model` 即可）
3. 双击 `bridge\start-bridge.cmd`
4. 回到游戏，阿D 说的就是模型现写、并且真的念出来的了

```json
{
  "api_key": "sk-xxxx",
  "base_url": "https://api.deepseek.com",
  "model": "deepseek-chat",
  "temperature": 0.9,
  "max_tokens": 200,
  "min_interval_sec": 8,
  "system_prompt": "",
  "zomboid_dir": "",
  "tts": { "enabled": true, "provider": "edge", "edge_voice": "zh-CN-YunjianNeural" }
}
```

- `system_prompt` 留空用内置人设；想换人设直接写中文进去
- `zomboid_dir` 留空用 `%USERPROFILE%\Zomboid`；存档在别处才填
- 走本地模型（Ollama / LM Studio）：`base_url` 填 `http://127.0.0.1:11434/v1`，`api_key` 随便填

---

## 五、游戏和 bridge 之间的协议

`Zomboid\ai_state.txt`（游戏写，每次覆盖）：

```
seq=12
reason=tick
hour=22
days=3
health=0.42
hunger=3
thirst=2
tired=1
pain=2
panic=3
outside=1
x=10500
y=8300
weapon=斧头
```

`Zomboid\ai_reply.txt`（bridge 写）：

```
seq=12
text=别在城里磨蹭了，往北走，天亮前找个有门的地方。
```

Lua 只认 **seq 比上次大** 的回信，所以文件不用清空，也不会重复播报。

触发时机：开局一次；之后每 10 个游戏分钟检查一次，最快 45 秒发一次。
回信 90 秒没来，就播本地兜底台词（所以 bridge 没开也不会卡住）。

---

## 六、钱和隐私

- 一次调用大约 300~500 token（含人设），DeepSeek 现价基本是**几厘钱一次**；玩一晚上几毛钱
- `api_key` 只存在本地 `config.json`，代码不往别处发；`bridge.log` 只记回信和错误
- 发出去的是数值状态（时间、血量、坐标、手里的东西），**不含存档内容**

---

## 七、下一步能加什么（按难度）

1. **游戏内打字对话**：加一个 `ISTextEntryBox`，把你打的问题一起发给模型 → 阿D 真的“回你话”（1~2 小时）
2. **声音贴进游戏**：现在语音走桌面扬声器；想做“游戏内音源”，得预先注册一批 sound 槽位再替换文件，或者走 Java Agent
3. **让 AI 影响世界**：模型输出结构化指令（“刷 3 只僵尸”“放一包补给”），Lua 解析执行 —— 这个最像“活人”
4. **零外部进程**：走 B 路线 Java Agent，把 HTTP 客户端暴露给 Lua
5. **声音克隆**：CosyVoice / GPT-SoVITS 本地起一个，把 `base_url` 指过去，就是“你自己的声音”在陪你

---

## 八、已知限制（说在前面）

- 我在沙箱里**没法启动游戏**，所以 Lua 这半边只做了静态检查；bridge、TTS、槽位写入、agent 的 premain/注册逻辑我都测过了
- 语音槽位是**一局一次性**的：300 句用完（约一整晚）需要重启游戏；装了 Java Agent 后没有这个限制
- 新增的 mod / 槽位要在**游戏启动时**才会被索引，所以装完必须重启游戏（不是重开存档）
- Java Agent 挂在 `ProjectZomboid64.json` 上：Steam 更新或「验证游戏文件」可能会把这个 json 换回原版，那时重跑一次 `agent\install-agent.cmd` 就行
- 如果游戏里不显示、或者 `console.txt` 有 `[DC_AIVoice]` 报错，把最后 50 行发我，我照着改
- 这版是“阿D 主动根据处境说话”，**还不是**你打字它回；想那样就加第 1 项

---

## 文件结构

```
ai-mod/
├─ install-ai.cmd / uninstall-ai.cmd / install-ai.ps1
├─ voice-samples/           5 个音色试听（同一句话）
│  ├─ yunjian.mp3  yunxi.mp3  yunyang.mp3
│  └─ xiaoxiao.mp3  xiaobei.mp3
├─ agent/                   Java Agent（真正的动态播放）
│  ├─ src/com/dcai/agent/Agent.java
│  ├─ build.cmd             javac -> dcaiv-agent.jar
│  ├─ install-agent.cmd     写 -javaagent 到 ProjectZomboid64.json
│  └─ uninstall-agent.cmd
├─ DC_AIVoice/
│  ├─ mod.info
│  └─ media/lua/client/DC_AIVoice.lua
└─ bridge/
   ├─ bridge.py             LLM 桥
   ├─ tts.py                语音（edge / sapi）
   ├─ config.example.json
   ├─ start-bridge.cmd
   ├─ setup-tts.cmd         pip install edge-tts miniaudio
   └─ test-bridge-offline.cmd
```
