package dcaiv.toolkit;

import com.sun.jna.Library;
import com.sun.jna.Native;
import com.sun.jna.Pointer;

/** Minimal Win32 bindings via the game's bundled JNA. Loads best-effort; failures land in ERROR. */
final class ImeNative {
    interface User32Lib extends Library {
        Pointer FindWindowW(String lpClassName, String lpWindowName);
        int GetWindowThreadProcessId(Pointer hWnd, int[] lpdwProcessId);
        boolean IsWindow(Pointer hWnd);
    }
    interface Kernel32Lib extends Library {
        int GetCurrentProcessId();
    }
    interface Imm32Lib extends Library {
        boolean ImmAssociateContextEx(Pointer hWnd, Pointer hIMC, int dwFlags);
    }

    static final User32Lib USER32;
    static final Kernel32Lib KERNEL32;
    static final Imm32Lib IMM32;
    static final int PID;
    static final String ERROR;

    static {
        User32Lib u = null; Kernel32Lib k = null; Imm32Lib m = null; String err = null; int pid = -1;
        try { u = (User32Lib) Native.loadLibrary("user32", User32Lib.class); }
        catch (Throwable t) { err = "user32:" + t; }
        try { k = (Kernel32Lib) Native.loadLibrary("kernel32", Kernel32Lib.class); if (k != null) pid = k.GetCurrentProcessId(); }
        catch (Throwable t) { err = (err == null ? "" : err + " ") + "kernel32:" + t; }
        try { m = (Imm32Lib) Native.loadLibrary("imm32", Imm32Lib.class); }
        catch (Throwable t) { err = (err == null ? "" : err + " ") + "imm32:" + t; }
        USER32 = u; KERNEL32 = k; IMM32 = m; PID = pid; ERROR = err;
    }

    private ImeNative() {}
}
