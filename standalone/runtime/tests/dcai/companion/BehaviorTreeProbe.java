package dcai.companion;

import static dcai.companion.bt.CompanionBehaviorTree.GOAL_FOLLOW;
import static dcai.companion.bt.CompanionBehaviorTree.GOAL_STAY;
import static dcai.companion.bt.core.BehaviorNode.State.FAILURE;
import static dcai.companion.bt.core.BehaviorNode.State.RUNNING;
import static dcai.companion.bt.core.BehaviorNode.State.SUCCESS;

import dcai.companion.bt.CompanionBehaviorTree;
import dcai.companion.bt.CompanionMotion;
import dcai.companion.bt.core.BehaviorNode;
import dcai.companion.bt.core.InverterNode;
import dcai.companion.bt.core.SelectorNode;
import dcai.companion.bt.core.SequenceNode;
import dcai.companion.bt.subtrees.follow.FollowSubTree;

/** Offline structural probe for the Knox-mirrored behavior tree. */
public final class BehaviorTreeProbe {
    private static void equal(Object expected, Object actual) {
        if (expected != actual && (expected == null || !expected.equals(actual)))
            throw new AssertionError(expected + " != " + actual);
    }

    private static final class FakeMotion implements CompanionMotion {
        Target target = new Target(106f, 100f, 0f, true);
        int walkCalls, stopCalls;
        boolean pathfinding;

        public Target ownerTarget() { return target; }
        public boolean walkToOwner() { walkCalls++; pathfinding = true; return true; }
        public void stopWalking() { stopCalls++; pathfinding = false; }
        public boolean isPathfinding() { return pathfinding; }
    }

    private static BehaviorNode leaf(final BehaviorNode.State fixed) {
        return new BehaviorNode("leaf") {
            @Override public State evaluate() { state = fixed; return fixed; }
        };
    }

    public static void main(String[] args) {
        // composite semantics
        SelectorNode sel = new SelectorNode("s");
        sel.addChild(leaf(FAILURE)).addChild(leaf(SUCCESS)).addChild(leaf(FAILURE));
        equal(SUCCESS, sel.evaluate());
        SequenceNode seq = new SequenceNode("q");
        seq.addChild(leaf(SUCCESS)).addChild(leaf(SUCCESS));
        equal(SUCCESS, seq.evaluate());
        seq.addChild(leaf(FAILURE));
        equal(FAILURE, seq.evaluate());
        InverterNode inv = new InverterNode("i");
        inv.addChild(leaf(SUCCESS));
        equal(FAILURE, inv.evaluate());
        InverterNode inv2 = new InverterNode("i2");
        inv2.addChild(leaf(RUNNING));
        equal(RUNNING, inv2.evaluate());

        // sequence suspends at a RUNNING child and resumes there
        SequenceNode susp = new SequenceNode("susp");
        final BehaviorNode gate = new BehaviorNode("gate") {
            @Override public State evaluate() { state = SUCCESS; return SUCCESS; }
        };
        final boolean[] thirdRan = {false};
        susp.addChild(gate).addChild(leaf(RUNNING)).addChild(new BehaviorNode("third") {
            @Override public State evaluate() { thirdRan[0] = true; state = SUCCESS; return SUCCESS; }
        });
        equal(RUNNING, susp.evaluate());
        if (thirdRan[0]) throw new AssertionError("sequence ran past a RUNNING child");
        equal(RUNNING, susp.evaluate());
        if (thirdRan[0]) throw new AssertionError("sequence restarted before the RUNNING child");

        // blackboard contract on the follow subtree
        CompanionBehaviorTree tree = new CompanionBehaviorTree();
        FollowSubTree fs = new FollowSubTree(tree);
        equal(FollowSubTree.DEFAULT_FOLLOW_DISTANCE, fs.getData(FollowSubTree.FOLLOW_DISTANCE));
        fs.evaluate();
        equal(1, fs.getData(FollowSubTree.TICKS));

        // goal switching and execution through the real tree
        FakeMotion m = new FakeMotion();
        tree.attach(m);
        equal(GOAL_STAY, tree.goal());
        tree.setDistance(2f);
        tree.tick(); // stay with no live path: idle, no calls
        equal(0, m.stopCalls);
        equal(0, m.walkCalls);
        m.pathfinding = true;
        tree.setDistance(2f);
        tree.tick(); // stay cancels a live path exactly once
        equal(1, m.stopCalls);
        tree.setGoal(GOAL_FOLLOW);
        equal(GOAL_FOLLOW, tree.goal());
        tree.setDistance(10f);
        tree.tick(); // far from owner: one path request
        equal(1, m.walkCalls);
        tree.tick(); // live path: no re-request
        equal(1, m.walkCalls);
        tree.setDistance(2f);
        tree.tick(); // within follow distance: no request
        equal(1, m.walkCalls);
        m.target = new CompanionMotion.Target(0f, 0f, 0f, false);
        tree.setDistance(10f);
        tree.tick(); // owner gone: fail-closed
        equal(1, m.walkCalls);
        tree.setGoal(GOAL_STAY);
        equal(GOAL_STAY, tree.goal());

        System.out.println("PASS behavior tree structure: composites, suspension, blackboard, goal switch, follow gate, stay cancel, fail-closed");
    }
}
