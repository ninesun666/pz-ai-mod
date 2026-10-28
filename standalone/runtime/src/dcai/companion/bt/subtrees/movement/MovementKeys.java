package dcai.companion.bt.subtrees.movement;

/**
 * Mirror of Knox MovementSubTree's data contract: target coordinates and path
 * flags on the subtree blackboard. Keys mirror Knox's MOVE_* names; furniture,
 * vehicle, and building keys are not replicated.
 */
public final class MovementKeys {
    public static final String MOVE_PATH = "MOVE_PATH";
    public static final String MOVE_NEEDS_RESTART = "MOVE_NEEDS_RESTART";
    public static final String MOVE_CHECK_INSIDE = "MOVE_CHECK_INSIDE";
    public static final String MOVE_INTERPOLATED_VEC = "MOVE_INTERPOLATED_VEC";
    public static final String MOVE_TARGET_X = "MOVE_TARGET_X";
    public static final String MOVE_TARGET_Y = "MOVE_TARGET_Y";
    public static final String MOVE_TARGET_Z = "MOVE_TARGET_Z";

    private MovementKeys() {}
}
