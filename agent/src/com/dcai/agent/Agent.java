package com.dcai.agent;

import java.io.File;
import java.io.FileOutputStream;
import java.io.PrintStream;
import java.lang.instrument.Instrumentation;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * Project Zomboid 的 Java Agent。
 *
 * 两种加载方式：
 *   -javaagent:dcaiv-agent.jar        启动时加载（premain）
 *   jattach / Attach API 动态挂载      运行中加载（agentmain）
 *
 * 能力：
 *   1. 往 Lua 全局塞 DCAgentPing / DCAgentPlay（音频直通）
 *   2. 监听 %USERPROFILE%\Zomboid\dcagent_cmd.txt，把里面的命令作用到正在跑的游戏上
 *
 * 命令（一行一条，文件整体替换即触发）：
 *   ping
 *   say <文字>      角色在聊天框里说一句
 *   halo <文字>     屏幕上方飘字
 *   heal            回满血
 *   item <完整ID>   往背包塞东西，例如 Base.CannedBeans
 *   god on|off
 *   stat            写一条状态到日志
 *
 * 日志：%USERPROFILE%\Zomboid\dcagent.log
 * 回执：%USERPROFILE%\Zomboid\dcagent_out.txt
 */
public final class Agent {

    private static PrintStream logStream;
    private static File cmdFile;
    private static File outFile;
    private static volatile String lastCmd = "";
    private static volatile boolean started;

    public static void premain(String args, Instrumentation inst) {
        start("premain", args);
    }

    public static void agentmain(String args, Instrumentation inst) {
        start("agentmain", args);
    }

    private static void start(String mode, String args) {
        if (started) {
            return;
        }
        started = true;
        initFiles();
        log("agent start (" + mode + "), args=" + args);
        Thread lua = new Thread(new Runnable() {
            public void run() {
                bootstrap();
            }
        }, "dcaiv-agent-lua");
        lua.setDaemon(true);
        lua.start();

        Thread cmd = new Thread(new Runnable() {
            public void run() {
                watchCommands();
            }
        }, "dcaiv-agent-cmd");
        cmd.setDaemon(true);
        cmd.start();
    }

    // ---------- 日志 ----------

    private static synchronized void initFiles() {
        if (logStream != null) {
            return;
        }
        try {
            String home = System.getenv("USERPROFILE");
            if (home == null || home.isEmpty()) {
                home = System.getProperty("user.home");
            }
            File dir = new File(home, "Zomboid");
            if (!dir.exists()) {
                dir.mkdirs();
            }
            cmdFile = new File(dir, "dcagent_cmd.txt");
            outFile = new File(dir, "dcagent_out.txt");
            logStream = new PrintStream(new FileOutputStream(new File(dir, "dcagent.log"), true), true, "UTF-8");
        } catch (Throwable t) {
            logStream = System.out;
        }
    }

    private static synchronized void log(String msg) {
        String line = "[" + new SimpleDateFormat("HH:mm:ss").format(new Date()) + "] " + msg;
        try {
            if (logStream != null) {
                logStream.println(line);
            }
        } catch (Throwable ignored) {
        }
        try {
            System.out.println("[DCAgent] " + msg);
        } catch (Throwable ignored) {
        }
    }

    private static synchronized void receipt(String msg) {
        log(msg);
        try {
            if (outFile != null) {
                Files.write(outFile.toPath(), (new SimpleDateFormat("HH:mm:ss").format(new Date()) + " " + msg + "\n").getBytes(StandardCharsets.UTF_8));
            }
        } catch (Throwable ignored) {
        }
    }

