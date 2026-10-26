package dcaiv.toolkit;

import com.sun.jna.Pointer;
import org.lwjgl.glfw.GLFWNativeWin32;
import org.lwjglx.opengl.Display;

/** Gets the HWND from the engine's actual GLFW window, avoiding title/desktop collisions. */
final class WindowHandle {
    static Pointer findForCurrentProcess() {
        long glfw = Display.getWindow();
        if (glfw == 0L) return null;
        long hwnd = GLFWNativeWin32.glfwGetWin32Window(glfw);
        return hwnd == 0L ? null : new Pointer(hwnd);
    }
    private WindowHandle() {}
}
