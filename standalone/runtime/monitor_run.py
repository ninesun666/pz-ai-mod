"""Read-only smoke monitor: python monitor_run.py <run_dir> [duration_sec].
Records transitions and latest diagnostics; captures the desktop every 30s after
world load. Does not send input. Stops at report.json or bounded duration.
"""
import json
import sys
import time
from pathlib import Path

TRANSITIONS = (
    'bootstrap loaded', 'world started', 'first game-thread tick',
    'registry ready', 'companion spawned', 'companion model active',
    'spawn failed', 'game exited', 'follow-probe PASS', 'follow-probe FAIL',
)


def capture(out_path):
    try:
        from PIL import ImageGrab
        ImageGrab.grab().save(out_path)
        return True
    except Exception:
        pass
    import subprocess
    escaped = str(out_path).replace("'", "''")
    ps = (
        'Add-Type -AssemblyName System.Drawing;Add-Type -AssemblyName System.Windows.Forms;'
        '$b=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds;'
        '$bmp=New-Object System.Drawing.Bitmap($b.Width,$b.Height);'
        '$g=[System.Drawing.Graphics]::FromImage($bmp);'
        '$g.CopyFromScreen(0,0,0,0,$b.Size);$g.Dispose();'
        f"$bmp.Save('{escaped}',[System.Drawing.Imaging.ImageFormat]::Png);"
        '$bmp.Dispose()'
    )
    result = subprocess.run(['powershell', '-NoProfile', '-Command', ps],
                            capture_output=True, timeout=15)
    if result.returncode:
        print('[monitor] capture failed: ' + result.stderr.decode(errors='replace')[-400:], flush=True)
    return result.returncode == 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    run_dir = Path(argv[0])
    duration = int(argv[1]) if len(argv) > 1 else 600
    seen = set()
    last_diag = None
    shots = 0
    started = time.monotonic()
    last_shot = -30.0
    print(f'[monitor] watching {run_dir} for {duration}s', flush=True)
    while time.monotonic() - started < duration:
        text = '\n'.join(p.read_text(encoding='utf-8', errors='replace')
                         for p in (run_dir / 'stdout.log', run_dir / 'stderr.log') if p.exists())
        lines = text.splitlines()
        for marker in TRANSITIONS:
            if marker in text and marker not in seen:
                seen.add(marker)
                last = next(line for line in reversed(lines) if marker in line)
                print(f'[monitor] {last.strip()}', flush=True)
        diag = next((line for line in reversed(lines) if '[DCStandalone] diag ' in line), None)
        if diag and diag != last_diag:
            print(f'[monitor] {diag.strip()}', flush=True)
            last_diag = diag
        elapsed = time.monotonic() - started
        if 'world started' in text and elapsed - last_shot >= 30:
            shots += 1
            out = run_dir / f'shot_{shots:03d}.png'
            try:
                ok = capture(out)
            except Exception as error:
                print(f'[monitor] capture error: {error}', flush=True)
                ok = False
            if ok:
                print(f'[monitor] shot {out.name}', flush=True)
            last_shot = elapsed
        report = run_dir / 'report.json'
        if report.exists():
            try:
                result = json.loads(report.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                pass  # A partially written report is retried on the next bounded poll.
            else:
                print(f"[monitor] terminal report passed={result.get('passed')} reason={result.get('reason')}", flush=True)
                break
        if 'game exited' in text or ('spawn failed' in text and 'companion spawned' not in text):
            print('[monitor] terminal log state reached', flush=True)
            break
        time.sleep(2)
    print(f'[monitor] done; {shots} capture attempts', flush=True)


if __name__ == '__main__':
    main()
