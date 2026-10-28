package dcai.companion;

import java.lang.instrument.ClassFileTransformer;
import java.lang.instrument.Instrumentation;
import java.security.ProtectionDomain;
import org.objectweb.asm.*;

/** Own narrowly scoped bootstrap. No mod scan, native proxy, updater or HTTP eval. */
public final class CompanionAgent {
    private static volatile Instrumentation instrumentation;
    private static volatile boolean stateMachineHooked;

    public static void premain(String args, Instrumentation inst) {
        instrumentation = inst;
        AutoInputDriver.startIfEnabled();
        inst.addTransformer(new ClassFileTransformer() {
            @Override public byte[] transform(ClassLoader loader, String name,
                    Class<?> redefined, ProtectionDomain domain, byte[] bytes) {
                if (probeNames < 30) {
                    probeNames++;
                    System.out.println("[DCAgent] transform #" + probeNames + " " + name);
                }
                if ("zombie/Lua/LuaManager".equals(name)) return transformLuaManager(bytes);
                if ("zombie/ai/StateMachine".equals(name)) {
                    stateMachineHooked = true;
                    return transformStateMachine(bytes);
                }
                return null;
            }
        }, false);
    }

    private static int probeNames;

    /** Force-apply the StateMachine hook if the class was loaded without our transformer. */
    public static void ensureStateMachineHooked() {
        try {
            if (stateMachineHooked || instrumentation == null) return;
            Class<?> sm = Class.forName("zombie.ai.StateMachine");
            System.out.println("[DCAgent] class loaded without transform; forcing retransform");
            instrumentation.retransformClasses(sm);
            stateMachineHooked = true;
            System.out.println("[DCAgent] retransform applied");
        } catch (Throwable t) {
            System.out.println("[DCAgent] retransform failed: " + t);
        }
    }

    /**
     * Debug telemetry (evidence for P2): log every state transition of the
     * companion with the exact engine call stack, so the actor kicking us out of
     * PathFindState/PlayerMovementState is identified, not guessed.
     */
    public static void onStateChange(zombie.ai.StateMachine sm, zombie.ai.State next) {
        try {
            if (hookProbe < 5) {
                hookProbe++;
                System.out.println("[DCAgent] changeState probe " + hookProbe
                    + " owner=" + String.valueOf(sm.getOwner())
                    + " to=" + tail(String.valueOf(next)));
            }
            if (!(sm.getOwner() instanceof CompanionActor)) return;
            String from = String.valueOf(sm.getCurrent());
            String to = String.valueOf(next);
            if (from.equals(to) || logCount >= 50) return;
            logCount++;
            System.out.println("[DCAgent] companion changeState " + tail(from) + " -> " + tail(to));
            new Exception("[DCAgent] changeState origin").printStackTrace(System.out);
        } catch (Throwable t) {
            if (hookProbe <= 5) System.out.println("[DCAgent] onStateChange threw " + t);
        }
    }

    private static int logCount;
    private static int hookProbe;

    private static String tail(String state) {
        int dot = state.lastIndexOf('.');
        return dot >= 0 ? state.substring(dot + 1) : state;
    }

    static byte[] transformStateMachine(byte[] bytes) {
        ClassReader reader = new ClassReader(bytes);
        ClassWriter writer = new ClassWriter(reader, ClassWriter.COMPUTE_MAXS);
        final int[] hooks = {0};
        reader.accept(new ClassVisitor(Opcodes.ASM9, writer) {
            @Override public MethodVisitor visitMethod(int access, String method,
                    String descriptor, String signature, String[] exceptions) {
                MethodVisitor target = super.visitMethod(access, method, descriptor, signature, exceptions);
                if (!"changeState".equals(method)
                        || !"(Lzombie/ai/State;Ljava/lang/Iterable;Z)V".equals(descriptor)) return target;
                hooks[0]++;
                return new MethodVisitor(Opcodes.ASM9, target) {
                    @Override public void visitCode() {
                        super.visitCode();
                        super.visitVarInsn(Opcodes.ALOAD, 0);
                        super.visitVarInsn(Opcodes.ALOAD, 1);
                        super.visitMethodInsn(Opcodes.INVOKESTATIC,
                            "dcai/companion/CompanionAgent", "onStateChange",
                            "(Lzombie/ai/StateMachine;Lzombie/ai/State;)V", false);
                    }
                };
            }
        }, 0);
        if (hooks[0] != 1) throw new IllegalStateException("expected exactly one StateMachine.changeState hook");
        System.out.println("[DCAgent] StateMachine.changeState transformed");
        return writer.toByteArray();
    }

    static byte[] transformLuaManager(byte[] bytes) {
        ClassReader reader = new ClassReader(bytes);
        ClassWriter writer = new ClassWriter(reader, ClassWriter.COMPUTE_MAXS);
        final int[] hooks = {0};
        reader.accept(new ClassVisitor(Opcodes.ASM9, writer) {
            @Override public MethodVisitor visitMethod(int access, String method,
                    String descriptor, String signature, String[] exceptions) {
                MethodVisitor target = super.visitMethod(access, method, descriptor, signature, exceptions);
                if (!"init".equals(method) || !"()V".equals(descriptor)) return target;
                hooks[0]++;
                return new MethodVisitor(Opcodes.ASM9, target) {
                    @Override public void visitInsn(int opcode) {
                        if (opcode == Opcodes.RETURN) {
                            super.visitMethodInsn(Opcodes.INVOKESTATIC,
                                "dcai/companion/CompanionBridge", "install", "()V", false);
                        }
                        super.visitInsn(opcode);
                    }
                };
            }
        }, 0);
        if (hooks[0] != 1) throw new IllegalStateException("expected exactly one LuaManager.init hook");
        return writer.toByteArray();
    }
}
