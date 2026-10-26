"""Build allowlisted release archives, then run offline regression; never launch game/network."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    steps = [
        [sys.executable, '-B', str(ROOT / 'tools/build_teammate_package.py')],
        [sys.executable, '-B', str(ROOT / 'tools/build_workshop_package.py')],
        [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(ROOT / 'tests'), '-p', 'test_*.py'],
    ]
    for index, command in enumerate(steps, 1):
        print(f'离线验收步骤 {index}/{len(steps)}', flush=True)
        result = subprocess.run(command, cwd=ROOT.parent)
        if result.returncode:
            print(f'验收失败：步骤 {index}；后续步骤未运行。', flush=True)
            return result.returncode
    print('构建与离线回归通过；不代表原生游戏、真实模型或可视验收完成。', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
