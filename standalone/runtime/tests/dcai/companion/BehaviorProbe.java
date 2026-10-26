package dcai.companion;

import static dcai.companion.BehaviorController.Action.*;
import static dcai.companion.BehaviorController.Intent.*;

public final class BehaviorProbe {
    private static void equal(Object expected, Object actual) {
        if (expected != actual) throw new AssertionError(expected + " != " + actual);
    }
    public static void main(String[] args) {
        BehaviorController b = new BehaviorController();
        equal(NONE, b.tick(0, 10, true, true));
        b.command(FOLLOW);
        equal(PATH_TO_OWNER, b.tick(1, 10, true, true));
        equal(NONE, b.tick(200, 8, true, true));
        equal(PATH_TO_OWNER, b.tick(751, 8, true, true));
        equal(CANCEL_PATH, b.tick(752, 1, true, true));
        equal(NONE, b.tick(800, 3, true, true));
        equal(PATH_TO_OWNER, b.tick(1501, 5, true, true));
        b.command(HOLD);
        b.command(RETREAT);
        equal(CANCEL_PATH, b.tick(1502, 7, true, true));
        equal(PATH_TO_OWNER, b.tick(1503, 3, true, true));
        equal(CANCEL_PATH, b.tick(1602, 3, false, true));
        equal(NONE, b.tick(1603, 30, true, false));
        boolean rejected = false;
        try { b.tick(1604, Double.NaN, true, true); }
        catch (IllegalArgumentException expected) { rejected = true; }
        if (!rejected) throw new AssertionError("invalid perception accepted");
        System.out.println("PASS deterministic behavior: hold/follow/regroup, hysteresis, cancellation, throttling, unavailable actor");
    }
}
