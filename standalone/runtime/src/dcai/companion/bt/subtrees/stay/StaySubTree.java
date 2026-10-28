package dcai.companion.bt.subtrees.stay;

import dcai.companion.bt.CompanionBehaviorTree;
import dcai.companion.bt.actions.StayAction;
import dcai.companion.bt.core.BehaviorNode;
import dcai.companion.bt.core.SequenceNode;
import dcai.companion.bt.subtrees.movement.MovementSubTree;

/**
 * Mirror of Knox StaySubTree: stop any live path, then the shared movement
 * subtree (a no-op without a published target).
 */
public final class StaySubTree extends SequenceNode {
    public StaySubTree(CompanionBehaviorTree tree) {
        super("StaySubTree");
        addChild(new StayAction(tree));
        addChild(new MovementSubTree(tree));
        for (BehaviorNode c : children()) c.setDataParent(this);
    }
}
