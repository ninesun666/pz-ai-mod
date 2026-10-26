package dcai.companion;

import zombie.characters.IsoLivingCharacter;
import zombie.core.skinnedmodel.visual.BaseVisual;
import zombie.core.skinnedmodel.visual.HumanVisual;
import zombie.core.skinnedmodel.visual.IHumanVisual;
import zombie.core.skinnedmodel.visual.ItemVisuals;
import zombie.iso.IsoCell;

/** Compilation probe only. Not yet inserted into a world or presented as a character.
 * No Knox or ZombieBuddy classes are used. Lazy visual handles virtual calls from super.
 */
public final class CompanionActor extends IsoLivingCharacter implements IHumanVisual {
    private HumanVisual humanVisual;
    private ItemVisuals itemVisuals;

    public CompanionActor(IsoCell cell, float x, float y, float z) {
        super(cell, x, y, z);
        initWornItems("Human");
        initAttachedItems("Human");
    }

    @Override public HumanVisual getHumanVisual() {
        if (humanVisual == null) humanVisual = new HumanVisual(this);
        return humanVisual;
    }
    @Override public BaseVisual getVisual() { return getHumanVisual(); }
    @Override public ItemVisuals getItemVisuals() {
        if (itemVisuals == null) itemVisuals = new ItemVisuals();
        itemVisuals.clear();
        super.getItemVisuals(itemVisuals);
        return itemVisuals;
    }
    @Override public void getItemVisuals(ItemVisuals out) { super.getItemVisuals(out); }
    @Override public boolean isSkeleton() { return false; }
}
