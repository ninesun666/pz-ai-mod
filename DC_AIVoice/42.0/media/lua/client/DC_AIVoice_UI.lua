--[[============================================================================
  DC_AIVoice 的左上角小面板 + 按 F7 说话

  bridge 写 %USERPROFILE%\Zomboid\aiv_ui.txt，格式：
      status=idle|listening|thinking
      line=21:40|别在城里磨蹭了
      line=21:52|……

  这个文件只负责“显示”和“按键”，不做任何网络/音频的事。
============================================================================]]

local UI_FILE    = "aiv_ui.txt"
local VOICE_FILE = "aiv_voice.txt"

local PANEL_X, PANEL_Y = 14, 62
local PANEL_W, PANEL_H = 430, 150
local REFRESH_MS = 400
local MAX_LINES  = 4

local panel = nil

local function readTextFile(name)
    local ok, lines = pcall(function()
        local reader = getFileReader(name, false)
        if not reader then return nil end
        local out = {}
        while true do
            local line = reader:readLine()
            if not line then break end
            out[#out + 1] = line
        end
        reader:close()
        return out
    end)
    if ok then return lines end
    return nil
end

local function writeTextFile(name, text)
    return pcall(function()
        local writer = getFileWriter(name, true, false)
        if not writer then return end
        writer:write(text)
        writer:close()
    end)
end

local function fit(font, text, maxWidth)
    if not text then return "" end
    local tm = getTextManager()
    if tm:MeasureStringX(font, text) <= maxWidth then return text end
    local s = text
    while #s > 1 and tm:MeasureStringX(font, s .. "...") > maxWidth do
        s = s:sub(1, #s - 1)
    end
    return s .. "..."
end

DCAI_UI = ISUIElement:derive("DCAI_UI")

function DCAI_UI:new(x, y, w, h)
    local o = ISUIElement.new(self, x, y, w, h)
    o.status = "idle"
    o.lines = {}
    o.lastRead = 0
    o.wantMouseEvents = false
    return o
end

function DCAI_UI:refresh()
    local data = readTextFile(UI_FILE)
    if not data then return end
    local lines = {}
    for _, raw in ipairs(data) do
        local key, value = raw:match("^([%w_]+)=(.*)$")
        if key == "status" then
            self.status = value
        elseif key == "line" then
            local t, text = value:match("^([^|]*)|(.*)$")
            if text then lines[#lines + 1] = { time = t, text = text } end
        end
    end
    self.lines = lines
end

function DCAI_UI:prerender()
    local now = getTimestamp()
    if now - (self.lastRead or 0) > REFRESH_MS then
        self.lastRead = now
        self:refresh()
    end

    local font = UIFont.Small
    local w, h = self.width, self.height

    self:drawRect(0, 0, w, h, 0.66, 0.04, 0.05, 0.06)
    self:drawRectBorder(0, 0, w, h, 0.95, 0.22, 0.40, 0.32)

    self:drawText("阿D  无线电", 10, 6, 0.62, 0.95, 0.72, 1, font)
    self:drawText(fit(font, "按 F7 说话", 110), w - 120, 6, 0.55, 0.62, 0.62, 1, font)

    local y = 26
    local shown = {}
    local start = math.max(1, #self.lines - MAX_LINES + 1)
    for i = start, #self.lines do
        shown[#shown + 1] = self.lines[i]
    end

    if #shown == 0 then
        self:drawText("还没有对话", 10, y, 0.55, 0.55, 0.55, 1, font)
    else
        for _, item in ipairs(shown) do
            self:drawText(item.time or "", 10, y, 0.55, 0.62, 0.68, 1, font)
            self:drawText(fit(font, item.text or "", w - 80), 58, y, 0.88, 0.90, 0.86, 1, font)
            y = y + 20
        end
    end

    local status = self.status or "idle"
    local text, r, g, b = "待机", 0.55, 0.58, 0.60
    if status == "listening" then
        text, r, g, b = "正在听... 说完停一下", 0.35, 0.95, 0.45
    elseif status == "thinking" then
        text, r, g, b = "阿D 在想...", 0.95, 0.85, 0.35
    elseif status == "speaking" then
        text, r, g, b = "阿D 在说话...", 0.45, 0.75, 0.95
    end
    self:drawText(fit(font, text, w - 20), 10, h - 22, r, g, b, 1, font)
end

local function ensurePanel()
    if panel then return end
    panel = DCAI_UI:new(PANEL_X, PANEL_Y, PANEL_W, PANEL_H)
    print("[DC_AIVoice] ui panel created")
    panel:initialise()
    panel:addToUIManager()
    if panel.javaObject then panel.javaObject:setConsumeMouseEvents(false) end
end

local function unusedRemovePanel()
    if panel then
        panel:removeFromUIManager()
        panel = nil
    end
end

Events.OnGameStart.Add(ensurePanel)

Events.OnKeyPressed.Add(function(key)
    if key ~= Keyboard.KEY_F7 then return end
    if not getPlayer() then return end
    writeTextFile(VOICE_FILE, "rec\n")
end)
