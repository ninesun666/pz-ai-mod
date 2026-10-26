-- Opt-in teammate UI. Numeric Unicode avoids native Lua compiler corruption.
require "ISUI/ISTextBox"
require "DC_AI_Teammate"
require "DC_AI_TeammateMailbox"
local function U(...)
    local ok, text = pcall(string.char, ...)
    if ok then return text end
    return utf8.char(...)
end
local phases = {
    ["idle"] = U(23578,26410,21551,21160),
    ["spawning"] = U(27491,22312,25307,21215),
    ["following"] = U(27491,22312,36319,38543),
    ["waiting"] = U(21407,22320,31561,24453),
    ["recovered"] = U(24050,24674,22797,38431,21451),
    ["pending"] = U(31561,24453,27169,22411,22238,22797),
    ["complete"] = U(24050,23436,25104),
    ["error"] = U(21457,29983,38169,35823),
}
local errors = {
    ["request already pending"] = U(19978,19968,26465,35831,27714,23578,26410,23436,25104,65292,35831,31245,20505),
    ["invalid request text"] = U(36755,20837,26080,25928,65306,35831,21247,20351,29992,25442,34892,25110,25511,21046,23383,31526,65292,25991,23383,19981,24471,36229,36807,53,49,50,20010,85,84,70,45,56,23383,33410),
    ["teammate not ready"] = U(35831,20808,25307,21215,25110,24674,22797,38431,21451),
    ["pending request timeout"] = U(27169,22411,22238,22797,36229,26102,65292,35831,26816,26597,26725,25509,31243,24207,21644,32593,32476),
    ["reply does not match pending identity"] = U(24050,25298,32477,26087,22238,22797,25110,36523,20221,19981,21305,37197,30340,22238,22797,65292,32487,32493,31561,24453,26377,25928,22238,22797),
    ["action completed; teammate speech unavailable"] = U(21160,20316,24050,25191,34892,65292,20294,38431,21451,26242,26102,26080,27861,35828,35805),
    ["npc API unavailable"] = U(78,80,67,25509,21475,19981,21487,29992,65292,35831,26816,26597,20381,36182,26159,21542,21551,29992),
    ["no player"] = U(29609,23478,23578,26410,36733,20837),
    ["player must be on ground floor z=0"] = U(35831,22312,22320,38754,23618,25307,21215,38431,21451),
    ["saved teammate unavailable"] = U(23384,26723,20013,30340,38431,21451,23578,19981,21487,29992),
    ["saved teammate is not in player group"] = U(23384,26723,20013,30340,38431,21451,19981,22312,20320,30340,38431,20237,20013),
    ["teammate not in group"] = U(38431,21451,19981,22312,20320,30340,38431,20237,20013),
    ["teammate world not ready"] = U(38431,21451,25152,22312,21306,22495,23578,26410,36733,20837),
    ["adjacent spawn square not loaded"] = U(38468,36817,29983,25104,20301,32622,23578,26410,36733,20837),
    ["adjacent spawn square is not free"] = U(38468,36817,27809,26377,21487,29992,30340,29983,25104,20301,32622),
    ["spawn timeout"] = U(25307,21215,36229,26102),
    ["adapter unavailable"] = U(38431,21451,27169,22359,19981,21487,29992),
    ["adapter has an error"] = U(38431,21451,27169,22359,20986,29616,38169,35823,65292,35831,26597,30475,29366,24577),
    ["remembered teammate identity mismatch"] = U(38431,21451,36523,20221,19981,19968,33268,65292,24050,25298,32477,25805,20316),
    ["ambiguous teammate identity"] = U(21457,29616,37325,22797,38431,21451,36523,20221,65292,24050,25298,32477,25805,20316),
    ["adapter command failed"] = U(38431,21451,26410,33021,25191,34892,25351,20196),
    ["sequence exhausted"] = U(35831,27714,24207,21495,24050,29992,23613,65292,35831,37325,26032,36827,20837,28216,25103),
    ["reply too large"] = U(27169,22411,22238,22797,36807,38271,65292,24050,25298,32477),
    ["action not allowed"] = U(27169,22411,21160,20316,19981,21463,25903,25345,65292,24050,25298,32477),
    ["invalid text"] = U(22238,22797,25991,23383,26684,24335,26080,25928),
    ["invalid identity"] = U(22238,22797,36523,20221,26684,24335,26080,25928),
    ["invalid sequence"] = U(22238,22797,24207,21495,26684,24335,26080,25928),
    ["invalid, duplicate or unknown field"] = U(22238,22797,21253,21547,26080,25928,12289,37325,22797,25110,26410,30693,23383,27573),
    ["expected exactly five fields"] = U(22238,22797,26684,24335,38169,35823,65292,24517,39035,21253,21547,20116,20010,23383,27573),
    ["teammate unavailable"] = U(38431,21451,26242,19981,21487,29992),
}
local function localizedError(err)
    if not err then return U(27491,24120) end
    return errors[tostring(err)] or U(21457,29983,20869,37096,38169,35823,65292,35831,26597,30475,28216,25103,26085,24535)
end
local function localizedPhase(phase)
    return phases[phase] or U(26410,30693,29366,24577)
end
local function notify(text)
    local p = getPlayer()
    if p then HaloTextHelper.addText(p, tostring(text)) end
end
local function command(action)
    local ok
    if action == "start" then ok = DC_AI_Teammate.start()
    elseif action == "follow" then ok = DC_AI_Teammate.follow()
    elseif action == "wait" then ok = DC_AI_Teammate.wait() end
    if not ok then notify(localizedError(DC_AI_Teammate.state.error or "teammate unavailable")) end
end
local function submit(_, button)
    if button.internal ~= "OK" then return end
    local text = button.parent.entry:getText()
    if not DC_AI_TeammateMailbox.request(text) then
        notify(localizedError(DC_AI_TeammateMailbox.status().error or "adapter command failed"))
    else
        notify(U(35831,27714,24050,21457,36865,65292,27491,22312,31561,24453,27169,22411,22238,22797,12290))
    end
end
local function talk()
    local box = ISTextBox:new(0, 0, 420, 180, U(19982,32,65,73,32,38431,21451,23545,35805,65288,38656,35201,27169,22411,26725,25509,31243,24207,65289), "", nil, submit, 0)
    box:initialise()
    if box.yes then box.yes:setTitle(U(30830,23450)) end
    if box.no then box.no:setTitle(U(21462,28040)) end
    box:addToUIManager()
end
Events.OnFillWorldObjectContextMenu.Add(function(playerIndex, context, objects, test)
    if test or playerIndex ~= 0 or isClient() or isServer() then return end
    local root = context:addOption(U(65,73,32,38431,21451), nil, nil)
    local menu = ISContextMenu:getNew(context)
    context:addSubMenu(root, menu)
    menu:addOption(U(25307,21215,65295,24674,22797,38431,21451), "start", command)
    menu:addOption(U(36319,38543,25105), "follow", command)
    menu:addOption(U(22312,36825,37324,31561,24453), "wait", command)
    menu:addOption(U(19982,38431,21451,23545,35805), nil, talk)
    menu:addOption(U(29366,24577), nil, function()
        local s = DC_AI_Teammate.state
        local m = DC_AI_TeammateMailbox.status()
        notify(localizedPhase(s.phase) .. " / " .. localizedPhase(m.phase) .. " / " .. localizedError(s.error or m.error))
    end)
end)
