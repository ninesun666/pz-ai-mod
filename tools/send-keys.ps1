param([int]$GamePid,[string]$Keys='m',[int]$DelayMs=300)
$p=Get-Process -Id $GamePid -ErrorAction Stop
Add-Type @'
using System; using System.Runtime.InteropServices;
public static class W {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int c);
}
'@
[W]::ShowWindow($p.MainWindowHandle,9)|Out-Null; [W]::SetForegroundWindow($p.MainWindowHandle)|Out-Null
Start-Sleep -Milliseconds 700
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.SendKeys]::SendWait($Keys)
"sent: $Keys"
