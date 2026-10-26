param(
    [string]$Output = "$PSScriptRoot\runtime\build\standalone-profile"
)
$ErrorActionPreference = 'Stop'
$root = Resolve-Path "$PSScriptRoot\.."
$out = [IO.Path]::GetFullPath($Output)
if (Test-Path $out) { throw "Output already exists; choose a fresh disposable directory: $out" }
New-Item -ItemType Directory -Force "$out\mods\DC_AIStandalone" | Out-Null
Copy-Item "$root\standalone\common" "$out\mods\DC_AIStandalone\common" -Recurse
Copy-Item "$root\standalone\42" "$out\mods\DC_AIStandalone\42" -Recurse
@"
VERSION = 1,

mods
{
    mod = DC_AIStandalone,
}

maps
{
}
"@ | Set-Content "$out\mods\default.txt" -Encoding UTF8
"version=8`nwidth=1280`nheight=720`nfullScreen=false`n" | Set-Content "$out\options.ini" -Encoding UTF8 -NoNewline
"DCStandalone disposable profile v1`n" | Set-Content "$out\.dc-standalone-disposable" -Encoding UTF8 -NoNewline
New-Item -ItemType File "$out\mods\reset-mods-42_00.txt" | Out-Null
Write-Output "Created clean profile: $out"
