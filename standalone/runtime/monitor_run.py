"""Live monitor for a smoke_game.py run: my own eyes during tests.

Usage: python monitor_run.py <run_dir> [duration_sec]
- Detects key transitions from stdout.log and prints one line per transition.
- Saves a full-screen capture every 30s into the run dir (shot_000.png ...).
- Exits when the log reports spawn failure/game exit or duration elapses.
"""
import ctypes
import json
import sys
import time
from pathlib import Path

run_dir = Path(sys.argv[1])
duration = int(sys.argv[2]) if len(sys.argv) > 2 else 600
log = run_dir / 'stdout.log'
err = run_dir / 'stderr.log'

TRANSITIONS = (
    'bootstrap loaded', 'world started', 'first game-thread tick',
    'registry ready', 'companion spawned', 'companion model active',
    'diag ', 'spawn failed', 'game exited',
)

AddType = None
import ctypes.wintypes as wt
user32 = ctypes.windll.user32


def capture(out_path):
    try:
        import PIL.ImageGrab as ig
        ig.grab().save(out_path)
        return True
    except Exception:
        pass
    # Fallback: GDI screen copy of the primary display.
    try:
        import clr  # pythonnet may not exist; keep silent
    except Exception:
        pass
    ps = (
        'Add-Type -AssemblyName System.Drawing;Add-Type -AssemblyName System.Windows.Forms;'
        '$b=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds;'
        '$bmp=New-Object System.Drawing.Bitmap($b.Width,$b.Height);'
        '$g=[System.Drawing.Graphics]::FromImage($bmp);'
        '$g.CopyFromScreen(0,0,0,0,$b.Size);$g.Dispose();'
        f'$bmp.Save(r\"{out_path}\",[System.Drawing.Imaging.ImageFormat]::Png);'
        '$bmp.Dispose()'
    )
    import subprocess
    return subprocess.run(['powershell', '-NoProfile', '-Command', ps],
                          capture_output=True).returncode == 0


def main():
    seen = set()
    shots = 0
    started = time.monotonic()
    last_shot = 0.0
    print(f'[monitor] watching {run_dir} for {duration}s', flush=True)
    while time.monotonic() - started < duration:
        text = ''
        for p in (log, err):
            if p.exists():
                text += p.read_text(encoding='utf-8', errors='replace')
        for marker in TRANSITIONS:
            if marker in text and marker not in seen:
                seen.add(marker)
                last = [l for l in text.splitlines() if marker in l][-1]
                print(f'[monitor] {time.strftime("%H:%M:%S")} {last.strip()[:160]}', flush=True)
        if 'companion spawned' in text and time.monotonic() - last_shot > 30:
            shots += 1
            out = run_dir / f'shot_{shots:03d}.png'
            if capture(str(out)):
                print(f'[monitor] shot {out.name}', flush=True)
            last_shot = time.monotonic()
        if 'game exited' in text or ('spawn failed' in text and 'companion spawned' not in text):
            print('[monitor] terminal state reached', flush=True)
            break
        time.sleep(2)
    print(f'[monitor] done; {shots} shots', flush=True)


if __name__ == '__main__':
    main()
