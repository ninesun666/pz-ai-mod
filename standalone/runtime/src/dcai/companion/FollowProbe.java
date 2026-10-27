package dcai.companion;

import zombie.characters.IsoPlayer;
import zombie.iso.IsoCell;
import zombie.iso.IsoGridSquare;
import zombie.iso.IsoWorld;

/**
 * Test-only live stimulus probe (-Ddcai.followProbe=true), driven from the
 * bridge tick after CompanionController.tick().
 *
 * Honesty rules of this probe:
 * - The STIMULUS is a player teleport (engine API on the owner only); the
 *   companion is never moved or teleported by this probe.
 * - A round PASSES only if the companion's own position changed by more than
 *   half the opened distance while distance fell under the recover threshold,
 *   which proves real A* locomotion, not a respawn or a second teleport.
 * - Any timeout is reported as FAIL, never swallowed.
 */
public final class FollowProbe {
    private static final boolean ENABLED = Boolean.getBoolean("dcai.followProbe");
    private static final int ROUNDS = 2;
    private static final int TELEPORT_TILES = 16;
    private static final double RECOVER_DIST = 3.5;
    private static final double MIN_ACTOR_TRAVEL = TELEPORT_TILES / 2.0;
    private static final long ROUND_TIMEOUT_MS = 90_000;
    private static final long COMMAND_TIMEOUT_MS = 15_000;
    private static final long LOG_PERIOD_MS = 1000;

    private enum Phase { WAIT_ACTOR, COMMAND, MONITOR, DONE, FAILED }

    private static Phase phase = Phase.WAIT_ACTOR;
    private static int round;
    private static long phaseStartMs;
    private static long lastLogMs;
    private static float actorStartX;
    private static float actorStartY;

    private FollowProbe() { }

    public static void tick(CompanionController controller) {
        if (!ENABLED || phase == Phase.DONE || phase == Phase.FAILED) return;
        long now = System.currentTimeMillis();
        switch (phase) {
            case WAIT_ACTOR:
                if (controller.canCommand()) {
                    phase = Phase.COMMAND;
                    phaseStartMs = now;
                }
                break;
            case COMMAND:
                if (controller.command("follow")) {
                    System.out.println("[DCStandalone] follow-probe intent=follow accepted");
                    startRound(controller, now);
                } else if (now - phaseStartMs > COMMAND_TIMEOUT_MS) {
                    fail("follow command not accepted: " + controller.lastError());
                }
                break;
            case MONITOR:
                monitor(controller, now);
                break;
            default:
                break;
        }
    }

    private static void startRound(CompanionController controller, long now) {
        round++;
        IsoPlayer owner = IsoPlayer.getInstance();
        CompanionActor actor = controller.liveActor();
        if (owner == null || actor == null) { fail("round start without owner/actor"); return; }
        int[][] directions = {{TELEPORT_TILES, 0}, {-TELEPORT_TILES, 0}, {0, TELEPORT_TILES}, {0, -TELEPORT_TILES}};
        for (int[] d : directions) {
            if (teleportOwner(owner, d[0], d[1])) {
                actorStartX = actor.getX();
                actorStartY = actor.getY();
                phaseStartMs = now;
                lastLogMs = 0;
                double dist = distance(owner, actor);
                System.out.println("[DCStandalone] follow-probe round=" + round
                    + " owner teleported " + d[0] + "," + d[1]
                    + " startDist=" + String.format("%.1f", dist));
                phase = Phase.MONITOR;
                return;
            }
        }
        fail("no loaded square to teleport the owner into");
    }

    private static void monitor(CompanionController controller, long now) {
        IsoPlayer owner = IsoPlayer.getInstance();
        CompanionActor actor = controller.liveActor();
        if (owner == null || actor == null) { fail("owner/actor vanished mid-round"); return; }
        double dist = distance(owner, actor);
        if (now - lastLogMs >= LOG_PERIOD_MS) {
            lastLogMs = now;
            System.out.println("[DCStandalone] follow-probe round=" + round
                + " dist=" + String.format("%.1f", dist)
                + " pathing=" + actor.isPathfinding());
        }
        if (dist <= RECOVER_DIST) {
            double travel = Math.sqrt(Math.pow(actor.getX() - actorStartX, 2) + Math.pow(actor.getY() - actorStartY, 2));
            if (travel >= MIN_ACTOR_TRAVEL) {
                System.out.println("[DCStandalone] follow-probe round=" + round + " PASS dist="
                    + String.format("%.1f", dist) + " actorTravel=" + String.format("%.1f", travel));
                if (round >= ROUNDS) {
                    phase = Phase.DONE;
                    System.out.println("[DCStandalone] follow-probe PASS");
                } else {
                    phase = Phase.WAIT_ACTOR;
                    phaseStartMs = now;
                }
            } else {
                fail("distance closed but companion did not really walk (travel="
                    + String.format("%.1f", travel) + ")");
            }
            return;
        }
        if (now - phaseStartMs > ROUND_TIMEOUT_MS) {
            fail("round " + round + " timeout, dist=" + String.format("%.1f", dist)
                + " pathing=" + actor.isPathfinding());
        }
    }

    /** Stimulus on the OWNER only: engine-proven setX/setY + setCurrentSquareFromPosition. */
    private static boolean teleportOwner(IsoPlayer owner, int dx, int dy) {
        IsoCell cell = IsoWorld.instance == null ? null : IsoWorld.instance.currentCell;
        if (cell == null) return false;
        float nx = owner.getX() + dx;
        float ny = owner.getY() + dy;
        IsoGridSquare square = cell.getGridSquare((int) nx, (int) ny, (int) owner.getZ());
        if (square == null || square.isSolid()) return false;
        owner.setX(nx);
        owner.setY(ny);
        owner.setCurrentSquareFromPosition();
        return true;
    }

    private static double distance(IsoPlayer owner, CompanionActor actor) {
        return Math.sqrt(Math.pow(owner.getX() - actor.getX(), 2) + Math.pow(owner.getY() - actor.getY(), 2));
    }

    private static void fail(String reason) {
        phase = Phase.FAILED;
        System.out.println("[DCStandalone] follow-probe FAIL " + reason);
    }
}
