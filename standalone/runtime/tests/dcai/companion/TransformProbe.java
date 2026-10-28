package dcai.companion;

import java.util.jar.JarFile;
import org.objectweb.asm.*;

/** Offline integration test against real class69 game bytes, without launching UI. */
public final class TransformProbe {
    public static void main(String[] args) throws Exception {
        byte[] original;
        try (JarFile game = new JarFile(args[0])) {
            original = game.getInputStream(game.getJarEntry("zombie/Lua/LuaManager.class")).readAllBytes();
        }
        byte[] result = CompanionAgent.transformLuaManager(original);
        int[] returns = {0};
        int[] installs = {0};
        new ClassReader(result).accept(new ClassVisitor(Opcodes.ASM9) {
            @Override public MethodVisitor visitMethod(int a, String n, String d, String s, String[] e) {
                if (!n.equals("init") || !d.equals("()V")) return null;
                return new MethodVisitor(Opcodes.ASM9) {
                    @Override public void visitInsn(int op) { if (op == Opcodes.RETURN) returns[0]++; }
                    @Override public void visitMethodInsn(int op, String owner, String name, String desc, boolean itf) {
                        if (owner.equals("dcai/companion/CompanionBridge") && name.equals("install")) installs[0]++;
                    }
                };
            }
        }, 0);
        if (returns[0] == 0 || installs[0] != returns[0]) throw new AssertionError("missing exit hook");
        System.out.println("PASS real LuaManager transformation: returns=" + returns[0] + " hooks=" + installs[0]);

        byte[] stateMachine;
        try (JarFile game = new JarFile(args[0])) {
            stateMachine = game.getInputStream(game.getJarEntry("zombie/ai/StateMachine.class")).readAllBytes();
        }
        byte[] hooked = CompanionAgent.transformStateMachine(stateMachine);
        int[] entries = {0};
        int[] stateHooks = {0};
        new ClassReader(hooked).accept(new ClassVisitor(Opcodes.ASM9) {
            @Override public MethodVisitor visitMethod(int a, String n, String d, String s, String[] e) {
                if (!n.equals("changeState") || !d.equals("(Lzombie/ai/State;Ljava/lang/Iterable;Z)V")) return null;
                return new MethodVisitor(Opcodes.ASM9) {
                    @Override public void visitMethodInsn(int op, String owner, String name, String desc, boolean itf) {
                        if (owner.equals("dcai/companion/CompanionAgent") && name.equals("onStateChange")) {
                            stateHooks[0]++;
                        }
                    }
                };
            }
        }, 0);
        new ClassReader(hooked).accept(new ClassVisitor(Opcodes.ASM9) {
            @Override public MethodVisitor visitMethod(int a, String n, String d, String s, String[] e) {
                if (n.equals("changeState")) entries[0]++;
                return null;
            }
        }, 0);
        if (entries[0] != 1 || stateHooks[0] != 1) {
            throw new AssertionError("missing StateMachine.changeState entry hook");
        }
        System.out.println("PASS real StateMachine transformation: changeState entry hook=1");
    }
}
