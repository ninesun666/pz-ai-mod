package dcai.companion;

import zombie.GameWindow;
import zombie.gameStates.GameLoadingState;
import zombie.gameStates.GameState;
import zombie.input.Mouse;

/**
 * Test-only synthetic input for unattended gate runs (-Ddcai.autoGate=1).
 *
 * The 2026-10-28 follow-gate runs stalled at the post-load "Click to Start"
 * screen: GameLoadingState.update() only leaves that phase when
 * Mouse.isButtonDown(LMB) (or a joypad A) is true, and isButtonDown() is a
 * direct read of the public static Mouse.buttonDownStates array (verified by
 * javap against B42.21). Writing that array from inside the game JVM is the
 * game's own input pipeline — no OS-level input, no desktop takeover.
 *
 * While the current game state is GameLoadingState this driver holds LMB true;
 * outside it the driver holds LMB false, so a stray synthetic press can never
 * leak a click into gameplay UI. Disposable-run mode only: never run with a
 * real profile.
 */
public final class AutoInputDriver {
    private AutoInputDriver() {}

    public static void startIfEnabled() {
        if (!Boolean.getBoolean("dcai.autoGate")) return;
        Thread t = new Thread(AutoInputDriver::run, "dcai-auto-input");
        t.setDaemon(true);
        t.start();
        System.out.println("[DCStandalone] auto input driver active (GameLoadingState LMB only)");
    }

    private static void run() {
        while (true) {
            try {
                boolean loading = false;
                if (GameWindow.states != null) {
                    GameState s = GameWindow.states.current;
                    loading = s instanceof GameLoadingState;
                }
                // GameLoadingState.update() reads Mouse.isButtonDown(0) — the
                // PHYSICAL button array slot 0, not the Mouse.LMB logical code
                // (10000). Writing index 10000 is out of bounds and silently
                // swallowed; verified by javap: iconst_0 before the call and
                // isButtonDown's direct buttonDownStates[i] read.
                boolean[] buttons = Mouse.buttonDownStates;
                if (buttons != null && buttons.length > 0) buttons[0] = loading;
            } catch (Throwable ignored) {
                // Early boot: input/state machine not initialized yet; next poll retries.
            }
            try {
                Thread.sleep(20L);
            } catch (InterruptedException e) {
                return;
            }
        }
    }
}
