#!/usr/bin/env python3
"""校验并安装 Knox 自译中文到模组 Translate/CN。"""
import json, re, sys
from pathlib import Path

EN = Path("ai-mod/test-profile/mods/KnoxEventExpanded/42/media/lua/shared/Translate/EN")
MERGED = Path("ai-mod/knox-i18n/cn_merged.json")
TARGETS = [
    Path("ai-mod/DC_AIVoice/42.0/media/lua/shared/Translate/CN"),
    Path("ai-mod/test-profile/mods/DC_AIVoice/42.0/media/lua/shared/Translate/CN"),
]
PH = re.compile(r"%[sdf]|\{[a-zA-Z_]+\}|<RGB:[^>]*>|\[/?[a-zA-Z]+\]")

def main():
    cn = json.loads(MERGED.read_text(encoding="utf-8"))
    problems = []
    stats = {}
    for f in sorted(EN.glob("*.json")):
        en_d = json.loads(f.read_text(encoding="utf-8"))
        cn_d = cn.get(f.name, {})
        miss = [k for k in en_d if k not in cn_d]
        if miss:
            problems.append(f"{f.name}: 缺 {len(miss)} 键 {miss[:3]}")
        ph_bad, leftover = [], []
        for k, ev in en_d.items():
            cv = cn_d.get(k)
            if cv is None:
                continue
            if sorted(PH.findall(ev)) != sorted(PH.findall(cv)):
                ph_bad.append(k)
            # 纯英文残留启发式（NPC/Knox 等专名豁免）
            letters = re.sub(r"[%{}\[\]<>0-9\s/,.:;!?()\-_'\"+]","",cv)
            if letters and not re.search(r"[\u4e00-\u9fff]", cv):
                leftover.append((k, cv))
        stats[f.name] = dict(total=len(en_d), translated=len(cn_d), placeholder_err=len(ph_bad), english_left=len(leftover))
        if ph_bad:
            problems.append(f"{f.name}: 占位符不一致 {ph_bad[:3]}")
        if leftover:
            problems.append(f"{f.name}: 疑似未译 {leftover[:3]}")
    for f, s in stats.items():
        print(f, s)
    if problems:
        print("== 问题 =="); [print(" -", p) for p in problems]
        sys.exit(2)
    for t in TARGETS:
        t.mkdir(parents=True, exist_ok=True)
        for fname, d in cn.items():
            (t / fname).write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("已安装 →", t)

if __name__ == "__main__":
    main()
