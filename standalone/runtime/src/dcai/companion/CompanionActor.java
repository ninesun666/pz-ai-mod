package dcai.companion;

import zombie.GameWindow;
import zombie.characters.IsoPlayer;
import zombie.characters.SurvivorDesc;
import zombie.iso.IsoCell;
import zombie.iso.IsoGridSquare;

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
        dressInRandomOutfit();
        resetModelNextFrame();
    }

    public boolean modelConfirmed() { return modelConfirmed; }

    public void confirmModel() { modelConfirmed = true; }

    /** Vanilla A* pathing toward a target. True = request accepted, not arrival proof. */
    public boolean walkTo(IsoPlayer target) {
        if (target == null) return false;
        pathToCharacter(target);
        return true;
    }

    public void stopWalking() {
        StopAllActionQueueWalking();
        setPathing(false);
        setVariable("bMoving", false);
        setVariable("bPathfind", false);
    }

    public boolean isPathfinding() {
        return isPathing();
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
