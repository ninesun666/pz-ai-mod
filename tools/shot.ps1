param([int]$GamePid,[string]$Out='ai-mod/verify/shot.png')
$p=Get-Process -Id $GamePid -ErrorAction Stop
$h=$p.MainWindowHandle
Add-Type @'
using System; using System.Runtime.InteropServices;
public static class S { [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h,out R r); [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h,ref P p); [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h); [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int c); public struct R{public int l,t,r,b;} public struct P{public int x,y;} }
'@
[S]::ShowWindow($h,9)|Out-Null; [S]::SetForegroundWindow($h)|Out-Null
Start-Sleep -Milliseconds 600
$r=New-Object S+R; [S]::GetClientRect($h,[ref]$r)|Out-Null
$q=New-Object S+P; $q.x=0;$q.y=0; [S]::ClientToScreen($h,[ref]$q)|Out-Null
Add-Type -AssemblyName System.Drawing
$bmp=New-Object System.Drawing.Bitmap($r.r,$r.b)
$g=[System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($q.x,$q.y,0,0,$bmp.Size)
$g.Dispose()
$dir=Split-Path $Out -Parent; if($dir -and -not (Test-Path $dir)){New-Item -ItemType Directory -Force $dir|Out-Null}
$bmp.Save($Out,[System.Drawing.Imaging.ImageFormat]::Png); $bmp.Dispose()
"saved $Out ($($r.r)x$($r.b))"
