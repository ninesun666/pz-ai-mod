-- Retired prototype: disabled before requires, UI creation or event registration.
-- Preserved in Git history for reference; not part of the standalone companion.
do return end

-- dsh-pet style companion overlay (assets MIT, github.com/PC2005-cloud/dsh-pet;
-- whale-girl assets MIT, github.com/huangdsa45/dsh_feiyu).
-- Draws ONLY the animated pet texture anchored to the AI teammate's screen
-- position. Uses ISUIElement (no background, no mouse capture) so the game
-- stays fully clickable. Disable with global DC_AI_PetOverlayOff = true.

require "ISUI/ISUIElement"

DC_AI_PetOverlay = DC_AI_PetOverlay or {}
local P = DC_AI_PetOverlay

local STATES = { "idle", "run", "sleep" }
local counts = {}
local function countFrames(state)
    if counts[state] then return counts[state] end
    local n = 0
    for i = 1, 99 do
        if not getTexture(string.format("DCPet_%s_%02d", state, i)) then break end
        n = i
    end
    counts[state] = n
    return n
end

local function npcWorldObject()
    local m = DC_AI_Teammate
    if not m or not m.spawnedMeta then return nil end
    local meta = m.spawnedMeta
    if meta.getWorldObject then
        local w = meta:getWorldObject()
        if w then return w end
    end
    return nil
end

local panel = nil

local PetEl = ISUIElement:derive("DCPetElement")

function PetEl:initialise()
    ISUIElement.initialise(self)
    self.ignoreMouse = true
    self.anchorTop = true
    self.anchorLeft = true
end

-- Force mouse pass-through: never consume any UI event.
function PetEl:onMouseDown(x, y) return false end
function PetEl:onMouseUp(x, y) return false end
function PetEl:onMouseUpOutside(x, y) return false end
function PetEl:onMouseRightDown(x, y) return false end
function PetEl:onMouseRightUp(x, y) return false end
function PetEl:onMouseRightDrag(x, y) return false end
function PetEl:onMouseMove(x, y, dx, dy) return false end
function PetEl:onMouseMoveOutside(x, y, dx, dy) return false end
function PetEl:onMouseWheel(x, y) return false end
function PetEl:isMouseOver() return false end
function PetEl:isOver(x, y) return false end

function PetEl:prerender()
    if DC_AI_PetOverlayOff then return end
    local m = DC_AI_Teammate
    if not m or not m.spawnedMeta or not m.state or m.state.phase == "idle" then return end
    local w = npcWorldObject()
    if not w then return end
    local sx, sy
    local ok = pcall(function() sx = w:getScreenX(); sy = w:getScreenY() end)
    if not ok or not sx or not sy then
        ok = pcall(function()
            sx = IsoUtils.worldToScreenX(w:getX(), w:getY(), w:getZ())
            sy = IsoUtils.worldToScreenY(w:getX(), w:getY(), w:getZ())
        end)
    end
    if not ok or not sx or not sy then
        if not P.warned then P.warned = true; print("[DC_AI_PetOverlay] no screen-coordinate API found") end
        return
    end
    local t = (getTimestampMs and getTimestampMs() or 0)
    local state = "idle"
    if m.state and m.state.phase == "waiting" then
        state = "sleep"
    else
        local wx, wy = w:getX(), w:getY()
        if P.lastT and t - P.lastT >= 250 then
            local dx, dy = wx - (P.lastX or wx), wy - (P.lastY or wy)
            if (dx * dx + dy * dy) > 0.02 then state = "run" end
            P.lastX, P.lastY, P.lastT = wx, wy, t
        elseif not P.lastT then
            P.lastX, P.lastY, P.lastT = wx, wy, t
        end
    end
    local n = countFrames(state)
    if n < 1 then return end
    local idx = 1 + (math.floor(t / 125) % n)
    local tex = getTexture(string.format("DCPet_%s_%02d", state, idx))
    if not tex then return end
    local uiw, uih = self:getWidth(), self:getHeight()
    local th = math.floor(uih * 0.22)
    local tw = math.floor(th * tex:getWidth() / tex:getHeight())
    local px = math.floor(sx * uiw / 1280) - math.floor(tw / 2)
    local py = math.floor(sy * uih / 720) - th - 10
    self:drawTexture(tex, px, py, 0.85, 1, 1, 1)
end

local function ensurePanel()
    if panel then return end
    local w = getCore():getScreenWidth()
    local h = getCore():getScreenHeight()
    panel = PetEl:new(0, 0, w, h)
    panel:initialise()
    panel:addToUIManager()
    print("[DC_AI_PetOverlay] element ready (transparent, mouse-through) " .. tostring(w) .. "x" .. tostring(h))
end

Events.OnGameStart.Add(ensurePanel)
