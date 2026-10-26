# Automated standalone gate

Run from `ai-mod`:

```powershell
./standalone/runtime/test.ps1 -Build
```

The gate runs all `test_standalone*.py` checks, `git diff --check`, and optionally the real B42 API ECJ build. It currently verifies source boundaries, stable identity persistence, fail-closed runtime probing, and Java compilation/packaging. It explicitly prints that this is **not gameplay acceptance**.

The gate does not launch a game, modify saves, or claim that a character is visible or controllable. Gameplay acceptance remains a separate manual/instrumented stage requiring a disposable profile.
