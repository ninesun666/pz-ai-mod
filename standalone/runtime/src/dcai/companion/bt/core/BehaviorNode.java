package dcai.companion.bt.core;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Structural mirror of Knox's BehaviorNode (research/decompiled/BehaviorNode.txt):
 * evaluation states, child list, and a blackboard shared through the dataParent
 * chain. Knox's constraint machinery (ActionConstraintResolver) and Lua-node
 * bridge are deliberately not replicated; see docs/STANDALONE_COMPANION_REWORK.md.
 */
public abstract class BehaviorNode {
    public enum State { SUCCESS, FAILURE, RUNNING, SKIPPED }

    protected State state = State.FAILURE;
    private BehaviorNode dataParent;
    private final List<BehaviorNode> children = new ArrayList<>();
    private final Map<String, Object> data = new HashMap<>();
    private final String name;

    protected BehaviorNode(String name) { this.name = name; }

    public abstract State evaluate();

    public final String name() { return name; }

    public final State state() { return state; }

    /** Chainable like Knox's addChild, so subtrees compose as statements. */
    public BehaviorNode addChild(BehaviorNode child) {
        children.add(child);
        return this;
    }

    public final List<BehaviorNode> children() { return children; }

    /** Points this node's blackboard writes/reads at the shared subtree board. */
    public final void setDataParent(BehaviorNode parent) { this.dataParent = parent; }

    /** Writes climb to the dataParent chain root (the owning subtree's board). */
    public final void setData(String key, Object value) {
        if (dataParent != null) dataParent.setData(key, value);
        else data.put(key, value);
    }

    public final Object getData(String key) {
        Object v = data.get(key);
        if (v != null) return v;
        return dataParent != null ? dataParent.getData(key) : null;
    }

    public void reset() {
        state = State.FAILURE;
        for (BehaviorNode c : children) c.reset();
    }
}
