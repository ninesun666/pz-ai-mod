package dcai.companion.bt.core;

/** Mirror of Knox InverterNode: flips SUCCESS/Failure; RUNNING and SKIPPED pass through. */
public final class InverterNode extends BehaviorNode {
    public InverterNode(String name) { super(name); }

    @Override
    public State evaluate() {
        if (children().size() != 1) throw new IllegalStateException("InverterNode needs exactly one child: " + name());
        State s = children().get(0).evaluate();
        if (s == State.SUCCESS) state = State.FAILURE;
        else if (s == State.FAILURE) state = State.SUCCESS;
        else state = s;
        return state;
    }
}
