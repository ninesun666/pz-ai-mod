package dcai.companion;

import zombie.characters.IsoPlayer;
import zombie.characters.SurvivorDesc;
import zombie.iso.IsoCell;
import zombie.iso.IsoGridSquare;
import zombie.iso.IsoWorld;

/**
 * Production companion controller: spawns the own actor once the Lua identity
 * is declared, routes menu commands into the deterministic behavior FSM and
 * reports honest status. No probe flags required; still fails closed.
 */
public final class CompanionController {
    private static final long BEHAVIOR_PERIOD_MS = 100;
    private static final long DIAG_PERIOD_MS = 5000;

    private CompanionActor actor;
    private BehaviorController behavior = new BehaviorController();
    private String companionId;
    private boolean declared;
    private boolean spawnFailed;
    private String lastError;
    private BehaviorController.Action lastAction = BehaviorController.Action.NONE;
    private long lastBehaviorTickMs = -1;
    private boolean pathWarned;
    private Float lastActorX;
    private Float lastActorY;
    private int stuckTicks;
    private boolean stuck;
    private boolean modelConfirmed;
    private long lastDiagMs;

    /** Called from Lua after ensureIdentity() succeeds. Accepts only one identity. */
    public synchronized boolean declareIdentity(String uuid, String assetId) {
        if (uuid == null || uuid.isEmpty()) { lastError = "identity uuid missing"; return false; }
        if (actor != null && !uuid.equals(companionId)) { lastError = "identity changed with live actor"; return false; }
        companionId = uuid;
        declared = true;
        lastError = null;
        return true;
    }

    public synchronized void tick() {
        if (!declared) return;
        if (actor == null && !spawnFailed) trySpawn();
        if (actor == null) return;
        if (!modelConfirmed && actor.modelConfirmed()) {
            modelConfirmed = true;
            System.out.println("[DCStandalone] companion model confirmed");
        }
        IsoPlayer owner = IsoPlayer.getInstance();
        if (owner == null || owner.getCurrentSquare() == null) return;
        long now = System.currentTimeMillis();
        if (now - lastDiagMs > DIAG_PERIOD_MS) {
            lastDiagMs = now;
            double dist = Math.sqrt(Math.pow(owner.getX() - actor.getX(), 2) + Math.pow(owner.getY() - actor.getY(), 2));
            System.out.println("[DCStandalone] diag " + actor.modelInstanceDiag()
                + " dist=" + String.format("%.1f", dist));
        }
        if (lastBehaviorTickMs >= 0 && now - lastBehaviorTickMs < BEHAVIOR_PERIOD_MS) return;
        if (lastBehaviorTickMs >= 0 && now < lastBehaviorTickMs) return; // clock went backwards; skip
        lastBehaviorTickMs = now;
        double dx = owner.getX() - actor.getX();
        double dy = owner.getY() - actor.getY();
        double distance = Math.sqrt(dx * dx + dy * dy);
        lastAction = behavior.tick(now, distance, true, true);
        switch (lastAction) {
            case PATH_TO_OWNER:
                updateStuckState();
                if (stuck && actor.isPathfinding()) {
                    actor.stopWalking(); // A live but unproductive path: cancel before re-request.
                    stuck = false;
                }
                if (actor.walkTo(owner) && !pathWarned) {
                    pathWarned = true;
                    System.out.println("[DCStandalone] path requested (locomotion arrival unverified)");
                }
                break;
            case CANCEL_PATH:
                actor.stopWalking();
                stuck = false;
                stuckTicks = 0;
                break;
            default: break;
        }
    }

    /** Three consecutive behavior ticks without position change count as stuck. */
    private void updateStuckState() {
        float ax = actor.getX();
        float ay = actor.getY();
        if (lastActorX == null || Math.abs(ax - lastActorX) > 0.01f || Math.abs(ay - lastActorY) > 0.01f) {
            stuckTicks = 0;
            stuck = false;
        } else {
            stuckTicks++;
            stuck = stuckTicks >= 3;
        }
        lastActorX = ax;
        lastActorY = ay;
    }

