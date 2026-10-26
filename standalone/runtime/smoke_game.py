"""Bounded real-game initialization smoke test. Does not enter a save.
Launches only the own agent and writes durable logs plus JSON evidence.
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
    args = parser.parse_args()
    jar = ROOT / 'standalone/runtime/build/DC_AIStandaloneRuntime.jar'
    if not jar.is_file():
        raise SystemExit('Build runtime first')
    run = ROOT / 'standalone/runtime/build/runs' / time.strftime('%Y%m%d-%H%M%S')
    profile = run / 'profile'
    profile.mkdir(parents=True)
    out = run / 'stdout.log'
    err = run / 'stderr.log'
    command = [str(args.game / 'jre64/bin/java.exe'), f'-javaagent:{jar}',
               '-Djava.awt.headless=true', '--enable-native-access=ALL-UNNAMED',
               '--add-exports=java.base/jdk.internal.misc=ALL-UNNAMED', '-Xmx2048m',
               '-Dzomboid.steam=0', '-Djava.library.path=win64/;.',
               '-cp', '.;projectzomboid.jar', 'zombie.gameStates.MainScreenState',
               f'-cachedir={profile}', '-nosteam']
    result = {'command': command, 'scope': 'Lua initialization only; no gameplay acceptance',
              'passed': False, 'profile': str(profile)}
    started = time.monotonic()
    with out.open('wb') as stdout, err.open('wb') as stderr:
        proc = subprocess.Popen(command, cwd=args.game, stdout=stdout, stderr=stderr)
        result['pid'] = proc.pid
        try:
            while time.monotonic() - started < args.timeout:
                text = out.read_text(encoding='utf-8', errors='replace') + err.read_text(encoding='utf-8', errors='replace')
                if '[DCStandalone] bridge installed on ' in text:
                    result['passed'] = True
                    result['reason'] = 'own bridge installed from real LuaManager.init'
                    break
                if proc.poll() is not None:
                    result['reason'] = f'game exited {proc.returncode}'
                    break
                time.sleep(0.5)
            else:
                result['reason'] = 'timeout awaiting bridge installation'
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
    print(json.dumps({'report': str(run / 'report.json'), **result}, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
