# Copy only the test-only driver; never install gameplay mods or alter shared configuration.
param([ValidateSet('driver-profile','test-profile')][string[]]$ProfileName = @('driver-profile'))
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$source = Join-Path $PSScriptRoot 'test-driver/DCTestDriver.lua'
foreach ($name in $ProfileName) {
    $target = Join-Path $root "$name/mods/DC_Toolkit/42/media/lua/client/DCTestDriver.lua"
    if (-not (Test-Path -LiteralPath $target)) { throw "Expected existing test driver: $target" }
    Copy-Item -LiteralPath $source -Destination $target
    Write-Host "Synced test-only driver: $name"
}
