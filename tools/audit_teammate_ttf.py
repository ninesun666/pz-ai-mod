"""Read-only TrueType/OpenType metadata and Unicode cmap audit; no font distribution."""
import argparse
import bisect
import json
from pathlib import Path
import struct
from audit_teammate_font import ui_texts


def inspect_font(data, texts):
    def u16(o): return struct.unpack_from('>H', data, o)[0]
    def u32(o): return struct.unpack_from('>I', data, o)[0]
    tables = {}
    for i in range(u16(4)):
        o = 12 + 16*i
        tables[data[o:o+4]] = (u32(o+8), u32(o+12))
    metadata = {}
    start, size = tables[b'name']
    base = start + u16(start+4)
    for i in range(u16(start+2)):
        platform, encoding, language, nid, length, offset = struct.unpack_from('>6H', data, start+6+12*i)
        if nid not in (0, 1, 5, 8, 13, 14): continue
        text = data[base+offset:base+offset+length].decode('utf-16-be' if platform in (0, 3) else 'latin-1')
        values = metadata.setdefault(str(nid), [])
        if text not in values: values.append(text)
    start, size = tables[b'cmap']
    groups = []
    for i in range(u16(start+2)):
        platform, encoding, offset = struct.unpack_from('>HHI', data, start+4+8*i)
        o = start+offset
        if (platform == 0 or (platform == 3 and encoding == 10)) and u16(o) == 12:
            groups = [struct.unpack_from('>III', data, o+16+12*j) for j in range(u32(o+12))]
            break
    if not groups: raise ValueError('需要 Unicode format 12 cmap；未找到，不能判断覆盖')
    starts = [g[0] for g in groups]
    def covered(cp):
        i = bisect.bisect_right(starts, cp)-1
        return i >= 0 and cp <= groups[i][1] and groups[i][2]+cp-groups[i][0] != 0
    required = set(''.join(texts))-set('\r\n\t')
    missing = sorted(c for c in required if not covered(ord(c)))
    return {'metadata': metadata, 'required_count': len(required), 'missing': missing,
            'coverage_pass': not missing, 'scope': '仅检查字体索引与内嵌元数据；不证明游戏加载、视觉显示或发行许可材料完整'}


def main():
    parser = argparse.ArgumentParser(description='只读检查本地 TTF 中文字形覆盖与许可元数据')
    parser.add_argument('--font', required=True, type=Path)
    parser.add_argument('--ui', type=Path, default=Path(__file__).resolve().parents[1]/'DC_AIVoice/42.0/media/lua/client/DC_AI_TeammateUI.lua')
    args = parser.parse_args()
    texts = ui_texts(args.ui.read_text(encoding='utf-8'))
    if not texts: parser.error('未提取到 UI 文字')
    result = inspect_font(args.font.read_bytes(), texts)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['coverage_pass'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
