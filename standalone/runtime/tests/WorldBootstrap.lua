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