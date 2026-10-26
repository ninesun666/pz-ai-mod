package dcaiv.toolkit;

/** Optional entry point: ZombieBuddy executes main(String[]) if present. */
public class Main {
    public static void main(String[] args) {
        System.out.println("[DC_Toolkit] init ime=" + (ImeNative.ERROR == null ? "native-ok" : ("blocked " + ImeNative.ERROR)));
    }
    private Main() {}
}
