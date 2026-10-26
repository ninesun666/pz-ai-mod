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
    onStart = function() print("[DCStandaloneTest] world started") end,
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
Events.OnMainMenuEnter.Add(tryLaunch)
Events.OnTick.Add(tryLaunch)
print("[DCStandaloneTest] bootstrap loaded")