    public synchronized boolean command(String intent) {
        if (actor == null) { lastError = "actor unavailable"; return false; }
        BehaviorController.Intent next;
        switch (intent) {
            case "follow": next = BehaviorController.Intent.FOLLOW; break;
            case "hold": next = BehaviorController.Intent.HOLD; break;
            case "retreat": next = BehaviorController.Intent.RETREAT; break;
            default: lastError = "invalid intent"; return false;
        }
        behavior.command(next);
        lastError = null;
        return true;
    }

    /** True only when a live actor exists, so the menu reflects reality. */
    public synchronized boolean canCommand() {
        return actor != null;
    }

    public synchronized String intent() {
        switch (behavior.currentIntent()) {
            case FOLLOW: return "follow";
            case RETREAT: return "retreat";
            default: return "hold";
        }
    }

    public synchronized String lastError() { return lastError; }

    public synchronized boolean isSpawnFailed() { return spawnFailed; }

    /** Test-only access for the follow stimulus probe; package-private on purpose. */
    synchronized CompanionActor liveActor() { return actor; }

    /** Detaches before a world save so the actor never enters the save file; identity is kept. */
    public synchronized void suspend() {
        if (actor != null) {
            actor.stopWalking();
            actor.removeFromWorld();
            actor.removeFromSquare();
            actor = null;
        }
        // declared stays true: the next tick respawns from the same identity, so a
        // reload can never produce a duplicate companion.
    }

    public synchronized void close() {
        if (actor != null) {
            actor.stopWalking();
            actor.removeFromWorld();
            actor.removeFromSquare();
        }
        actor = null;
        declared = false;
        companionId = null;
        spawnFailed = false;
        lastError = null;
    }

    private void trySpawn() {
        try {
            IsoPlayer owner = IsoPlayer.getInstance();
            IsoCell cell = IsoWorld.instance == null ? null : IsoWorld.instance.currentCell;
            if (owner == null || cell == null || owner.getCurrentSquare() == null) return;
            IsoGridSquare spot = findSpotNear(owner, cell);
            if (spot == null) return;
            SurvivorDesc desc = new SurvivorDesc(false);
            desc.setFemale(true);
            desc.setForename("大肥鱼");
            desc.setSurname("");
            // Knox-proven construction: the IsoPlayer in-world constructor runs the
            // engine's full character pipeline (model, dressing, animation, render).
            CompanionActor candidate = new CompanionActor(cell, desc, (int) spot.getX(), (int) spot.getY(), (int) spot.getZ());
            // Knox-proven spawn sequence (逆向笔记-knox核心.md L344→L450): the
            // in-world constructor alone leaves the actor OUT of the update loop —
            // pathing never executes. addToWorld() registers it for updates.
            candidate.addToWorld();
            actor = candidate;
            spawnFailed = false;
            System.out.println("[DCStandalone] companion spawned id=" + companionId
                + " at " + actor.getX() + "," + actor.getY());
        } catch (RuntimeException failure) {
            spawnFailed = true; // Never silently retry-loop a broken spawn.
            lastError = "spawn failed: " + failure.getMessage();
            System.out.println("[DCStandalone] " + lastError);
        }
    }

    /** Product rule: stand 2-3 tiles from the player on a loaded, solid-free square. */
    private IsoGridSquare findSpotNear(IsoPlayer owner, IsoCell cell) {
        int px = (int) owner.getX();
        int py = (int) owner.getY();
        int pz = (int) owner.getZ();
        int[][] offsets = {{2,0},{-2,0},{0,2},{0,-2},{2,2},{-2,2},{2,-2},{-2,-2},{3,0},{0,3},{-3,0},{0,-3}};
        for (int[] offset : offsets) {
            IsoGridSquare square = cell.getGridSquare(px + offset[0], py + offset[1], pz);
            if (square == null || square.isSolid()) continue;
            return square;
        }
        return null;
    }
}
