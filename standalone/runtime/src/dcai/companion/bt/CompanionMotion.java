package dcai.companion.bt;

/**
 * Locomotion seam between the behavior tree and CompanionActor. Knox's nodes
 * hold a MetaNpcCharacter; our tree holds a CompanionMotion so probes can drive
 * the structure offline without the game JVM.
 */
public interface CompanionMotion {
    final class Target {
        public final float x, y, z;
        public final boolean present;

        public Target(float x, float y, float z, boolean present) {
            this.x = x;
            this.y = y;
            this.z = z;
            this.present = present;
        }
    }

    Target ownerTarget();

    /** True = path request accepted, not arrival proof (same contract as walkTo). */
    boolean walkToOwner();

    void stopWalking();

    boolean isPathfinding();
}
