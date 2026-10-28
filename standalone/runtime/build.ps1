param(
    [string]$GameDir = "D:\SteamLibrary\steamapps\common\ProjectZomboid",
    [string]$Ecj = "$PSScriptRoot\..\..\.local-tools\ecj-3.43.0.jar",
    [string]$Asm = "$PSScriptRoot\..\..\.local-tools\asm-9.9.jar"
)
$ErrorActionPreference = "Stop"
$root = Resolve-Path "$PSScriptRoot\..\.."
$src = Join-Path $root "standalone\runtime\src"
$out = Join-Path $root "standalone\runtime\build\classes"
$jar = Join-Path $root "standalone\runtime\build\DC_AIStandaloneRuntime.jar"
if (!(Test-Path $GameDir)) { throw "GameDir not found: $GameDir" }
if (!(Test-Path $Ecj)) { throw "ECJ not found: $Ecj" }
if (!(Test-Path $Asm)) { throw "ASM not found: $Asm" }
New-Item -ItemType Directory -Force $out | Out-Null
$gameJars = (Get-ChildItem $GameDir -Filter "*.jar" | ForEach-Object FullName) -join ";"
$cp = "$gameJars;$Asm"
$java = Join-Path $GameDir "jre64\bin\java.exe"
$files = Get-ChildItem (Join-Path $src "dcai\companion") -Filter "*.java" -Recurse | ForEach-Object FullName
& $java -jar $Ecj -17 -proc:none -encoding UTF-8 -classpath $cp -d $out $files
if ($LASTEXITCODE -ne 0) { throw "ECJ failed: $LASTEXITCODE" }
$testSrc = Join-Path $root "standalone\runtime\tests"
$testFiles = Get-ChildItem $testSrc -Filter "*.java" -Recurse | ForEach-Object FullName
if ($testFiles) {
    & $java -jar $Ecj -17 -proc:none -encoding UTF-8 -classpath "$cp;$out" -d $out $testFiles
    if ($LASTEXITCODE -ne 0) { throw "ECJ tests failed: $LASTEXITCODE" }
}
$gameJar = Join-Path $GameDir "projectzomboid.jar"
& $java -cp "$out;$cp" dcai.companion.TransformProbe $gameJar
if ($LASTEXITCODE -ne 0) { throw "Transform probe failed: $LASTEXITCODE" }
& $java -cp "$out;$cp" dcai.companion.BehaviorProbe
if ($LASTEXITCODE -ne 0) { throw "Behavior probe failed: $LASTEXITCODE" }
& $java -cp "$out;$cp" dcai.companion.BehaviorTreeProbe
if ($LASTEXITCODE -ne 0) { throw "Behavior tree probe failed: $LASTEXITCODE" }
& $java -cp "$out;$cp" dcai.companion.ModProfileProbe "$PSScriptRoot\build\parser-profile.txt"
if ($LASTEXITCODE -ne 0) { throw "Profile parser probe failed: $LASTEXITCODE" }
& $java -cp "$out;$cp" dcai.companion.ActorConstructionProbe
if ($LASTEXITCODE -ne 0) { throw "Actor construction probe failed: $LASTEXITCODE" }
& $java -cp "$out;$cp" dcai.companion.CompanionLifecycleProbe
if ($LASTEXITCODE -ne 0) { throw "Lifecycle probe failed: $LASTEXITCODE" }
$manifest = Join-Path $root "standalone\runtime\build\MANIFEST.MF"
@"
Manifest-Version: 1.0
Premain-Class: dcai.companion.CompanionAgent
Can-Redefine-Classes: false
Can-Retransform-Classes: false

"@ | Set-Content -Encoding ascii $manifest
$env:DC_PROBE_CLASSES = $out
$env:DC_PROBE_JAR = $jar
$env:DC_PROBE_MANIFEST = $manifest
python -c "import os, pathlib, zipfile; root=pathlib.Path(os.environ['DC_PROBE_CLASSES']); asm=pathlib.Path(r'.local-tools/asm-9.9.jar'); z=zipfile.ZipFile(os.environ['DC_PROBE_JAR'],'w',zipfile.ZIP_DEFLATED); z.write(os.environ['DC_PROBE_MANIFEST'],'META-INF/MANIFEST.MF'); [z.write(p,p.relative_to(root).as_posix()) for p in root.rglob('*.class')]; az=zipfile.ZipFile(asm); [z.writestr(i,az.read(i)) for i in az.namelist() if i.startswith('org/objectweb/asm/') and i.endswith('.class')]; z.writestr('THIRD-PARTY-NOTICES/ASM-LICENSE.txt', pathlib.Path('.local-tools/ASM-LICENSE.txt').read_bytes()); az.close(); z.close()"
if ($LASTEXITCODE -ne 0) { throw "packaging failed: $LASTEXITCODE" }
Write-Output "Built probe jar: $jar"
