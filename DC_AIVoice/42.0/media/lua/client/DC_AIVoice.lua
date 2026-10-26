--[[============================================================================
  DC_AIVoice —— 阿D·AI 版
  版本 0.1

  把游戏状态写成一个小文件，交给外面的 bridge.py 去调大模型；
  模型回的话再由这个模组显示在屏幕上。

  为什么不用纯 Lua 直接发 HTTP：
    Project Zomboid 的 Lua 是 Kahlua（Lua 5.1 fork）+ 游戏自己暴露的 Java 对象，
    没有 socket / http / 线程。所以网络请求必须由外部进程做（见 README）。

  文件协议（都在 %USERPROFILE%\Zomboid\ 下，纯文本，UTF-8）：
    游戏 -> bridge : ai_state.txt    每行 key=value，含 seq / reason / 状态
    bridge -> 游戏 : ai_reply.txt    第一行 seq=<回应的 seq>，第二行 text=<一句话>

  没装 bridge 也能跑：等不到回应就用本地兜底台词，不会卡住。
============================================================================]]

local STATE_FILE   = "ai_state.txt"
local REPLY_FILE   = "ai_reply.txt"

local SEND_EVERY_MS = 45000   -- 最快多久发一次状态给 bridge
local POLL_EVERY_MS = 800     -- 多久看一眼有没有回信
local FALLBACK_MS   = 90000   -- 发出去这么久还没回信，就说本地兜底台词

local PREFIX = "【无线电】阿D："

local FALLBACK = {
    "……信号不太好。你还在吗？",
    "我这边听不清，先说一句：注意背后。",
    "喂？喂？……算了，你自己小心点。",
}

local seq = 0
local lastReplySeq = 0
local lastSendAt = 0
local lastPollAt = 0
local pendingSeq = nil
local pendingAt = 0
local lastText = nil
local fallbackIndex = 0

-- 小工具 ---------------------------------------------------------------------

local function log(msg)
    if print then print("[DC_AIVoice] " .. tostring(msg)) end
end

local function nowMs()
    if getTimestampMs then
        local ok, t = pcall(getTimestampMs)
        if ok and t then return t end
    end
    local ok, t = pcall(getTimestamp)
    if ok and t then return t * 1000 end
    return 0
end

local function moodleLevel(player, name)
    local ok, level = pcall(function()
        local mt = MoodleType[name]
        if not mt then return -1 end
        return player:getMoodles():getMoodleLevel(mt)
    end)
    if ok and level then return level end
    return -1
end

local function healthOf(player)
    local ok, h = pcall(function() return player:getHealth() end)
    if ok and h then return h end
    return 1
end

local function isOutside(player)
    local ok, out = pcall(function() return player:isOutside() end)
    return ok and out
end

local function round2(v)
    return string.format("%.2f", v)
end

-- 写状态给 bridge -------------------------------------------------------------

local function writeState(reason)
    local player = getPlayer()
    if not player then return false end

    seq = seq + 1
    local time = getGameTime()
    local rows = {}

    local function add(k, v) rows[#rows + 1] = k .. "=" .. tostring(v) end

    add("seq", seq)
    add("reason", reason or "tick")
    add("hour", time:getHour())
    add("days", time:getNightsSurvived())
    add("health", round2(healthOf(player)))
    add("hunger", moodleLevel(player, "FOOD_EATEN"))
    add("thirst", moodleLevel(player, "THIRST"))
    add("tired", moodleLevel(player, "TIRED"))
    add("pain", moodleLevel(player, "PAIN"))
    add("panic", moodleLevel(player, "PANIC"))
    add("outside", isOutside(player) and 1 or 0)

    pcall(function()
        add("x", math.floor(player:getX()))
        add("y", math.floor(player:getY()))
    end)

    pcall(function()
        local weapon = player:getPrimaryHandItem()
        if weapon then add("weapon", weapon:getDisplayName()) end
    end)

    local payload = table.concat(rows, "\n") .. "\n"
    local ok = pcall(function()
        local writer = getFileWriter(STATE_FILE, true, false)
        if not writer then return end
        writer:write(payload)
        writer:close()
    end)

    if ok then
        lastSendAt = nowMs()
        pendingSeq = seq
        pendingAt = nowMs()
    else
        log("write state failed")
    end
    return ok
end

-- 读 bridge 的回信 ------------------------------------------------------------

local function readReply()
    local ok, lines = pcall(function()
        local reader = getFileReader(REPLY_FILE, false)
        if not reader then return nil end
        local collected = {}
        while true do
            local line = reader:readLine()
            if not line then break end
            collected[#collected + 1] = line
        end
        reader:close()
        return collected
    end)

    if not ok or not lines or #lines == 0 then return nil end

    local replySeq = 0
    local text = nil
    local sound = nil
    local wav = nil
    for _, line in ipairs(lines) do
        local k, v = line:match("^([%w_]+)=(.*)$")
        if k == "seq" then
            replySeq = tonumber(v) or 0
        elseif k == "text" then
            text = v
        elseif k == "sound" then
            sound = v
        elseif k == "wav" then
            wav = v
        end
    end
    if replySeq > 0 and text and #text > 0 then return replySeq, text, sound, wav end
    return nil
end

-- 显示 -----------------------------------------------------------------------

local function speakLine(text)
    local ok = pcall(function()
        local player = getPlayer()
        if player then HaloTextHelper.addText(player, PREFIX .. text) end
    end)
    if ok then lastText = text end
    return ok
end

local function playVoice(soundName, player)
    if not soundName or soundName == "" then return false end
    local ok = pcall(function()
        local square = player:getSquare()
        if square then
            -- 在玩家脚下播，带 3D 定位；radius 大一点，别走两步就听不见
            getSoundManager():PlayWorldSoundWav(soundName, square, 1.0, 22.0, 1.0, true)
        else
            getSoundManager():PlaySound(soundName, false, 1.0)
        end
    end)
    if ok then return true end
    return pcall(function() getSoundManager():PlaySound(soundName, false, 1.0) end)
end

local function fallbackLine()
    fallbackIndex = fallbackIndex % #FALLBACK + 1
    speakLine(FALLBACK[fallbackIndex])
end

-- 事件 -----------------------------------------------------------------------

local function onGameStart()
    log("started")
    seq = 0
    lastReplySeq = 0
    lastSendAt = 0
    pendingSeq = nil
    writeState("start")
end

local function onTenMinutes()
    if nowMs() - lastSendAt < SEND_EVERY_MS then return end
    writeState("tick")
end

local function onPlayerUpdate()
    local now = nowMs()
    if now - lastPollAt < POLL_EVERY_MS then return end
    lastPollAt = now

    local replySeq, text, sound, wav = readReply()
    if replySeq then
        if replySeq > lastReplySeq and text ~= lastText then
            lastReplySeq = replySeq
            pendingSeq = nil
            speakLine(text)
            local player = getPlayer()
            if player then
                local played = false
                if wav and wav ~= "" and DCAgentPlay then
                    local ok, result = pcall(DCAgentPlay, wav)
                    played = ok and result == "ok"
                end
                if not played then playVoice(sound, player) end
            end
        end
    elseif pendingSeq and (now - pendingAt) > FALLBACK_MS then
        pendingSeq = nil
        fallbackLine()
    end
end

Events.OnGameStart.Add(onGameStart)
Events.EveryTenMinutes.Add(onTenMinutes)
Events.OnPlayerUpdate.Add(onPlayerUpdate)
