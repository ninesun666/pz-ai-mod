# Round 13: real combat proven

## Native combat4 success
`test-profile/live-combat4.log`:
- 1400: one zombie spawned health1, NPC health1.
- 1425,1427,1436,1441,1446: OnHitZombie attributed to exact spawned zombie AND exact teammate world object; weapon Base.MetalBar.
- 1431 health0.9134595; 1440 health0.868578; 1445 health0.1649946.
- 1447 OnZombieDead hitSeen=true.
- 1448 END ticks734 hitSeen=true deadSeen=true, paused automatically.
No forced hits/damage/Kill/god/healing/stat setters; normal melee AI with pre-existing preset weapon. Disposable fresh world only; original saves untouched. PID4588 stopped after proof; job pwsh-7b6ebddc51cf4b57 collected. All prior combat1/2/3 jobs also stopped and collected.

## Diagnostics and changes
Combat1 paused on Knox procgen overlay after recovery; set started=true in recovery bootstrap enables existing cleanup. Combat2 failed empty zombie list. Actual jar GlobalObject.javap.txt lines14025-14040 proves addZombiesInOutfit returns empty when IsoWorld.getZombiesDisabled and not debug. Prior world had Zombies6 (none). Combat4 used fresh disposable world Zombies3 (normal) with normal spawn API, not debug bypass.

New test-only DC_AI_CombatTest.lua observes OnHitZombie/OnZombieDead plus health. Automatically loaded (also required by test bootstrap), one spawn after180ticks, pauses at death or1980ticks. Current bootstrap config is create, Zombies3, persistence save at1200ticks (death pause stopped before that). Combat test module currently runs automatically; DISABLE before UI-only/reload work. Old recovered proof save DC_AITeammate_1811762178 / NPC146 is still available.

Production mailbox speech change: replaced player-only HaloTextHelper.addText with NPC world:Say(reply.text) pcall; on failure lastError='action completed; teammate speech unavailable' rather than silent swallow. Actual jar Halo signatures accept IsoPlayer. Tests6 mailbox groups and UI direct script passed. Source+isolated deployed mailbox hashD81BAD4531F98D92B3C349F96C16ADD27CA9BE01C32B6A2A2BF3BA16A7FEA919. Actual visual speech still UNVERIFIED. Need regression covering presence of Halo API and speech failure.

Unittest discover30 bridge/protocol cases pass, adapter and UI import checks pass. Mailbox6 plain tests executed separately pass.

Remaining: actual UI right-click and text rendering; package/install; actual configured model integration (no key known). Keep goal active. No background game jobs left.
