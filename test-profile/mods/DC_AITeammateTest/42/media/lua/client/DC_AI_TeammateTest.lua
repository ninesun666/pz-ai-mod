-- Retired Knox live bootstrap: never auto-load old worlds during rework.
do return end

-- DC_AI_Teammate live test bootstrap.
-- Disposable world only; install only in ai-mod/test-profile.
require "OptionScreens/MainScreen"
require "DebugUIs/DebugScenarios"
require "DC_AI_TestPersistenceConfig"
local persistence = DC_AI_TestPersistenceConfig
local testWorld
local savedOnce = false
local recoveryChecked = false

local launched = false
local scenario = {
    name = "DC AI Teammate disposable test",
    world = "Muldraugh, KY",
    startLoc = { x = 11778, y = 6749, z = 0 },
    setSandbox = function() SandboxVars.Zombies = 3 end,
    onStart = function() print("DC_AITeammate: disposable world started") end,
}

local function uniqueWorldName()
    for _ = 1, 20 do
        local n = "DC_AITeammate_" .. tostring(ZombRand(100000)) .. tostring(ZombRand(100000))
        if not checkSaveFolderExists("Sandbox" .. getFileSeparator() .. n) then return n end
    end
end

local function launchTest()
    if launched or isClient() or isServer() then return end
    local ok, err = pcall(function()
        local m = MainScreen and MainScreen.instance
        if not (m and not m.inGame and m.desc and CharacterCreationMain.instance) then return end
        if persistence.mode == "reload" then
            local name = persistence.world
            if type(name) ~= "string" or not name:match("^DC_AITeammate_[0-9]+$") then error("invalid reload world") end
            if not checkSaveFolderExists("Sandbox" .. getFileSeparator() .. name) then error("missing reload save") end
            launched = true
            testWorld = name
            print("DC_AITeammate: RELOAD world=" .. name .. " expected=" .. tostring(persistence.npcId))
            MainScreen.continueLatestSave("Sandbox", name)
            return
        end
        if selectedDebugScenario then return end
        local worldName = uniqueWorldName()
        testWorld = worldName
        if not worldName then error("no unique disposable world name available") end
        launched = true
        ActiveMods.getById("currentGame"):copyFrom(ActiveMods.getById("default"))
        m:setDefaultSandboxVars()
        selectedDebugScenario = scenario
        scenario.setSandbox()
        getWorld():setGameMode("Sandbox")
        getWorld():setMap(scenario.world)
        createWorld(worldName)
        GameWindow.doRenderEvent(false)
        Events.OnNewGame.Add(DebugScenarios.ongamestart)
        Events.LoadGridsquare.Add(DebugScenarios.onloadgs)
        forceChangeState(LoadingQueueState.new())
        print("DC_AITeammate: launching disposable world " .. worldName)
    end)
    if not ok then
        launched = false
        print("DC_AITeammate: launch aborted: " .. tostring(err))
    end
end

local started = false
local reportTicks = 0
local function startAdapter()
    if started then return end
    local player = getSpecificPlayer and getSpecificPlayer(0) or getPlayer()
    if not player then return end
    if SurvivalGuide and SurvivalGuide.instance and SurvivalGuide.instance:isVisible() then
        SurvivalGuide.instance:setVisible(false)
        if getGameSpeed() == 0 then setGameSpeed(1) end
    end
    if persistence.mode == "reload" then
        local p = getSpecificPlayer and getSpecificPlayer(0) or getPlayer()
        if not p then return end
        if recoveryChecked then return end
        recoveryChecked = true
        started = true
        if SurvivalGuide and SurvivalGuide.instance and SurvivalGuide.instance:isVisible() then
            SurvivalGuide.instance:setVisible(false)
            if getGameSpeed() == 0 then setGameSpeed(1) end
        end
        local id = p:getModData().DC_AI_TeammateNpcId
        print("DC_AITeammate: RECOVER saved id=" .. tostring(id) .. " expected=" .. tostring(persistence.npcId))
        require "DC_AI_Teammate"
        require "DC_AI_UIObserve"
        local ok, err = pcall(function()
            if tostring(id) ~= tostring(persistence.npcId) then error("saved identity does not match manifest") end
            local result = DC_AI_Teammate.start()
            if result ~= true or DC_AI_Teammate.state.phase ~= "recovered" then error("recovery start failed") end
            recoveryChecked = true
            print("DC_AITeammate: RECOVER result=true phase=recovered npc=" .. DC_AI_Teammate.state.npcId)
            local api = KnoxEventLoader.getAPI("npc")
            local list = api:getNpcs()
            for i = 0, list:size() - 1 do
                local meta = list:get(i)
                if tostring(meta:getId()) == id then
                    local w = meta:getWorldObject()
                    print("DC_AITeammate: RECOVER TELEMETRY member=" .. tostring(api:getGroup(p):inGroup(meta))
                        .. " goal=" .. tostring(meta:getGoalPretty()) .. " sub=" .. tostring(meta:getSubGoalPretty())
                        .. " npcX=" .. tostring(w and w:getX()) .. " npcY=" .. tostring(w and w:getY())
                        .. " playerX=" .. tostring(p:getX()) .. " playerY=" .. tostring(p:getY()))
                    require "DC_AI_CombatTest"
                end
            end
        end)
        if not ok then print("DC_AITeammate: RECOVER error=" .. tostring(err)) end
        return
    end
    started = true
    local ok, err = pcall(function()
        require "DC_AI_Teammate"
        require "DC_AI_UIObserve"
        local result = DC_AI_Teammate.start()
        print("DC_AITeammate: adapter start result=" .. tostring(result))
    end)
    if not ok then print("DC_AITeammate: adapter start error=" .. tostring(err)) end
    if ok and persistence.mode == "create" and persistence.combat then require "DC_AI_CombatTest" end
