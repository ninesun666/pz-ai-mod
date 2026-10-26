package dcai.companion;

import java.lang.instrument.ClassFileTransformer;
import java.lang.instrument.Instrumentation;
import java.security.ProtectionDomain;
import org.objectweb.asm.*;

/** Own narrowly scoped bootstrap. No mod scan, native proxy, updater or HTTP eval. */
public final class CompanionAgent {
    public static void premain(String args, Instrumentation instrumentation) {
        instrumentation.addTransformer(new ClassFileTransformer() {
            @Override public byte[] transform(ClassLoader loader, String name,
                    Class<?> redefined, ProtectionDomain domain, byte[] bytes) {
                return "zombie/Lua/LuaManager".equals(name) ? transformLuaManager(bytes) : null;
            }
        }, false);
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
