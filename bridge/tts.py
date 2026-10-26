#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS：让阿D 真的开口。

两种引擎：
  sapi  — Windows 自带（System.Speech），零依赖，音色偏机械，但立刻能用
          zh-CN 一般有：Microsoft Huihui Desktop / Huihui / Kangkang / Yaoyao
  edge  — 微软 Edge 的在线神经语音（和小智默认用的是同一套），音色多、自然
          需要：python -m pip install edge-tts miniaudio

命令行：
  python tts.py --list                         列出可用音色
  python tts.py --test "你好" --provider sapi   只合成不播放，看看 wav
  python tts.py --say "你好" --provider sapi    合成并播放
"""

import argparse
import ctypes
import io
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import wave

DEFAULTS = {
    "enabled": True,
    "provider": "edge",
    "sapi_voice": "Microsoft Huihui Desktop",
    "edge_voice": "zh-CN-YunjianNeural",
    "rate": 0,
    "volume": 100,
    "only_when_foreground": True,
    "max_chars": 80,
}


def merge_defaults(cfg: dict) -> dict:
    out = dict(DEFAULTS)
    for key, value in (cfg or {}).items():
        if value is not None:
            out[key] = value
    return out


def pz_is_foreground() -> bool:
    """只在游戏窗口在前台时说话，免得切出去还被念。"""
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return False
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, buf, 512)
        title = buf.value or ""
        return ("Zomboid" in title) or ("僵尸毁灭工程" in title)
    except Exception:  # noqa: BLE001
        return True


class Speaker:
    def __init__(self, cfg: dict | None = None, log=print):
        self.cfg = merge_defaults(cfg or {})
        self.log = log
        self._lock = threading.Lock()
        self._last = 0.0

    # ---------- 对外 ----------

    def speak(self, text: str, blocking: bool = False) -> bool:
        if not self.cfg.get("enabled", True):
            return False
        text = (text or "").strip()
        if not text:
            return False

        limit = int(self.cfg.get("max_chars", 80))
        if limit > 0 and len(text) > limit:
            text = text[:limit]

        if self.cfg.get("only_when_foreground", True) and not pz_is_foreground():
            self.log("当前不在游戏窗口，跳过语音")
            return False

        if blocking:
            return self._speak_blocking(text)
        threading.Thread(target=self._speak_blocking, args=(text,), daemon=True).start()
        return True

    # ---------- 内部 ----------

    def _speak_blocking(self, text: str) -> bool:
        with self._lock:  # 一次只说一句
            provider = str(self.cfg.get("provider", "sapi")).lower()
            try:
                if provider == "edge":
                    if self._speak_edge(text):
                        return True
                    self.log("edge 不可用，退回 sapi")
                return self._speak_sapi(text)
            except Exception as exc:  # noqa: BLE001
                self.log(f"语音失败: {exc}")
                return False

    def render_to_slot(self, text: str) -> str | None:
        """渲染成 wav，写进游戏 media/sound 的预置槽位，返回槽位名（给 Lua 播）。"""
        sound_dir = self.cfg.get("game_sound_dir")
        if not sound_dir:
            return None
        slot_count = int(self.cfg.get("slot_count", 300))
        index = getattr(self, "_slot", 0) % max(1, slot_count)
        self._slot = (index + 1) % max(1, slot_count)
        name = "dcav_%04d" % index
        path = os.path.join(sound_dir, name + ".wav")
        try:
            if self.render_wav(text, path):
                return name
        except Exception as exc:  # noqa: BLE001
            self.log(f"写入槽位失败: {exc}")
        return None

    def copy_to_slot(self, src_path: str) -> str | None:
        """把已经渲染好的 wav 复制到游戏槽位（避免重复合成）。"""
        sound_dir = self.cfg.get("game_sound_dir")
        if not sound_dir or not src_path:
            return None
        slot_count = int(self.cfg.get("slot_count", 300))
        index = getattr(self, "_slot", 0) % max(1, slot_count)
        self._slot = (index + 1) % max(1, slot_count)
        name = "dcav_%04d" % index
        try:
            shutil.copyfile(src_path, os.path.join(sound_dir, name + ".wav"))
            return name
        except Exception as exc:  # noqa: BLE001
            self.log(f"复制到槽位失败: {exc}")
            return None

    def render_wav(self, text: str, out_path: str) -> bool:
        """把一句话渲染成 16-bit PCM WAV（游戏内 FMOD 能直接吃）。"""
        text = (text or "").strip()
        limit = int(self.cfg.get("max_chars", 80))
        if limit > 0 and len(text) > limit:
            text = text[:limit]
        if not text:
            return False

        provider = str(self.cfg.get("provider", "edge")).lower()
        if provider == "edge":
            mp3 = self._edge_mp3(text)
            if mp3:
                try:
                    if self._mp3_to_wav(mp3, out_path):
                        return True
                finally:
                    try:
                        os.remove(mp3)
                    except OSError:
                        pass
            self.log("edge 渲染失败，退回 sapi")

        wav = self.synthesize_to_file(text)
        if not wav:
            return False
        try:
            tmp = out_path + ".tmp"
            shutil.copyfile(wav, tmp)
            os.replace(tmp, out_path)
            return True
        finally:
            shutil.rmtree(os.path.dirname(wav), ignore_errors=True)

    def _edge_mp3(self, text: str) -> str | None:
        if not self._edge_installed():
            return None
        tmpdir = tempfile.mkdtemp(prefix="dcaiv_")
        mp3_path = os.path.join(tmpdir, "speech.mp3")
        rate_pct = int(self.cfg.get("rate", 0)) * 5  # -10..10 -> -50%..+50%
        volume_pct = int(self.cfg.get("volume", 100)) - 100
        cmd = [
            sys.executable, "-m", "edge_tts",
            "--voice", str(self.cfg.get("edge_voice", "zh-CN-YunjianNeural")),
            "--rate=%+d%%" % rate_pct,
            "--volume=%+d%%" % volume_pct,
            "--text", text,
            "--write-media", mp3_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        if result.returncode != 0 or not os.path.exists(mp3_path) or os.path.getsize(mp3_path) < 1000:
            self.log("edge 合成失败: " + (result.stderr or "").strip()[:200])
            shutil.rmtree(tmpdir, ignore_errors=True)
            return None
        return mp3_path

    def _mp3_to_wav(self, mp3_path: str, out_path: str) -> bool:
        try:
            import miniaudio  # type: ignore
        except ImportError:
            self.log("没装 miniaudio，无法把 mp3 转 wav（pip install miniaudio）")
            return False

        decoded = miniaudio.decode_file(mp3_path)
        samples = decoded.samples
        if hasattr(samples, "tobytes"):
            raw = samples.tobytes()
        else:
            raw = bytes(samples)

        # float32 -> int16
        import array
        arr = array.array("f")
        arr.frombytes(raw[: (len(raw) // 4) * 4])
        pcm = array.array("h", (max(-32767, min(32767, int(s * 32767))) for s in arr))
        data = pcm.tobytes()

        tmp = out_path + ".tmp"
        with wave.open(tmp, "wb") as wf:
            wf.setnchannels(decoded.nchannels)
            wf.setsampwidth(2)
            wf.setframerate(decoded.sample_rate)
            wf.writeframes(data)
        os.replace(tmp, out_path)
        if os.path.getsize(out_path) < 2000:
            self.log("生成的 wav 太小，可能没声音")
            return False
        return True


    def _speak_sapi(self, text: str) -> bool:
        wav_path = self.synthesize_to_file(text)
        if not wav_path:
            return False
        try:
            import winsound
            winsound.PlaySound(wav_path, winsound.SND_FILENAME)
            return True
        finally:
            shutil.rmtree(os.path.dirname(wav_path), ignore_errors=True)

    def synthesize_to_file(self, text: str) -> str | None:
        """SAPI 合成到 wav，不播放。返回路径，调用者负责删除。"""
        tmpdir = tempfile.mkdtemp(prefix="dcaiv_")
        text_path = os.path.join(tmpdir, "text.txt")
        wav_path = os.path.join(tmpdir, "speech.wav")
        ps_path = os.path.join(tmpdir, "say.ps1")

        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)

        script = r"""
