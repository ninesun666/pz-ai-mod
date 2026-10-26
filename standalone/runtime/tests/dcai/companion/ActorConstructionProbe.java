package dcai.companion;

import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.ClassVisitor;
import org.objectweb.asm.MethodVisitor;
import org.objectweb.asm.Opcodes;

/** Static bytecode guard, not a game-world constructor/render acceptance. */
public final class ActorConstructionProbe {
    public static void main(String[] args) throws Exception {
        List<Integer> operands = new ArrayList<>();
        int[] constructors = {0};
        try (InputStream bytes = ActorConstructionProbe.class.getResourceAsStream("CompanionActor.class")) {
            if (bytes == null) throw new AssertionError("actor class missing");
            new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9) {
                @Override public MethodVisitor visitMethod(int access, String name, String desc,
                        String signature, String[] exceptions) {
                    if (!name.equals("<init>")) return null;
                    return new MethodVisitor(Opcodes.ASM9) {
                        @Override public void visitInsn(int opcode) { operands.add(opcode); }
                        @Override public void visitVarInsn(int opcode, int index) {
                            // Loading a caller-supplied cell here would violate detachment.
                            operands.add(opcode);
                        }
                        @Override public void visitIntInsn(int opcode, int value) { operands.add(opcode); }
                        @Override public void visitLdcInsn(Object value) { operands.add(Opcodes.LDC); }
                        @Override public void visitMethodInsn(int opcode, String owner, String name,
                                String descriptor, boolean isInterface) {
                            if (!owner.equals("zombie/characters/IsoLivingCharacter") || !name.equals("<init>")) return;
                            if (!descriptor.equals("(Lzombie/iso/IsoCell;FFF)V"))
                                throw new AssertionError("unreviewed base constructor: " + descriptor);
                            int n = operands.size();
                            List<Integer> expected = List.of(Opcodes.ALOAD, Opcodes.ACONST_NULL,
                                    Opcodes.FCONST_0, Opcodes.FCONST_0, Opcodes.FCONST_0);
                            if (!operands.subList(Math.max(0, n - 5), n).equals(expected))
                                throw new AssertionError("actor must invoke super(null,0f,0f,0f): " + operands);
                            constructors[0]++;
                        }
                    };
                }
            }, ClassReader.SKIP_DEBUG | ClassReader.SKIP_FRAMES);
        }
        if (constructors[0] != 1) throw new AssertionError("expected exactly one reviewed constructor");
        System.out.println("PASS actor detached-constructor bytecode (not live construction/rendering)");
    }
}
