import java.lang.reflect.*;
public class KahluaLiteralProbe {
 static String units(String s){StringBuilder b=new StringBuilder();for(char c:s.toCharArray())b.append(String.format("U+%04X ",(int)c));return b.toString().trim();}
 static void run(Object platform,Object table,String src)throws Exception{
  Class<?> tableClass=Class.forName("se.krka.kahlua.vm.KahluaTable"), compiler=Class.forName("se.krka.kahlua.luaj.compiler.LuaCompiler"), threadClass=Class.forName("se.krka.kahlua.vm.KahluaThread");
  Object closure=compiler.getMethod("loadstring",String.class,String.class,tableClass).invoke(null,src,"literal-probe",table);
  Object thread=threadClass.getConstructor(Class.forName("se.krka.kahlua.vm.Platform"),tableClass).newInstance(platform,table);
  threadClass.getField("debugOwnerThread").set(thread,Thread.currentThread());
  Class<?> platformClass=Class.forName("se.krka.kahlua.vm.Platform");
  Class<?> stringLib=Class.forName("se.krka.kahlua.stdlib.StringLib");
  stringLib.getMethod("register",platformClass,tableClass).invoke(null,platform,table);
  Object[] result=(Object[])threadClass.getMethod("pcall",Object.class,Object[].class).invoke(thread,closure,new Object[0]);
  System.out.println("SRC="+src);
  for(int i=0;i<result.length;i++){Object x=result[i];System.out.println(i+"="+(x instanceof String?"STRING "+units((String)x):String.valueOf(x)));}
 }
 public static void main(String[] args)throws Exception{
  Class<?> platformClass=Class.forName("se.krka.kahlua.j2se.J2SEPlatform"); Object platform=platformClass.getConstructor().newInstance(); Object table=platformClass.getMethod("newTable").invoke(platform);
  run(platform,table,"return 'ABC', #'ABC', string.byte('ABC',1)");
  run(platform,table,"return '中', #'中', string.byte('中',1)");
  run(platform,table,"return '😀', #'😀', string.byte('😀',1), string.byte('😀',2)");
 }
}
