-- Independent companion registry and command state.
-- This first vertical slice owns identity and local intent only; it does not
-- create a fake survivor, overlay, or call Knox/ZombieBuddy.
DC_AI_Standalone = DC_AI_Standalone or {}
local M = DC_AI_Standalone
M.SCHEMA = 1
M.state = {
    phase = "disabled",
    intent = "hold",
    companionId = nil,
    assetId = "deepseek_whale_girl",
    error = nil,
}

local function player()
    return getPlayer and getPlayer() or nil
end

local function uuidPart()
    if not ZombRand then error("identity random source unavailable") end
    return string.format("%08x", ZombRand(0, 0x7fffffff))
end

local function newId()
    return "dc-whale-" .. uuidPart() .. "-" .. uuidPart()
end

local boundPlayer = nil
local started = false
local function bindPlayer(p)
    if boundPlayer == p then return end
    boundPlayer = p
    started = false
    M.state.phase = "disabled"
    M.state.intent = "hold"
    M.state.companionId = nil
    M.state.assetId = "deepseek_whale_girl"
    M.state.error = nil
end

local function data()
    local p = boundPlayer or player()
    return p and p.getModData and p:getModData() or nil
end

local function saveIdentity()
    local d = data()
    if not d then return false end
    d.DC_AI_Standalone = d.DC_AI_Standalone or {}
    d.DC_AI_Standalone.schema = M.SCHEMA
    d.DC_AI_Standalone.companionId = M.state.companionId
    d.DC_AI_Standalone.assetId = M.state.assetId
    d.DC_AI_Standalone.intent = M.state.intent
    return true
end

local function restoreIdentity()
    local d = data()
    local saved = d and d.DC_AI_Standalone
    if type(saved) ~= "table" then return false end
    if type(saved.companionId) ~= "string" or saved.companionId == "" then return false end
    M.state.companionId = saved.companionId
    if type(saved.assetId) == "string" and saved.assetId ~= "" then M.state.assetId = saved.assetId end
    if saved.intent == "follow" or saved.intent == "hold" or saved.intent == "retreat" then
        M.state.intent = saved.intent
    else
        M.state.intent = "hold"
    end
    M.state.phase = "identity-restored"
    M.state.error = nil
    return true
end

function M.ensureIdentity()
    local p = player()
    bindPlayer(p)
    if not p then return false end
    local d = data()
    if not d then return false end
    if M.state.companionId then return saveIdentity() end
    local saved = d.DC_AI_Standalone
    if saved ~= nil then
        if type(saved) ~= "table" or saved.schema ~= M.SCHEMA then
            M.state.error = "unsupported identity schema"
            return false
        end
        if restoreIdentity() then return true end
        M.state.error = "invalid saved identity"
        return false
    end
    M.state.companionId = newId()
    M.state.phase = "identity-created"
    return saveIdentity()
end

function M.canCommand()
    -- No live identity-bound locomotion executor is connected yet.
    return false
end

function M.command(intent)
    M.state.error = "actor unavailable"
    return false
end

function M.status()
    return M.state
end

local function onWorldTick()
    local p = player()
    if not p then return end
    bindPlayer(p)
    if started then return end
    if not M.ensureIdentity() then return end
    started = true
    print("[DC_AI_Standalone] registry ready id=" .. tostring(M.state.companionId) ..
        " asset=" .. tostring(M.state.assetId) .. " intent=" .. tostring(M.state.intent))
end

if Events and Events.OnTick then Events.OnTick.Add(onWorldTick) end
