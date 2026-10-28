-- TEST ONLY: installed exclusively by smoke_game.py --world.
require "OptionScreens/MainScreen"
require "DebugUIs/DebugScenarios"
local launched = false
local scenario = {
    name = "DC standalone disposable actor probe",
    world = "Muldraugh, KY",
    startLoc = {x=11778, y=6749, z=0},
    setSandbox = function()
        SandboxVars.Zombies = 6
    end,
    onStart = function()
        print("[DCStandaloneTest] world started")
        -- After loading, the game can sit paused (speed 0) so Lua OnTick never
        -- advances; restore normal speed so automated probes keep ticking.
        local ok, err = pcall(setGameSpeed, 1)
        if not ok then print("[DCStandaloneTest] setGameSpeed failed: " .. tostring(err)) end
        -- In-game evidence capture: the engine dumps its OWN framebuffer via
        -- takeScreenshot(name). The argument is a RELATIVE filename written
        -- into the profile's Screenshots dir (Core lambda: getScreenshotDir()
        -- + separator + name; an absolute path concatenates into an invalid
        -- path and writePng's failure is swallowed). Desktop capture returns
        -- black frames on locked/direct-scanout desktops; this path cannot.
        -- smoke_game.py copies the shots into the run dir afterwards.
        local shotN = 0
        local tickAcc = 0
        Events.OnTick.Add(function()
            tickAcc = tickAcc + 1
            if tickAcc % 1200 == 1 then -- first tick, then every ~20s at 60fps
                shotN = shotN + 1
                local name = "game_shot_" .. string.format("%03d", shotN) .. ".png"
                local okS, errS = pcall(takeScreenshot, name)
                print("[DCStandaloneTest] game screenshot " .. name .. " ok=" .. tostring(okS)
                    .. (okS and "" or (" err=" .. tostring(errS))))
            end
        end)
        local diagDone = {}
        local function probe(name)
            if diagDone[name] then return end
            diagDone[name] = true
            local okp, paused = pcall(isGamePaused)
            print("[DCStandaloneTest] probe " .. name .. " paused=" .. tostring(okp and paused)
                .. " speed=" .. tostring(getGameSpeed and getGameSpeed()))
        end
        for _, name in ipairs({"OnTick", "OnTickEvenPaused", "OnPostRender", "OnPlayerUpdate", "OnPreRender"}) do
            local ev = Events[name]
            if ev then ev.Add(function() probe(name) end) end
        end
    end,
}
local function tryLaunch()
    if launched or isClient() or isServer() then return end
    local menu = MainScreen and MainScreen.instance
    if not (menu and menu.desc and CharacterCreationMain.instance) then return end
    launched = true
    local world = "DCStandaloneProbe_" .. tostring(ZombRand(1000000000))
    ActiveMods.getById("currentGame"):copyFrom(ActiveMods.getById("default"))
    menu:setDefaultSandboxVars()
    selectedDebugScenario = scenario
    scenario.setSandbox()
    getWorld():setGameMode("Sandbox")
    getWorld():setMap(scenario.world)
    createWorld(world)
    GameWindow.doRenderEvent(false)
    Events.OnNewGame.Add(DebugScenarios.ongamestart)
    Events.LoadGridsquare.Add(DebugScenarios.onloadgs)
    print("[DCStandaloneTest] launching disposable world " .. world)
    forceChangeState(LoadingQueueState.new())
end
local constructorProbed = false
Events.OnGameStateEnter.Add(function(s)
    if not constructorProbed and DCStandaloneProbeConstructor ~= nil then
        constructorProbed = true
        DCStandaloneProbeConstructor()
    end
    local ok1, terms = pcall(function() return instanceof(s, "TermsOfServiceState") end)
    local ok2, main = pcall(function() return instanceof(s, "MainScreenState") end)
    local ok3, ver = pcall(function() return getCore():getTermsOfServiceVersion() end)
    local function cn()
        local ok, n = pcall(function() return tostring(s) end)
        return ok and n or "<unknown>"
    end
    print("[DCStandaloneDiag] OnGameStateEnter class=" .. cn() .. " terms=" .. tostring(ok1 and terms)
        .. " main=" .. tostring(ok2 and main) .. " termsVersion=" .. tostring(ok3 and ver))
end)
Events.OnMainMenuEnter.Add(function()
    print("[DCStandaloneDiag] OnMainMenuEnter main=" .. tostring(MainScreen and MainScreen.instance ~= nil)
        .. " desc=" .. tostring(MainScreen and MainScreen.instance and MainScreen.instance.desc ~= nil)
        .. " ccm=" .. tostring(CharacterCreationMain and CharacterCreationMain.instance ~= nil))
    tryLaunch()
end)
Events.OnTick.Add(tryLaunch)
print("[DCStandaloneTest] bootstrap loaded")