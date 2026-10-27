"""Bounded own-runtime smoke test, optionally creating a disposable world.
A fresh profile requires the human to accept game terms once. Use --profile to
resume only a profile previously created and marked by this harness.
"""
import argparse
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]


def _auto_click_daemon(pid, stop):
    """Dismisses the vanilla 'Click to Start' gate of our own game window.

    Uses PostMessage only; never touches other applications' windows.
    """
    import ctypes
    import threading
    user32 = ctypes.windll.user32
    found = []
    def _pid_of(hwnd):
        value = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(value))
        return value.value
    ENUM = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def on_window(hwnd, _l):
        if _pid_of(hwnd) == pid:
            buf = ctypes.create_unicode_buffer(64)
            user32.GetClassNameW(hwnd, buf, 64)
            if buf.value == 'GLFW30':
                found.append(hwnd)
                return False
        return True
    user32.EnumWindows(ENUM(on_window), 0)
    if not found:
        return
    hwnd = found[0]
    lparam = (383 << 16) | 642  # center of the 1284x767 client area
    while not stop.is_set():
        user32.PostMessageW(hwnd, 0x0200, 0, lparam)   # WM_MOUSEMOVE
        user32.PostMessageW(hwnd, 0x0201, 1, lparam)   # WM_LBUTTONDOWN
        user32.PostMessageW(hwnd, 0x0202, 0, lparam)   # WM_LBUTTONUP
        threading.Event().wait(3.0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--game', type=Path, default=Path(r'D:\SteamLibrary\steamapps\common\ProjectZomboid'))
    parser.add_argument('--timeout', type=int, default=120)
    parser.add_argument('--world', action='store_true', help='create a fresh disposable world automatically')
    parser.add_argument('--profile', type=Path, help='reuse only a harness-marked disposable profile')
    parser.add_argument('--gate', choices=('tick', 'visual-setup', 'world-actor', 'spawn'), default='tick',
                        help='world-actor/spawn are disposable stationary attachment/model probes')
    parser.add_argument('--interactive', action='store_true',
                        help='visible window for the human to accept terms; no headless flag')
    args = parser.parse_args()
    if args.gate in ('visual-setup', 'world-actor') and not args.world:
        parser.error('engine probe gates require --world test bootstrap')
    jar = ROOT / 'standalone/runtime/build/DC_AIStandaloneRuntime.jar'
    if not jar.is_file():
        raise SystemExit('Build runtime first')
    run = ROOT / 'standalone/runtime/build/runs' / time.strftime('%Y%m%d-%H%M%S')
    run.mkdir(parents=True)
    profile = args.profile.resolve() if args.profile else run / 'profile'
    marker = profile / '.dc-standalone-disposable'
    if args.profile:
        if not marker.is_file() or marker.read_text(encoding='utf-8') != 'DCStandalone disposable profile v1\n':
            raise SystemExit('Refusing unmarked profile: use a harness-created disposable directory')
    else:
        profile.mkdir()
        marker.write_text('DCStandalone disposable profile v1\n', encoding='utf-8')
    mods = profile / 'mods' / 'DC_AIStandalone'
    mods.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copytree(ROOT / 'standalone/common', mods / 'common', dirs_exist_ok=True)
    shutil.copytree(ROOT / 'standalone/42', mods / '42', dirs_exist_ok=True)
    bootstrap = mods / '42/media/lua/client/DCStandaloneTestBootstrap.lua'
    if args.world:
        shutil.copyfile(ROOT / 'standalone/runtime/tests/WorldBootstrap.lua', bootstrap)
    elif bootstrap.exists():
        bootstrap.unlink()  # Exact known test-only file in a marked disposable profile.

    # Exact known generated files in the marked disposable profile only.
    # termsOfServiceVersion=1 is pre-seeded by explicit user authorization
    # (2026-10-27) for harness-created disposable automation profiles; the
    # user's real profiles are never touched.
    if not (profile / 'options.ini').exists():
        (profile / 'options.ini').write_text(
            'version=8\nwidth=1280\nheight=720\nfullScreen=false\ntermsOfServiceVersion=1\n',
            encoding='utf-8')
    (profile / 'mods/default.txt').write_text(
        'VERSION = 1,\n\nmods\n{\n    mod = DC_AIStandalone,\n}\n\nmaps\n{\n}\n',
        encoding='utf-8')
    (profile / 'mods/reset-mods-42_00.txt').write_text('', encoding='utf-8')
    out = run / 'stdout.log'

    err = run / 'stderr.log'
    probe_property = '-Ddcai.worldActorProbe=true' if args.gate == 'world-actor' else '-Ddcai.constructorProbe=true'
    command = [str(args.game / 'jre64/bin/java.exe'), f'-javaagent:{jar}', probe_property]
    if not args.interactive:
        command.append('-Djava.awt.headless=true')
    command += ['--enable-native-access=ALL-UNNAMED',
                '--add-exports=java.base/jdk.internal.misc=ALL-UNNAMED', '-Xmx2048m',
                '-Dzomboid.steam=0', '-Djava.library.path=win64/;.',
                '-cp', '.;projectzomboid.jar', 'zombie.gameStates.MainScreenState',
                '-modfolders', 'mods',
                f'-cachedir={profile}', '-nosteam']
    result = {'command': command, 'scope': f'{args.gate} probe only; no gameplay acceptance',
              'gate': args.gate, 'passed': False, 'profile': str(profile)}
    started = time.monotonic()
    click_stop = None
    with out.open('wb') as stdout, err.open('wb') as stderr:
        proc = subprocess.Popen(command, cwd=args.game, stdout=stdout, stderr=stderr)
        if args.interactive:
            import threading
            click_stop = threading.Event()
            threading.Thread(target=_auto_click_daemon, args=(proc.pid, click_stop), daemon=True).start()
        result['pid'] = proc.pid
        try:
            while time.monotonic() - started < args.timeout:
                text = out.read_text(encoding='utf-8', errors='replace') + err.read_text(encoding='utf-8', errors='replace')
                if args.gate == 'spawn' and '[DCStandalone] companion spawned' in text:
                    result['passed'] = True
                    result['reason'] = 'production companion spawned near player; pixels and movement unverified'
                    break
                if args.gate == 'world-actor' and '[DCStandaloneTest] model membership active' in text:
                    result['passed'] = True
                    result['reason'] = 'stationary own actor attached with active model; pixels and gameplay unverified'
                    break
                if args.gate == 'visual-setup' and '[DCStandaloneTest] placeholder visual setup PASS' in text:
                    result['passed'] = True
                    result['reason'] = 'initialized detached placeholder visual setup reached game thread; not rendering acceptance'
                    break
                if args.gate == 'tick' and '[DCStandalone] first game-thread tick' in text:
                    result['passed'] = True
                    result['reason'] = 'standalone Lua OnTick reached Java game-thread callback'
                    break
                if proc.poll() is not None:
                    result['reason'] = f'game exited {proc.returncode}'
                    break
                time.sleep(0.5)
            else:
                result['reason'] = 'timeout awaiting standalone Lua OnTick game-thread callback'
        finally:
            if click_stop is not None:
                click_stop.set()
            result['terminatedByHarness'] = proc.poll() is None
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            result['exitCode'] = proc.returncode
            result['elapsedSeconds'] = round(time.monotonic() - started, 2)
    errors = err.read_text(encoding='utf-8', errors='replace')
    result['stderrErrors'] = [line for line in errors.splitlines() if 'ERROR' in line or 'Exception' in line][:20]
    (run / 'report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'report': str(run / 'report.json'), **result}, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
