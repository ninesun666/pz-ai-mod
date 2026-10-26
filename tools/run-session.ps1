# run-session.ps1 — isolated test orchestrator. Never saves or stops the game automatically.
# CLI: pwsh -File ai-mod\tools\run-session.ps1 -StepsJson '["cmd=ping","cmd=snapshot"]'
# Or: -StepsFile <UTF-8 JSON array file>. In-process PowerShell may use -Steps @(...).
param(
    [string[]]$Steps,
    [string]$StepsJson,
    [string]$StepsFile,
    [switch]$ValidateOnly,
    [int]$ReadyTimeoutSec = 420,
    [int]$StepTimeoutSec = 30,
    [switch]$NoQuit, # Compatibility only: automatic shutdown is always disabled.
    [ValidatePattern('^[a-zA-Z0-9_-]+$')]
    [string]$ProfileName = 'driver-profile'
)
$ErrorActionPreference = 'Stop'
$inputs = @('Steps', 'StepsJson', 'StepsFile' | Where-Object { $PSBoundParameters.ContainsKey($_) })
if ($inputs.Count -gt 1) { throw 'Specify only one of -Steps, -StepsJson, -StepsFile.' }
if ($PSBoundParameters.ContainsKey('StepsFile')) { $StepsJson = Get-Content -LiteralPath $StepsFile -Raw -Encoding UTF8 }
if ($PSBoundParameters.ContainsKey('StepsJson') -or $PSBoundParameters.ContainsKey('StepsFile')) {
    $decoded = ConvertFrom-Json -InputObject $StepsJson -NoEnumerate
    if ($decoded -isnot [array]) { throw 'Steps JSON must be an array of command strings.' }
    foreach ($value in $decoded) { if ($value -isnot [string]) { throw 'Every step must be a string.' } }
    $Steps = [string[]]$decoded
} elseif (-not $PSBoundParameters.ContainsKey('Steps')) { $Steps = @('cmd=ping', 'cmd=snapshot') }
if (-not $Steps -or $Steps.Count -eq 0) { throw 'At least one step is required.' }
foreach ($step in $Steps) {
    # Explicit scalar fields only; reject the old comma-joined CLI argument, never guess/split it.
    if ($step -notmatch '^cmd=(ping|snapshot|teleport|speed|ime|save)(;[a-z_]+=[a-zA-Z0-9_.+-]+)*$') {
        throw "Invalid step '$step'. Use -StepsJson or -StepsFile for pwsh -File; quit is disabled."
    }
    $keys = @{}
    foreach ($pair in ($step -split ';')) {
        $key = ($pair -split '=', 2)[0]
        if ($keys.ContainsKey($key) -or $key -in @('session','seq')) { throw "Duplicate/reserved field: $key" }
        $keys[$key] = $true
    }
    if ($step.Length -gt 450) { throw 'Step exceeds protocol size limit.' }
}
if ($ReadyTimeoutSec -lt 1 -or $StepTimeoutSec -lt 1) { throw 'Timeouts must be positive.' }
if ($ValidateOnly) { ConvertTo-Json -InputObject @($Steps) -Compress; exit 0 }
$aimod = Split-Path $PSScriptRoot -Parent
$game = 'D:\SteamLibrary\steamapps\common\ProjectZomboid'
$profile = Join-Path $aimod $ProfileName
$luaDir = Join-Path $profile 'Lua'
$logs = Join-Path $aimod 'logs'
New-Item $logs -ItemType Directory -Force | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$logOut = Join-Path $logs "run-session-$stamp.out.log"
$logErr = Join-Path $logs "run-session-$stamp.err.log"
$report = Join-Path $logs "run-session-$stamp.report.txt"
$session = ([guid]::NewGuid().ToString('N'))

# 0) 同配置档拒跑（双实例写同一协议文件）；其他配置档实例仅警告
$others = Get-CimInstance Win32_Process -Filter "Name='java.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'MainScreenState' }
if ($others | Where-Object { $_.CommandLine -match [regex]::Escape($profile) }) {
    Write-Host "ABORT: 本配置档 ($ProfileName) 已有实例在跑。"; exit 2
}
if ($others) { Write-Host "[warn] 其他配置档有游戏实例在跑 (PID $($others.ProcessId -join ','))，继续。" }

# 1) 清协议文件 + 清单健康检查
'in', 'out', 'ready' | ForEach-Object { Remove-Item (Join-Path $luaDir "dctest_$_.txt") -Force -ErrorAction SilentlyContinue }
New-Item $luaDir -ItemType Directory -Force | Out-Null
$dflt = Join-Path $profile 'mods\default.txt'
if ((Test-Path $dflt) -and ((Get-Item $dflt).Length -lt 50)) {
    Write-Host "WARN: $dflt 只有 $((Get-Item $dflt).Length) 字节（疑似被崩溃回写清空），请恢复后再跑。"
}

