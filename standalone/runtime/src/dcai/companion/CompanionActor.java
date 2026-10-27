package dcai.companion;

import zombie.characters.IsoLivingCharacter;
import zombie.core.skinnedmodel.visual.BaseVisual;
import zombie.core.skinnedmodel.visual.HumanVisual;
import zombie.core.skinnedmodel.visual.IHumanVisual;
import zombie.core.skinnedmodel.visual.ItemVisuals;
import zombie.iso.IsoCell;
import zombie.iso.IsoGridSquare;
import zombie.iso.IsoWorld;

/** Own actor shell. Detached until an audited world factory attaches it. */
public final class CompanionActor extends IsoLivingCharacter implements IHumanVisual {
    private HumanVisual humanVisual;
    private ItemVisuals itemVisuals;
    private CompanionLifecycle lifecycle;
    private boolean visualsReady;
    private boolean modelRequested;
    private boolean actionGroupReady;

    public boolean isActionGroupReady() { return actionGroupReady; }
    /** Explicit model request; a returned true is membership, not visible-pixel proof. */
    public boolean requestPlaceholderModel() {
        requireGameThread();
        if (!isAttached() || !isPlaceholderVisualReady()) return false;
        if (!modelRequested) {
            setSceneCulled(false);
            modelRequested = isAddedToModelManager();
        }
        return modelRequested && hasActiveModel();
    }

    @Override public void render(float x, float y, float z,
            zombie.core.textures.ColorInfo color, boolean a, boolean b,
            zombie.core.opengl.Shader shader) {
        if (modelRequested && hasActiveModel()) super.render(x, y, z, color, a, b, shader);
    }

    @Override public void renderlast() {
        if (modelRequested && hasActiveModel()) super.renderlast();
    }

    /** Placeholder human model only; not the final whale-girl asset. */
    public void initializePlaceholderVisuals() {
        requireGameThread();
        if (visualsReady) return;
        if (isAttached()) throw new IllegalStateException("initialize visuals before attachment");
        initWornItems("Human");
        initAttachedItems("Human");
        zombie.characters.SurvivorDesc desc = new zombie.characters.SurvivorDesc(false);
        desc.setFemale(true);
        desc.setForename("大肥鱼");
        desc.setSurname("[placeholder]");
        desc.setInstance(this);
        setDescriptor(desc);
        setFemale(true);
        getHumanVisual().copyFrom(desc.getHumanVisual());
        initSpritePartsEmpty();
        zombie.characters.action.ActionGroup group =
                zombie.characters.action.ActionGroup.getActionGroup("player");
        if (group == null || group.getInitialState() == null)
            throw new IllegalStateException("player action group missing idle state");
        getActionContext().setGroup(group);
        actionGroupReady = true;
        setVariable("bMoving", false);
        setVariable("bPathfind", false);
        visualsReady = true;
    }

    public CompanionActor(IsoCell ignoredCell) {
        super(null, 0, 0, 0);
        // Worn/attached groups are initialized by the world factory after game data is ready.
    }

    public boolean isPlaceholderVisualReady() {
        return visualsReady && getDescriptor() != null && isFemale()
                && getWornItems() != null && getAttachedItems() != null && legsSprite != null
                && actionGroupReady;
    }

    /** Main/world-thread only. No inherited physiology or animation update is called. */
    public boolean attachAt(IsoCell targetCell, float x, float y, float z) {
        requireGameThread();
        if (lifecycle == null) lifecycle = new CompanionLifecycle();
        lifecycle.requireOwnerThread();
        if (lifecycle.phase() != CompanionLifecycle.Phase.DETACHED || targetCell == null || IsoWorld.instance == null
                || IsoWorld.instance.currentCell != targetCell || !Float.isFinite(x)
                || !Float.isFinite(y) || !Float.isFinite(z) || x < 0 || y < 0 || z < 0) return false;
        IsoGridSquare square = targetCell.getGridSquare((int) x, (int) y, (int) z);
        if (square == null) return false;
        setX(x); setY(y); setZ(z);
        setNextX(x); setNextY(y);
        setLastX(x); setLastY(y); setLastZ(z);
        setCurrent(square);
        setMovingSquareNow();
        // Manual attachment bypasses vanilla spawn fades: without this the actor
        // renders at alpha 0 — a ghost that occupies the world but is invisible.
        setAlphaAndTarget(1f);
        targetCell.addMovingObject(this);
        lifecycle.attach();
        return true;
    }

    /** Idempotent world-thread teardown; no persistence or implicit revival. */
    public void detach() {
        if (lifecycle == null) return;
        requireGameThread();
        if (lifecycle.phase() != CompanionLifecycle.Phase.ATTACHED) return;
        if (isAddedToModelManager()) setSceneCulled(true);
        removeFromWorld();
        removeFromSquare();
        setMovingSquare(null);
        lifecycle.close();
    }

    public boolean isAttached() {
        return lifecycle != null && lifecycle.phase() == CompanionLifecycle.Phase.ATTACHED;
    }

    /** Requests vanilla A* pathing toward the owner. True = request accepted, not arrival proof. */
    public boolean walkTo(zombie.characters.IsoGameCharacter target) {
        requireGameThread();
        if (!isAttached() || !actionGroupReady || target == null) return false;
        pathToCharacter(target);
        return true;
    }

    /** Cancels pending pathing; idempotent. */
    public void stopWalking() {
        requireGameThread();
        if (!isAttached()) return;
        StopAllActionQueueWalking();
        setPathing(false);
        setVariable("bMoving", false);
        setVariable("bPathfind", false);
    }

    public boolean isPathfinding() {
        return isPathing();
    }

    private static void requireGameThread() {
        Thread current = Thread.currentThread();
        if (current != zombie.GameWindow.gameThread)
            throw new IllegalStateException("companion actor mutation off game thread: " + current.getName());
    }

    /** Inherited preupdate has server/equipment paths that cast to IsoPlayer; suppress them. */
    @Override public void preupdate() { /* owned scheduler hook; no IsoPlayer cast paths */ }
    @Override public void update() { /* owned scheduler hook; no bodyDamage path */ }
    @Override public void postupdate() {
        if (!isAttached() || !modelRequested || !actionGroupReady || !hasActiveModel()) return;
        requireGameThread();
        getActionContext().update();
        // Public vanilla wrapper updates animator, animation player/model slot and lighting.
        // This does not implement locomotion/root-motion or prove visible pixels.
        updateForServerGui();
    }
    @Override public HumanVisual getHumanVisual() {
        if (humanVisual == null) humanVisual = new HumanVisual(this);
        return humanVisual;
    }
    @Override public BaseVisual getVisual() { return getHumanVisual(); }
    @Override public ItemVisuals getItemVisuals() {
        if (itemVisuals == null) itemVisuals = new ItemVisuals();
        itemVisuals.clear();
        getItemVisuals(itemVisuals);
        return itemVisuals;
    }
    @Override public void getItemVisuals(ItemVisuals out) {
        if (getWornItems() != null) super.getItemVisuals(out);
    }
    @Override public boolean isSkeleton() { return false; }
}
