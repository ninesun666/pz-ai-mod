#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DC_AIVoice 的桥：把游戏写出来的状态喂给大模型，再把回话写回游戏。

为什么需要它：
    Project Zomboid 的 Lua（Kahlua）没有 socket/http/线程，
    所以网络请求只能由这个外部进程做。游戏和它之间只交换两个纯文本文件：

        %USERPROFILE%\\Zomboid\\ai_state.txt   游戏 -> 这里
        %USERPROFILE%\\Zomboid\\ai_reply.txt   这里 -> 游戏

用法：
    python bridge.py             正常跑（需要 config.json 里的 api_key）
    python bridge.py --offline   不联网，练手用：固定回一句，验证文件链路
    python bridge.py --once      只处理一次然后退出（调试用）
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib import error, request

HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "config.json"
LOG_PATH = HERE / "bridge.log"

sys.path.insert(0, str(HERE))
import tts as tts_module  # noqa: E402  (同目录的 tts.py)
import voice as voice_module  # noqa: E402  (同目录的 voice.py)

DEFAULT_SYSTEM = """你叫阿D，是《僵尸毁灭工程》里一个躲在诺克斯另一头的幸存者。
你靠一台时好时坏的无线电，和一个叫“他”的陌生人说话。

说话规则：
- 像真人朋友：短、口语、有点黑色幽默，会关心，也会吐槽。
- 每次只说一到两句，总长不超过 40 个字。
- 不要写旁白、不要写动作、不要用括号，不要解释规则。
- 永远不要提自己是 AI、模型或程序。
- 你看不见他，只能根据给他的状态猜；不确定就别编具体地点。
- 他在危险里就提醒他先活下来，他在安全里就陪他说句闲话。"""


def log(msg: str) -> None:
    line = time.strftime("%H:%M:%S ") + msg
    print(line, flush=True)
    try:
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def load_config() -> dict:
    cfg_path = CONFIG_PATH
    if not cfg_path.exists():
        example = HERE / "config.example.json"
        if not example.exists():
            raise SystemExit(
                "找不到 config.json。把 config.example.json 复制成 config.json，填上 api_key 再跑。"
            )
        log("没找到 config.json，先用 config.example.json（没有 key，只能用 --offline）")
        cfg_path = example
    with cfg_path.open("r", encoding="utf-8-sig") as f:
        cfg = json.load(f)

    cfg.setdefault("base_url", "https://api.deepseek.com")
    cfg.setdefault("model", "deepseek-chat")
    cfg.setdefault("temperature", 0.9)
    cfg.setdefault("max_tokens", 200)
    cfg.setdefault("min_interval_sec", 8)
    cfg.setdefault("system_prompt", DEFAULT_SYSTEM)
    cfg.setdefault("zomboid_dir", "")

    asr = cfg.get("asr") or {}
    cfg.setdefault("asr_provider", asr.get("provider", "local"))
    cfg.setdefault("asr_model_size", asr.get("model_size", "base"))
    cfg.setdefault("asr_language", asr.get("language", "zh"))
    cfg.setdefault("asr_seconds", asr.get("seconds", 6))

    if not cfg.get("api_key"):
        cfg["api_key"] = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    return cfg


def zomboid_dir(cfg: dict) -> Path:
    if cfg.get("zomboid_dir"):
        return Path(cfg["zomboid_dir"]).expanduser()
    return Path(os.environ.get("USERPROFILE", Path.home())) / "Zomboid"


def find_game_dir(cfg: dict) -> Path | None:
    if cfg.get("game_dir"):
        return Path(cfg["game_dir"])
    roots = []
    for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles")):
        if base:
            roots.append(Path(base) / "Steam")
    for drive in "CDEFGH":
        roots.append(Path(f"{drive}:\\SteamLibrary"))
    for root in roots:
        candidate = root / "steamapps" / "common" / "ProjectZomboid"
        if (candidate / "ProjectZomboid64.exe").exists():
            return candidate
    return None


def parse_state(text: str) -> dict:
    state = {}
    for line in text.splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            state[key.strip()] = value.strip()
    return state


MOODLE_WORDS = {
    "-1": "",
    "0": "",
    "1": "有一点",
    "2": "明显",
    "3": "很严重",
    "4": "快撑不住了",
}