# 2) 启动（权威参数来自 ProjectZomboid64.json + 等号 -cachedir + ZB 代理配置）
$java = Join-Path $game 'jre64\bin\java.exe'
$agentArg = "-agentlib:zbNative=config_dir=$profile\zb-config,policy=deny-new"
$jvm = @($agentArg, '-Djava.awt.headless=true', '--enable-native-access=ALL-UNNAMED',
    '--add-exports=java.base/jdk.internal.misc=ALL-UNNAMED', '-Xmx3072m', '-Dzomboid.steam=1',
    '-Dzomboid.znetlog=1', '-Djava.library.path=win64/;.', '-XX:-CreateCoredumpOnCrash',
    '-XX:-OmitStackTraceInFastThrow', '-XX:+UseZGC', '-cp', '.;projectzomboid.jar',
    'zombie.gameStates.MainScreenState', "-cachedir=$profile")
$proc = Start-Process -FilePath $java -ArgumentList $jvm -WorkingDirectory $game `
    -RedirectStandardOutput $logOut -RedirectStandardError $logErr -PassThru
Write-Host "[launch] PID=$($proc.Id) session=$session log=$logOut"

# 3) 等 ready（文件出现 或 日志 DRIVER_READY）
$readyFile = Join-Path $luaDir 'dctest_ready.txt'
$deadline = (Get-Date).AddSeconds($ReadyTimeoutSec)
$ready = $false
while ((Get-Date) -lt $deadline) {
    if ($proc.HasExited) { break }
    if (Test-Path -LiteralPath $readyFile) {
        $readyText = Get-Content -LiteralPath $readyFile -Raw -ErrorAction SilentlyContinue
        if ($readyText -match '^protocol=2;') { $ready = $true; break }
    }
    Start-Sleep -Milliseconds 800
}
$results = New-Object System.Collections.Generic.List[string]
$fail = 0
function Add-Result($line) { $script:results.Add($line); Write-Host $line }
if (-not $ready) { Add-Result "READY: FAIL (timeout/exited=$($proc.HasExited))"; $fail++ }
else { Add-Result "READY: PASS session=$session" }

# 4) 逐条执行；每个请求带 session+seq，拒绝旧会话的响应
$seq = 0
if ($ready -and -not $proc.HasExited) {
    foreach ($step in $steps) {
        $seq++
        $inLine = "session=$session;seq=$seq;$step"
        Set-Content -Path (Join-Path $luaDir 'dctest_in.txt') -Value $inLine -NoNewline -Encoding Ascii
        $outFile = Join-Path $luaDir 'dctest_out.txt'
        $dl = (Get-Date).AddSeconds($StepTimeoutSec)
        $got = $null
        while ((Get-Date) -lt $dl) {
            if ($proc.HasExited) { break }
            if (Test-Path $outFile) {
                $txt = Get-Content $outFile -Raw -ErrorAction SilentlyContinue
                if ($txt -and $txt -match "^session=$([regex]::Escape($session));seq=$seq;") { $got = $txt.Trim(); break }
            }
            Start-Sleep -Milliseconds 300
        }
        if ($got) {
            $pass = $got -match '(^|;)ok=1(;|$)'
            if (-not $pass) { $fail++ }
            Add-Result ("STEP {0,2} [{1}] -> {2} {3}" -f $seq, $step, ($(if ($pass) { 'PASS' } else { 'FAIL' })), $got)
        } else { $fail++; Add-Result ("STEP {0,2} [{1}] -> TIMEOUT" -f $seq, $step); break }
    }
}

# 5) No automatic quit, save, Runtime.exit, or forced kill. Leave lifecycle to the operator.
if (-not $proc.HasExited) { Add-Result "SHUTDOWN: NOT_REQUESTED (no automatic quit/kill)" }

# 6) 诊断摘要 + 报告
$diag = @()
foreach ($pat in @('\[DC_Toolkit\]', '\[ZB\].*(patch|Jar|toolkit)', 'ERROR', 'Exception')) {
    $hit = Select-String -Path $logOut, $logErr -Pattern $pat -ErrorAction SilentlyContinue | Select-Object -First 4
    foreach ($h in $hit) { $diag += ($h.Filename + ':' + $h.LineNumber + ' ' + $h.Line.Trim()) }
}
$summary = "SUMMARY: $(if ($fail -eq 0) { 'ALL-PASS' } else { "$fail FAILED" })"
Add-Result $summary
$results + ($diag | Select-Object -First 12) | Set-Content -Path $report -Encoding UTF8
Write-Host "report: $report"
exit $(if ($fail -eq 0) { 0 } else { 1 })
