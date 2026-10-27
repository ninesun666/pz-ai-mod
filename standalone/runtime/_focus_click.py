"""Brings our own game window to front, dismisses Click-to-Start, unpauses.
Usage: python _focus_click.py <pid>
"""
import ctypes
import sys
import time

pid = int(sys.argv[1])
user32 = ctypes.windll.user32
found = []


def pid_of(h):
    v = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(h, ctypes.byref(v))
    return v.value


ENUM = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)


def on_w(h, _):
    if pid_of(h) == pid:
        b = ctypes.create_unicode_buffer(64)
        user32.GetClassNameW(h, b, 64)
        if b.value == 'GLFW30':
            found.append(h)
            return False
    return True


user32.EnumWindows(ENUM(on_w), 0)
if not found:
    print('no GLFW30 window for pid', pid)
    raise SystemExit(1)
hwnd = found[0]

# Focus: attach to the foreground thread's input queue so Windows allows the switch.
user32.SetForegroundWindow.argtypes = [ctypes.c_void_p]
user32.SwitchToThisWindow.argtypes = [ctypes.c_void_p, ctypes.c_bool]
fg = user32.GetForegroundWindow()
fg_thread = user32.GetWindowThreadProcessId(fg, None)
our_thread = ctypes.windll.kernel32.GetCurrentThreadId()
user32.AttachThreadInput(our_thread, fg_thread, True)
user32.SwitchToThisWindow(hwnd, True)
time.sleep(0.4)
user32.AttachThreadInput(our_thread, fg_thread, False)
print('foreground now pid:', pid_of(user32.GetForegroundWindow()))

# Real click at window center to dismiss Click-to-Start / unpause.
r = ctypes.wintypes.RECT() if hasattr(ctypes, 'wintypes') else None
import ctypes.wintypes as wt
rect = wt.RECT()
user32.GetWindowRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(wt.RECT)]
user32.GetWindowRect(hwnd, ctypes.byref(rect))
cx = (rect.left + rect.right) // 2
cy = (rect.top + rect.bottom) // 2
print('click at', cx, cy)
user32.SetCursorPos(cx, cy)
time.sleep(0.15)
user32.mouse_event(2, 0, 0, 0, 0)
time.sleep(0.08)
user32.mouse_event(4, 0, 0, 0, 0)
time.sleep(1.0)
user32.SetCursorPos(cx, cy)
user32.mouse_event(2, 0, 0, 0, 0)
time.sleep(0.08)
user32.mouse_event(4, 0, 0, 0, 0)
print('clicked twice')
