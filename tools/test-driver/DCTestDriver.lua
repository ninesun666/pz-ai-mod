-- AUTHORITATIVE: tools/test-driver/DCTestDriver.lua; deploy with sync-test-driver.ps1.
-- Test-only driver; protocol v2 requires session and seq; quit is always disabled.
-- 信箱: dctest_in.txt / dctest_out.txt（单行 k=v 协议，ASCII）
-- 心跳: dctest_ready.txt 每 60 tick 重写（编排器用它判活/判卡）
-- 命令: ping | snapshot | teleport;x;y;z | speed;n | ime;on=0/1 | save | quit
DCTestDriver = DCTestDriver or {}
local D = DCTestDriver
local IN, OUT, READY = "dctest_in.txt", "dctest_out.txt", "dctest_out_ready_marker_unused"
READY = "dctest_ready.txt"
local lastSeq, lastTick, pollAt = 0, 0, 0
local activeSession, lastLine = nil, nil

local function readAll(path, max)
	local r = getFileReader(path, false)
	if not r then return nil end
	local ok, res = pcall(function()
		local buf = {}
		for i = 1, max or 512 do
			local c = r:read()
			if c == -1 then return table.concat(buf) end
			if type(c) ~= "number" or c < 32 or c > 126 then error("non-ascii protocol") end
			buf[#buf + 1] = string.char(c)
		end
		error("line too long")
	end)
	pcall(function() r:close() end)
	if not ok then return nil, "invalid_input" end
	return res
end

local function writeAll(path, line)
	local ok, err = pcall(function()
		local w = getFileWriter(path, false, false)
		if not w then error("writer unavailable") end
		w:write(line .. "\n")
		w:close()
	end)
	return ok, err
end

local function parseKV(line)
	local t, err = {}, nil
	if line == "" or string.find(line, ";;", 1, true) or string.sub(line, -1) == ";" then err = "bad_fields" end
	for pair in string.gmatch(line or "", "[^;]+") do
		local k, v = string.match(pair, "^([%w_]+)=([^;=]+)$")
		if not k then err = "bad_fields"
		elseif t[k] ~= nil then err = "duplicate_field"
		else t[k] = v end
	end
	return t, err
end

local function cleanError(value)
	return string.sub(string.gsub(tostring(value), "[^%w_ .:-]", "_"), 1, 180)
end

local function safe(f, ...)
	local ok, a = pcall(f, ...)
	if not ok then return nil, tostring(a) end
	return a
end

local function fmt(n)
	if type(n) ~= "number" then return "?" end
	return string.format("%.1f", n)
end

local function cmdSnapshot()
	local parts = { "ok=1" }
	local p = safe(getSpecificPlayer, 0)
	if p then
		local x = safe(p.getX, p); local y = safe(p.getY, p); local z = safe(p.getZ, p)
		parts[#parts + 1] = "px=" .. fmt(x); parts[#parts + 1] = "py=" .. fmt(y); parts[#parts + 1] = "pz=" .. fmt(z)
	else
		parts[#parts + 1] = "px=none"
	end
	parts[#parts + 1] = "speed=" .. tostring(safe(getGameSpeed) or "?")
	parts[#parts + 1] = "paused=" .. tostring(safe(isGamePaused) or "?")
	local ime = safe(dcImeStatus)
	if type(ime) == "string" then parts[#parts + 1] = "ime=" .. string.gsub(ime, "[;%s]", ",") end
	local a = rawget(_G, "DC_AI_Teammate")
	if a and a.state then parts[#parts + 1] = "npc=" .. tostring(a.state.phase) end
	return table.concat(parts, ";")
end

local function execute(cmd)
	local c = cmd.cmd
	if c == "ping" then return "ok=1;pong=1"
	elseif c == "snapshot" then return cmdSnapshot()
	elseif c == "teleport" then
		local p = safe(getSpecificPlayer, 0)
		if not p then return "ok=0;err=no_player" end
		local x, y, z = tonumber(cmd.x), tonumber(cmd.y), tonumber(cmd.z or "0")
		if not x or not y or not z then return "ok=0;err=bad_args" end
		local e1 = select(2, safe(p.setX, p, x))
		local e2 = select(2, safe(p.setY, p, y))
		local e3 = select(2, safe(p.setZ, p, z))
		if e1 or e2 or e3 then return "ok=0;err=set_" .. tostring(e1 or e2 or e3) end
		return "ok=1;moved=" .. fmt(x) .. "," .. fmt(y)
	elseif c == "speed" then
		local n = tonumber(cmd.n)
		if not n or n < 0 or n > 3 then return "ok=0;err=bad_speed" end
		local e = select(2, safe(setGameSpeed, n))
		if e then return "ok=0;err=" .. tostring(e) end
		return "ok=1;speed=" .. n
	elseif c == "ime" then
		if cmd.on ~= "0" and cmd.on ~= "1" then return "ok=0;err=bad_ime" end
		local fn = (cmd.on == "1") and dcImeAttach or dcImeDetach
		local r, e = safe(fn)
		if e or r == nil then return "ok=0;err=" .. tostring(e or "no_fn") end
		return "ok=1;ime=" .. cmd.on
	elseif c == "save" then
		local e = select(2, safe(saveGame))
		if e then return "ok=0;err=" .. tostring(e) end
		return "ok=1;saved=1"
	elseif c == "quit" then
		-- dcTestQuit/Runtime.exit is not an engine graceful shutdown API.
		return "ok=0;err=quit_disabled"
	end
	return "ok=0;err=unknown_cmd"
end

local function poll()
	local line, readErr = readAll(IN, 512)
	if not line then
		if readErr then writeAll(OUT, "session=invalid;seq=0;ok=0;err=" .. readErr) end
		return
	end
	if line == lastLine then return end
	lastLine = line
	local msg, parseErr = parseKV(line)
	local session = msg.session
	local seq = tonumber(msg.seq)
	local validSession = session and #session <= 64 and string.match(session, "^[%w_-]+$")
	local validSeq = msg.seq and string.match(msg.seq, "^[1-9]%d*$") and seq and seq <= 2147483647
	local prefix = "session=" .. (validSession and session or "invalid") .. ";seq=" .. (validSeq and msg.seq or "0") .. ";"
	local reply
	if not validSession or not validSeq then reply = "ok=0;err=bad_identity"
	elseif parseErr then reply = "ok=0;err=" .. parseErr
	elseif activeSession and session ~= activeSession then reply = "ok=0;err=session_mismatch"
	elseif seq <= lastSeq then reply = "ok=0;err=stale_seq"
	else
		activeSession, lastSeq = session, seq
		if not msg.cmd then reply = "ok=0;err=no_cmd"
		else
			local ok, result = pcall(execute, msg)
			reply = ok and result or ("ok=0;err=execution_error;detail=" .. cleanError(result))
		end
	end
	local ok, err = writeAll(OUT, prefix .. reply)
	if not ok then print("[DCTEL] reply_write_failed: " .. cleanError(err)) end
end

function D.onTick()
	lastTick = lastTick + 1
	if lastTick >= pollAt then
		pollAt = lastTick + 10
		local ok, err = pcall(poll)
		if not ok then print("[DCTEL] poll_error: " .. cleanError(err)) end
	end
	if lastTick % 60 == 0 then
		writeAll(READY, "protocol=2;alive=" .. lastTick .. ";seq=" .. lastSeq)
	end
end

Events.OnTick.Add(D.onTick)
Events.OnGameStart.Add(function() writeAll(READY, "protocol=2;alive=" .. lastTick .. ";game=1") end)
writeAll(READY, "protocol=2;alive=0;boot=1")
print("[DCTEL] DRIVER_READY")
