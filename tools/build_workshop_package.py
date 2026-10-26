"""Stage only own release files; never copy profiles or upload anything."""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import hashlib
import json
from build_teammate_package import ROOT, FILES


def build():
    # Match official ModTemplate/Contents/mods capitalization.
    prefix = 'DC_AI_Teammate/'
    payload = {prefix + 'Contents/' + name: path.read_bytes()
               for name, path in FILES.items() if name.startswith('mods/')}
    for name in ('workshop.txt', 'README.md', '更新记录.md', '发布说明.md', '发布检查清单.md', '依赖与许可说明.md'):
        payload[prefix + name] = (ROOT / 'publish-draft' / name).read_bytes()
    payload[prefix + '安装说明.md'] = (ROOT / 'TEAMMATE_INSTALL_DRAFT.md').read_bytes()
    metadata = payload[prefix + 'workshop.txt'].decode('utf-8')
    assert 'visibility=private' in metadata.splitlines()
    assert not any(line.startswith('id=') for line in metadata.splitlines())
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in payload.items()}
    output = ROOT / 'dist/DC_AI_Teammate-workshop-draft.zip'
    output.parent.mkdir(parents=True, exist_ok=True)
    entries = dict(payload)
    entries[prefix + 'SHA256.json'] = json.dumps(
        manifest, ensure_ascii=False, indent=2, sort_keys=True).encode('utf-8')
    with ZipFile(output, 'w', ZIP_DEFLATED) as z:
        for name in sorted(entries):
            info = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = ZIP_DEFLATED
            z.writestr(info, entries[name])
    with ZipFile(output) as z:
        assert z.testzip() is None
        assert set(z.namelist()) == set(payload) | {prefix + 'SHA256.json'}
        for name, digest in manifest.items():
            assert hashlib.sha256(z.read(name)).hexdigest() == digest
    print('Validated private Workshop draft:', output)
    print('NOT upload-ready: final preview image, ownership/submission rights, bridge download URL, native Chinese glyph/IME/speech-display acceptance and explicit upload confirmation pending.')


if __name__ == '__main__':
    build()
