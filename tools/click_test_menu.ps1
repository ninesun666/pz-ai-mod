param([int]$GamePid,[double]$X,[double]$Y)
$p=Get-CimInstance Win32_Process -Filter "ProcessId=$GamePid"
if($p.CommandLine -notlike '*default-workspace\ai-mod\test-profile*'){throw 'Not isolated test'}
Add-Type @'
using System; using System.Runtime.InteropServices;
public static class ClickNative { [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow(); [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h,out RECT r); [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h,ref POINT p); [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y); [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint x,uint y,uint d,UIntPtr e); public struct RECT{public int l,t,r,b;} public struct POINT{public int x,y;} }
'@
$h=(Get-Process -Id $GamePid).MainWindowHandle
if($h -eq 0 -or [ClickNative]::GetForegroundWindow() -ne $h){throw 'wrong foreground'}
$r=New-Object ClickNative+RECT
[ClickNative]::GetClientRect($h,[ref]$r)|Out-Null
$q=New-Object ClickNative+POINT
$q.x=[int]($X*$r.r/1280); $q.y=[int]($Y*$r.b/720)
[ClickNative]::ClientToScreen($h,[ref]$q)|Out-Null
[ClickNative]::SetCursorPos($q.x,$q.y)|Out-Null
# Allow the native menu to update mouseOver before mouse-down.
Start-Sleep -Milliseconds 400
if([ClickNative]::GetForegroundWindow() -ne $h){throw 'foreground changed'}
[ClickNative]::mouse_event(2,0,0,0,[UIntPtr]::Zero)
Start-Sleep -Milliseconds 150
[ClickNative]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
