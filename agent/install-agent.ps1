#Requires -Version 5.1
<#
  把 dcaiv-agent.jar 挂到 Project Zomboid 的 JVM 上（-javaagent）。
  装完必须重启游戏才生效。

  用法：
    双击 install-agent.cmd                安装
    双击 uninstall-agent.cmd              卸载
    powershell -File install-agent.ps1 -DryRun
#>

[CmdletBinding()]
param([switch]$Uninstall, [switch]$DryRun)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$jar = Join-Path $here 'dcaiv-agent.jar'
$argText = '-javaagent:dcaiv-agent.jar'

function Line([string]$msg, [string]$color = 'Gray') { Write-Host $msg -ForegroundColor $color }

function Write-TextShared([string]$path, [string]$content) {
    # 游戏运行时 json 被占用，用共享句柄写
    $bytes = (New-Object System.Text.UTF8Encoding($false)).GetBytes($content)
    $fs = [System.IO.File]::Open($path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::ReadWrite)
    try { $fs.SetLength(0); $fs.Write($bytes, 0, $bytes.Length) } finally { $fs.Close() }
}

function Find-GameDir {
    $roots = New-Object System.Collections.Generic.List[string]
    foreach ($vdf in @(
        (Join-Path ${env:ProgramFiles(x86)} 'Steam\steamapps\libraryfolders.vdf'),
        (Join-Path $env:ProgramFiles 'Steam\steamapps\libraryfolders.vdf'))) {
        if (-not (Test-Path -LiteralPath $vdf)) { continue }
        foreach ($m in [regex]::Matches((Get-Content -LiteralPath $vdf -Raw), '"path"\s+"([^"]+)"')) {
            $roots.Add(($m.Groups[1].Value -replace '\\\\', '\'))
        }
    }
    foreach ($g in @('C:\Program Files (x86)\Steam', 'D:\SteamLibrary', 'E:\SteamLibrary', 'F:\SteamLibrary')) { $roots.Add($g) }
    foreach ($root in ($roots | Select-Object -Unique)) {
        $cand = Join-Path $root 'steamapps\common\ProjectZomboid'
        if (Test-Path -LiteralPath (Join-Path $cand 'ProjectZomboid64.exe')) { return $cand }
    }
    return $null
}

Line '=== 找 Project Zomboid ===' 'Cyan'
$gameDir = Find-GameDir
if (-not $gameDir) { Line '没找到游戏目录。' 'Red'; exit 1 }
Line "  $gameDir" 'Green'

$jsonPath = Join-Path $gameDir 'ProjectZomboid64.json'
$targetJar = Join-Path $gameDir 'dcaiv-agent.jar'

$config = Get-Content -LiteralPath $jsonPath -Raw | ConvertFrom-Json
$topArgs = @($config.vmArgs)

if ($Uninstall) {
    $newArgs = @($topArgs | Where-Object { $_ -ne $argText })
    if ($newArgs.Count -eq $topArgs.Count) {
        Line '  vmArgs 里没有 javaagent 参数' 'Yellow'
    } elseif ($DryRun) {
        Line '  (DryRun) 会删掉 -javaagent 参数'
    } else {
        $config.vmArgs = $newArgs
        Write-TextShared $jsonPath ($config | ConvertTo-Json -Depth 10)
        Line '  已删掉 -javaagent 参数' 'Green'
    }
    if (Test-Path -LiteralPath $targetJar) {
        if ($DryRun) { Line '  (DryRun) 会删除 dcaiv-agent.jar' }
        else { Remove-Item -LiteralPath $targetJar -Force; Line '  已删除 dcaiv-agent.jar' 'Green' }
    }
    exit 0
}

if (-not (Test-Path -LiteralPath $jar)) { Line "找不到 $jar，先双击 build.cmd 编译。" 'Red'; exit 1 }

if ($topArgs -contains $argText) {
    Line '  vmArgs 里已经有 javaagent 参数，跳过' 'Yellow'
} elseif ($DryRun) {
    Line "  (DryRun) 会加 $argText"
} else {
    $config.vmArgs = @($argText) + $topArgs
    Write-TextShared $jsonPath ($config | ConvertTo-Json -Depth 10)
    Line '  已写入 -javaagent（原文件备份为 ProjectZomboid64.json.bak-dcaiv）' 'Green'
}

if ($DryRun) { Line '  (DryRun) 会复制 dcaiv-agent.jar'; exit 0 }

if (-not (Test-Path -LiteralPath (Join-Path $gameDir 'ProjectZomboid64.json.bak-dcaiv'))) {
    Copy-Item -LiteralPath $jsonPath -Destination (Join-Path $gameDir 'ProjectZomboid64.json.bak-dcaiv') -Force
}
Copy-Item -LiteralPath $jar -Destination $targetJar -Force
Line '  已复制 dcaiv-agent.jar' 'Green'

Line ''
Line '重启游戏后看日志：' 'Cyan'
Line '  %USERPROFILE%\Zomboid\dcagent.log' 'White'
Line '  出现 "registered DCAgentPing / DCAgentPlay" 就说明 Lua 那侧通了' 'Gray'
