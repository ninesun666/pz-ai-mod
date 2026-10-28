package dcai.companion.bt.actions;

import dcai.companion.bt.core.BehaviorNode;
import dcai.companion.bt.subtrees.movement.MovementKeys;

/**
 * Structural mirror of Knox InterpolatePathAction. Knox interpolates the found
 * path into the MOVE_INTERPOLATED_VEC board slot; our locomotion candidate uses
 * the vanilla PathFindState loop directly, so this node only maintains the
 * restart flag. Interpolation itself is unverified and not claimed.
 */
public final class InterpolatePathAction extends BehaviorNode {
    public InterpolatePathAction() { super("InterpolatePathAction"); }

    @Override
    public State evaluate() {
        Object needsRestart = getData(MovementKeys.MOVE_NEEDS_RESTART);
        if (Boolean.TRUE.equals(needsRestart)) setData(MovementKeys.MOVE_NEEDS_RESTART, Boolean.FALSE);
        state = State.SUCCESS;
        return state;
    }
}
