-- Retired prototype: disabled before requires, UI creation or event registration.
-- Preserved in Git history for reference; not part of the standalone companion.
do return end

-- Opt-in, main-thread mailbox. Never starts/spawns/recruits a teammate.
DC_AI_TeammateMailbox = {}
local M = DC_AI_TeammateMailbox
local MAX_WIRE, MAX_TEXT, MAX_SEQ = 4096, 512, 9007199254740991
local TIMEOUT, POLL_MS = 60000, 250
local session, pending, sequence = nil, nil, 0
local phase, lastError, nextPoll = "idle", nil, 0
local function fail(message) phase,lastError="error",tostring(message); return false end
local function nowMs()
 local n
 if getTimestampMs then n=getTimestampMs() elseif getTimestamp then n=getTimestamp()*1000 end
 if type(n)~="number" or n<0 or n>MAX_SEQ or n~=math.floor(n) then error("valid timestamp unavailable") end
 return n
end
local function decimal(v) return type(v)=="string" and #v<=128 and (v=="0" or v:match("^[1-9][0-9]*$")~=nil) end
local function nonce(v) return type(v)=="string" and #v>=16 and #v<=128 and v:match("^[A-Za-z0-9_-]+$")~=nil end
local function forbidden(cp)
 return cp<32 or (cp>=127 and cp<=159) or cp==173 or (cp>=1536 and cp<=1541) or cp==1564 or cp==1757 or cp==1807 or (cp>=8203 and cp<=8207) or (cp>=8232 and cp<=8238) or (cp>=8288 and cp<=8303) or cp==65279 or (cp>=65529 and cp<=65531) or cp==917505 or (cp>=917536 and cp<=917631) or (cp>=2192 and cp<=2193) or cp==2274 or cp==6158 or cp==69821 or cp==69837 or (cp>=78896 and cp<=78911) or (cp>=113824 and cp<=113827) or (cp>=119155 and cp<=119162)
end
-- Kahlua strings use Java UTF-16 units; normal Lua strings use UTF-8 bytes.
local probeOK, probe = pcall(string.char, 20013)
local UTF16 = probeOK and #probe == 1 and string.byte(probe) == 20013
local function validText(s)
 if type(s)~="string" or #s>MAX_TEXT then return false end
 local i,bytes=1,0
 while i<=#s do
  local b=s:byte(i); local cp,count,min=b,0,0
  if UTF16 then
   if b>=55296 and b<=56319 then
    local low=s:byte(i+1)
    if not low or low<56320 or low>57343 then return false end
    cp,count=65536+(b-55296)*1024+low-56320,1
   elseif b>=56320 and b<=57343 then return false end
  else
   if b>=194 and b<=223 then cp,count,min=b-192,1,128 elseif b>=224 and b<=239 then cp,count,min=b-224,2,2048 elseif b>=240 and b<=244 then cp,count,min=b-240,3,65536 elseif b>=128 then return false end
   for j=1,count do local c=s:byte(i+j); if not c or c<128 or c>191 then return false end; cp=cp*64+c-128 end
  end
  if cp<min or cp>1114111 or (cp>=55296 and cp<=57343) or forbidden(cp) then return false end
  bytes=bytes+(cp<128 and 1 or cp<2048 and 2 or cp<65536 and 3 or 4)
  if bytes>MAX_TEXT then return false end
  i=i+count+1
 end
 return true
end
local function utf8Char(cp)
 if cp<128 then return string.char(cp) end
 if cp<2048 then return string.char(192+math.floor(cp/64),128+cp%64) end
 if cp<65536 then return string.char(224+math.floor(cp/4096),128+math.floor(cp/64)%64,128+cp%64) end
 return string.char(240+math.floor(cp/262144),128+math.floor(cp/4096)%64,128+math.floor(cp/64)%64,128+cp%64)
