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
    }
}
