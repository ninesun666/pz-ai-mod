-- Native context-menu only: no keyboard conflicts, mouse handlers or overlay.
require "DC_AI_Standalone"
local M = DC_AI_Standalone
local labels = {
    follow = "大肥鱼：跟随",
    hold = "大肥鱼：停留",
    retreat = "大肥鱼：重新集合",
}

local function dispatch(_, intent)
    -- Revalidate at selection time: readiness can change after the menu opens.
    if not M.canCommand() then return end
    M.command(intent)
end

local function fill(playerIndex, context, worldobjects, test)
    if test then return end
    -- The current registry supports primary local player only, not split-screen.
    if playerIndex ~= 0 or not getSpecificPlayer(0) then return end
    for _, intent in ipairs({"follow", "hold", "retreat"}) do
        local option = context:addOption(labels[intent], nil, dispatch, intent)
        if not M.canCommand() then
            option.notAvailable = true
            option.name = labels[intent] .. "（实体尚未就绪）"
        end
    end
end

Events.OnFillWorldObjectContextMenu.Add(fill)
