-- Independent runtime capability probe; never creates UI or captures input.
local checked = false
local constructorChecked = false
local function onTick()
    if DCStandaloneTick == nil then
        if not checked then
            checked = true
            print("[DCStandalone] runtime missing: actor features remain disabled")
        end
        return
    end
    DCStandaloneTick()
    if not constructorChecked and DCStandaloneProbeConstructor ~= nil then
        constructorChecked = true
        local ok, result = pcall(DCStandaloneProbeConstructor)
        if not ok then
            print("[DCStandalone] detached constructor probe failed: " .. tostring(result))
        elseif result ~= true then
            print("[DCStandalone] detached constructor probe returned non-true")
        end
    end
end
if Events and Events.OnTick then Events.OnTick.Add(onTick) end
-- The game can sit paused (focus loss, speed 0) during automated runs; this
-- engine event keeps probes ticking so acceptance does not stall.
if Events and Events.OnTickEvenPaused then Events.OnTickEvenPaused.Add(onTick) end
