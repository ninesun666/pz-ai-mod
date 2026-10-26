# Runtime bridge dependency note

`CompanionAgent.java` currently uses ASM only as a local compile/runtime-probe dependency. The project does not yet redistribute an agent JAR or ASM binary.

- ASM artifact inspected: `org.ow2.asm:asm:9.9`.
- License metadata inspected from its POM: BSD-3-Clause.
- Source: https://asm.ow2.io/

Before shipping any Java agent, choose and document a pinned ASM version, include the complete BSD notice, verify support for class-file major 69, and build a self-contained artifact. The current probe is not a release package and does not claim that `-javaagent` has run in-game.
