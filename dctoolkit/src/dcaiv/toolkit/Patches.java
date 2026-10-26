package dcaiv.toolkit;

import me.zed_0xff.zombie_buddy.Patch;

/** All patch advice bodies run on the main/render thread. */
public final class Patches {

    /** Main-thread heartbeat: discovers the game window and enforces the IME policy. */
    @Patch(className = "zombie.input.GameKeyboard", methodName = "update", warmUp = true)
    public static class KeyboardTick {
        @Patch.OnEnter
        public static void enter() { ImeControl.mainThreadTick(); }
    }

    /** Any Java text box gaining focus -> reattach IME (Chinese typing works). */
    @Patch(className = "zombie.ui.UITextBox2", methodName = "focus", warmUp = false)
    public static class TextBoxFocus {
        @Patch.OnEnter
        public static void enter() { ImeControl.setTextEntry(true); }
    }

    /** ... and losing focus -> detach again (WASD can never be swallowed). */
    @Patch(className = "zombie.ui.UITextBox2", methodName = "unfocus", warmUp = false)
    public static class TextBoxUnfocus {
        @Patch.OnEnter
        public static void enter() { ImeControl.setTextEntry(false); }
    }

    private Patches() {}
}
