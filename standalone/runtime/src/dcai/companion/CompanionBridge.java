package dcai.companion;

import se.krka.kahlua.j2se.KahluaTableImpl;
import se.krka.kahlua.vm.JavaFunction;
import se.krka.kahlua.vm.KahluaTable;
import se.krka.kahlua.vm.LuaCallFrame;
import zombie.GameWindow;
import zombie.Lua.LuaManager;

/** Restricted game bridge. Six fixed functions, no dynamic evaluation surface. */
public final class CompanionBridge {
    private static KahluaTable installedEnvironment;
    private static Thread installThread;
    private static long ticks;
    private static final CompanionController controller = new CompanionController();

    public static void install() {
        if (LuaManager.env == null) throw new IllegalStateException("Lua env missing");
        if (LuaManager.env == installedEnvironment) return;
        installedEnvironment = LuaManager.env;
        installThread = Thread.currentThread();
        ticks = 0;
        // A new Lua environment means a new world/session: drop the previous world's
        // actor reference so nothing stale survives a reload in the same JVM.
        controller.close();
        LuaManager.env.rawset("DCStandaloneTick", new JavaFunction() {
            @Override public int call(LuaCallFrame frame, int count) {
                if (Thread.currentThread() != GameWindow.gameThread)
                    throw new IllegalStateException("companion tick called off game thread");
                ticks++;
                if (ticks == 1) System.out.println("[DCStandalone] first game-thread tick");
                controller.tick();
                FollowProbe.tick(controller);
                return frame.push((double) ticks);
            }
        });
        LuaManager.env.rawset("DCStandaloneSuspend", new JavaFunction() {
            @Override public int call(LuaCallFrame frame, int count) {
                if (Thread.currentThread() != GameWindow.gameThread)
                    throw new IllegalStateException("companion suspend off game thread");
                controller.suspend();
                return 0;
            }
        });
        LuaManager.env.rawset("DCStandaloneClose", new JavaFunction() {
            @Override public int call(LuaCallFrame frame, int count) {
                if (Thread.currentThread() != GameWindow.gameThread)
                    throw new IllegalStateException("companion close off game thread");
                controller.close();
                return 0;
            }
        });
        LuaManager.env.rawset("DCStandaloneDeclareIdentity", new JavaFunction() {
            @Override public int call(LuaCallFrame frame, int count) {
                if (Thread.currentThread() != GameWindow.gameThread)
                    throw new IllegalStateException("identity declare off game thread");
                if (count < 1 || !(frame.get(0) instanceof String))
                    throw new IllegalStateException("identity uuid missing");
                String uuid = (String) frame.get(0);
                String assetId = count >= 2 && frame.get(1) instanceof String ? (String) frame.get(1) : "";
                return frame.push(controller.declareIdentity(uuid, assetId), Boolean.TRUE);
            }
        });
        LuaManager.env.rawset("DCStandaloneCommand", new JavaFunction() {
            @Override public int call(LuaCallFrame frame, int count) {
                if (Thread.currentThread() != GameWindow.gameThread)
                    throw new IllegalStateException("companion command off game thread");
                if (count < 1 || !(frame.get(0) instanceof String))
                    throw new IllegalStateException("intent missing");
                return frame.push(controller.command((String) frame.get(0)), Boolean.TRUE);
            }
        });
        LuaManager.env.rawset("DCStandaloneStatus", new JavaFunction() {
            @Override public int call(LuaCallFrame frame, int count) {
                if (Thread.currentThread() != GameWindow.gameThread)
                    throw new IllegalStateException("companion status off game thread");
                KahluaTable status = new KahluaTableImpl(null);
                status.rawset("present", controller.canCommand());
                status.rawset("intent", controller.intent());
                status.rawset("spawnFailed", controller.isSpawnFailed());
                status.rawset("error", controller.lastError());
                return frame.push(status);
            }
        });
        System.out.println("[DCStandalone] bridge installed on " + installThread.getName());
        System.out.println("[DCStandalone] active mods=" + zombie.modding.ActiveMods.getById("default").getMods());
        System.out.println("[DCStandalone] discovered=" + (zombie.gameStates.ChooseGameInfo.getModDetails("DC_AIStandalone") != null));
    }
}
