package dcai.companion;

import se.krka.kahlua.vm.JavaFunction;
import se.krka.kahlua.vm.KahluaTable;
import se.krka.kahlua.vm.LuaCallFrame;
import zombie.GameWindow;
import zombie.Lua.LuaManager;

/** Restricted probe interface. No spawn or arbitrary evaluation is exposed. */
public final class CompanionBridge {
    private static KahluaTable installedEnvironment;
    private static Thread installThread;
    private static long ticks;

    public static void install() {
        if (LuaManager.env == null) throw new IllegalStateException("Lua env missing");
        if (LuaManager.env == installedEnvironment) return;
        installedEnvironment = LuaManager.env;
        installThread = Thread.currentThread();
        ticks = 0;
        LuaManager.env.rawset("DCStandaloneTick", new JavaFunction() {
            @Override public int call(LuaCallFrame frame, int count) {
                if (Thread.currentThread() != GameWindow.gameThread)
                    throw new IllegalStateException("companion tick called off game thread");
                ticks++;
                if (ticks == 1) System.out.println("[DCStandalone] first game-thread tick");
                return frame.push((double) ticks);
            }
        });
        System.out.println("[DCStandalone] bridge installed on " + installThread.getName());
    }
}
