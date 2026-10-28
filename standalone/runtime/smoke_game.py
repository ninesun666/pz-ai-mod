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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--game', type=Path, default=Path(r'D:\SteamLibrary\steamapps\common\ProjectZomboid'))
    parser.add_argument('--timeout', type=int, default=120)
    parser.add_argument('--world', action='store_true', help='create a fresh disposable world automatically')
    parser.add_argument('--profile', type=Path, help='reuse only a harness-marked disposable profile')
    parser.add_argument('--gate', choices=('tick', 'visual-setup', 'world-actor', 'spawn', 'follow'), default='tick',
                        help='world-actor/spawn are disposable stationary attachment/model probes; '
                             'follow is the live follow-locomotion acceptance (player teleport stimulus)')
    parser.add_argument('--interactive', action='store_true',
                        help='visible window for the human to accept terms; no headless flag')
    parser.add_argument('--dwell', type=int, default=0,
                        help='seconds to keep the game alive after the gate passes (for visual evidence)')
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
    # Chinese translation/font mod by explicit user request: CJK glyphs for our
    # context-menu labels. Loads after our mod (排序置底).
    cn_mod_src = ROOT / 'test-profile/mods/B42Trans_CN_As1'
    if cn_mod_src.is_dir():
        shutil.copytree(cn_mod_src, profile / 'mods/B42Trans_CN_As1', dirs_exist_ok=True)
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
            'version=8\nwidth=1280\nheight=720\nfullScreen=false\ntermsOfServiceVersion=1\nlanguage=CN\n',
            encoding='utf-8')
    (profile / 'mods/default.txt').write_text(
        'VERSION = 1,\n\nmods\n{\n    mod = DC_AIStandalone,\n    mod = B42Trans_CN,\n}\n\nmaps\n{\n}\n',
        encoding='utf-8')
    (profile / 'mods/reset-mods-42_00.txt').write_text('', encoding='utf-8')
    out = run / 'stdout.log'

    err = run / 'stderr.log'
    # Read-only evidence monitor: desktop screenshots every 30s after world
    # load, transition log, stops at report.json. Bounded by duration.
    monitor = None
    if args.world:
        import sys as _sys
        monitor = subprocess.Popen(
            [_sys.executable, str(ROOT / 'standalone/runtime/monitor_run.py'),
             str(run), str(args.timeout + 90)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    probe_property = '-Ddcai.worldActorProbe=true' if args.gate == 'world-actor' else '-Ddcai.constructorProbe=true'
    if args.gate == 'follow':
        probe_property = '-Ddcai.followProbe=true'
    command = [str(args.game / 'jre64/bin/java.exe'), f'-javaagent:{jar}', probe_property]
    if args.world:
        # Unattended world entry: in-game synthetic LMB dismisses the post-load
        # "Click to Start" phase via Mouse.buttonDownStates (AutoInputDriver).
        # NOTE: Boolean.getBoolean needs the literal "true"; "1" is false.
        command.append('-Ddcai.autoGate=true')
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
    with out.open('wb') as stdout, err.open('wb') as stderr:
        proc = subprocess.Popen(command, cwd=args.game, stdout=stdout, stderr=stderr)
        result['pid'] = proc.pid
        try:
            while time.monotonic() - started < args.timeout:
                text = out.read_text(encoding='utf-8', errors='replace') + err.read_text(encoding='utf-8', errors='replace')
                if args.gate == 'spawn' and '[DCStandalone] companion spawned' in text:
                    result['passed'] = True
                    result['reason'] = 'production companion spawned near player; pixels and movement unverified'
                    if args.dwell > 0:
                        result['dwellSeconds'] = args.dwell
                        deadline = time.monotonic() + args.dwell
                        while time.monotonic() < deadline and proc.poll() is None:
                            time.sleep(0.5)
                    break
                if args.gate == 'follow' and '[DCStandalone] follow-probe PASS' in text:
                    result['passed'] = True
                    result['reason'] = 'companion closed teleport-opened distance by its own pathing twice; input/UI acceptance not covered'
                    if args.dwell > 0:
                        result['dwellSeconds'] = args.dwell
                        deadline = time.monotonic() + args.dwell
                        while time.monotonic() < deadline and proc.poll() is None:
                            time.sleep(0.5)
                    break
                if args.gate == 'follow' and '[DCStandalone] follow-probe FAIL' in text:
                    result['reason'] = 'follow probe reported failure in log'
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
                if result['passed'] and args.dwell > 0:
                    result['dwellSeconds'] = args.dwell
                    deadline = time.monotonic() + args.dwell
                    while time.monotonic() < deadline and proc.poll() is None:
                        time.sleep(0.5)
                    break
                time.sleep(0.5)
            else:
                text = out.read_text(encoding='utf-8', errors='replace') + err.read_text(encoding='utf-8', errors='replace')
                if args.gate == 'follow' and '[DCStandalone] follow-probe round=' in text:
                    result['reason'] = 'timeout awaiting follow completion after game-thread probe started'
                elif '[DCStandalone] first game-thread tick' in text:
                    result['reason'] = f'timeout awaiting {args.gate} gate after game-thread callback'
                elif '[DCStandaloneTest] world started' in text:
                    result['reason'] = 'timeout after world loaded; gameplay callback not observed (check Click to Start)'
                else:
                    result['reason'] = 'timeout awaiting standalone Lua OnTick game-thread callback'
        finally:
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
    if monitor is not None and monitor.poll() is None:
        monitor.terminate()  # report.json exists; monitor would stop on its own too
    print(json.dumps({'report': str(run / 'report.json'), **result}, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
