# DC_Toolkit 构建：javac(1.8) 编译 -> jar -> 部署到测试模组
$ErrorActionPreference = 'Stop'
$game = 'D:\SteamLibrary\steamapps\common\ProjectZomboid'
$aimod = Split-Path $PSScriptRoot -Parent
$jdk   = 'C:\Users\gjx\Desktop\workspace\workspace\envronment\jdk-17.0.8\bin'
$build = Join-Path $PSScriptRoot 'build'
$mods  = Join-Path $aimod 'test-profile\mods\DC_Toolkit\42\media\java'
$driverMods = Join-Path $aimod 'driver-profile\mods\DC_Toolkit\42\media\java'

Remove-Item $build -Recurse -Force -ErrorAction SilentlyContinue
New-Item $build -ItemType Directory | Out-Null

$src = Get-ChildItem "$PSScriptRoot\src\dcaiv\toolkit\*.java" | ForEach-Object FullName
& "$jdk\javac.exe" -encoding UTF-8 -source 17 -target 17 `
    -sourcepath "$PSScriptRoot\stubs;$PSScriptRoot\src" `
    -cp "$game\ZombieBuddy.jar" -d $build $src
if ($LASTEXITCODE -ne 0) { throw "javac failed ($LASTEXITCODE)" }

# 只打包 dcaiv/**（桩类绝不进 jar）
& "$jdk\jar.exe" cf "$PSScriptRoot\dctoolkit.jar" -C $build dcaiv
if ($LASTEXITCODE -ne 0) { throw "jar failed ($LASTEXITCODE)" }

New-Item $mods -ItemType Directory -Force | Out-Null
Copy-Item "$PSScriptRoot\dctoolkit.jar" "$mods\dctoolkit.jar" -Force
New-Item $driverMods -ItemType Directory -Force | Out-Null
Copy-Item "$PSScriptRoot\dctoolkit.jar" "$driverMods\dctoolkit.jar" -Force
Write-Host "OK: $((Get-Item "$mods\dctoolkit.jar").Length) bytes -> $mods\dctoolkit.jar"
