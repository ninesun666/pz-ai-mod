# Standalone Companion Rework

This branch replaces the old Knox/ZombieBuddy runtime dependency with an independently implemented companion.

## Current phase

- The former Knox adapter, mailbox, context-menu UI, pet overlay, and disposable Knox bootstrap are intentionally disabled before any `require`, event registration, or UI creation.
- `upstream/ZombieBuddy` is a pinned source reference only. It is not loaded by the mod and is not copied into the release package.
- Upstream license: MIT. If source or substantial portions are adapted later, retain `upstream/ZombieBuddy/LICENSE.txt` and attribution.

## Design constraints

- No Knox Event Expanded NPC runtime dependency.
- No ZombieBuddy runtime dependency in the released companion.
- No mandatory text input for ordinary companion control.
- Game logic must remain functional when the model bridge is unavailable.
- Character identity, save/reload recovery, and behavior state are owned by this project.

## Planned vertical slice

1. Establish an independently owned companion entity/renderer path.
2. Add keyboard/context actions for follow, hold, retreat, and assist without opening a text box.
3. Implement deterministic follow/retreat/assist behavior before adding model-driven dialogue.
4. Persist one stable companion identity and verify a real B42 save/reload.
5. Add model/voice reactions as optional event-driven flavor, never as the action executor.

No step is considered complete from log output alone; each requires in-game verification.

## Behavior-tree layer: Knox structural replica (decision 2026-10-28)

User decision: reuse ZombieBuddy where possible; replicate Knox's behavior-tree
core structure 1:1, discarding what we do not need.

Replicated (our code, Knox's structure; reference dumps stay local under
`research/decompiled/`):

- `bt/core`: BehaviorNode (+state enum, blackboard with dataParent chain),
  SequenceNode, SelectorNode, InverterNode, BehaviorTreeBase
- `bt/CompanionBehaviorTree` (NpcBehaviorTree role) with Knox-style goal
  switching (`setGoal`, FollowSubTree / StaySubTree)
- `bt/subtrees`: FollowSubTree (`Inverter(IsFollowing) → SetFollowPoint →
  Movement`), StaySubTree (`Stay → Movement`), MovementSubTree
  (`Interpolate → MoveToSquare`) with Knox's MOVE_* / FOLLOW_DISTANCE / TICKS
  data keys
- `bt/CompanionMotion` seam so probes drive the structure without the game JVM;
  CompanionActor implements it

Discarded: ActionConstraintResolver constraint machinery, Lua node bridge, the
other 66 Knox subtrees (farming/fight/reload/driving/encounter/...), squad/group
meta, procgen backstory. `InterpolatePathAction` is a structural placeholder
(interpolation unverified, not claimed).

Controller dispatch now routes through the tree; the follow-gate marker text is
unchanged. Offline verification: `BehaviorTreeProbe` + `tests/
test_standalone_source.py::BehaviorTreeMirrorTests`. Live follow acceptance is
still blocked on the P2 locomotion candidate (see
`docs/P2_INVESTIGATION_20261028.md`).
