package dcai.companion;

/**
 * Pure lifecycle state machine for a companion owned by one runtime thread.
 *
 * <p>This type deliberately has no engine, actor, or spawning behavior.  A
 * manager may attach its own actor while in {@link Phase#ATTACHED}; this class
 * only records and validates that lifecycle.</p>
 */
public final class CompanionLifecycle implements AutoCloseable {
    public enum Phase {
        DETACHED,
        ATTACHED,
        DISPOSED
    }

    private final Thread ownerThread;
    private Phase phase = Phase.DETACHED;

    /** Bind this lifecycle to the thread constructing it. */
    public CompanionLifecycle() {
        this(Thread.currentThread());
    }

    /** Bind this lifecycle to an explicit owner thread. */
    public CompanionLifecycle(Thread ownerThread) {
        if (ownerThread == null) {
            throw new IllegalArgumentException("owner thread missing");
        }
        this.ownerThread = ownerThread;
    }

    public Thread ownerThread() {
        return ownerThread;
    }

    public synchronized Phase phase() {
        return phase;
    }

    /** Transition DETACHED -> ATTACHED. */
    public synchronized void attach() {
        requireOwnerThread();
        requirePhase(Phase.DETACHED, "attach");
        phase = Phase.ATTACHED;
    }

    /** Transition ATTACHED -> DETACHED; never creates or revives an actor. */
    public synchronized void detach() {
        requireOwnerThread();
        requirePhase(Phase.ATTACHED, "detach");
        phase = Phase.DETACHED;
    }

    /**
     * Dispose this lifecycle.  Closing an already disposed lifecycle is a
     * no-op, which makes teardown safe to call from multiple cleanup paths on
     * the owner thread.  Even repeated close requires that same owner thread.
     */
    @Override
    public synchronized void close() {
        requireOwnerThread();
        if (phase == Phase.DISPOSED) {
            return;
        }
        phase = Phase.DISPOSED;
    }

    /** Assert that the caller owns this lifecycle and it is attached. */
    public synchronized void requireAttached() {
        requireOwnerThread();
        requirePhase(Phase.ATTACHED, "use attached companion");
    }

    /** Assert ownership without changing state. */
    public void requireOwnerThread() {
        if (Thread.currentThread() != ownerThread) {
            throw new IllegalStateException("companion lifecycle owned by " + ownerThread.getName());
        }
    }

    private void requirePhase(Phase expected, String operation) {
        if (phase != expected) {
            throw new IllegalStateException(operation + " invalid in phase " + phase);
        }
    }
}
