package dcaiv.toolkit;

import me.zed_0xff.zombie_buddy.Patch;

public final class Patches {
    @Patch(className = "org.lwjglx.opengl.Display", methodName = "processMessages", warmUp = true)
    public static class KeyboardTick {
        @Patch.OnEnter public static void enter() { ImeControl.mainThreadTick(); }
    }
    private Patches() {}
}
