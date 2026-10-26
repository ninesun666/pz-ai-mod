package dcaiv.toolkit;

import com.sun.jna.Pointer;

/**
 * IME guard state machine. ALL Win32 calls happen on the main/render thread
 * (the thread that owns the game window) via the GameKeyboard.update patch tick;
 * imm32 association is thread-affine, so no background thread performs apply().
 *
 * Policy: default DETACH (IME never swallows WASD). While any UITextBox2 has
 * focus, ATTACH so text entry / Chinese input works; detach again on unfocus.
 */
public final class ImeControl {
    public static final int MODE_DETACH = 0;
    public static final int MODE_ATTACH = 1;
    private static final String WINDOW_TITLE = "Project Zomboid";

    private static volatile int targetMode = MODE_DETACH;
    private static volatile boolean textEntry = false;
    private static volatile Pointer hwnd = null;
    private static volatile String lastStatus = "init";

    /** Called from the GameKeyboard.update patch advice (main thread, every frame). */
    public static void mainThreadTick() {
        try {
            if (ImeNative.ERROR != null) {
                if (!lastStatus.startsWith("blocked")) lastStatus = "blocked:" + ImeNative.ERROR;
                return;
            }
            if (hwnd == null) {
                Pointer p = ImeNative.USER32.FindWindowW(null, WINDOW_TITLE);
                if (p != null && ImeNative.USER32.IsWindow(p)) {
                    int[] proc = new int[1];
                    ImeNative.USER32.GetWindowThreadProcessId(p, proc);
                    if (proc[0] == ImeNative.PID) {
                        hwnd = p;
                        apply(effective());
                    }
                }
            } else if (!ImeNative.USER32.IsWindow(hwnd)) {
                hwnd = null; // window recreated; rediscover next frame
                lastStatus = "window_lost_rediscovering";
            }
        } catch (Throwable t) {
            lastStatus = "tick:" + t;
        }
    }

    private static int effective() { return textEntry ? MODE_ATTACH : targetMode; }

    /** IACE_DEFAULT = 1 restores the default IME context; 0 with hIMC=NULL disassociates. */
    private static void apply(int mode) {
        if (hwnd == null) { lastStatus = "pending_window"; return; }
        if (ImeNative.IMM32 == null) { lastStatus = "blocked_imm32"; return; }
        boolean ok = false;
        try { ok = ImeNative.IMM32.ImmAssociateContextEx(hwnd, null, mode == MODE_ATTACH ? 1 : 0); }
        catch (Throwable t) { lastStatus = "apply:" + t; return; }
        lastStatus = (ok ? "ok" : "imm_returned_false") + " mode=" + (mode == MODE_ATTACH ? "attach" : "detach")
                + " hwnd=0x" + Pointer.nativeValue(hwnd);
    }

    /** UITextBox2.focus / dcImeTextEntry(true). Runs on main thread. */
    public static void setTextEntry(boolean on) {
        textEntry = on;
        if (hwnd != null) apply(effective());
    }

    public static void setDetached() { targetMode = MODE_DETACH; if (!textEntry && hwnd != null) apply(MODE_DETACH); }
    public static void setAttached() { targetMode = MODE_ATTACH; if (!textEntry && hwnd != null) apply(MODE_ATTACH); }

    public static String status() {
        return lastStatus + " hwnd=" + (hwnd == null ? "pending" : "found") + " textEntry=" + textEntry
                + " target=" + (targetMode == MODE_ATTACH ? "attach" : "detach");
    }

    private ImeControl() {}
}
