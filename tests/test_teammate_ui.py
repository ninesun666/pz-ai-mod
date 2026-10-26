"""Local UI wiring regression; does not prove in-game rendering."""
from pathlib import Path
from lupa import LuaRuntime
lua = LuaRuntime()
lua.execute('''
require=function() end
calls={}
DC_AI_Teammate={state={phase='following',error=nil},start=function() calls.start=true; return true end,follow=function() calls.follow=true; return true end,wait=function() calls.wait=true; return true end}
DC_AI_TeammateMailbox={request=function(text) calls.text=text; return true end,status=function() return {phase='idle'} end}
getPlayer=function() return {} end
HaloTextHelper={addText=function(p,t) calls.notice=t end}
isClient=function() return false end
isServer=function() return false end
Events={OnFillWorldObjectContextMenu={Add=function(f) fill=f end}}
menu={options={}}
function menu:addOption(label,target,callback) local o={target=target,callback=callback}; self.options[label]=o; return o end
function menu:addSubMenu(root,sub) end
ISContextMenu={getNew=function() return menu end}
ISTextBox={new=function(self,x,y,w,h,label,default,target,callback,player)
 calls.box={callback=callback,initialise=function(self)
  self.yes={internal='OK',setTitle=function(_,t) calls.okTitle=t end}
  self.no={internal='CANCEL',setTitle=function(_,t) calls.cancelTitle=t end}
 end,addToUIManager=function() end}; return calls.box
end}
''')
lua.execute((Path(__file__).resolve().parents[1]/'DC_AIVoice/42.0/media/lua/client/DC_AI_TeammateUI.lua').read_text(encoding='utf-8'))
lua.execute('''
fill(0,menu,{},true); assert(next(menu.options)==nil)
fill(1,menu,{},false); assert(next(menu.options)==nil)
fill(0,menu,{},false)
for _,label in ipairs({'招募／恢复队友','跟随我','在这里等待','与队友对话','状态'}) do
 local o=menu.options[label]; assert(o); o.callback(o.target)
end
assert(calls.start and calls.follow and calls.wait and calls.box)
assert(calls.okTitle=='确定' and calls.cancelTitle=='取消')
assert(calls.notice=='正在跟随 / 尚未启动 / 正常')
DC_AI_Teammate.state.error='pending request timeout'
menu.options['状态'].callback()
assert(calls.notice=='正在跟随 / 尚未启动 / 模型回复超时，请检查桥接程序和网络')
DC_AI_Teammate.state.error='unexpected Java exception'
menu.options['状态'].callback()
assert(calls.notice=='正在跟随 / 尚未启动 / 发生内部错误，请查看游戏日志')
DC_AI_Teammate.state.error=nil
calls.box.callback(nil,{internal='CANCEL'}); assert(calls.text==nil)
calls.box.callback(nil,{internal='OK',parent={entry={getText=function() return 'follow me' end}}})
assert(calls.text=='follow me')
''')
print('PASS: UI opt-in menu, player gating, command wiring, talk submit/cancel')
