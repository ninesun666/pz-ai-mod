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
        if (Boolean.getBoolean("dcai.constructorProbe")) {
            LuaManager.env.rawset("DCStandaloneProbeConstructor", new JavaFunction() {
                @Override public int call(LuaCallFrame frame, int count) {
                    if (Thread.currentThread() != GameWindow.gameThread)
                        throw new IllegalStateException("constructor probe off game thread");
                    CompanionActor actor = new CompanionActor(null);
                    actor.initializePlaceholderVisuals();
                    if (actor.isAttached() || actor.getCurrentSquare() != null)
                        throw new IllegalStateException("constructor registered actor into world");
                    if (actor.getHumanVisual() == null || actor.getItemVisuals() == null)
                        throw new IllegalStateException("constructor missing own visual interface");
                    if (!actor.isPlaceholderVisualReady())
                        throw new IllegalStateException("placeholder visual preconditions missing");
                    System.out.println("[DCStandaloneTest] placeholder visual setup PASS (not rendered)");
                    System.out.println("[DCStandaloneTest] detached constructor PASS on " + Thread.currentThread().getName());
                    return frame.push(true);
                }
            });
        }
        System.out.println("[DCStandalone] bridge installed on " + installThread.getName());
        System.out.println("[DCStandalone] active mods=" + zombie.modding.ActiveMods.getById("default").getMods());
        System.out.println("[DCStandalone] discovered=" + (zombie.gameStates.ChooseGameInfo.getModDetails("DC_AIStandalone") != null));
    }
}
