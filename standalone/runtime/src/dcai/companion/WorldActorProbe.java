package dcai.companion;

import zombie.GameWindow;
import zombie.characters.IsoPlayer;
import zombie.iso.IsoCell;
import zombie.iso.IsoWorld;

/** Disposable-world-only stationary probe. Never enabled by normal production startup. */
public final class WorldActorProbe {
    private CompanionActor actor;
    private boolean attempted;
    private boolean modelReported;

    public void tick() {
        if (Thread.currentThread() != GameWindow.gameThread)
            throw new IllegalStateException("world actor probe off game thread");
        IsoPlayer owner = IsoPlayer.getInstance();
        IsoCell cell = IsoWorld.instance == null ? null : IsoWorld.instance.currentCell;
        if (owner == null || cell == null || owner.getCurrentSquare() == null) return;
        if (!attempted) {
            float x = owner.getX() + 1.0f;
            float y = owner.getY();
            float z = owner.getZ();
            if (cell.getGridSquare((int) x, (int) y, (int) z) == null) return;
            attempted = true; // Never silently duplicate after partial initialization/failure.
            actor = new CompanionActor(null);
            actor.initializePlaceholderVisuals();
            if (!actor.attachAt(cell, x, y, z))
                throw new IllegalStateException("stationary probe attach rejected");
            System.out.println("[DCStandaloneTest] own actor attached (stationary placeholder; not gameplay acceptance)");
        }
        if (actor != null && actor.requestPlaceholderModel() && !modelReported) {
            modelReported = true;
            System.out.println("[DCStandaloneTest] model membership active (pixels unverified)");
        }
    }

    public void close() {
        if (actor != null) actor.detach();
        actor = null;
        // attempted intentionally retained: a disposed probe cannot revive.
    }
}
