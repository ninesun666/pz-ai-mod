package dcai.companion.bt.core;

/**
 * Mirror of Knox BehaviorTreeBase: a named tree with a Sequence root. Subclasses
 * build the root's children; NpcBehaviorTree's role is taken by
 * dcai.companion.bt.CompanionBehaviorTree.
 */
public abstract class BehaviorTreeBase {
    protected final SequenceNode rootNode;
    private final String name;

    protected BehaviorTreeBase(String name) {
        this.name = name;
        rootNode = new SequenceNode(name + "Root");
    }

    public final String name() { return name; }

    protected final BehaviorNode.State walk() { return rootNode.evaluate(); }

    public void reset() { rootNode.reset(); }
}
