package dcai.companion;

import zombie.GameWindow;
import zombie.characters.IsoPlayer;
import zombie.characters.SurvivorDesc;
import zombie.iso.IsoCell;
import zombie.ai.states.PathFindState;

/**
 * Own companion, following the Knox-proven architecture: extend IsoPlayer so the
 * engine's full character pipeline (model, dressing, animation, rendering) works
 * out of the box. Our earlier IsoLivingCharacter subclass fought the render
 * pipeline and produced an invisible ghost.
 *
 * The constructor builds the actor IN-WORLD (engine registers it), then the
 * caller records lifecycle state. No detached state exists on this class.
 */
public final class CompanionActor extends IsoPlayer {
    private boolean modelConfirmed;

    public CompanionActor(IsoCell cell, SurvivorDesc desc, int x, int y, int z) {
        super(cell, desc, x, y, z);
        if (Thread.currentThread() != GameWindow.gameThread)
            throw new IllegalStateException("companion construction off game thread");
        setSceneCulled(false);
        setAlphaAndTarget(1f);
        // B42's NPC state is represented by an AIComponent, not a boolean.
        // IsoPlayer.updateInternal2() uses this path to obtain movement controls;
        // without it, the private vanilla input updater treats us as a human player.
        setNpc(true);
        dressInRandomOutfit();
        resetModelNextFrame();
    }

    public boolean modelConfirmed() { return modelConfirmed; }

    public void confirmModel() { modelConfirmed = true; }

    /** Vanilla A* pathing toward a target. True = request accepted, not arrival proof. */
    public boolean walkTo(IsoPlayer target) {
        if (target == null) return false;
        if (getCurrentState() == PathFindState.instance()
            && Math.abs(getPathFindBehavior2().getTargetX() - target.getX()) < 1f
            && Math.abs(getPathFindBehavior2().getTargetY() - target.getY()) < 1f
            && (int) getPathFindBehavior2().getTargetZ() == (int) target.getZ()) return true;
        pathToCharacter(target);
        // pathToAux only writes animation flags; NPC IdleState does not consume
        // the request. PathFindState.execute owns the native PFB2.update loop.
        changeState(PathFindState.instance());
        return true;
    }

    public void stopWalking() {
        StopAllActionQueueWalking();
        getPathFindBehavior2().cancel();
        if (getCurrentState() == PathFindState.instance()) setDefaultState();
        setPath2(null);
        setPathing(false);
        setVariable("bMoving", false);
        setVariable("bPathfind", false);
    }

    public boolean isPathfinding() {
        return getCurrentState() == PathFindState.instance();
    }

    public String movementDiag() {
        return "npc=" + isNpc() + " state=" + getCurrentState()
            + " hasPath=" + hasPath() + " finder=" + getFinder().progress
            + " shouldMove=" + getPathFindBehavior2().shouldBeMoving()
            + " pos=" + getX() + "," + getY() + "," + getZ();
    }

    /** Render-side diagnostic: is an engine model instance actually bound to us? */
    public String modelInstanceDiag() {
        zombie.core.skinnedmodel.model.ModelInstance mi = getModelInstance();
        if (mi == null) return "instance=null";
        return "instance=present anim=" + (getAnimationPlayer() != null)
            + " mesh=" + (mi.model != null)
            + " tex=" + (mi.tex != null)
            + " refs=" + mi.renderRefCount;
    }
}
