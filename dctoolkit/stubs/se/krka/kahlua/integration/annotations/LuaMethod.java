// 编译桩：仅用于 javac，不进 jar。运行时链接游戏内真类（FQN 一致）。
package se.krka.kahlua.integration.annotations;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface LuaMethod {
    String name();
    boolean global() default false;
}
