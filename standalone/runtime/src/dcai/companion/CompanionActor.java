package dcai.companion;

import dcai.companion.bt.CompanionMotion;
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
public final class CompanionActor extends IsoPlayer implements CompanionMotion {
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
        dressAsWhaleGirl();
        resetModelNextFrame();
    }

    public boolean modelConfirmed() { return modelConfirmed; }

    /**
     * Route A appearance (DEC-1, docs/DESIGN_PRODUCT.md): blue/white whale-girl
     * palette. The DCWhaleGirl outfit is our own mod's clothing pipeline
     * (42/media/clothing + scripts, adapted from the local CosplayShop workshop
     * mod — see standalone/42/media/ASSET_NOTICE.md for provenance). We dress
     * the CHARACTER (IsoGameCharacter.dressInNamedOutfit, javap-verified) so
     * worn items exist immediately; if the outfit is missing (mod assets not
     * mounted) we fall back to the vanilla Nurse palette. Hair stays deep-sea
     * navy via HumanVisual.
     */
    private void dressAsWhaleGirl() {
        SurvivorDesc d = getDescriptor();
        boolean ownOutfit = false;
        try {
            dressInNamedOutfit("DCWhaleGirl");
            ownOutfit = getWornItems() != null && getWornItems().size() > 0;
        } catch (Throwable t) {
            System.out.println("[DCStandalone] DCWhaleGirl dressing threw: " + t);
        }
        if (!ownOutfit) {
            System.out.println("[DCStandalone] DCWhaleGirl outfit not resolved, falling back to vanilla Nurse");
            d.dressInNamedOutfit("Nurse");
        } else {
            System.out.println("[DCStandalone] dressed in DCWhaleGirl, wornItems=" + getWornItems().size());
        }
        d.getHumanVisual().setHairModel("Long");
        d.getHumanVisual().setHairColor(new zombie.core.ImmutableColor(0.09f, 0.16f, 0.38f));
    }

    public void confirmModel() { modelConfirmed = true; }

    @Override
    public Target ownerTarget() {
        IsoPlayer owner = IsoPlayer.getInstance();
        if (owner == null || owner.getCurrentSquare() == null) return new Target(0f, 0f, 0f, false);
        return new Target(owner.getX(), owner.getY(), owner.getZ(), true);
    }

    @Override
    public boolean walkToOwner() { return walkTo(IsoPlayer.getInstance()); }

    /** Vanilla A* pathing toward a target. True = request accepted, not arrival proof. */
    public boolean walkTo(IsoPlayer target) {
        if (target == null) return false;
        zombie.pathfind.PathFindBehavior2 pfb = getPathFindBehavior2();
        if (!pfb.isGoalNone()
            && Math.abs(pfb.getTargetX() - target.getX()) < 1f
            && Math.abs(pfb.getTargetY() - target.getY()) < 1f
            && (int) pfb.getTargetZ() == (int) target.getZ()) return true;
        localPath = null; // new destination invalidates the retained route
        pathToCharacter(target);
        // We no longer enter PathFindState: its exit() wipes path2 and the finder
        // on every engine state churn (~1s), killing the native request mid-flight.
        // pumpPathfind() drives PFB2.update() per tick instead (Knox's IsoNpcPlayer
        // pumps it from its own update loop the same way).
        return true;
    }

    /** Per-tick pump for the native path request; no-op without a goal. */
    public void pumpPathfind() {
        if (getPathFindBehavior2().isGoalNone()) return;
        getPathFindBehavior2().update();
    }

    public boolean isPathfinding() {
        return !getPathFindBehavior2().isGoalNone();
    }

    private zombie.pathfind.Path localPath;
    private int localPathIndex;

    /**
     * Keep our own copy of the most recently found path: the engine's state churn
     * clears path2 on every PathFindState exit, but the route itself stays valid.
     */
    private void retainPath() {
        zombie.pathfind.Path path = getPath2();
        if (path == null || path.isEmpty()) return;
        zombie.pathfind.PathNode last = path.getNode(path.size() - 1);
        if (localPath != null && !localPath.isEmpty()
                && Math.abs(localPath.getNode(localPath.size() - 1).x - last.x) < 0.01f
                && Math.abs(localPath.getNode(localPath.size() - 1).y - last.y) < 0.01f) {
            return; // same route already retained
        }
        if (localPath == null) localPath = new zombie.pathfind.Path();
        localPath.copyFrom(path);
        localPathIndex = 0;
    }

    /** AIComponent control vars, or null before setNpc(true) installed the component. */
    private zombie.ai.AIBrainPlayerControlVars controlVars() {
        Object component = getECSComponentMap().get(zombie.characters.component.AIComponent.class);
        return component instanceof zombie.characters.component.AIComponent
            ? ((zombie.characters.component.AIComponent) component).getHumanControlVars()
            : null;
    }

    /**
     * Per-tick synthetic NPC movement input. B42's official NPC seam: the vanilla
     * IsoPlayer.updateInternal2() NPC branch reads AIComponent humanControlVars
     * strafeX/strafeY and writes them into deltaX/deltaY (javap IsoPlayer
     * 8086-8119, 8200-8205), so the engine moves us exactly like a keyboard-driven
     * player, with full collision. Direction: first path node further than 0.6
     * tiles (no corner cutting); straight at the owner only while a requested
     * path is still pending.
     */
    public void driveFollowMovement(IsoPlayer owner, boolean wantMove) {
        zombie.ai.AIBrainPlayerControlVars vars = controlVars();
        if (vars == null) return;
        float strafeX = 0f;
        float strafeY = 0f;
        if (wantMove && owner != null) {
            float tx = owner.getX();
            float ty = owner.getY();
            retainPath();
            if (localPath != null) {
                while (localPathIndex < localPath.size()) {
                    zombie.pathfind.PathNode node = localPath.getNode(localPathIndex);
                    float ndx = node.x - getX();
                    float ndy = node.y - getY();
                    if (ndx * ndx + ndy * ndy > 0.36f) {
                        tx = node.x;
                        ty = node.y;
                        break;
                    }
                    localPathIndex++;
                }
                if (localPathIndex >= localPath.size()) localPath = null; // route exhausted
            }
            float dx = tx - getX();
            float dy = ty - getY();
            float len = (float) Math.sqrt(dx * dx + dy * dy);
            if (len > 0.35f && Float.isFinite(len)) {
                // Strafe input is facing-relative: turn toward the target, then
                // request pure forward motion.
                setDirectionAngle((float) Math.atan2(dy, dx));
                strafeX = 1f;
                strafeY = 0f;
            }
        }
        vars.strafeX = strafeX;
        vars.strafeY = strafeY;
        vars.justMoved = strafeX != 0f || strafeY != 0f;
    }

    /** Zero the synthetic input so HOLD/arrivals never keep sliding. */
    public void stopDriveMovement() {
        zombie.ai.AIBrainPlayerControlVars vars = controlVars();
        if (vars == null) return;
        vars.strafeX = 0f;
        vars.strafeY = 0f;
        vars.justMoved = false;
    }

    public void stopWalking() {
        StopAllActionQueueWalking();
        getPathFindBehavior2().cancel();
        if (getCurrentState() == PathFindState.instance()) setDefaultState();
        setPath2(null);
        setPathing(false);
        setVariable("bMoving", false);
        setVariable("bPathfind", false);
        localPath = null;
        localPathIndex = 0;
        stopDriveMovement();
        if (!stopOriginLogged) {
            stopOriginLogged = true;
            new Exception("[DCStandalone] stopWalking call origin (logged once)").printStackTrace();
        }
    }

    private boolean stopOriginLogged;

    public String movementDiag() {
        zombie.ai.AIBrainPlayerControlVars vars = controlVars();
        String drive = vars == null ? "n/a" : String.format("%.2f,%.2f", vars.strafeX, vars.strafeY);
        zombie.iso.Vector2 deferred = getDeferredMovement(new zombie.iso.Vector2());
        zombie.pathfind.Path path = getPath2();
        return "npc=" + isNpc() + " state=" + shortState()
            + " hasPath=" + hasPath() + " finder=" + getFinder().progress
            + " shouldMove=" + getPathFindBehavior2().shouldBeMoving()
            + " pathLen=" + (path == null ? -1 : path.size())
            + " local=" + (localPath == null ? -1 : localPath.size()) + "/" + localPathIndex
            + " drive=" + drive
            + " face=" + String.format("%.2f,%.2f",
                getForwardDirection().x, getForwardDirection().y)
            + " deferred=" + String.format("%.3f", (float) Math.sqrt(deferred.x * deferred.x + deferred.y * deferred.y))
            + " moving=" + isMoving()
            + " animFrame=" + isAnimationUpdatingThisFrame()
            + " pos=" + getX() + "," + getY() + "," + getZ();
    }

    String shortState() {
        String name = String.valueOf(getCurrentState());
        int dot = name.lastIndexOf('.');
        return dot >= 0 ? name.substring(dot + 1) : name;
    }

    /** Render-side diagnostic: is an engine model instance actually bound to us? */
    public String modelInstanceDiag() {
        zombie.core.skinnedmodel.model.ModelInstance mi = getModelInstance();
        if (mi == null) return "instance=null";
        zombie.core.skinnedmodel.animation.AnimationPlayer anim = getAnimationPlayer();
        String set = String.valueOf(GetAnimSetName());
        String clip = "none";
        if (anim != null) {
            clip = anim.getAnimationClip() == null ? "none" : "playing";
        }
        return "instance=present anim=" + (anim != null)
            + " set=" + set + " clip=" + clip
            + " mesh=" + (mi.model != null)
            + " tex=" + (mi.tex != null)
            + " refs=" + mi.renderRefCount;
    }
}
