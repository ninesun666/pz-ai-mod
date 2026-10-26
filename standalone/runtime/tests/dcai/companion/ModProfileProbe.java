package dcai.companion;

import java.nio.file.Files;
import java.nio.file.Path;
import zombie.modding.ActiveMods;
import zombie.modding.ActiveModsFile;

/** Checks the actual engine parser before spending a full game launch. */
public final class ModProfileProbe {
    public static void main(String[] args) throws Exception {
        Path path = Path.of(args[0]);
        Files.createDirectories(path.getParent());
        Files.writeString(path, "VERSION = 1,\nmods\n{\n mod = DC_AIStandalone,\n}\nmaps\n{\n}\n");
        ActiveMods mods = new ActiveMods("standalone-profile-probe");
        if (!new ActiveModsFile().read(path.toString(), mods))
            throw new AssertionError("engine rejected profile");
        if (!mods.getMods().equals(java.util.List.of("DC_AIStandalone")))
            throw new AssertionError("unexpected parsed mods: " + mods.getMods());
        System.out.println("PASS native B42 ActiveModsFile parser: " + mods.getMods());
    }
}
