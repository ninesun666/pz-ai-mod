package dcai.companion.bt.core;

/**
 * Mirror of Knox SequenceNode: SUCCESS when every child succeeds in order,
 * FAILURE on the first failure, RUNNING suspends at the failing-progress child.
 */
/** Subtrees extend this node, mirroring Knox's FollowSubTree/StaySubTree. */
public class SequenceNode extends BehaviorNode {
    private int runningIndex = -1;

    public SequenceNode(String name) { super(name); }

    @Override
    public State evaluate() {
        int start = runningIndex >= 0 ? runningIndex : 0;
        for (int i = start; i < children().size(); i++) {
            State s = children().get(i).evaluate();
            if (s == State.RUNNING) {
                runningIndex = i;
                state = State.RUNNING;
                return state;
            }
            if (s != State.SUCCESS) {
                runningIndex = -1;
                state = State.FAILURE;
                return state;
            }
        }
        runningIndex = -1;
        state = State.SUCCESS;
        return state;
    }

    @Override
    public void reset() {
        runningIndex = -1;
        super.reset();
    }
}
