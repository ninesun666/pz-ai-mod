package dcai.companion.bt;

import dcai.companion.bt.core.BehaviorNode;
import dcai.companion.bt.core.BehaviorTreeBase;
import dcai.companion.bt.subtrees.follow.FollowSubTree;
import dcai.companion.bt.subtrees.stay.StaySubTree;

/**
 * Mirror of Knox NpcBehaviorTree scoped to our vertical slice: one active goal
 * subtree under the root, switched by setGoal like Knox's goal/subgoal protocol.
 * Only FollowSubTree and StaySubTree exist; the other 66 Knox subtrees are
 * deliberately not replicated.
 */
public final class CompanionBehaviorTree extends BehaviorTreeBase {
    public static final String GOAL_FOLLOW = "FollowSubTree";
    public static final String GOAL_STAY = "StaySubTree";

    private final FollowSubTree follow;
    private final StaySubTree stay;
    private String goal = GOAL_STAY;
    private CompanionMotion motion;
    private float distance;

    public CompanionBehaviorTree() {
        super("CompanionBehaviorTree");
        follow = new FollowSubTree(this);
        stay = new StaySubTree(this);
        rootNode.addChild(stay);
    }

    public void attach(CompanionMotion motion) { this.motion = motion; }

    public CompanionMotion motion() { return motion; }

    /** Owner distance in squares, fed by the controller before each tick. */
    public void setDistance(float distance) { this.distance = distance; }

    public float distance() { return distance; }

    public String goal() { return goal; }

    public synchronized void setGoal(String next) {
        if (next == null || next.equals(goal)) return;
        reset();
        rootNode.children().clear();
        rootNode.addChild(GOAL_FOLLOW.equals(next) ? follow : stay);
        goal = next;
    }

    /** One full tree pass per behavior tick; a finished pass resets for the next. */
    public synchronized void tick() {
        if (motion == null) return;
        BehaviorNode.State s = walk();
        if (s != BehaviorNode.State.RUNNING) rootNode.reset();
    }
}
