package dcai.companion.bt.actions;

import dcai.companion.bt.CompanionBehaviorTree;
import dcai.companion.bt.core.BehaviorNode;

/**
 * Mirror of Knox StayAction: stop any live path. Idempotent per tick; a full
 * stop on an already-idle companion is skipped so savegames see no churn.
 */
public final class StayAction extends BehaviorNode {
    private final CompanionBehaviorTree tree;

    public StayAction(CompanionBehaviorTree tree) {
        super("StayAction");
        this.tree = tree;
    }

    @Override
    public State evaluate() {
        if (tree.motion().isPathfinding()) tree.motion().stopWalking();
        state = State.SUCCESS;
        return state;
    }
}
