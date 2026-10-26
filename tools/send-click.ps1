param([int]$GamePid,[int]$X,[int]$Y)
Add-Type @'
using System; using System.Runtime.InteropServices;
public static class MC {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int c);
  [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h,out R r);
  [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h,ref P p);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint dx,uint dy,uint d,IntPtr e);
  public struct R{public int l,t,r,b;} public struct P{public int x,y;}
}
'@
$p=Get-Process -Id $GamePid -ErrorAction Stop
$h=$p.MainWindowHandle
[MC]::ShowWindow($h,9)|Out-Null; [MC]::SetForegroundWindow($h)|Out-Null
Start-Sleep -Milliseconds 600
$r=New-Object MC+R; [MC]::GetClientRect($h,[ref]$r)|Out-Null
$q=New-Object MC+P; $q.x=0;$q.y=0; [MC]::ClientToScreen($h,[ref]$q)|Out-Null
$sx=$q.x+[int]($X*$r.r/853); $sy=$q.y+[int]($Y*$r.b/480)
[MC]::SetCursorPos($sx,$sy)|Out-Null; Start-Sleep -Milliseconds 120
[MC]::mouse_event(2,0,0,0,[IntPtr]::Zero); Start-Sleep -Milliseconds 60; [MC]::mouse_event(4,0,0,0,[IntPtr]::Zero)
"clicked client($X,$Y) -> screen($sx,$sy) client=$($r.r)x$($r.b)"
