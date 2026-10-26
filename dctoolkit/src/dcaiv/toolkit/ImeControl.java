package dcaiv.toolkit;
import com.sun.jna.Pointer;

/** Window-owner-thread IME association guard. No global keyboard/layout changes. */
public final class ImeControl {
    private static Pointer hwnd, original;
    private static boolean captured;
    private static volatile boolean forceAttach;
    private static volatile String lastStatus="pending";
    private static String logged="";
    private static long ticks;

    public static void mainThreadTick() {
        try {
            if(ImeNative.ERROR!=null) throw new IllegalStateException(ImeNative.ERROR);
            Pointer window=WindowHandle.findForCurrentProcess();
            if(window==null) return;
            int[] pid=new int[1];
            int owner=ImeNative.USER32.GetWindowThreadProcessId(window,pid);
            int current=ImeNative.KERNEL32.GetCurrentThreadId();
            if(pid[0]!=ImeNative.PID || owner!=current) {
                report("blocked_thread owner="+owner+" current="+current+" pid="+pid[0]); return;
            }
            if(hwnd==null || Pointer.nativeValue(hwnd)!=Pointer.nativeValue(window)) {
                hwnd=window; original=null; captured=false;
            }
            boolean typing=forceAttach || TextEntryState.active();
            Pointer observed=ImeNative.IMM32.ImmGetContext(hwnd);
            if(observed!=null) ImeNative.IMM32.ImmReleaseContext(hwnd,observed);
            if(!captured) { original=observed; captured=true; }
            if(typing) {
                if(original!=null && (observed==null || Pointer.nativeValue(observed)!=Pointer.nativeValue(original)))
                    ImeNative.IMM32.ImmAssociateContext(hwnd,original);
            } else if(observed!=null) {
                ImeNative.IMM32.ImmAssociateContext(hwnd,null);
            }
            Pointer actual=ImeNative.IMM32.ImmGetContext(hwnd);
            if(actual!=null) ImeNative.IMM32.ImmReleaseContext(hwnd,actual);
            boolean ok=typing ? (original==null ? actual==null : actual!=null && Pointer.nativeValue(actual)==Pointer.nativeValue(original)) : actual==null;
            ticks++;
            report((ok?"verified":"FAILED")+" mode="+(typing?"text":"gameplay")+" context="+(actual!=null)+" original="+(original!=null)+" owner="+owner+" current="+current);
        } catch(Throwable t) { report("error:"+t); }
    }
    public static void restore() {
        try {
            if(hwnd!=null && captured && ImeNative.USER32.GetWindowThreadProcessId(hwnd,new int[1])==ImeNative.KERNEL32.GetCurrentThreadId()) {
                ImeNative.IMM32.ImmAssociateContext(hwnd,original);
                report("restored_before_destroy");
            }
        } catch(Throwable t) { report("restore_error:"+t); }
    }
    private static void report(String s) { lastStatus=s; if(!s.equals(logged)){ logged=s; System.out.println("[DCIME] "+s); } }
    public static void setDetached(){ forceAttach=false; }
    public static void setAttached(){ forceAttach=true; }
    public static String status(){return lastStatus+" ticks="+ticks;}
    private ImeControl(){}
}
