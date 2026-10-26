# CompanionActor compile probe

The self-owned candidate `standalone/runtime/src/dcai/companion/CompanionActor.java` compiles with ECJ 3.43.0 running on the game's Zulu Java 25 runtime, against the actual JARs in the Project Zomboid installation. Compile exit code was 0; only warnings were emitted.

This proves only Java type compatibility. It does **not** prove constructor safety, world insertion, ticking, rendering, pathfinding, damage, or save/reload. The generated class output is ignored and not a deliverable.

Command shape used:

```powershell
java -jar .local-tools/ecj-3.43.0.jar -17 -proc:none -classpath <actual game jars> -d standalone/runtime/build/classes standalone/runtime/src/dcai/companion/CompanionActor.java
```

The ECJ JAR is a local build tool and is not part of the mod package.
