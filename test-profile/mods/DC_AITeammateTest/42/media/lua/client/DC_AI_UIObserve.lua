require "DC_AI_TeammateUI"
local U=function(...) return string.char(...) end
local tracked={}
local dialog
local originalNew=ISTextBox.new
function ISTextBox:new(...)
 local box=originalNew(self,...)
 if box.text==U(19982,32,65,73,32,38431,21451,23545,35805,65288,38656,35201,27169,22411,26725,25509,31243,24207,65289) then dialog=box end
 if dialog==box then
  local originalClick=box.onclick
  box.onclick=function(target,button,...)
   local before=DC_AI_TeammateMailbox.status()
   print("DC_DIALOG_CLICK: "..tostring(button.internal).." beforeSeq="..tostring(before.seq).." beforePending="..tostring(before.pending))
   originalClick(target,button,...)
   local after=DC_AI_TeammateMailbox.status()
   print("DC_DIALOG_AFTER: seq="..tostring(after.seq).." pending="..tostring(after.pending).." phase="..tostring(after.phase).." error="..tostring(after.error))
  end
 end
 return box
end
local function names(menu)
 local a={}
 if not menu or not menu.options then return "" end
 for i=1,menu.numOptions do local o=menu.options[i]; if o then a[#a+1]=tostring(o.name or "") end end
 return table.concat(a,"|")
end
Events.OnTick.Add(function()
 if dialog and not dialog.dcPrefilled then
  dialog.dcPrefilled=true
  if dialog.entry and dialog.entry.setText then dialog.entry:setText(U(35831,22312,36825,37324,31561,24453)) end
 end
 if dialog and dialog:isVisible() and not dialog.dcLogged then
  dialog.dcLogged=true
  for _,button in ipairs({dialog.yes,dialog.no}) do
   print("DC_DIALOG_POS: "..tostring(button.internal)..":"..tostring(button:getAbsoluteX()+button:getWidth()/2)..","..tostring(button:getAbsoluteY()+button:getHeight()/2))
  end
  print("DC_DIALOG: text="..tostring(dialog.text).." ok="..tostring(dialog.yes and dialog.yes.title).." cancel="..tostring(dialog.no and dialog.no.title).." okInternal="..tostring(dialog.yes and dialog.yes.internal).." cancelInternal="..tostring(dialog.no and dialog.no.internal))
 end
 for _,menu in ipairs(tracked) do
  if menu and menu.isVisible and menu:isVisible() and menu.options then
   local snapshot={}
   for i=1,menu.numOptions do
    local o=menu.options[i]
    if o then snapshot[#snapshot+1]=tostring(o.name or "")..":"..tostring(menu:getX()+menu:getWidth()/2)..","..tostring(menu:getItemY(i)+menu.itemHgt/2) end
   end
   local text=table.concat(snapshot,"|")
   if menu.dcLastPositions~=text then menu.dcLastPositions=text; print("DC_UI_POS: "..text) end
  end
 end
end)
Events.OnFillWorldObjectContextMenu.Add(function(playerIndex, context, objects, test)
 if test or playerIndex ~= 0 then return end
 local root=context:getOptionFromName(U(65,73,32,38431,21451))
 if not root then print("DC_UI_LIVE: submenu_root_missing=true"); return end
 local sub=context:getSubMenu(root.subOption)
 if not sub then print("DC_UI_LIVE: submenu_missing=true"); return end
 tracked={context,sub}
 print("DC_UI_LIVE: submenu_options="..names(sub))
 local expected={U(25307,21215,65295,24674,22797,38431,21451),U(36319,38543,25105),U(22312,36825,37324,31561,24453),U(19982,38431,21451,23545,35805),U(29366,24577)}
 local found={}
 for i=1,sub.numOptions do local o=sub.options[i]; if o then found[tostring(o.name or "")]=true end end
 local ok=true
 for i=1,#expected do if not found[expected[i]] then ok=false end end
 print("DC_UI_LIVE: submenu_chinese_options="..tostring(ok))
 for i=1,sub.numOptions do
  local o=sub.options[i]
  if o and o.onSelect and not o.dcWrapped then
   local original,label=o.onSelect,tostring(o.name)
   o.dcWrapped=true
   o.onSelect=function(...)
    print("DC_UI_CLICK: "..label)
    original(...)
    local s=DC_AI_Teammate.state
    print("DC_UI_AFTER: phase="..tostring(s.phase).." npc="..tostring(s.npcId).." error="..tostring(s.error))
   end
  end
 end
end)
