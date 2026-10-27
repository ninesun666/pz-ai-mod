package dcai.companion;

import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.ClassVisitor;
import org.objectweb.asm.MethodVisitor;
import org.objectweb.asm.Opcodes;

/** Static bytecode guard, not a game-world constructor/render acceptance.
 *  Architecture guard: the actor MUST extend IsoPlayer (the Knox-proven base)
 *  and construct in-world via (IsoCell, SurvivorDesc, III). */
public final class ActorConstructionProbe {
    public static void main(String[] args) throws Exception {
        int[] constructors = {0};
        String[] superName = {null};
        try (InputStream bytes = ActorConstructionProbe.class.getResourceAsStream("CompanionActor.class")) {
            if (bytes == null) throw new AssertionError("actor class missing");
            new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9) {
                @Override public void visit(int version, int access, String name, String signature,
                        String superNm, String[] interfaces) {
                    superName[0] = superNm;
                    super.visit(version, access, name, signature, superNm, interfaces);
                }
                @Override public MethodVisitor visitMethod(int access, String name, String desc,
                        String signature, String[] exceptions) {
                    if (!name.equals("<init>")) return null;
                    return new MethodVisitor(Opcodes.ASM9) {
                        private final List<Integer> operands = new ArrayList<>();
                        @Override public void visitVarInsn(int opcode, int index) { operands.add(opcode); }
                        @Override public void visitMethodInsn(int opcode, String owner, String name2,
                                String descriptor, boolean isInterface) {
                            if (!owner.equals("zombie/characters/IsoPlayer") || !name2.equals("<init>")) return;
                            if (!descriptor.equals("(Lzombie/iso/IsoCell;Lzombie/characters/SurvivorDesc;III)V"))
                                throw new AssertionError("unreviewed base constructor: " + descriptor);
                            int n = operands.size();
                            List<Integer> expected = List.of(Opcodes.ALOAD, Opcodes.ALOAD,
                                    Opcodes.ILOAD, Opcodes.ILOAD, Opcodes.ILOAD);
                            if (!operands.subList(Math.max(0, n - 5), n).equals(expected))
                                throw new AssertionError("must pass cell/desc/x/y/z straight through: " + operands);
                            constructors[0]++;
                        }
                    };
                }
            }, ClassReader.SKIP_DEBUG | ClassReader.SKIP_FRAMES);
        }
        if (!"zombie/characters/IsoPlayer".equals(superName[0]))
            throw new AssertionError("actor must extend IsoPlayer (Knox-proven base): " + superName[0]);
        if (constructors[0] != 1) throw new AssertionError("expected exactly one reviewed constructor");
        System.out.println("PASS actor IsoPlayer-constructor bytecode (not live construction/rendering)");
    }
}