def describe(state: dict) -> str:
    bits = []

    hour = state.get("hour")
    if hour is not None:
        try:
            h = int(float(hour))
            period = "凌晨" if h < 5 else "早上" if h < 9 else "上午" if h < 12 else "中午" if h < 14 else "下午" if h < 18 else "傍晚" if h < 21 else "夜里"
            bits.append(f"现在是{period}{h}点")
        except ValueError:
            pass

    days = state.get("days")
    if days is not None:
        bits.append(f"已经活了{days}天")

    health = state.get("health")
    if health is not None:
        try:
            pct = int(float(health) * 100)
            if pct < 30:
                bits.append(f"伤得很重，血量{pct}%")
            elif pct < 65:
                bits.append(f"受伤了，血量{pct}%")
            else:
                bits.append(f"血量{pct}%")
        except ValueError:
            pass

    for key, label in (("hunger", "饿"), ("thirst", "渴"), ("tired", "累"), ("pain", "疼"), ("panic", "慌")):
        level = state.get(key, "0")
        word = MOODLE_WORDS.get(level, "")
        if word:
            bits.append(f"{label}：{word}")

    outside = state.get("outside")
    if outside == "1":
        bits.append("在室外")
    elif outside == "0":
        bits.append("在室内")

    weapon = state.get("weapon")
    if weapon:
        bits.append(f"手里拿着{weapon}")

    reason = state.get("reason")
    if reason == "start":
        bits.append("这是他第一次接上无线电")

    return "；".join(bits)


def build_user_prompt(state: dict) -> str:
    scene = describe(state) or "情况不明"
    return (
        f"现在的情况：{scene}。\n"
        "用无线电对他说一句话。只输出这句话本身。"
    )


def offline_reply(state: dict) -> str:
    return f"（离线测试）收到 seq={state.get('seq', '?')}，链路通了。"


def call_model(cfg: dict, state: dict) -> str:
    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    payload = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": cfg["system_prompt"]},
            {"role": "user", "content": build_user_prompt(state)},
        ],
        "temperature": cfg.get("temperature", 0.9),
        "max_tokens": cfg.get("max_tokens", 200),
        "stream": False,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + cfg["api_key"],
        },
        method="POST",
    )
    with request.urlopen(req, timeout=40) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def clean_reply(text: str, limit: int = 120) -> str:
    text = (text or "").strip()
    text = text.replace("\r", " ").replace("\n", " ")
    for prefix in ("阿D：", "阿D:", "【无线电】"):
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    if len(text) > limit:
        text = text[:limit]
    return text


def write_reply(path: Path, seq: str, text: str, sound: str | None = None, wav: str | None = None) -> None:
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        f.write(f"seq={seq}\n")
        f.write(f"text={text}\n")
        if sound:
            f.write(f"sound={sound}\n")
        if wav:
            f.write(f"wav={wav}\n")
    os.replace(tmp, path)


# ---------- 序号 / UI 面板 / 语音对话 ----------

_UI_LINES = []
_SEQ = 0
_ZDIR = Path(".")


def next_seq() -> int:
    global _SEQ
    _SEQ += 1
    try:
        (_ZDIR / "aiv_seq.txt").write_text(str(_SEQ), encoding="utf-8")
    except OSError:
        pass
    return _SEQ


def now_hhmm() -> str:
    return time.strftime("%H:%M")


def append_ui_line(who: str, text: str) -> None:
    _UI_LINES.append((now_hhmm(), who + text))
    if len(_UI_LINES) > 8:
        del _UI_LINES[:-8]


def ui_write(status: str) -> None:
    path = _ZDIR / "aiv_ui.txt"
    tmp = path.with_suffix(".tmp")
    try:
        with tmp.open("w", encoding="utf-8", newline="\n") as f:
            f.write("status=" + status + "\n")
            for t, line in _UI_LINES[-6:]:
                f.write(f"line={t}|{line}\n")
        os.replace(tmp, path)
    except OSError as exc:
        log(f"ui 写入失败: {exc}")


