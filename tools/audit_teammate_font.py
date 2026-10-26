"""Read-only BMFont glyph coverage audit; no game mutation or visual acceptance."""
import argparse
import json
from pathlib import Path
import re


def audit(font, texts):
    ids = {int(value) for value in re.findall(r'^char\s+id=(\d+)\b', font, re.M)}
    if not ids:
        raise ValueError('字体索引没有可识别的字符记录')
    required = set(''.join(texts)) - set('\r\n\t')
    missing = sorted(required - {chr(value) for value in ids})
    return {'glyph_count': len(ids), 'required_count': len(required),
            'missing': [{'character': c, 'codepoint': f'U+{ord(c):04X}'} for c in missing],
            'coverage_pass': not missing,
            'scope': '仅检查字形索引，不证明贴图可用、屏幕显示或输入法正常'}


def ui_texts(source):
    # This project's UI literals use U(decimal codepoints); ignore U(...) declaration.
    values = re.findall(r'\bU\(([\d,\s]+)\)', source)
    return [''.join(chr(int(n.strip())) for n in value.split(',')) for value in values]


def main():
    parser = argparse.ArgumentParser(description='只读检查 AI 队友中文菜单所需字形')
    parser.add_argument('--font', required=True, type=Path)
    parser.add_argument('--ui', type=Path, default=Path(__file__).resolve().parents[1] / 'DC_AIVoice/42.0/media/lua/client/DC_AI_TeammateUI.lua')
    args = parser.parse_args()
    texts = ui_texts(args.ui.read_text(encoding='utf-8'))
    if not texts:
        parser.error('没有提取到菜单文字，不能报告通过')
    result = audit(args.font.read_text(encoding='utf-8'), texts)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['coverage_pass'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
