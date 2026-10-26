#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音输入：麦克风录音 + 识别。

本地识别（默认，免费）：
    pip install sounddevice faster-whisper
    模型第一次会自动下载（base 约 145MB，small 约 500MB）

在线识别（可选，OpenAI 兼容 /audio/transcriptions）：
    config 里 asr.provider = "api"，需要 api_key（可和 LLM 用同一个）

用法：
    python voice.py --list              列出麦克风
    python voice.py --record 5 out.wav  录 5 秒
    python voice.py --say out.wav       识别一个 wav
"""

import os
import sys
import wave

SAMPLE_RATE = 16000

_models = {}


def list_input_devices():
    try:
        import sounddevice as sd
    except ImportError:
        return []
    result = []
    for index, dev in enumerate(sd.query_devices()):
        if dev.get("max_input_channels", 0) > 0:
            result.append((index, dev.get("name", "?"), dev.get("max_input_channels")))
    return result


def record(path: str, seconds: float = 6.0, device=None) -> bool:
    try:
        import numpy as np  # noqa: F401
        import sounddevice as sd
    except ImportError:
        return False

    frames = int(seconds * SAMPLE_RATE)
    audio = sd.rec(frames, samplerate=SAMPLE_RATE, channels=1, dtype="int16", device=device)
    sd.wait()
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())
    return True


def _local_model(size: str):
    model = _models.get(size)
    if model is None:
        from faster_whisper import WhisperModel

        model = WhisperModel(size, device="cpu", compute_type="int8")
        _models[size] = model
    return model


def transcribe_local(path: str, size: str = "base", language: str = "zh") -> str:
    model = _local_model(size)
    segments, _info = model.transcribe(path, language=language or None, vad_filter=True, beam_size=1)
    text = "".join(seg.text for seg in segments).strip()
    try:
        import zhconv  # whisper 有时吐繁体
        text = zhconv.convert(text, "zh-cn")
    except Exception:  # noqa: BLE001
        pass
    return text


def transcribe_api(path: str, cfg: dict) -> str:
    import json
    import uuid
    from urllib import request

    base = str(cfg.get("asr_base_url") or cfg.get("base_url") or "https://api.openai.com/v1").rstrip("/")
    url = base + "/audio/transcriptions"
    boundary = "----dcaiv" + uuid.uuid4().hex
    with open(path, "rb") as f:
        audio = f.read()

    fields = {
        "model": str(cfg.get("asr_model") or "whisper-1"),
        "language": str(cfg.get("asr_language") or "zh"),
    }
    body = b""
    for key, value in fields.items():
        body += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (boundary, key, value)).encode("utf-8")
    body += ("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"audio.wav\"\r\n"
             "Content-Type: audio/wav\r\n\r\n" % boundary).encode("utf-8")
    body += audio + b"\r\n"
    body += ("--%s--\r\n" % boundary).encode("utf-8")

    req = request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "multipart/form-data; boundary=" + boundary,
            "Authorization": "Bearer " + str(cfg.get("api_key", "")),
        },
        method="POST",
    )
    with request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return str(data.get("text", "")).strip()


def transcribe(path: str, cfg: dict) -> str:
    provider = str(cfg.get("asr_provider") or "local").lower()
    if provider == "api":
        return transcribe_api(path, cfg)
    try:
        return transcribe_local(path, str(cfg.get("asr_model_size") or "base"), str(cfg.get("asr_language") or "zh"))
    except ImportError:
        return ""


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="DC_AIVoice voice input")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--record", type=float, help="record N seconds")
    parser.add_argument("--out", default="test_record.wav", help="output wav for --record")
    parser.add_argument("--say", help="transcribe a wav file")
    parser.add_argument("--device", type=int, help="input device index")
    parser.add_argument("--model", default="base")
    args = parser.parse_args()

    if args.list:
        devices = list_input_devices()
        if not devices:
            print("没有可用的麦克风（或没装 sounddevice）")
            return 1
        for index, name, ch in devices:
            print(f"  [{index}] {name}  ({ch} ch)")
        return 0

    if args.record:
        ok = record(args.out, args.record, args.device)
        print("recorded" if ok else "record failed", args.out)
        return 0 if ok else 1

    if args.say:
        text = transcribe_local(args.say, args.model)
        print(text)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
