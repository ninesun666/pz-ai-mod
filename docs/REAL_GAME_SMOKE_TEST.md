# Real-game smoke test

After building the probe JAR, run:

```powershell
python standalone/runtime/smoke_game.py --timeout 120
```

The script creates a disposable cachedir under `standalone/runtime/build/runs/`, launches B42 with only the project-owned `-javaagent`, waits for `[DCStandalone] bridge installed on ...`, writes `report.json`, and terminates the process within the bound. It does not load a save and does not claim gameplay acceptance.

A concurrent process using `-agentlib:zbNative` or a shared cachedir invalidates the run; stop unrelated test sessions before interpreting the report.
