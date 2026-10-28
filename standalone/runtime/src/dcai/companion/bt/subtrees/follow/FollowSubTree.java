package dcai.companion.bt.subtrees.follow;

import dcai.companion.bt.CompanionBehaviorTree;
import dcai.companion.bt.actions.SetFollowPointAction;
import dcai.companion.bt.conditions.IsFollowingCondition;
import dcai.companion.bt.core.BehaviorNode;
import dcai.companion.bt.core.InverterNode;
import dcai.companion.bt.core.SequenceNode;
import dcai.companion.bt.subtrees.movement.MovementSubTree;

/**
 * Mirror of Knox FollowSubTree: while NOT within follow distance, publish the
 * owner square and move to it. Close enough inverts to FAILURE so no path is
 * re-requested. Knox's vehicle keys and hand constraints are dropped.
 */
public final class FollowSubTree extends SequenceNode {
    public static final String FOLLOW_DISTANCE = "FOLLOW_DISTANCE";
    public static final String TICKS = "TICKS";
    public static final float DEFAULT_FOLLOW_DISTANCE = 3.0f;

    public FollowSubTree(CompanionBehaviorTree tree) {
        super("FollowSubTree");
        setData(FOLLOW_DISTANCE, DEFAULT_FOLLOW_DISTANCE);
        addChild(new InverterNode("notFollowing").addChild(new IsFollowingCondition(tree)));
        addChild(new SetFollowPointAction(tree));
        addChild(new MovementSubTree(tree));
        for (BehaviorNode c : children()) c.setDataParent(this);
    }

    @Override
    public State evaluate() {
        Object t = getData(TICKS);
        setData(TICKS, (t instanceof Integer ? (Integer) t : 0) + 1);
        return super.evaluate();
    }
}
