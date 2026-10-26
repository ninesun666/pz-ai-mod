"""Build an allowlisted teammate-only ZIP. Never reads config secrets or saves."""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    **{f'mods/DC_AI_Teammate/42/media/lua/client/{name}': ROOT / 'DC_AIVoice/42.0/media/lua/client' / name for name in (
        'DC_AI_Teammate.lua', 'DC_AI_TeammateMailbox.lua', 'DC_AI_TeammateUI.lua')},
    'mods/DC_AI_Teammate/common/mod.info': ROOT / 'teammate-package/common/mod.info',
    'mods/DC_AI_Teammate/common/poster.png': ROOT / 'teammate-package/common/poster.png',
    'bridge/teammate_bridge.py': ROOT / 'bridge/teammate_bridge.py',
    'bridge/teammate_protocol.py': ROOT / 'bridge/teammate_protocol.py',
    'bridge/teammate-config.example.json': ROOT / 'bridge/teammate-config.example.json',
    'README.md': ROOT / 'TEAMMATE_INSTALL_DRAFT.md',
}

# 集大成单模组：内置简体字体修复（OFL Noto Sans SC 自烘焙）与 Knox 简体汉化（自译）
for sub in ('fonts',):
    base = ROOT / 'DC_AIVoice/42.0/media' / sub
    if base.exists():
        for p in sorted(base.rglob('*')):
            if p.is_file():
                FILES[f'mods/DC_AI_Teammate/42/media/{sub}/{p.relative_to(base).as_posix()}'] = p
_translate_cn = ROOT / 'DC_AIVoice/42.0/media/lua/shared/Translate/CN'
if _translate_cn.exists():
    for p in sorted(_translate_cn.glob('*.json')):
        FILES[f'mods/DC_AI_Teammate/42/media/lua/shared/Translate/CN/{p.name}'] = p

def build():
    payload = {name: path.read_bytes() for name, path in FILES.items()}
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in payload.items()}
    output = ROOT / 'dist/DC_AI_Teammate-preview.zip'
    output.parent.mkdir(parents=True, exist_ok=True)
    entries = dict(payload)
    entries['SHA256.json'] = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode('utf-8')
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        for name in sorted(entries):
            info = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, entries[name])
    with ZipFile(output) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == set(payload) | {'SHA256.json'}
        for name, digest in manifest.items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == digest
    print(f'Validated {len(payload)} allowlisted files: {output}')

if __name__ == '__main__':
    build()
