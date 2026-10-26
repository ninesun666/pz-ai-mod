param([int]$GamePid,[byte[]]$Scans=@(0x01),[int]$GapMs=80)
Add-Type @'
using System; using System.Runtime.InteropServices;
public static class SI2 {
  [StructLayout(LayoutKind.Sequential)] public struct MOUSEINPUT { public int dx,dy; public uint mouseData,dwFlags,time; public IntPtr dwExtraInfo; }
  [StructLayout(LayoutKind.Sequential)] public struct KEYBDINPUT { public ushort wVk,wScan; public uint dwFlags,time; public IntPtr dwExtraInfo; }
  [StructLayout(LayoutKind.Explicit)] public struct KIU { [FieldOffset(0)] public MOUSEINPUT mi; [FieldOffset(0)] public KEYBDINPUT ki; }
  [StructLayout(LayoutKind.Sequential)] public struct INPUT { public uint type; public KIU u; }
  public const uint KEYUP=0x0002, SC=0x0008;
  [DllImport("user32.dll",SetLastError=true)] public static extern uint SendInput(uint n, INPUT[] inputs, int size);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int c);
}
'@
$p=Get-Process -Id $GamePid -ErrorAction Stop
[SI2]::ShowWindow($p.MainWindowHandle,9)|Out-Null; [SI2]::SetForegroundWindow($p.MainWindowHandle)|Out-Null
Start-Sleep -Milliseconds 600
$sz=[Runtime.InteropServices.Marshal]::SizeOf([SI2+INPUT]::new())
$okAll=$true
foreach($sc in $Scans){
  $dn=[SI2+INPUT]::new(); $dn.type=1; $dn.u.ki.wScan=$sc; $dn.u.ki.dwFlags=[SI2]::SC
  $up=[SI2+INPUT]::new(); $up.type=1; $up.u.ki.wScan=$sc; $up.u.ki.dwFlags=([SI2]::SC -bor [SI2]::KEYUP)
  $r1=[SI2]::SendInput(1,@($dn),$sz); Start-Sleep -Milliseconds $GapMs
  $r2=[SI2]::SendInput(1,@($up),$sz)
  if($r1 -ne 1 -or $r2 -ne 1){ $okAll=$false; "FAILED scan=0x{0:X2} down=$r1 up=$r2 size=$sz err=$([Runtime.InteropServices.Marshal]::GetLastWin32Error())" -f $sc }
  Start-Sleep -Milliseconds $GapMs
}
if($okAll){ "sent scans OK (size=$sz): $($Scans -join ',')" }
