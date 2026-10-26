# ZombieBuddy source reference

- Official source: https://github.com/zed-0xff/ZombieBuddy
- Local source checkout: `upstream/ZombieBuddy` (separate Git repository; intentionally excluded from the project source commit).
- Pinned revision: `7794d9f974b509f9f800b266f76c15cd9eb6bfa6`
- License file inspected at that revision: `LICENSE.txt`.
- Copyright line: `Copyright (c) 2025 Andrey "Zed" Zaikin`.
- License is MIT text: modification and redistribution permitted, provided copyright and permission notice are included in copies or substantial portions. Acknowledgment alone is not a substitute.

## Inspection findings

The upstream is a Java instrumentation framework, not a human teammate AI. `java/src/main/java/me/zed_0xff/zombie_buddy/Agent.java` installs instrumentation, exposes classes and loads patch resources. Its general mod discovery/approval, experimental HTTP evaluation and multiplayer-related patches are not requirements of our single companion.

Build entry is `java/build.gradle` (Gradle wrapper under `java/`); root `Rakefile` orchestrates platform builds. The pinned build declares Java 25 and ByteBuddy, ASM, BouncyCastle and Gson dependencies. Their licenses and exact selected subset must be reviewed separately before any redistribution.

## Adaptation policy

Download is complete; adaptation and compilation are NOT yet complete. The upstream checkout is reference material only and is not loaded by our mod. The intended runtime owns its bootstrap and only the minimum reviewed Lua exposure/main-thread integration required by the companion. No Knox runtime, no ZombieBuddy Workshop prerequisite, no `-agentlib:zbNative` launcher argument in the future clean harness. Do not merely rename an upstream binary and call that independent implementation.

No compiled upstream or game classes are committed or redistributed here. If adapted source is incorporated, copy its exact license/notice with it, record origin and modifications, and include transitive notices in the build artifact.
