package dcai.companion.bt.actions;

import dcai.companion.bt.CompanionBehaviorTree;
import dcai.companion.bt.CompanionMotion;
import dcai.companion.bt.core.BehaviorNode;
import dcai.companion.bt.subtrees.movement.MovementKeys;

/** Mirror of Knox SetFollowPointAction: publish the owner's square as move target. */
public final class SetFollowPointAction extends BehaviorNode {
    private final CompanionBehaviorTree tree;

    public SetFollowPointAction(CompanionBehaviorTree tree) {
        super("SetFollowPointAction");
        this.tree = tree;
    }

    @Override
    public State evaluate() {
        CompanionMotion.Target t = tree.motion().ownerTarget();
        if (!t.present) {
            state = State.FAILURE; // fail-closed: no owner, no path request
            return state;
        }
        setData(MovementKeys.MOVE_TARGET_X, t.x);
        setData(MovementKeys.MOVE_TARGET_Y, t.y);
        setData(MovementKeys.MOVE_TARGET_Z, t.z);
        setData(MovementKeys.MOVE_CHECK_INSIDE, Boolean.TRUE);
        state = State.SUCCESS;
        return state;
    }
}
