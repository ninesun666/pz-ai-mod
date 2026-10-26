-- Disposable profile ONLY. One physical combat encounter; no forced damage/stat changes.
require "DC_AI_TestPersistenceConfig"
if not DC_AI_TestPersistenceConfig.combat then return end
local ticks,spawned,zombie,npc=0,false,nil,nil
local hitSeen,deadSeen=false,false
Events.OnHitZombie.Add(function(zed,wielder,bodyPart,weapon)
 if zed==zombie and wielder==npc then hitSeen=true; print("DC_COMBAT: HIT body="..tostring(bodyPart).." weapon="..tostring(weapon and weapon:getFullType())) end
end)
Events.OnZombieDead.Add(function(zed)
 if zed==zombie then deadSeen=true; print("DC_COMBAT: DEATH hitSeen="..tostring(hitSeen)) end
end)
Events.OnTick.Add(function()
 local ok,err=pcall(function()
  if not DC_AI_Teammate or (DC_AI_Teammate.state.phase~="recovered" and DC_AI_Teammate.state.phase~="following" and DC_AI_Teammate.state.phase~="waiting") then return end
  ticks=ticks+1
  if ticks==1980 or deadSeen then
   print("DC_COMBAT: END ticks="..ticks.." hitSeen="..tostring(hitSeen).." deadSeen="..tostring(deadSeen))
   setGameSpeed(0)
   return
  end
  if ticks>1980 then return end
  if not spawned and ticks>=180 then
   spawned=true
  npc=DC_AI_Teammate.spawnedMeta and DC_AI_Teammate.spawnedMeta:getWorldObject()
  if not npc then error("recovered teammate world object unavailable") end
   local x,y,z=math.floor(npc:getX())+3,math.floor(npc:getY()),math.floor(npc:getZ())
   local sq=getCell():getGridSquare(x,y,z)
   if not sq or not sq:isFree(false) then error("combat tile not free") end
   local list=addZombiesInOutfit(x,y,z,1,nil,50)
   if not list or list:size()<1 then error("combat spawn count="..tostring(list and list:size() or -1)) end
   if list:size()>1 then error("combat spawn count="..tostring(list:size())) end
   zombie=list:get(0)
   print("DC_COMBAT: spawned health="..tostring(zombie:getHealth()).." npcHealth="..tostring(npc:getHealth()))
  end
  if zombie and ticks%60==0 then
   local meta=DC_AI_Teammate.spawnedMeta
   print("DC_COMBAT: tick="..ticks.." zombieHealth="..tostring(zombie:getHealth()).." zombieDead="..tostring(zombie:isDead())
    .." npcHealth="..tostring(npc:getHealth()).." goal="..tostring(meta:getGoalPretty()).." sub="..tostring(meta:getSubGoalPretty()))
  end
 end)
 if not ok then print("DC_COMBAT: error="..tostring(err)) end
end)
