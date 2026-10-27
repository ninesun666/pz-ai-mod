# Round 11 results

Native9 failed Unicode request: source literal based UTF16 probe and test literal corrupt under actual Lua compiler. Native9 PID8372 stopped verified isolated; job pwsh-1fd88468392d4b23 collected.

Actual jar standalone probes prove Lua StringLib uses UTF16 but LuaCompiler.loadstring corrupts non-ASCII literals (LexState casts units to low8 bytes then UTF8 decodes). Evidence tests/KahluaLiteralProbe.evidence.txt. Avoid native nonASCII literals in .lua; use translation data or numeric string.char for tests.

Fixed source mailbox probe to pcall(string.char,20013), #probe==1, byte==20013 (ASCII source only); source+deployed match at deployment hash923FB55C5456867E79723A48F71FA709EDC0519E1617831140B2DFE53B617451. Six mailbox test groups pass. Test runner request now numeric string.char Chinese+emoji.

Native10 disposable DC_AITeammate_4355136609, NPC121. live-native10.log line1420 request=true. Python strict parser read actual game request and exact matched 请在这里等待😀 (assert succeeded). Wrote correlated simulated Unicode wait '[测试] 我在这里等你😀'. Lines1456 onward mailbox complete/error=nil and adapter waiting/Stay. Prior stale native8 reply correctly rejected identity (pending remained until valid replacement); no model call. This proves real Unicode transport+dispatch, NOT rendered text glyphs: display is pcall with no telemetry; must still visually verify.

UI file deployed to isolated mod and loaded without noted test error; actual right-click interaction/visual rendering NOT verified. Native10 PID30444 stopped after proof and job pwsh-4c2362048e8543ee collected. No running test game jobs.

Save/reload investigation (child1b1ec17d finished): canonical MainScreen.continueLatestSave('Sandbox', exact disposable bare save name); never latestSave globals/createWorld. MainScreen.lua1194-1297 handles validation/reset/load, onResetLua1935-1943. save(true) stock usage; flush/event semantics unproven. Normal quit via getCore():quit() with isQuitCooldown guard after setGameSpeed(1), pauseSoundAndMusic(), setShowPausedMessage(true). Need durable exact world+expected NPC test manifest, separate create vs reload; suppress movement/mailbox/new spawn on reload, assert same saved ID/member/world object before recovery. Combat, reload, UI visual, packaging, configured real-model roundtrip remain.
