package dcai.companion;

import static dcai.companion.CompanionLifecycle.Phase.ATTACHED;
import static dcai.companion.CompanionLifecycle.Phase.DETACHED;
import static dcai.companion.CompanionLifecycle.Phase.DISPOSED;

/** Pure JVM lifecycle checks; no Project Zomboid classes or engine startup. */
public final class CompanionLifecycleProbe {
    private static void equal(Object expected, Object actual) {
        if (expected != actual) throw new AssertionError(expected + " != " + actual);
    }

    private static void rejects(Runnable action, String label) {
        try {
            action.run();
            throw new AssertionError("accepted invalid operation: " + label);
        } catch (IllegalStateException expected) {
            // expected
        }
    }

    public static void main(String[] args) throws Exception {
        CompanionLifecycle lifecycle = new CompanionLifecycle();
        equal(DETACHED, lifecycle.phase());
        rejects(lifecycle::detach, "detach before attach");
        lifecycle.attach();
        equal(ATTACHED, lifecycle.phase());
        lifecycle.requireAttached();
        rejects(lifecycle::attach, "attach twice");
        lifecycle.detach();
        equal(DETACHED, lifecycle.phase());
        rejects(lifecycle::requireAttached, "use while detached");
        lifecycle.attach();
        lifecycle.close();
        equal(DISPOSED, lifecycle.phase());
        lifecycle.close(); // idempotent
        rejects(lifecycle::requireAttached, "use after close");
        rejects(lifecycle::attach, "revive after close");
        rejects(lifecycle::detach, "detach after close");

        try {
            new CompanionLifecycle(null);
            throw new AssertionError("null owner accepted");
        } catch (IllegalArgumentException expected) {
            // expected
        }
        CompanionLifecycle explicit = new CompanionLifecycle(Thread.currentThread());
        equal(Thread.currentThread(), explicit.ownerThread());
        explicit.close();
        explicit.close(); // detached teardown is idempotent too

        CompanionLifecycle threaded = new CompanionLifecycle();
        final Throwable[] failure = new Throwable[1];
        Thread other = new Thread(() -> {
            try {
                rejects(threaded::attach, "foreign attach");
                rejects(threaded::detach, "foreign detach");
                rejects(threaded::requireAttached, "foreign attached use");
                rejects(threaded::requireOwnerThread, "foreign ownership check");
                rejects(threaded::close, "foreign live close");
                equal(DETACHED, threaded.phase()); // observations are safe
            } catch (Throwable unexpected) {
                failure[0] = unexpected;
            }
        }, "non-owner");
        other.start();
        other.join();
        if (failure[0] != null) {
            throw new AssertionError("foreign thread validation failed", failure[0]);
        }
        equal(DETACHED, threaded.phase());
        threaded.close();
        equal(DISPOSED, threaded.phase());
        Thread afterClose = new Thread(() -> {
            try {
                rejects(threaded::close, "foreign disposed close");
                equal(DISPOSED, threaded.phase());
            } catch (Throwable unexpected) {
                failure[0] = unexpected;
            }
        }, "non-owner-after-close");
        afterClose.start();
        afterClose.join();
        if (failure[0] != null) {
            throw new AssertionError("disposed thread validation failed", failure[0]);
        }

        System.out.println("PASS companion lifecycle: transitions, owner binding, invalid-state rejection, idempotent close, no revive");
    }
}
