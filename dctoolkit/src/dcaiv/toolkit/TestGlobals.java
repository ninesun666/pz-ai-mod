package dcaiv.toolkit;

import se.krka.kahlua.integration.annotations.LuaMethod;

/** Lua-callable globals (registered by the ZombieBuddy exposer). */
public final class TestGlobals {

    @LuaMethod(name = "dcImeDetach", global = true)
    public static boolean imeDetach() { ImeControl.setDetached(); return true; }

    @LuaMethod(name = "dcImeAttach", global = true)
    public static boolean imeAttach() { ImeControl.setAttached(); return true; }

    @LuaMethod(name = "dcImeStatus", global = true)
    public static String imeStatus() { return ImeControl.status(); }

    /** Graceful test exit: call saveGame() in Lua first; exits after a short grace period. */
    @LuaMethod(name = "dcTestQuit", global = true)
    public static boolean testQuit() {
        Thread t = new Thread(new Runnable() {
            public void run() {
                try { Thread.sleep(800); } catch (InterruptedException e) { /* fall through */ }
                Runtime.getRuntime().exit(0);
            }
        }, "dc-test-quit");
        t.setDaemon(true);
        t.start();
        return true;
    }

    private TestGlobals() {}
}