    private static void sleep(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException ie) {
            Thread.currentThread().interrupt();
        }
    }

    // ---------- Lua 侧 ----------

    private static void bootstrap() {
        Class<?> luaManager;
        try {
            luaManager = Class.forName("zombie.Lua.LuaManager");
        } catch (Throwable t) {
            log("no LuaManager in this JVM, agent stays idle");
            return;
        }
        for (int i = 0; i < 900; i++) {
            try {
                Field envField = luaManager.getField("env");
                Object env = envField.get(null);
                if (env != null) {
                    registerLua(env);
                    return;
                }
            } catch (Throwable t) {
                log("waiting for LuaManager.env: " + t);
            }
            sleep(200);
        }
        log("gave up waiting for LuaManager.env");
    }

    private static void registerLua(Object env) {
        try {
            Class<?> tableCls = Class.forName("se.krka.kahlua.vm.KahluaTable");
            Method rawset = tableCls.getMethod("rawset", Object.class, Object.class);
            rawset.invoke(env, "DCAgentPing", newFn("ping"));
            rawset.invoke(env, "DCAgentPlay", newFn("play"));
            log("registered DCAgentPing / DCAgentPlay");
        } catch (Throwable t) {
            log("register failed: " + t);
        }
    }

    private static Object newFn(final String kind) throws Exception {
        final Class<?> javaFunction = Class.forName("se.krka.kahlua.vm.JavaFunction");
        return java.lang.reflect.Proxy.newProxyInstance(
                javaFunction.getClassLoader(),
                new Class<?>[]{javaFunction},
                new java.lang.reflect.InvocationHandler() {
                    public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
                        if (!"call".equals(method.getName())) {
                            return "toString".equals(method.getName()) ? "DCAgent:" + kind : null;
                        }
                        Object frame = args[0];
                        int nArgs = ((Integer) args[1]).intValue();
                        if ("ping".equals(kind)) {
                            push(frame, "pong from agent");
                            return Integer.valueOf(1);
                        }
                        String path = "";
                        if (nArgs >= 1) {
                            try {
                                Object v = frame.getClass().getMethod("get", int.class).invoke(frame, Integer.valueOf(1));
                                path = String.valueOf(v);
                            } catch (Throwable ignored) {
                            }
                        }
                        push(frame, playWav(path) ? "ok" : "fail");
                        return Integer.valueOf(1);
                    }
                });
    }

    private static void push(Object frame, Object value) {
        try {
            frame.getClass().getMethod("push", Object.class).invoke(frame, value);
        } catch (Throwable t) {
            log("push failed: " + t);
        }
    }

    private static boolean playWav(String path) {
        if (path == null || path.isEmpty()) {
            return false;
        }
        File f = new File(path);
        if (!f.isFile()) {
            log("play: file not found " + path);
            return false;
        }
        try {
            Class<?> jf = Class.forName("fmod.javafmod");
            long sound = ((Number) jf.getMethod("FMOD_System_CreateSound", String.class, long.class)
                    .invoke(null, f.getAbsolutePath(), Long.valueOf(8L))).longValue(); // 8 = FMOD_2D
            if (sound == 0L) {
                log("play: CreateSound returned 0");
                return false;
            }
            long channel = ((Number) jf.getMethod("FMOD_System_PlaySound", long.class, boolean.class)
                    .invoke(null, Long.valueOf(sound), Boolean.FALSE)).longValue();
            log("played " + f.getName() + " (channel " + channel + ")");
            return channel != 0L;
        } catch (Throwable t) {
            log("play error: " + t);
            return false;
        }
    }

    // ---------- 命令通道 ----------

    private static void watchCommands() {
        log("watching " + (cmdFile == null ? "?" : cmdFile.getAbsolutePath()));
        while (true) {
            try {
                if (cmdFile != null && cmdFile.isFile()) {
                    String content = new String(Files.readAllBytes(cmdFile.toPath()), StandardCharsets.UTF_8).trim();
                    if (!content.isEmpty() && !content.equals(lastCmd)) {
                        lastCmd = content;
                        for (String line : content.split("\\r?\\n")) {
                            String cmd = line.trim();
                            if (!cmd.isEmpty() && !cmd.startsWith("#")) {
                                execute(cmd);
                            }
                        }
                    }
                }
            } catch (Throwable t) {
                log("cmd loop: " + t);
            }
            sleep(250);
        }
    }

    private static void execute(String cmd) {
        try {
            String[] parts = cmd.split("\\s+", 2);
            String verb = parts[0].toLowerCase();
            String arg = parts.length > 1 ? parts[1] : "";

            if ("ping".equals(verb)) {
                receipt("pong");
                return;
            }
            if ("mods".equals(verb)) {
                Object fs = Class.forName("zombie.ZomboidFileSystem").getField("instance").get(null);
                java.util.List<String> list = new java.util.ArrayList<String>();
                fs.getClass().getMethod("getAllModFolders", java.util.List.class).invoke(fs, list);
                StringBuilder sb = new StringBuilder("mods(" + list.size() + "): ");
                for (String s : list) { sb.append(s).append(" | "); }
                receipt(sb.toString());
                return;
            }
            if ("stat".equals(verb)) {
                Object p = player();
                if (p == null) { receipt("no player yet (still in main menu?)"); return; }
                receipt("stat hp=" + invoke(p, "getHealth") + " x=" + invoke(p, "getX") + " y=" + invoke(p, "getY"));
                return;
            }
            if ("say".equals(verb)) {
                Object p = player();
                if (p == null) { receipt("no player yet (still in main menu?)"); return; }
                p.getClass().getMethod("Say", String.class).invoke(p, arg);
                receipt("say ok: " + arg);
                return;
            }
            if ("halo".equals(verb)) {
                Object p = player();
                if (p == null) { receipt("no player yet (still in main menu?)"); return; }
                Class<?> halo = Class.forName("zombie.characters.HaloTextHelper");
                Class<?> isoPlayer = Class.forName("zombie.characters.IsoPlayer");
                halo.getMethod("addText", isoPlayer, String.class).invoke(null, p, arg);
                receipt("halo ok");
                return;
            }
            if ("heal".equals(verb)) {
                Object p = player();
                if (p == null) { receipt("no player yet (still in main menu?)"); return; }
                p.getClass().getMethod("setHealth", float.class).invoke(p, Float.valueOf(1.0F));
                receipt("heal ok");
                return;
            }
            if ("god".equals(verb)) {
                Object p = player();
                if (p == null) { receipt("no player yet (still in main menu?)"); return; }
                boolean on = !"off".equalsIgnoreCase(arg);
                p.getClass().getMethod("setGodMod", boolean.class).invoke(p, Boolean.valueOf(on));
                receipt("god " + (on ? "on" : "off"));
                return;
            }
            if ("item".equals(verb)) {
                Object p = player();
                if (p == null) { receipt("no player yet (still in main menu?)"); return; }
                Object inv = p.getClass().getMethod("getInventory").invoke(p);
                Object item = inv.getClass().getMethod("AddItem", String.class).invoke(inv, arg);
                receipt(item == null ? ("item failed: " + arg) : ("item ok: " + arg));
                return;
            }
            receipt("unknown command: " + cmd);
        } catch (Throwable t) {
            Throwable cause = t.getCause() != null ? t.getCause() : t;
            receipt("error on [" + cmd + "]: " + cause);
        }
    }

    private static Object player() throws Exception {
        Class<?> isoPlayer = Class.forName("zombie.characters.IsoPlayer");
        return isoPlayer.getMethod("getInstance").invoke(null);
    }

    private static Object invoke(Object target, String method) throws Exception {
        return target.getClass().getMethod(method).invoke(target);
    }

    private Agent() {
    }
}
