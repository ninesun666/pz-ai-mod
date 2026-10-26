// 编译桩：仅用于 javac，不进 jar。
package com.sun.jna;

public class Pointer {
    public Pointer(long value) {}
    public static long nativeValue(Pointer p) { return 0; }
}
