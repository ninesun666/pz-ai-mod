import java.lang.reflect.*;
public class KahluaUnicodeProbe {
 static Class<?> frameClass, libClass;
 static Object invoke(int index, Object... args) throws Exception {
  Object platform=Class.forName("se.krka.kahlua.j2se.J2SEPlatform").getConstructor().newInstance();
  Object table=platform.getClass().getMethod("newTable").invoke(platform);
  Object coroutine=Class.forName("se.krka.kahlua.vm.Coroutine").getConstructor(platform.getClass().getInterfaces()[0],Class.forName("se.krka.kahlua.vm.KahluaTable")).newInstance(platform,table);
  Object frame=frameClass.getConstructor(coroutine.getClass()).newInstance(coroutine);
  frameClass.getMethod("setTop",int.class).invoke(frame,args.length);
  for(int i=0;i<args.length;i++) frameClass.getMethod("set",int.class,Object.class).invoke(frame,i,args[i]);
  Constructor<?> ctor=libClass.getDeclaredConstructor(int.class);ctor.setAccessible(true);
  int count=(Integer)libClass.getMethod("call",frameClass,int.class).invoke(ctor.newInstance(index),frame,args.length);
  int top=(Integer)frameClass.getMethod("getTop").invoke(frame);
  return count==0?null:frameClass.getMethod("get",int.class).invoke(frame,top-count);
 }
 static String units(String s){StringBuilder b=new StringBuilder();for(char c:s.toCharArray())b.append(String.format("U+%04X ",(int)c));return b.toString().trim();}
 public static void main(String[] args)throws Exception{
  frameClass=Class.forName("se.krka.kahlua.vm.LuaCallFrame");libClass=Class.forName("se.krka.kahlua.stdlib.StringLib");
  System.out.println("byte(Chinese Zhong)="+invoke(2,"\u4e2d"));
  System.out.println("char(20013)="+units((String)invoke(1,20013.0)));
  System.out.println("char(228,184,173)="+units((String)invoke(1,228.0,184.0,173.0)));
  System.out.println("byte(emoji,1)="+invoke(2,"\ud83d\ude00",1.0));
  System.out.println("byte(emoji,2)="+invoke(2,"\ud83d\ude00",2.0));
 }
}