end
local function newSession(now)
 if not ZombRand then error("ZombRand unavailable") end
 local p={"dc",string.format("%.0f",now)}
 for i=1,4 do local r=ZombRand(1000000000); if type(r)~="number" or r<0 or r>=1000000000 or r~=math.floor(r) then error("invalid ZombRand result") end; p[#p+1]=string.format("%09d",r) end
 local result=table.concat(p,"_"); if not nonce(result) then error("invalid session token") end; return result
end
local function ready(expected)
 local a=DC_AI_Teammate; if not a or not a.state then return nil,"adapter unavailable" end
 local s=a.state; if s.phase~="following" and s.phase~="waiting" and s.phase~="recovered" then return nil,"teammate not ready" end
 if s.error then return nil,"adapter has an error" end
 local player=getPlayer and getPlayer(); local data=player and player.getModData and player:getModData(); local id=data and data.DC_AI_TeammateNpcId
 if not decimal(id) or s.npcId~=id or (expected and expected~=id) then return nil,"remembered teammate identity mismatch" end
 local api=KnoxEventLoader and KnoxEventLoader.getAPI and KnoxEventLoader.getAPI("npc"); if not api then return nil,"npc API unavailable" end
 local list,found=api:getNpcs(),nil; if not list then return nil,"teammate unavailable" end
 for i=0,list:size()-1 do local meta=list:get(i); if meta and meta.getId and tostring(meta:getId())==id then if found then return nil,"ambiguous teammate identity" end; found=meta end end
 local group=api:getGroup(player); if not found or not group or not group:inGroup(found) then return nil,"teammate not in group" end
 local world=found:getWorldObject(); if not world or not world:getSquare() then return nil,"teammate world not ready" end
 return {id=id,world=world,adapter=a}
end
local function parse(wire)
 if #wire>MAX_WIRE then return nil,"reply too large" end; if wire:sub(-1)=="\n" then wire=wire:sub(1,-2) end
 local f,count={},0
 for line in (wire.."\n"):gmatch("(.-)\n") do local k,v=line:match("^([a-z_]+)=(.*)$"); if not k or (k~="session" and k~="seq" and k~="npc_id" and k~="action" and k~="text") or f[k]~=nil then return nil,"invalid, duplicate or unknown field" end; f[k],count=v,count+1 end
 if count~=5 then return nil,"expected exactly five fields" end
 if not nonce(f.session) or not decimal(f.npc_id) then return nil,"invalid identity" end
 if not f.seq:match("^[1-9][0-9]*$") or #f.seq>16 or (#f.seq==16 and f.seq>"9007199254740991") then return nil,"invalid sequence" end
 if f.action~="none" and f.action~="follow" and f.action~="wait" then return nil,"action not allowed" end
 if not validText(f.text) then return nil,"invalid text" end; return f
end
local function readReply()
 local r=getFileReader("dc_teammate_reply.txt",false); if not r then return nil end
 local ok,result=pcall(function()
  local c,b,high={},0,nil
  for i=1,MAX_WIRE do local cp=r:read(); if cp==-1 then if high then error("unpaired UTF-16 surrogate") end; return table.concat(c) end; if type(cp)~="number" or cp<0 or cp>65535 or cp~=math.floor(cp) then error("invalid reader character") end
   local unit=cp
   if high then if cp<56320 or cp>57343 then error("unpaired UTF-16 surrogate") end; cp,high=65536+(high-55296)*1024+cp-56320,nil elseif cp>=55296 and cp<=56319 then high,cp=cp,nil elseif cp>=56320 and cp<=57343 then error("unpaired UTF-16 surrogate") end
   if cp then b=b+(cp<128 and 1 or cp<2048 and 2 or cp<65536 and 3 or 4); if b>MAX_WIRE then error("reply too large") end end
   if UTF16 then c[#c+1]=string.char(unit) elseif cp then c[#c+1]=utf8Char(cp) end
  end; error("reply too large")
 end)
 local closed=pcall(function() r:close() end); if not ok then error(result) end; if not closed then error("reply close failed") end; return result
end
local function requestImpl(text)
 if pending then return fail("request already pending") end; if not validText(text) then return fail("invalid request text") end
 local target,err=ready(); if not target then return fail(err) end; local now=nowMs(); if not session then session=newSession(now) end; if sequence>=MAX_SEQ then return fail("sequence exhausted") end
 sequence=sequence+1; local seq=string.format("%.0f",sequence); local wire="session="..session.."\nseq="..seq.."\nnpc_id="..target.id.."\naction=none\ntext="..text.."\n"; pending={session=session,seq=seq,npc_id=target.id,started=now}
 local w; local ok,we=pcall(function() w=getFileWriter("dc_teammate_request.txt",true,false); if not w then error("request writer unavailable") end; w:write(wire) end); local closed=true; if w then closed=pcall(function() w:close() end) end
 if not ok or not closed then pending=nil; return fail(not ok and we or "request close failed") end; phase,lastError,nextPoll="pending",nil,now; return true
end
function M.request(text) local ok,r=pcall(requestImpl,text); if not ok then return fail(r) end; return r end
function M.status() return {phase=phase,error=lastError,session=session,seq=sequence,pending=pending~=nil,npcId=pending and pending.npc_id or nil} end
local function tickImpl()
 if not pending then return end; local now=nowMs(); if now<pending.started or now-pending.started>=TIMEOUT then pending=nil; return fail("pending request timeout") end; if now<nextPoll then return end; nextPoll=now+POLL_MS
 local wire=readReply(); if not wire then return end; local reply,err=parse(wire); if not reply then return fail(err) end; if reply.session~=pending.session or reply.seq~=pending.seq or reply.npc_id~=pending.npc_id then return fail("reply does not match pending identity") end
 local id=pending.npc_id; pending=nil -- consume before action
 local target,targetErr=ready(id); if not target then return fail(targetErr) end; local result=true; if reply.action=="follow" then result=target.adapter.follow() elseif reply.action=="wait" then result=target.adapter.wait() end; if result~=true then return fail("adapter command failed") end; phase,lastError="complete",nil
 if reply.text~="" then
  local current=ready(id)
  if not current then lastError="action completed; teammate speech unavailable" end
  if current then
   local shown=pcall(function() current.world:Say(reply.text) end)
   if not shown then
    lastError="action completed; teammate speech unavailable"
    print("[DC_AI_TeammateMailbox] "..lastError)
   end
  end
 end
end
Events.OnTick.Add(function() if DC_AI_TeammateMailbox~=M then return end; local ok,e=pcall(tickImpl); if not ok then fail(e) end end)
