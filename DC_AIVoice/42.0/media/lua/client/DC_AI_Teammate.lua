-- Retired prototype: disabled before requires, UI creation or event registration.
-- Preserved in Git history for reference; not part of the standalone companion.
do return end

-- AI teammate adapter for Knox Event Expanded NPC.
-- All calls must run on the game's main Lua thread.
-- This module does not heal, enable god mode, or alter damage.

DC_AI_Teammate = DC_AI_Teammate or {}
DC_AI_Teammate.version = "0.2-test"
DC_AI_Teammate.state = DC_AI_Teammate.state or { phase = "idle", error = nil, npcId = nil, startedAt = 0 }

local M = DC_AI_Teammate
local timeoutMs = 30000

local function nowMs()
    if getTimestampMs then return getTimestampMs() end
    return math.floor((getTimestamp and getTimestamp() or 0) * 1000)
end

local function log(s)
    print("[DC_AI_Teammate] " .. tostring(s))
end

local function fail(s)
    M.state.phase = "error"
    M.state.error = tostring(s)
    log("ERROR " .. tostring(s))
    return false
end

local function npcApi()
    if not KnoxEventLoader or not KnoxEventLoader.getAPI then return nil end
    return KnoxEventLoader.getAPI("npc")
end

local function listIds(api)
    local ids = {}
    local list = api:getNpcs()
    if list then
        for i = 0, list:size() - 1 do
            local n = list:get(i)
            if n and n.getId then ids[tostring(n:getId())] = true end
        end
    end
    return ids
end

local function findNewMeta(api, before)
    local list = api:getNpcs()
    if not list then return nil end
    local found = nil
    for i = 0, list:size() - 1 do
        local n = list:get(i)
        if n and n.getId and not before[tostring(n:getId())] then
            if found then error("ambiguous spawn: multiple new NPCs; refusing recruitment") end
            found = n
        end
    end
    return found
end

local function findSavedMeta(api, id)
    if not id then return nil end
    local list = api:getNpcs()
    if not list then return nil end
    for i = 0, list:size() - 1 do
        local n = list:get(i)
        if n and n.getId and tostring(n:getId()) == tostring(id) then return n end
    end
    return nil
end

local function savedNpcId(player)
    if not player or not player.getModData then return nil end
    local data = player:getModData()
    return data and data.DC_AI_TeammateNpcId
end

local function checkedMeta(api, player, id)
    if not player then return nil, "no player" end
    local meta = findSavedMeta(api, id)
    if not meta then return nil, "saved teammate unavailable" end
    local group = api:getGroup(player)
    if not group or not group:inGroup(meta) then
        return nil, "saved teammate is not in player group"
    end
    local world = meta:getWorldObject()
    if not world or not world:getSquare() then return nil, "teammate world not ready" end
    return meta
end

local function applySquad(api, player)
    local squad = api:getSquad(player)
    if not squad then return false, "squad unavailable" end
    squad:setWeaponPreference(WeaponPreference.ANY)
    squad:setWeaponReady(WeaponReady.READY)
    squad:setFollowDistance(FollowDistance.BALANCED)
    squad:setFightStance(FightStance.STAY)
    return true
end

local function persistNpcId(player, id)
    if not player or not player.getModData then return false end
    local data = player:getModData()
    if not data then return false end
    data.DC_AI_TeammateNpcId = tostring(id)
    return true
end

local function finish(meta, player)
    local api = npcApi()
    if not api then return fail("npc API unavailable") end
    local exactId = meta:getId()
    M.state.npcId = tostring(exactId)
    M.spawnedMeta = meta
    local group = api:getGroup(player)
    if not group then return fail("group unavailable") end
    group:joinGroup(meta, true)
    if not group:inGroup(meta) then return fail("joinGroup did not establish membership") end
    group:sendToGroup(meta)
    if meta.switchDialogueTree then meta:switchDialogueTree("GroupDialogue") end
    meta:setGoal("RoamingSubTree")
    meta:setSubGoal("FollowSubTree")
    local ok, err = applySquad(api, player)
    if not ok then return fail(err) end
    M.state.phase = "following"
    M.state.error = nil
    persistNpcId(player, M.state.npcId)
    log("following npc=" .. M.state.npcId .. " goal=" .. tostring(meta:getGoalPretty()) .. " sub=" .. tostring(meta:getSubGoalPretty()))
    return true
end

local function startImpl()
    if M.spawnAttempted then return false end
    if M.state.phase ~= "idle" then return false end
    local player = getPlayer()
    if not player then return fail("no player") end
    local pz = player:getZ()
    if pz ~= 0 then return fail("player must be on ground floor z=0") end
    local api = npcApi()
    if not api then return fail("npc API unavailable") end
    if not api:getGroup(player) then return fail("group unavailable before spawn") end
    if not api:getSquad(player) then return fail("squad unavailable before spawn") end
    local savedId = savedNpcId(player)
    if savedId then
        local recovered, recoverErr = checkedMeta(api, player, savedId)
        if recovered then
            M.state.npcId = tostring(recovered:getId())
            M.spawnedMeta = recovered
            M.state.phase = "recovered"
            M.state.error = nil
            log("recovered npc=" .. M.state.npcId)
            return true
        end
        log("saved id " .. tostring(savedId) .. " unusable (" .. tostring(recoverErr) .. "); clearing and spawning fresh")
        local data = player:getModData()
        if data then data.DC_AI_TeammateNpcId = nil end
    end
    M.before = listIds(api)
    local sq = player:getSquare()
    if not sq then return fail("player square unavailable") end
    local offsets = { {1,0}, {-1,0}, {0,1}, {0,-1}, {1,1}, {-1,-1} }
    local target
    for _, off in ipairs(offsets) do
        local cand = getCell():getGridSquare(sq:getX() + off[1], sq:getY() + off[2], sq:getZ())
        if cand and cand:isFree(false) then target = cand break end
    end
    if not target then return fail("adjacent spawn square is not free") end
    local x, y, z = target:getX(), target:getY(), target:getZ()
    M.state = { phase = "spawning", error = nil, npcId = nil, startedAt = nowMs() }
    M.spawnAttempted = true
    local spawned
    local ok, err = pcall(function() spawned = api:spawnNpc("SurvivorNpc", x, y) end)
    if not ok then return fail("spawn failed: " .. tostring(err)) end
    M.spawnedMeta = spawned
    if spawned and spawned.getId and spawned:getId() ~= -1 then
        M.state.npcId = tostring(spawned:getId())
        persistNpcId(player, M.state.npcId)
    end
    log("spawn requested at " .. tostring(x) .. "," .. tostring(y) .. " returned=" .. tostring(spawned ~= nil))
    return true
