
## Round 5 live evidence
- Read current goal: goal-fe56f7c2-8fc9-4f3e-9358-b7988da363b4 remains active, revision 3.
- The native-agent live test actually passed menu -> disposable Sandbox world: live-native2.log lines 563, 643, 931-934, 984 show unique world launch, world start, OnGameTimeLoaded, adapter start, spawn request; line 984 shows GameLoadingState exit. Native agent and Knox Java patches loaded.
- The isolated game process then remained open (PID 28688 at last inspection); loading confirmation click was sent only after checking the target process/window. No original save was used. Process must be collected/stopped after next evidence.
- Crucial current result: live log has no `following npc` / adapter error after spawn request. Therefore real spawn->world-object->group recruitment is NOT proven. It may be waiting for NPC metadata to phase in or adapter polling event may not run as expected. Do not claim live teammate success yet.
- jstack after-click showed game main thread in normal render loop, MainThread runnable, Knox NpcLootThread/NpcPathfindingThread alive; not a Java deadlock. MainScreen loading prompt was confirmed. GameLoadingState exited at line 984.
- Expanded direct Lua tests passed: `python ai-mod/tests/test_teammate_adapter.py`; coverage includes spawn-once, STAY, modData persistence write, follow/wait command exports, blocked/unloaded tile, spawn exception, missing player/API, timeout, ambiguous NPC and missing teammate. This is lupa mock testing, not real Knox AI.
- Adapter source has M.start/follow/wait and now polls OnTick + OnPlayerUpdate; this last event addition has NOT yet been rerun through unit test or live profile. It has safe no-heal/no-god behavior and FightStance.STAY default.
- Live test runner currently calls adapter.start from OnGameTimeLoaded and starts one spawn. It does not yet log periodic status or fail immediately when spawn remains unresolved; add telemetry before next run.