param([string]$TextFile, [string]$OutFile, [string]$Voice, [int]$Rate, [int]$Volume)
Add-Type -AssemblyName System.Speech
$text = Get-Content -LiteralPath $TextFile -Raw -Encoding UTF8
if (-not $text) { exit 2 }
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
if ($Voice) {
    try { $synth.SelectVoice($Voice) } catch { }
}
$synth.Rate = $Rate
$synth.Volume = $Volume
$synth.SetOutputToWaveFile($OutFile)
$synth.Speak($text)
$synth.Dispose()
"""
        with open(ps_path, "w", encoding="utf-8") as f:
            f.write(script)

        cmd = [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_path,
            "-TextFile", text_path, "-OutFile", wav_path,
            "-Voice", str(self.cfg.get("sapi_voice") or ""),
            "-Rate", str(int(self.cfg.get("rate", 0))),
            "-Volume", str(int(self.cfg.get("volume", 100))),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0 or not os.path.exists(wav_path) or os.path.getsize(wav_path) < 1000:
            self.log("sapi 合成失败: " + (result.stderr or "").strip()[:200])
            shutil.rmtree(tmpdir, ignore_errors=True)
            return None
        return wav_path

    # ---------- Edge 神经语音 ----------

    def _speak_edge(self, text: str) -> bool:
        if not self._edge_installed():
            return False

        tmpdir = tempfile.mkdtemp(prefix="dcaiv_")
        mp3_path = os.path.join(tmpdir, "speech.mp3")
        rate_pct = int(self.cfg.get("rate", 0)) * 5  # -10..10 -> -50%..+50%
        volume_pct = int(self.cfg.get("volume", 100)) - 100

        cmd = [
            sys.executable, "-m", "edge_tts",
            "--voice", str(self.cfg.get("edge_voice", "zh-CN-YunjianNeural")),
            "--rate=%+d%%" % rate_pct,
            "--volume=%+d%%" % volume_pct,
            "--text", text,
            "--write-media", mp3_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        if result.returncode != 0 or not os.path.exists(mp3_path) or os.path.getsize(mp3_path) < 1000:
            self.log("edge 合成失败: " + (result.stderr or "").strip()[:200])
            shutil.rmtree(tmpdir, ignore_errors=True)
            return False

        ok = self._play_audio(mp3_path, tmpdir)
        shutil.rmtree(tmpdir, ignore_errors=True)
        return ok

    @staticmethod
    def _edge_installed() -> bool:
        try:
            __import__("edge_tts")
            return True
        except ImportError:
            return False

    def _play_audio(self, path: str, tmpdir: str) -> bool:
        # 1) miniaudio：能解 mp3，也能直接出 PCM
        try:
            import miniaudio  # type: ignore

            decoded = miniaudio.decode_file(path)
            pcm = decoded.samples.tobytes() if hasattr(decoded.samples, "tobytes") else bytes(decoded.samples)
            wav_bytes = self._pcm_to_wav(pcm, decoded.sample_rate, decoded.nchannels, decoded.sample_width)
            import winsound
            winsound.PlaySound(wav_bytes, winsound.SND_MEMORY)
            return True
        except ImportError:
            pass
        except Exception as exc:  # noqa: BLE001
            self.log(f"miniaudio 播放失败: {exc}")

        # 2) ffmpeg 转 wav，再 winsound
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg:
            wav_path = os.path.join(tmpdir, "speech.wav")
            result = subprocess.run(
                [ffmpeg, "-y", "-loglevel", "error", "-i", path, wav_path],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0 and os.path.exists(wav_path):
                import winsound
                winsound.PlaySound(wav_path, winsound.SND_FILENAME)
                return True

        self.log("装了 edge-tts 但没法播放 mp3：再装 miniaudio（pip install miniaudio）或 ffmpeg")
        return False

    @staticmethod
    def _pcm_to_wav(pcm: bytes, rate: int, channels: int, width: int) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(width)
            wf.setframerate(rate)
            wf.writeframes(pcm)
        return buf.getvalue()


def list_sapi_voices() -> list[str]:
    script = (
        "Add-Type -AssemblyName System.Speech; "
        "(New-Object System.Speech.Synthesis.SpeechSynthesizer).GetInstalledVoices() | "
        "ForEach-Object { $_.VoiceInfo.Name + '|' + $_.VoiceInfo.Culture + '|' + $_.VoiceInfo.Gender }"
    )
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True, text=True, timeout=30,
    )
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def list_edge_voices(prefix: str = "zh-") -> list[str]:
    try:
        import asyncio
        import edge_tts  # type: ignore
    except ImportError:
        return []

    async def run():
        return await edge_tts.list_voices()

    voices = asyncio.run(run())
    result = []
    for v in voices:
        if str(v.get("ShortName", "")).startswith(prefix):
            result.append(f"{v['ShortName']} | {v.get('Gender', '')}")
    return sorted(result)


def main() -> int:
    parser = argparse.ArgumentParser(description="DC_AIVoice TTS")
    parser.add_argument("--list", action="store_true", help="列出可用音色")
    parser.add_argument("--test", help="只合成不播放（输出 wav/mp3 路径）")
    parser.add_argument("--say", help="合成并播放")
    parser.add_argument("--provider", default="sapi", choices=["sapi", "edge"])
    parser.add_argument("--voice", help="音色名（sapi 用全名，edge 用 ShortName）")
    parser.add_argument("--rate", type=int, default=0, help="-10..10")
    parser.add_argument("--volume", type=int, default=100, help="0..100")
    args = parser.parse_args()

    if args.list:
        print("== SAPI（Windows 自带，零依赖）==")
        for line in list_sapi_voices():
            print("  " + line)
        print("\n== Edge 神经语音（需 pip install edge-tts）==")
        edge = list_edge_voices("zh-")
        if edge:
            for line in edge:
                print("  " + line)
        else:
            print("  （没装 edge-tts，或者只显示 zh- 开头的）")
        return 0

    cfg = {
        "provider": args.provider,
        "rate": args.rate,
        "volume": args.volume,
        "only_when_foreground": False,
        "enabled": True,
    }
    if args.voice:
        if args.provider == "sapi":
            cfg["sapi_voice"] = args.voice
        else:
            cfg["edge_voice"] = args.voice

    speaker = Speaker(cfg)

    if args.test:
        if args.provider == "edge":
            print("edge 是流式在线语音，--test 不支持；直接 --say 听效果，或用 --list 换音色")
            return 0
        path = speaker.synthesize_to_file(args.test)
        if path:
            print("已生成:", path)
            return 0
        return 1

    if args.say:
        ok = speaker.speak(args.say, blocking=True)
        print("ok" if ok else "失败")
        return 0 if ok else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
