package dcai.companion;

import zombie.characters.IsoLivingCharacter;
import zombie.core.skinnedmodel.visual.BaseVisual;
import zombie.core.skinnedmodel.visual.HumanVisual;
import zombie.core.skinnedmodel.visual.IHumanVisual;
import zombie.core.skinnedmodel.visual.ItemVisuals;
import zombie.iso.IsoCell;

/** Compilation probe only. Not yet inserted into a world or presented as a character.
 * Uses only base-game types. Lazy visual handles virtual calls from super.
 */
public final class CompanionActor extends IsoLivingCharacter implements IHumanVisual {
    private HumanVisual humanVisual;
    private ItemVisuals itemVisuals;

    public CompanionActor(IsoCell cell) {
        // Nonzero super coordinates auto-register a partially initialized actor.
        // This constructor deliberately stays detached; a world factory is still required.
        super(null, 0, 0, 0);
        // Worn/attached groups are initialized by the world factory after game data is ready.

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
