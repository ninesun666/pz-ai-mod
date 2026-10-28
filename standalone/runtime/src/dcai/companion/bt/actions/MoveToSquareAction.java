package dcai.companion.bt.actions;

import dcai.companion.bt.CompanionBehaviorTree;
import dcai.companion.bt.core.BehaviorNode;
import dcai.companion.bt.subtrees.movement.MovementKeys;

/**
 * Mirror of Knox MoveToSquareAction scoped to owner-following: request a path to
 * the published target square. Without a target the node is a no-op SUCCESS, so
 * StaySubTree can embed MovementSubTree exactly like Knox does.
 */
public final class MoveToSquareAction extends BehaviorNode {
    /** Gate-visible marker text; must stay identical for smoke_game.py follow gate. */
    public static final String PATH_REQUESTED_MARKER =
        "[DCStandalone] path requested (locomotion arrival unverified)";

    private final CompanionBehaviorTree tree;
    private boolean announced;

    public MoveToSquareAction(CompanionBehaviorTree tree) {
        super("MoveToSquareAction");
        this.tree = tree;
    }

    @Override
    public State evaluate() {
        Object tx = getData(MovementKeys.MOVE_TARGET_X);
        Object ty = getData(MovementKeys.MOVE_TARGET_Y);
        Object tz = getData(MovementKeys.MOVE_TARGET_Z);
        if (tx == null || ty == null || tz == null) {
            state = State.SUCCESS;
            return state;
        }
        if (tree.motion().isPathfinding()) {
            state = State.SUCCESS; // live path: do not spam re-requests
            return state;
        }
        boolean accepted = tree.motion().walkToOwner();
        if (accepted && !announced) {
            announced = true;
            System.out.println(PATH_REQUESTED_MARKER);
        }
        state = accepted ? State.SUCCESS : State.FAILURE;
        return state;
    }
}
