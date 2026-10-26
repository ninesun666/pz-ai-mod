#!/usr/bin/env python3
"""烘焙 Noto Sans SC → Project Zomboid BMFont 图集（简体缺字根治）。

用法: bake_zomboid_fonts.py <输出根目录> [--sets 1x,2x,3x,4x]
输出: <输出根>/CN/{1x,2x,3x,4x}/zomboid{Small,Medium,Large}Chinese.fnt + _NN.png

规格严格对齐原版 42.21（实测提取）:
  1x: Small 19/19/15  Medium 29/29/23  Large 33/33/27
  2x: Small 26/26/21  Medium 33/33/27  Large 40/40/32
  3x: Small 33/33/27  Medium 40/40/32  Large 45/45/36
  4x: Small 38/38/31  Medium 45/45/36  Large 50/50/40   (size/lineHeight/base)
页 512x512, spacing=1, padding=0, outline=0, aa=2; 字形存 alpha 通道, RGB=白。
"""
import argparse, time
from pathlib import Path
import numpy as np
from PIL import Image, ImageFont

FONT_PATH = r"C:\Windows\Fonts\NotoSansSC-VF.ttf"
PAGE_W = PAGE_H = 512
SPACING = 1
WEIGHT = 400
FACE = "Noto Sans SC"

SPEC = {  # scale -> [(slot, size, lineHeight, base)]
    "1x": [("Small", 19, 19, 15), ("Medium", 29, 29, 23), ("Large", 33, 33, 27)],
    "2x": [("Small", 26, 26, 21), ("Medium", 33, 33, 27), ("Large", 40, 40, 32)],
    "3x": [("Small", 33, 33, 27), ("Medium", 40, 40, 32), ("Large", 45, 45, 36)],
    "4x": [("Small", 38, 38, 31), ("Medium", 45, 45, 36), ("Large", 50, 50, 40)],
}
SLOT_FILE = {"Small": "zomboidSmallChinese", "Medium": "zomboidMediumChinese", "Large": "zomboidLargeChinese"}


def build_charset(extra_paths=()):
    seen = set()

    def add(cps):
        seen.update(cps)
    add(range(0x20, 0x7F))       # ASCII 可打印
    add(range(0xA1, 0x180))       # Latin-1 补充/常用符号
    add(range(0x386, 0x3FF))      # 希腊字母(官方字料含β等)
    add(range(0x2010, 0x2027))    # 破折/引号/省略
    add(range(0x3000, 0x3020))    # CJK 标点
    add([0x30FB])                 # 中点
    add(range(0xFF01, 0xFF5F))    # 全角形式
    # GB2312 一二级汉字全集（双字节区 B0A1-F7FE）
    for hi in range(0xB0, 0xF8):
        for lo in range(0xA1, 0xFF):
            try:
                seen.update(ord(c) for c in bytes([hi, lo]).decode("gb2312"))
            except Exception:
                pass
    # 官方简体翻译字料 + 模组自身字符串（防 GB2312 外字符漏网）
    for p in extra_paths:
        path = Path(p)
        if path.is_dir():
            files = [q for q in path.rglob("*") if q.suffix in (".txt", ".json", ".lua")]
        else:
            files = [path]
        for f in files:
            try:
                seen.update(ord(ch) for ch in f.read_text(encoding="utf-8", errors="ignore")
                            if ord(ch) >= 0x20 and not ch.isspace())
            except Exception:
                pass
    seen.discard(0x13)  # 控制字符不入集
    return sorted(c for c in seen if c >= 0x20)


class Sheet:
    """numpy 页合成器：shelf 打包，字形直接写 alpha 通道。"""

    def __init__(self):
        self.pages = [np.zeros((PAGE_H, PAGE_W, 4), dtype=np.uint8)]
        self.px = self.py = self.rowh = 0
        self.pi = 0

    def alloc(self, w, h):
        if w > PAGE_W:
            w = PAGE_W
        if self.px + w + SPACING > PAGE_W:
            self.px = 0
            self.py += self.rowh + SPACING
            self.rowh = 0
        if self.py + h + SPACING > PAGE_H:
            self.pages.append(np.zeros((PAGE_H, PAGE_W, 4), dtype=np.uint8))
            self.pi = len(self.pages) - 1
            self.px = self.py = self.rowh = 0
        x, y = self.px, self.py
        self.px += w + SPACING
        self.rowh = max(self.rowh, h)
        return self.pi, x, y

    def blit(self, pi, x, y, arr):
        h, w = arr.shape[:2]
        self.pages[pi][y:y + h, x:x + w] = arr


