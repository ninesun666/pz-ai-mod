-- Disposable live model integration observer, no fabricated replies.
require "DC_AI_TestPersistenceConfig"
if not DC_AI_TestPersistenceConfig.modelTest then return end
require "DC_AI_TeammateMailbox"
local ticks,requested,finished=0,false,false
Events.OnTick.Add(function()
 if finished or not DC_AI_Teammate or DC_AI_Teammate.state.phase~="recovered" and not requested then return end
 ticks=ticks+1
 if not requested and ticks>=180 then
  requested=true
  print("DC_MODEL_LIVE: request="..tostring(DC_AI_TeammateMailbox.request(string.char(35831,22312,36825,37324,31561,24453,65292,25105,21435,30475,30475,21069,38754,12290))))
 end
 if requested and ticks%60==0 then
  local s=DC_AI_TeammateMailbox.status()
  print("DC_MODEL_LIVE: mailbox="..s.phase.." error="..tostring(s.error).." adapter="..DC_AI_Teammate.state.phase.." npc="..tostring(DC_AI_Teammate.state.npcId))
  if s.phase=="complete" then
   local m=DC_AI_Teammate.spawnedMeta
   print("DC_MODEL_LIVE: COMPLETE goal="..tostring(m:getGoalPretty()).." sub="..tostring(m:getSubGoalPretty()).." member="..tostring(KnoxEventLoader.getAPI("npc"):getGroup(getPlayer()):inGroup(m)))
   finished=true
  end
 end
end)
