package dcai.companion;

/** Pure deterministic intent arbitration. No engine mutation or model/network calls. */
public final class BehaviorController {
    public enum Intent { FOLLOW, HOLD, RETREAT }
    public enum Action { NONE, PATH_TO_OWNER, CANCEL_PATH }
    private Intent intent = Intent.HOLD;
    private boolean pathing;
    private long lastRequest;
    private boolean requested;
    private long lastTick = -1;
    private boolean cancelPending;

    public void command(Intent next) {
        if (next == null) throw new IllegalArgumentException("intent missing");
        if (intent != next) {
            cancelPending = cancelPending || pathing;
            pathing = false;
            requested = false;
        }
        intent = next;
    }

    public Action tick(long nowMs, double distance, boolean ownerReady, boolean actorReady) {
        if (nowMs < 0 || nowMs < lastTick) throw new IllegalArgumentException("nonmonotonic time");
        if (!Double.isFinite(distance) || distance < 0) throw new IllegalArgumentException("invalid distance");
        lastTick = nowMs;
        if (cancelPending) {
            cancelPending = false;
            return Action.CANCEL_PATH;
        }
        if (!ownerReady || !actorReady || intent == Intent.HOLD) {
            if (pathing) { pathing = false; return Action.CANCEL_PATH; }
            return Action.NONE;
        }
        double stop = intent == Intent.RETREAT ? 1.5 : 2.0;
        double start = intent == Intent.RETREAT ? 2.5 : 4.0;
        if (distance <= stop) {
            if (pathing) { pathing = false; return Action.CANCEL_PATH; }
            return Action.NONE;
        }
        if (!pathing && distance < start) return Action.NONE;
        if (requested && nowMs - lastRequest < 750) return Action.NONE;
        pathing = true;
        requested = true;
        lastRequest = nowMs;
        return Action.PATH_TO_OWNER;
    }
}
