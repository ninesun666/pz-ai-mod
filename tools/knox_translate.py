#!/usr/bin/env python3
"""Knox Event Expanded 英→简体中文翻译流水线（自译，供单一模组内置）。

用法: knox_translate.py            # 断点续传运行
依赖: 已授权模型端点（进程内使用，不落盘）
输入: ai-mod/knox-i18n/en_source.json
输出: ai-mod/knox-i18n/cn_partial.json（增量）→ 全部完成后合并为 cn_merged.json
"""
import json, os, sys, time, urllib.request
from pathlib import Path

WORK = Path("ai-mod/knox-i18n")
SRC = WORK / "en_source.json"
PARTIAL = WORK / "cn_partial.json"
MERGED = WORK / "cn_merged.json"
ENDPOINT = "http://192.168.1.3:8080/v1/chat/completions"
MODEL = "gpt-6-astra"
BATCH = 40

GLOSSARY = {
    "Safehouse": "安全屋", "Loot/Looting": "搜刮", "Squad": "小队", "Group": "队伍",
    "Follow": "跟随", "Stay": "原地待命", "Threat": "威胁", "Quest": "任务",
    "Sandbox": "沙盒", "Morale": "士气", "Robbery": "抢劫", "Distress": "求救",
    "NPC": "NPC", "Backpack": "背包", "Melee": "近战", "Firearm": "枪械",
    "Ammo": "弹药", "Perk/Skill": "特长/技能", "Zombie": "僵尸", "Survivor": "幸存者",
    "Encounter": "遭遇", "Trade": "交易", "Patrol": "巡逻", "Forage": "采集",
}

SYSTEM = """你是资深简体中文游戏本地化译者，正在翻译《Project Zomboid》（僵尸毁灭工程）B42 的 NPC 模组 Knox Event Expanded 的界面文本。

规则：
1. 只输出一个 JSON 对象，键与输入完全一致（一字不差），值为简体中文译文。
2. 必须翻译每一个键，不得遗漏、不得保留英文原文（品牌名、NPC、Knox 等专有名词除外）。
3. 严格原样保留： %s %d 等格式符、{花括号占位符}、<RGB:...>、[img]等标记、换行符。
4. 术语表：""" + "；".join(f"{k}→{v}" for k, v in GLOSSARY.items()) + """
5. 风格：僵尸末日生存游戏界面用语，简短自然，符合中文游戏习惯。"""


def call_model(items, key):
    prompt = "翻译以下 JSON（键→英文原文），返回键完全相同的 JSON（键→简体中文译文）：\n" + json.dumps(items, ensure_ascii=False)
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=body, headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer " + key,
    })
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode("utf-8"))
    content = data["choices"][0]["message"]["content"]
    return json.loads(content)


def main():
    key = os.environ.get("MODEL_KEY")
    if not key:
        print("缺少 MODEL_KEY 环境变量"); sys.exit(2)
    src = json.loads(SRC.read_text(encoding="utf-8"))
    flat = [(fname, k, v) for fname, d in src.items() for k, v in d.items()]
    done = {}
    if PARTIAL.exists():
        done = json.loads(PARTIAL.read_text(encoding="utf-8"))
        print(f"续传: 已有 {len(done)} 条", flush=True)
    todo = [(f, k, v) for f, k, v in flat if f"::{f}::{k}" not in done]
    print(f"总计 {len(flat)} 条, 待译 {len(todo)} 条", flush=True)
    fails = 0
    for i in range(0, len(todo), BATCH):
        chunk = todo[i:i + BATCH]
        items = {f"{f}::{k}": v for f, k, v in chunk}
        for attempt in range(3):
            try:
                res = call_model(items, key)
                if not isinstance(res, dict):
                    raise ValueError("非对象响应")
                missing = [kk for kk in items if kk not in res or not str(res[kk]).strip()]
                if missing:
                    raise ValueError(f"缺 {len(missing)} 键: {missing[:3]}")
                for kk, vv in res.items():
                    done[kk] = str(vv)
                PARTIAL.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
                fails = 0
                break
            except Exception as e:
                print(f"批次 {i//BATCH} 第{attempt+1}次失败: {e}", flush=True)
                time.sleep(3 * (attempt + 1))
        else:
            fails += 1
            if fails >= 3:
                print("连续失败过多，中止（可续传）"); sys.exit(1)
        print(f"进度 {min(i+BATCH,len(todo))}/{len(todo)}", flush=True)
    # 合并回按文件结构
    merged = {fname: {} for fname in src}
    for kk, vv in done.items():
        fname, _, k = kk.partition("::")
        merged.setdefault(fname, {})[k] = vv
    MERGED.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"完成: {len(done)} 条 → {MERGED}")


if __name__ == "__main__":
    main()
