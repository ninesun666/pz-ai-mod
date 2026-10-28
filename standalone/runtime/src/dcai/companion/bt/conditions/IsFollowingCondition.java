package dcai.companion.bt.conditions;

import dcai.companion.bt.CompanionBehaviorTree;
import dcai.companion.bt.core.BehaviorNode;
import dcai.companion.bt.subtrees.follow.FollowSubTree;

/** Mirror of Knox IsFollowingCondition: SUCCESS while inside follow distance. */
public final class IsFollowingCondition extends BehaviorNode {
    private final CompanionBehaviorTree tree;

    public IsFollowingCondition(CompanionBehaviorTree tree) {
        super("IsFollowingCondition");
        this.tree = tree;
    }

    @Override
    public State evaluate() {
        Object d = getData(FollowSubTree.FOLLOW_DISTANCE);
        float limit = d instanceof Float ? (Float) d : FollowSubTree.DEFAULT_FOLLOW_DISTANCE;
        state = tree.distance() <= limit ? State.SUCCESS : State.FAILURE;
        return state;
    }
}
