package dcaiv.toolkit;
import com.sun.jna.Library;
import com.sun.jna.Native;
import com.sun.jna.Pointer;

/** Win64 bindings; never locate a window by title. */
public final class ImeNative {
    public interface User32Lib extends Library {
        int GetWindowThreadProcessId(Pointer hwnd, int[] pid);
        boolean IsWindow(Pointer hwnd);
    }
    public interface Kernel32Lib extends Library {
        int GetCurrentProcessId();
        int GetCurrentThreadId();
    }
    public interface Imm32Lib extends Library {
        Pointer ImmGetContext(Pointer hwnd);
        boolean ImmReleaseContext(Pointer hwnd, Pointer context);
        Pointer ImmAssociateContext(Pointer hwnd, Pointer context);
    }
    static final User32Lib USER32;
    static final Kernel32Lib KERNEL32;
    static final Imm32Lib IMM32;
    static final int PID;
    static final String ERROR;
    static {
        User32Lib u=null; Kernel32Lib k=null; Imm32Lib m=null; int pid=0; String err=null;
        try {
            u=(User32Lib)Native.loadLibrary("user32",User32Lib.class);
            k=(Kernel32Lib)Native.loadLibrary("kernel32",Kernel32Lib.class);
            m=(Imm32Lib)Native.loadLibrary("imm32",Imm32Lib.class);
            pid=k.GetCurrentProcessId();
        } catch(Throwable t) { err=t.toString(); }
        USER32=u; KERNEL32=k; IMM32=m; PID=pid; ERROR=err;
    }
    private ImeNative() {}
}