end

function M.start()
    local ok, result = pcall(startImpl)
    if not ok then return fail(result) end
    return result
end

function M.tick()
    if M.state.phase ~= "spawning" then return end
    if nowMs() - M.state.startedAt > timeoutMs then return fail("spawn timeout") end
    local player = getPlayer()
    local api = npcApi()
    if not player or not api then return fail("player/API disappeared") end
    local meta
    if M.spawnedMeta and M.spawnedMeta.getId and M.spawnedMeta:getId() ~= -1 then
        meta = M.spawnedMeta
    else
        meta = findNewMeta(api, M.before)
    end
    if not meta then return end
    M.spawnedMeta = meta
    M.state.npcId = tostring(meta:getId())
    persistNpcId(player, M.state.npcId)
    local world = meta:getWorldObject()
    if not world then return end
    finish(meta, player)
end

local function commandNpc(player)
    local api = npcApi()
    if not api then return nil, "npc API unavailable" end
    local id = M.state.npcId or savedNpcId(player)
    local meta, err = checkedMeta(api, player, id)
    if not meta then return nil, err end
    return meta
end

local function followImpl()
    local meta, err = commandNpc(getPlayer())
    if not meta then return fail(err) end
    if not tellNpcFollow then return fail("tellNpcFollow unavailable") end
    local ok, callErr = pcall(tellNpcFollow, nil, meta)
    if not ok then return fail(callErr) end
    meta:setGoal("RoamingSubTree")
    meta:setSubGoal("FollowSubTree")
    M.state.phase, M.state.error = "following", nil
    return true
end

local function waitImpl()
    local player = getPlayer()
    local meta, err = commandNpc(player)
    if not meta then return fail(err) end
    if not tellNpcStay then return fail("tellNpcStay unavailable") end
    local sq = meta:getWorldObject() and meta:getWorldObject():getSquare()
    if not sq then return fail("teammate square unavailable") end
    local ok, callErr = pcall(tellNpcStay, meta, sq:getX(), sq:getY(), sq:getZ())
    if not ok then return fail(callErr) end
    M.state.phase, M.state.error = "waiting", nil
    return true
end

function M.follow()
    local ok, result = pcall(followImpl)
    if not ok then return fail(result) end
    return result
end

function M.wait()
    local ok, result = pcall(waitImpl)
    if not ok then return fail(result) end
    return result
end

function M.status()
    local s = M.state
    print("[DC_AI_Teammate] phase=" .. tostring(s.phase) .. " npcId=" .. tostring(s.npcId) .. " error=" .. tostring(s.error))
    return s
end

local function pollTick()
    local ok, err = pcall(M.tick)
    if not ok then fail(err) end
end

Events.OnTick.Add(pollTick)
Events.OnGameTimeLoaded.Add(function() log("loaded; call DC_AI_Teammate.start() on main thread") end)

-- Auto-teammate on world entry. Set global DC_AI_TeammateAutoStart = false to disable.
-- Priority: recover a saved teammate (resume following) > re-join an orphaned saved
-- teammate > spawn a fresh teammate on an adjacent square. Runs once per session.
local autoStarted = false
local function autoStartTick()
    if autoStarted then return end
    if DC_AI_TeammateAutoStart == false then autoStarted = true return end
    local player = getPlayer()
    if not player or player:getZ() ~= 0 then return end
    local api = npcApi()
    if not api or not api:getGroup(player) or not api:getSquad(player) then return end
    local savedId = savedNpcId(player)
    if savedId then
        local meta = findSavedMeta(api, savedId)
        if meta then
            local checked, err = checkedMeta(api, player, savedId)
            if checked then
                autoStarted = true
                M.follow()
                log("AUTO recovered following npc=" .. tostring(checked:getId()))
                return
            end
            if err == "saved teammate is not in player group" then
                autoStarted = true
                finish(meta, player)
                log("AUTO rejoined saved npc=" .. tostring(meta:getId()))
                return
            end
            log("AUTO saved npc invalid (" .. tostring(err) .. "); clearing id and spawning fresh")
        end
        local data = player:getModData()
        if data then data.DC_AI_TeammateNpcId = nil end
    end
    autoStarted = true
    M.start()
    log("AUTO spawn requested beside player")
end
Events.OnTick.Add(function() local ok, e = pcall(autoStartTick); if not ok then log("AUTO error " .. tostring(e)); autoStarted = true end end)
