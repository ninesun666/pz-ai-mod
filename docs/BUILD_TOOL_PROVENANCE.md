# Build tool provenance

The local Java 25 runtime probe used:

- Eclipse ECJ 3.43.0, downloaded from Maven Central, SHA-256 `C786468C65E906498E7E36ECE4E0D04C6D3DD34C9A61B34A3A5B512801911A82`.
- ASM 9.9, downloaded from Maven Central, SHA-256 `03D99A74AD1EE5C71334EF67437F4EF4FE3488CAA7C96D8645ABC73C8E2017D4`.
- Actual Project Zomboid JARs from the locally installed game; none are redistributed.

The current checked-in Java source is still a probe. `.local-tools/` is ignored and no compiler, ASM binary, game JAR or generated class is part of the mod release. If the bridge becomes a release artifact, package an exact ASM BSD-3-Clause notice and separately document ECJ as a build-only tool.
