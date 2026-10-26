#Requires -Version 5.1
<#
  把 DC_AIVoice 装进 Project Zomboid 的 mods 文件夹。
  （桥程序 bridge.py 不用装，放哪都行，直接跑。）

  用法：
    双击 install-ai.cmd
    powershell -File install-ai.ps1 -DryRun     只看装到哪
    powershell -File install-ai.ps1 -Uninstall  卸载
#>

[CmdletBinding()]
param(
    [switch]$Uninstall,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

$modName = 'DC_AIVoice'
$here    = Split-Path -Parent $MyInvocation.MyCommand.Path
$src     = Join-Path $here $modName

function Line([string]$msg, [string]$color = 'Gray') { Write-Host $msg -ForegroundColor $color }

function Get-SteamRoots {
    $roots = New-Object System.Collections.Generic.List[string]
    $vdfCandidates = @(
        (Join-Path ${env:ProgramFiles(x86)} 'Steam\steamapps\libraryfolders.vdf'),
        (Join-Path $env:ProgramFiles 'Steam\steamapps\libraryfolders.vdf')
    )
    foreach ($vdf in $vdfCandidates) {
        if (-not (Test-Path -LiteralPath $vdf)) { continue }
        try {
            foreach ($m in [regex]::Matches((Get-Content -LiteralPath $vdf -Raw), '"path"\s+"([^"]+)"')) {
                $roots.Add($m.Groups[1].Value -replace '\\\\', '\')
            }
        } catch { }
    }
    foreach ($guess in @('C:\Program Files (x86)\Steam', 'D:\SteamLibrary', 'E:\SteamLibrary', 'F:\SteamLibrary')) {
        $roots.Add($guess)
    }
    return $roots | Select-Object -Unique
}

function Find-GameDir {
    foreach ($root in (Get-SteamRoots)) {
        $candidate = Join-Path $root 'steamapps\common\ProjectZomboid'
        if (Test-Path -LiteralPath (Join-Path $candidate 'ProjectZomboid64.exe')) { return $candidate }
    }
    return $null
}

Line '=== 找 Project Zomboid 安装目录 ===' 'Cyan'
$gameDir = Find-GameDir
if (-not $gameDir) {
    Line '没找到游戏目录，请手动复制：' 'Red'
    Line '  ai-mod\DC_AIVoice  ->  <Steam>\steamapps\common\ProjectZomboid\mods\DC_AIVoice' 'Yellow'
    exit 1
}
Line "  找到: $gameDir" 'Green'

$modsDir = Join-Path $env:USERPROFILE 'Zomboid\mods'
$dest    = Join-Path $modsDir $modName

if ($Uninstall) {
    if (Test-Path -LiteralPath $dest) {
        if ($DryRun) { Line "  (DryRun) 会删除: $dest" }
        else { Remove-Item -LiteralPath $dest -Recurse -Force; Line "  已删除: $dest" 'Green' }
    } else { Line '  没装过。' 'Yellow' }
    $slotFiles = Get-ChildItem -Path (Join-Path $gameDir 'media\sound') -Filter 'dcav_*.wav' -ErrorAction SilentlyContinue
    if ($slotFiles) {
        if ($DryRun) { Line "  (DryRun) 会删除 $($slotFiles.Count) 个语音槽位" }
        else { $slotFiles | Remove-Item -Force; Line "  已删除 $($slotFiles.Count) 个语音槽位" 'Green' }
    }
    exit 0
}

if (-not (Test-Path -LiteralPath $src)) { Line "找不到源目录: $src" 'Red'; exit 1 }

if ($DryRun) {
    Line "  (DryRun) 会复制到: $dest"
    Line "  (DryRun) 会在 $gameDir\media\sound 生成 300 个 dcav_XXXX.wav 语音槽位"
    exit 0
}

if (-not (Test-Path -LiteralPath $modsDir)) { New-Item -ItemType Directory -Path $modsDir -Force | Out-Null }
if (Test-Path -LiteralPath $dest) { Remove-Item -LiteralPath $dest -Recurse -Force }
Copy-Item -LiteralPath $src -Destination $dest -Recurse -Force
Line "  模组已装到: $dest" 'Green'

# ---- 生成语音槽位（游戏启动时索引；运行期 bridge 覆盖内容再播放）----
$slotDir = Join-Path $gameDir 'media\sound'
$slotCount = 300
$created = 0
if (Test-Path -LiteralPath $slotDir) {
    for ($i = 0; $i -lt $slotCount; $i++) {
        $slotPath = Join-Path $slotDir ('dcav_{0:D4}.wav' -f $i)
        if (Test-Path -LiteralPath $slotPath) { continue }
        $ms = New-Object System.IO.MemoryStream
        $bw = New-Object System.IO.BinaryWriter($ms)
        $sampleRate = 44100
        $dataSize = 16
        $bw.Write([System.Text.Encoding]::ASCII.GetBytes('RIFF'))
        $bw.Write([int](36 + $dataSize))
        $bw.Write([System.Text.Encoding]::ASCII.GetBytes('WAVE'))
        $bw.Write([System.Text.Encoding]::ASCII.GetBytes('fmt '))
        $bw.Write([int]16)
        $bw.Write([int16]1)
        $bw.Write([int16]1)
        $bw.Write([int]$sampleRate)
        $bw.Write([int]($sampleRate * 2))
        $bw.Write([int16]2)
        $bw.Write([int16]16)
        $bw.Write([System.Text.Encoding]::ASCII.GetBytes('data'))
        $bw.Write([int]$dataSize)
        $bw.Write((New-Object byte[] $dataSize))
        $bw.Flush()
        [System.IO.File]::WriteAllBytes($slotPath, $ms.ToArray())
        $bw.Dispose()
        $ms.Dispose()
        $created++
    }
    Line "  语音槽位: 新建 $created 个（共 $slotCount 个）" 'Green'
} else {
    Line "  找不到 $slotDir，跳过槽位生成" 'Yellow'
}

Line ''
Line '=== 接着 ===' 'Cyan'
Line '  1. 游戏主菜单 →「模组」→ 勾选「无线电里的阿D·AI」' 'White'
Line '  2. 先跑 bridge（不需要 key 也能测）：双击 ai-mod\bridge\test-bridge-offline.cmd' 'White'
Line '  3. 想接真模型：把 config.example.json 复制成 config.json，填 api_key，双击 start-bridge.cmd' 'White'