def bake_one(out_dir: Path, slot: str, size: int, line_h: int, base: int, charset, font_cache):
    if size not in font_cache:
        f = ImageFont.truetype(FONT_PATH, size)
        try:
            f.set_variation_by_axes([WEIGHT])
        except Exception:
            pass
        font_cache[size] = (f, f.getmetrics()[0])
    font, ascent = font_cache[size]

    glyphs = []
    for cp in charset:
        ch = chr(cp)
        try:
            adv = font.getlength(ch)
        except Exception:
            continue
        if adv <= 0 and cp != 0x20:
            continue
        try:
            bbox = font.getbbox(ch)
        except Exception:
            continue
        if not bbox:
            glyphs.append((cp, None, 0, 0, int(round(adv))))
            continue
        x0, y0, x1, y1 = bbox
        w, h = x1 - x0, y1 - y0
        if w <= 0 or h <= 0:
            glyphs.append((cp, None, 0, 0, int(round(adv))))
            continue
        if w > PAGE_W or h > PAGE_H:
            continue
        mask = font.getmask(ch, mode="L")
        if mask.size != (w, h):
            if mask.size[0] >= x1 and mask.size[1] >= y1:
                img = Image.frombytes("L", mask.size, bytes(mask)).crop((x0, y0, x1, y1))
                a = np.frombuffer(img.tobytes(), dtype=np.uint8).reshape(h, w)
            else:
                continue
        else:
            a = np.frombuffer(bytes(mask), dtype=np.uint8).reshape(h, w)
        rgba = np.zeros((h, w, 4), dtype=np.uint8)
        rgba[..., 0:3] = 255
        rgba[..., 3] = a
        glyphs.append((cp, rgba, x0, y0, int(round(adv))))

    glyphs.sort(key=lambda g: (-(g[1].shape[0] if g[1] is not None else 0), g[0]))

    sheet = Sheet()
    entries = []
    for cp, arr, x0, y0, adv in glyphs:
        if arr is None:
            if cp == 0x20:  # 空格：照原版给 1x1 空位，避免 0 尺寸兼容风险
                pi, px, py = sheet.alloc(1, 1)
                entries.append((cp, px, py, 1, 1, 0, 0, adv, pi))
            else:
                entries.append((cp, 0, 0, 0, 0, 0, 0, adv, 0))
            continue
        h, w = arr.shape[:2]
        pi, px, py = sheet.alloc(w, h)
        sheet.blit(pi, px, py, arr)
        yoff = y0 - (ascent - base)
        entries.append((cp, px, py, w, h, x0, yoff, adv, pi))

    stem = SLOT_FILE[slot]
    n = len(sheet.pages)
    for i, arr in enumerate(sheet.pages):
        Image.fromarray(arr, "RGBA").save(out_dir / f"{stem}_{i:02d}.png")
    lines = [
        f'info face="{FACE}" size={size} bold=0 italic=0 charset="" unicode=1 stretchH=100 smooth=1 aa=2 padding=0,0,0,0 spacing=1,1 outline=0',
        f"common lineHeight={line_h} base={base} scaleW={PAGE_W} scaleH={PAGE_H} pages={n} packed=0 alphaChnl=0 redChnl=4 greenChnl=4 blueChnl=4",
    ]
    for i in range(n):
        lines.append(f'page id={i} file="{stem}_{i:02d}.png"')
    lines.append(f"chars count={len(entries)}")
    for cp, px, py, w, h, xo, yo, adv, pi in sorted(entries):
        lines.append(f"char id={cp} x={px} y={py} width={w} height={h} xoffset={xo} yoffset={yo} xadvance={adv} page={pi} chnl=15")
    lines.append("kernings count=0")
    (out_dir / f"{stem}.fnt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return n, len(entries)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--sets", default="1x,2x,3x,4x")
    ap.add_argument("--corpus", action="append", default=[
        r"D:\SteamLibrary\steamapps\common\ProjectZomboid\media\lua\shared\Translate\CN",
        r"ai-mod\DC_AIVoice\42.0\media\lua",
    ], help="字料来源目录(官方翻译+模组字符串)")
    args = ap.parse_args()
    out = Path(args.out)
    charset = build_charset(args.corpus)
    print(f"字符集 {len(charset)} 个码位", flush=True)
    t0 = time.time()
    font_cache = {}
    total = 0
    for scale in args.sets.split(","):
        d = out / "CN" / scale
        d.mkdir(parents=True, exist_ok=True)
        for slot, size, lh, base in SPEC[scale]:
            t1 = time.time()
            n, cnt = bake_one(d, slot, size, lh, base, charset, font_cache)
            total += n
            print(f"[{scale}/{slot}] size={size} glyphs={cnt} pages={n} 用时{time.time()-t1:.0f}s", flush=True)
    print(f"完成: 共 {total} 页, 总用时 {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
