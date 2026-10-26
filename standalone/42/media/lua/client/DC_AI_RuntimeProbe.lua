-- Independent runtime capability probe; never creates UI or captures input.
local checked = false
Events.OnTick.Add(function()
    if type(DCStandaloneTick) ~= "function" then
        if not checked then
            checked = true
            print("[DCStandalone] runtime missing: actor features remain disabled")
        end
        return
    end
    DCStandaloneTick()
end)