end

local commandStage = 0
local followingTicks = 0
local mailboxRequested = false
local movementDone = false
local movementStartX, movementStartY
Events.OnPlayerUpdate.Add(function()
    local ok, err = pcall(function()
        startAdapter()
        if persistence.mode == "reload" then return end
        reportTicks = reportTicks + 1
        if persistence.mode == "create" and reportTicks >= 1200 and not savedOnce then
            savedOnce = true
            local id = getPlayer():getModData().DC_AI_TeammateNpcId
            if not id or not testWorld then error("save identity unavailable") end
            local w = getFileWriter("dc_teammate_persistence.txt", true, false)
            w:write(testWorld .. "\n" .. tostring(id) .. "\n")
            w:close()
            print("DC_AITeammate: SAVE requested world=" .. testWorld .. " npc=" .. tostring(id))
            save(true)
            print("DC_AITeammate: SAVE returned; requesting normal desktop quit")
            setGameSpeed(1)
            pauseSoundAndMusic()
            setShowPausedMessage(true)
            getCore():quitToDesktop()
            return
        end
        local adapter = DC_AI_Teammate
        if not adapter then return end
        if adapter.state.phase == "following" or adapter.state.phase == "waiting" then
            followingTicks = followingTicks + 1
            if commandStage == 0 and followingTicks >= 60 then
                local result = adapter.wait()
                print("DC_AITeammate: WAIT result=" .. tostring(result))
                commandStage = 1
            elseif commandStage == 1 and followingTicks >= 180 then
                local result = adapter.follow()
                print("DC_AITeammate: FOLLOW result=" .. tostring(result))
                commandStage = 2
            elseif commandStage == 2 and not movementDone and followingTicks >= 300 then
                local p = getPlayer()
                movementStartX, movementStartY = p:getX(), p:getY()
                movementDone = true -- latch even if path setup fails
                require "TimedActions/WalkToTimedAction"
                local dest = getCell():getGridSquare(math.floor(movementStartX)+8, math.floor(movementStartY)+4, 0)
                if not dest or not dest:isFree(false) then error("walk destination not free") end
                ISTimedActionQueue.add(ISWalkToTimedAction:new(p, dest))
                print("DC_AITeammate: WALK requested from " .. tostring(movementStartX) .. "," .. tostring(movementStartY)
                    .. " to " .. tostring(dest:getX()) .. "," .. tostring(dest:getY()))
            end
        end
            if movementDone and not mailboxRequested and followingTicks >= 900 then
                mailboxRequested = true
                require "DC_AI_TeammateMailbox"
                print("DC_AITeammate: MAILBOX request=" .. tostring(DC_AI_TeammateMailbox.request(string.char(35831,22312,36825,37324,31561,24453,55357,56832))))
            end
        if reportTicks % 60 == 0 then
            if DC_AI_TeammateMailbox then
                local ms = DC_AI_TeammateMailbox.status()
                print("DC_AITeammate: MAILBOX phase=" .. tostring(ms.phase) .. " error=" .. tostring(ms.error))
            end
            adapter.status()
            local api = KnoxEventLoader.getAPI("npc")
            local list = api:getNpcs()
            for i = 0, list:size() - 1 do
                local meta = list:get(i)
                if tostring(meta:getId()) == adapter.state.npcId then
                    local w = meta:getWorldObject()
                    local p = getPlayer()
                    print("DC_AITeammate: TELEMETRY npc=" .. adapter.state.npcId
                        .. " member=" .. tostring(api:getGroup(p):inGroup(meta))
                        .. " goal=" .. tostring(meta:getGoalPretty())
                        .. " sub=" .. tostring(meta:getSubGoalPretty())
                        .. " npcX=" .. tostring(w and w:getX())
                        .. " npcY=" .. tostring(w and w:getY())
                        .. " playerX=" .. tostring(p:getX())
                        .. " playerY=" .. tostring(p:getY()))
                end
            end
        end
    end)
    if not ok then print("DC_AITeammate: test error=" .. tostring(err)) end
end)
-- Read-only diagnostic: render events continue even if gameplay is paused.
local lastRenderReport = 0
Events.OnRenderTick.Add(function()
    if not started then return end
    local now = getTimestampMs()
    if now - lastRenderReport < 5000 then return end
    lastRenderReport = now
    local ok, err = pcall(function()
        if NpcProcGenWorldMap_instance then
            print("DC_AITeammate: closing isolated Knox procgen setup without export")
            NpcProcGenWorldMap_instance:closeWithoutExport()
        end
        print("DC_AITeammate: RENDER speed=" .. tostring(getGameSpeed())
            .. " playerUpdates=" .. tostring(reportTicks)
            .. " menu=" .. tostring(MainScreen.instance and MainScreen.instance:getIsVisible())
            .. " guide=" .. tostring(SurvivalGuide and SurvivalGuide.instance and SurvivalGuide.instance:isVisible()))
    end)
    if not ok then print("DC_AITeammate: render diagnostic error=" .. tostring(err)) end
end)
Events.OnMainMenuEnter.Add(launchTest)
Events.OnTick.Add(function()
    if launched then return end
    local m = MainScreen and MainScreen.instance
    if m and m:getIsVisible() then launchTest() end
end)
