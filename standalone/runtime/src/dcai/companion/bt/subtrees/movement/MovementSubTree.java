package dcai.companion.bt.subtrees.movement;

import dcai.companion.bt.CompanionBehaviorTree;
import dcai.companion.bt.actions.InterpolatePathAction;
import dcai.companion.bt.actions.MoveToSquareAction;
import dcai.companion.bt.core.BehaviorNode;
import dcai.companion.bt.core.SequenceNode;

/**
 * Mirror of Knox MovementSubTree: interpolation slot then the square move. The
 * data contract lives in MovementKeys; Knox's furniture/vehicle/building keys
 * are dropped with the subtrees that used them.
 */
public final class MovementSubTree extends SequenceNode {
    public MovementSubTree(CompanionBehaviorTree tree) {
        super("MovementSubTree");
        addChild(new InterpolatePathAction());
        addChild(new MoveToSquareAction(tree));
        for (BehaviorNode c : children()) c.setDataParent(this);
    }
}