def call_chat(cfg: dict, messages: list) -> str:
    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    payload = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": cfg.get("temperature", 0.9),
        "max_tokens": cfg.get("max_tokens", 200),
        "stream": False,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + cfg["api_key"],
        },
        method="POST",
    )
    with request.urlopen(req, timeout=40) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def speak_reply(reply: str, speaker, reply_path: Path) -> None:
    seq = next_seq()
    wav_path = None
    if speaker is not None and speaker.cfg.get("agent", True) and speaker.cfg.get("agent_wav_dir"):
        target = Path(speaker.cfg["agent_wav_dir"]) / f"line_{seq}.wav"
        try:
            if speaker.render_wav(reply, str(target)):
                wav_path = str(target)
        except Exception as exc:  # noqa: BLE001
            log(f"wav 渲染失败: {exc}")
    write_reply(reply_path, seq, reply, None, wav_path)


def voice_turn(cfg, state, user_text, speaker, reply_path, offline=False):
    if offline:
        reply = "（离线）我听见了：" + user_text
    else:
        messages = [
            {"role": "system", "content": cfg["system_prompt"]},
            {"role": "user", "content": (
                "他在无线电里对你说：" + user_text + "\n"
                "现在的情况：" + (describe(state) or "不明") + "\n"
                "用无线电回他一句，一到两句，不超过 40 字。只输出这句话。"
            )},
        ]
        reply = call_chat(cfg, messages)
    reply = clean_reply(reply)
    if not reply:
        return None
    speak_reply(reply, speaker, reply_path)
    append_ui_line("阿D：", reply)
    return reply


def watch_voice(cfg, state, speaker, reply_path, offline):
    cmd_path = _ZDIR / "aiv_voice.txt"
    if not cmd_path.exists():
        return
    try:
        content = cmd_path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return
    if content != "rec":
        return
    try:
        cmd_path.write_text("done", encoding="utf-8")
    except OSError:
        pass

    ui_write("listening")
    audio = _ZDIR / "aiv_voice.wav"
    seconds = float(cfg.get("asr_seconds", 6))
    if not voice_module.record(str(audio), seconds):
        log("录音失败：检查麦克风 / pip install sounddevice")
        ui_write("idle")
        return
    text = voice_module.transcribe(str(audio), cfg)
    log("听到: " + (text or "(空)"))
    if not text:
        ui_write("idle")
        return
    append_ui_line("你：", text)
    ui_write("thinking")
    try:
        voice_turn(cfg, state, text, speaker, reply_path, offline)
    except Exception as exc:  # noqa: BLE001
        log(f"对话失败: {exc}")
    ui_write("idle")


