// 编译桩：仅用于 javac，不进 jar。运行时链接游戏自带 JNA（真实 loadLibrary 存在于 JNA4/5）。
package com.sun.jna;

public final class Native {
    public static Object loadLibrary(String name, Class<?> interfaceClass) { return null; }
}