def process_once(cfg: dict, state_path: Path, reply_path: Path, offline: bool, speaker=None) -> bool:
    try:
        raw = state_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False

    state = parse_state(raw)
    seq = state.get("seq")
    if not seq:
        return False

    try:
        if offline:
            text = offline_reply(state)
        else:
            text = call_model(cfg, state)
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        log(f"API HTTP {exc.code}: {detail}")
        return False
    except Exception as exc:  # noqa: BLE001
        log(f"API 调用失败: {exc}")
        return False

    text = clean_reply(text)
    if not text:
        log("模型返回了空文本，跳过")
        return False

    wav_path = None
    if speaker is not None and speaker.cfg.get("agent", True) and speaker.cfg.get("agent_wav_dir"):
        target = Path(speaker.cfg["agent_wav_dir"]) / f"line_{seq}.wav"
        try:
            if speaker.render_wav(text, str(target)):
                wav_path = str(target)
        except Exception as exc:  # noqa: BLE001
            log(f"agent wav 渲染失败: {exc}")

    sound_name = None
    if speaker is not None and str(speaker.cfg.get("output", "game")).lower() in ("game", "both"):
        if wav_path:
            sound_name = speaker.copy_to_slot(wav_path)
        else:
            sound_name = speaker.render_to_slot(text)

    write_reply(reply_path, next_seq(), text, sound_name, wav_path)
    append_ui_line("阿D：", text)
    log(f"seq={seq} -> {text}" + (f"  [{sound_name}]" if sound_name else ""))
    if speaker is not None and str(speaker.cfg.get("output", "game")).lower() in ("desktop", "both"):
        speaker.speak(text)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="DC_AIVoice bridge")
    parser.add_argument("--offline", action="store_true", help="不联网，固定回一句（测试链路）")
    parser.add_argument("--once", action="store_true", help="只处理一次就退出")
    parser.add_argument("--no-tts", action="store_true", help="只显示文字，不出声")
    parser.add_argument("--state", help="覆盖 state 文件路径（调试用）")
    parser.add_argument("--reply", help="覆盖 reply 文件路径（调试用）")
    parser.add_argument("--interval", type=float, help="最小调用间隔秒数（调试用）")
    args = parser.parse_args()

    cfg = load_config()
    zdir = zomboid_dir(cfg)
    global _ZDIR, _SEQ
    _ZDIR = zdir
    try:
        _SEQ = int((zdir / "aiv_seq.txt").read_text(encoding="utf-8").strip() or 0)
    except (OSError, ValueError):
        _SEQ = 0
    state_path = Path(args.state) if args.state else zdir / "ai_state.txt"
    reply_path = Path(args.reply) if args.reply else zdir / "ai_reply.txt"
    interval = args.interval if args.interval is not None else float(cfg.get("min_interval_sec", 8))

    if not args.offline and not cfg.get("api_key"):
        log("没有 api_key：先按离线模式跑（回固定台词）。填好 config.json 的 api_key 再重启本程序。")
        args.offline = True

    log(f"看着 {state_path}")
    log(f"回信写 {reply_path}")
    if args.offline:
        log("离线模式：不联网")

    tts_cfg = dict(cfg.get("tts") or {})
    if args.no_tts:
        tts_cfg["enabled"] = False

    output = str(tts_cfg.get("output", "game")).lower()
    if output in ("game", "both"):
        game_dir = find_game_dir(cfg)
        if game_dir:
            sound_dir = game_dir / "media" / "sound"
            tts_cfg["game_sound_dir"] = str(sound_dir)
            tts_cfg.setdefault("slot_count", 300)
            if not (sound_dir / "dcav_0000.wav").exists():
                log("警告：游戏里还没生成语音槽位 —— 先跑一次 install-ai.cmd 再重启游戏")
        else:
            log("没找到游戏目录，语音改为桌面播放")
            tts_cfg["output"] = "desktop"

    # Java agent 直通：把 wav 写在 Zomboid 目录，游戏里 DCAgentPlay 直接播
    if tts_cfg.get("enabled", True) and tts_cfg.get("agent", True):
        agent_dir = zdir / "dcaiv"
        try:
            agent_dir.mkdir(parents=True, exist_ok=True)
            for old in sorted(agent_dir.glob("line_*.wav"))[:-40]:
                try:
                    old.unlink()
                except OSError:
                    pass
            tts_cfg["agent_wav_dir"] = str(agent_dir)
        except OSError as exc:
            log(f"建 dcaiv 目录失败: {exc}")
            tts_cfg["agent"] = False

    speaker = tts_module.Speaker(tts_cfg, log=log)
    if tts_cfg.get("enabled", True):
        provider = str(tts_cfg.get("provider", "edge")).lower()
        voice = tts_cfg.get("edge_voice") if provider == "edge" else tts_cfg.get("sapi_voice")
        log(f"语音: {provider} / {voice} / 输出={tts_cfg.get('output')}")
        if provider == "edge" and not tts_module.Speaker._edge_installed():
            log("没装 edge-tts，会退回 sapi（pip install edge-tts miniaudio 可换神经语音）")
    else:
        log("语音已关闭")

    last_seq = None
    last_call = 0.0
    last_state = {}

    while True:
        try:
            if state_path.exists():
                raw = state_path.read_text(encoding="utf-8", errors="replace")
                state = parse_state(raw)
                last_state = state
                seq = state.get("seq")
                now = time.time()
                if seq and seq != last_seq and now - last_call >= interval:
                    if process_once(cfg, state_path, reply_path, args.offline, speaker):
                        last_seq = seq
                        last_call = now
                    else:
                        last_seq = seq  # 失败也记一下，别死循环重试

            watch_voice(cfg, last_state, speaker, reply_path, args.offline)
        except KeyboardInterrupt:
            log("收到 Ctrl+C，退出")
            return 0
        except Exception as exc:  # noqa: BLE001
            log(f"循环异常: {exc}")

        if args.once:
            return 0
        time.sleep(0.5)


if __name__ == "__main__":
    sys.exit(main())
