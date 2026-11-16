#!/usr/bin/env python3
"""BroCode - eDEX-UI style hacker terminal. Dibuat oleh Nathan.
Jalankan: python3 brocode.py   (terminal minimal 100x30)"""
import curses, time, math, os, socket, threading, queue, platform, shlex
from collections import deque
import tools

try: import psutil
except ImportError: psutil = None

LOGO = [
 r"   ___    ___   ",
 r"  /   \  /   \  ",
 r" |  O  ||  O  | ",
 r"  \___/==\___/  ",
 r"   BROCODE v1.0 ",
]
BOOT = ["BroCode kernel init ...", "mount /dev/osint ........ OK", "loading module: nmap_wrapper",
 "loading module: dns/whois/geoip", "loading module: phishing_heuristics",
 "loading module: ssl/http inspector", "loading module: username_osint",
 "network interface up", "entropy pool seeded", "starting UI ...", "Welcome back, {user}"]
KEYS = ["` 1 2 3 4 5 6 7 8 9 0 - =", "Q W E R T Y U I O P [ ]", "A S D F G H J K L ; '", "Z X C V B N M , . /"]

def sysinfo():
    if psutil:
        cpu = psutil.cpu_percent(); m = psutil.virtual_memory().percent
        n = psutil.net_io_counters(); return cpu, m, n.bytes_sent, n.bytes_recv, time.time() - psutil.boot_time()
    try:
        load = os.getloadavg()[0] / (os.cpu_count() or 1) * 100
        mem = {l.split(":")[0]: int(l.split()[1]) for l in open("/proc/meminfo")}
        m = 100 - mem["MemAvailable"] / mem["MemTotal"] * 100
        up = float(open("/proc/uptime").read().split()[0])
    except Exception: load, m, up = 0, 0, 0
    return min(load, 100), m, 0, 0, up

def bar(p, w): 
    n = int(w * p / 100); return "[" + "|" * n + " " * (w - n) + f"] {p:3.0f}%"

def spark(vals, w):
    ch = " .:-=+*#%@"; vs = list(vals)[-w:]; mx = max(vs + [1])
    return "".join(ch[min(9, int(v / mx * 9))] for v in vs).rjust(w)

def fmt_up(s):
    s = int(s); return f"{s//86400}d {s%86400//3600:02d}:{s%3600//60:02d}:{s%60:02d}"

def globe(r, t):
    """Bola dunia ASCII berputar; mengembalikan list baris."""
    h, w = 2 * r + 1, 4 * r + 2
    grid = [[" "] * w for _ in range(h)]
    for la in range(-84, 90, 12):
        for lo in range(0, 360, 7):
            a, b = math.radians(la), math.radians(lo + t * 20)
            x, y, z = math.cos(a) * math.sin(b), math.sin(a), math.cos(a) * math.cos(b)
            if z < 0: continue
            cx, cy = int(r * 2 + x * r * 2), int(r - y * r)
            if 0 <= cx < w and 0 <= cy < h: grid[cy][cx] = "@" if z > .7 else "o" if z > .35 else "."
    return ["".join(row).rstrip() for row in grid]

ALIASES = {"nmap":"1","port":"2","ports":"2","discover":"3","host":"3","dns":"4","whois":"5","geo":"6",
 "ip":"6","headers":"7","http":"7","ssl":"8","tls":"8","sub":"9","subdomain":"9","phish":"a","phishing":"a",
 "user":"b","username":"b","trace":"c","traceroute":"c"}
M, R, G, C, Y = 1, 2, 3, 4, 5   # color pairs

class App:
    def __init__(s, scr):
        s.scr = scr; s.out = deque(maxlen=3000); s.q = queue.Queue(); s.buf = ""; s.hist = []; s.hi = 0
        s.scroll = 0; s.running = False; s.stop = False; s.lastkey = ("", 0); s.t0 = time.time()
        s.up = deque([0] * 60, 60); s.down = deque([0] * 60, 60); s.prev = None; s.stats = sysinfo(); s.lt = 0
        s.user = os.environ.get("USER", "operator"); s.host = socket.gethostname()
        for l in ("Ketik 'help' untuk daftar perintah. Contoh: nmap scanme.nmap.org",
                  "PERINGATAN: pakai hanya pada target milikmu / dengan izin tertulis.", ""):
            s.out.append(l)

    # ---- util gambar ----
    def put(s, y, x, txt, attr=0):
        H, W = s.scr.getmaxyx()
        if 0 <= y < H and 0 <= x < W:
            try: s.scr.addstr(y, x, txt[:W - x - (1 if y == H - 1 else 0)], attr)
            except curses.error: pass

    def panel(s, y, x, h, w, title):
        a = curses.color_pair(M)
        s.put(y, x, "┌─ " + title + " " + "─" * max(0, w - len(title) - 5) + "┐", a)
        for i in range(1, h - 1): s.put(y + i, x, "│", a); s.put(y + i, x + w - 1, "│", a)
        s.put(y + h - 1, x, "└" + "─" * (w - 2) + "┘", a)

    # ---- boot ----
    def boot(s):
        s.scr.erase(); H, W = s.scr.getmaxyx()
        for i, l in enumerate(LOGO): s.put(H // 2 - 8 + i, (W - len(l)) // 2, l, curses.color_pair(R) | curses.A_BOLD)
        for i, l in enumerate(BOOT):
            s.put(H // 2 - 2 + i, (W - 40) // 2, f"[{time.strftime('%H:%M:%S')}] " + l.format(user=s.user), curses.color_pair(M))
            s.scr.refresh(); time.sleep(0.12)
        time.sleep(0.5)

    # ---- data ----
    def update(s):
        now = time.time()
        if now - s.lt >= 1:
            st = sysinfo()
            if s.prev and st[2]:
                s.up.append(st[2] - s.prev[2]); s.down.append(st[3] - s.prev[3])
            elif not st[2]: s.up.append(0); s.down.append(0)
            s.prev = st; s.stats = st; s.lt = now
        while True:
            try: item = s.q.get_nowait()
            except queue.Empty: break
            if item is None: s.running = False; s.out.append("── selesai ──")
            else: s.out.append(item)
            s.scroll = 0

    # ---- command ----
    def run(s, cmd):
        s.out.append(f"{s.user}@brocode:~$ {cmd}")
        try: p = shlex.split(cmd)
        except ValueError: p = cmd.split()
        if not p: return
        c = p[0].lower()
        if c in ("quit", "exit", "q"): raise SystemExit
        if c == "clear": s.out.clear(); return
        if c == "help":
            s.out.extend(["Perintah:  <tool> <target>   contoh: nmap scanme.nmap.org",
              "           nmap <host> [quick|service|full|os]",
              "           stop (hentikan job) | clear | quit | PgUp/PgDn scroll", "Tool:"])
            for k, n, f, a, ex in tools.TOOLS: s.out.append(f"  [{k}] {n:<15}<{a}>  mis: {ex}")
            return
        if c == "stop": s.stop = True; return
        key = ALIASES.get(c, c)
        t = next((x for x in tools.TOOLS if x[0] == key), None)
        if not t: s.out.append(f"perintah tidak dikenal: {c} (ketik help)"); return
        if len(p) < 2: s.out.append(f"pakai: {c} <{t[3]}>   mis: {t[4]}"); return
        if s.running: s.out.append("job lain masih berjalan (ketik 'stop')"); return
        s.running, s.stop = True, False
        def job():
            try:
                for line in t[2](*p[1:3]):
                    if s.stop: s.q.put("[dihentikan]"); break
                    s.q.put(line)
            except Exception as e: s.q.put(f"[x] error: {e}")
            s.q.put(None)
        threading.Thread(target=job, daemon=True).start()

    def key(s, k):
        if k in (curses.KEY_ENTER, 10, 13):
            if s.buf.strip(): s.hist.append(s.buf); s.hi = len(s.hist); s.run(s.buf.strip())
            s.buf = ""
        elif k in (curses.KEY_BACKSPACE, 127, 8): s.buf = s.buf[:-1]
        elif k == curses.KEY_UP and s.hist: s.hi = max(0, s.hi - 1); s.buf = s.hist[s.hi]
        elif k == curses.KEY_DOWN and s.hist:
            s.hi = min(len(s.hist), s.hi + 1); s.buf = s.hist[s.hi] if s.hi < len(s.hist) else ""
        elif k == curses.KEY_PPAGE: s.scroll += 5
        elif k == curses.KEY_NPAGE: s.scroll = max(0, s.scroll - 5)
        elif k == 3 and s.running: s.stop = True
        elif 32 <= k < 127: s.buf += chr(k); s.lastkey = (chr(k).upper(), time.time())

    # ---- render ----
    def draw(s):
        s.scr.erase(); H, W = s.scr.getmaxyx()
        if H < 26 or W < 90: s.put(0, 0, f"Perbesar terminal (min 90x26), sekarang {W}x{H}"); return
        LW = RW = 28; CW = W - LW - RW; top, bot = 2, H - 8
        mag, red = curses.color_pair(M), curses.color_pair(R) | curses.A_BOLD
        cpu, mem, _, _, up = s.stats
        s.put(0, 1, "◉ BROCODE", red); s.put(0, W // 2 - 4, time.strftime("%H:%M:%S"), mag | curses.A_BOLD)
        s.put(0, W - len(s.host) - 14, f"{s.user}@{s.host}", mag)
        # kiri: sistem + network + tools
        s.panel(top - 1, 0, 8, LW, "SYSTEM")
        for i, l in enumerate([f"OS   {platform.system()} {platform.release()[:14]}", f"UP   {fmt_up(up)}",
                               "CPU " + bar(cpu, 12), "RAM " + bar(mem, 12), f"PY   {platform.python_version()}"]):
            s.put(top + i, 2, l)
        s.panel(top + 7, 0, 7, LW, "NETWORK TRAFFIC")
        s.put(top + 8, 2, "UP   " + spark(s.up, LW - 9), curses.color_pair(G))
        s.put(top + 9, 2, "DOWN " + spark(s.down, LW - 9), curses.color_pair(C))
        s.put(top + 10, 2, f"↑{s.up[-1]/1024:6.1f}K/s  ↓{s.down[-1]/1024:6.1f}K/s")
        mh = bot - (top + 14) + 2
        s.panel(top + 14, 0, mh, LW, "TOOLS")
        for i, (k, n, *_ ) in enumerate(tools.TOOLS[:mh - 2]): s.put(top + 15 + i, 2, f"[{k}] {n}", curses.color_pair(Y))
        # kanan: globe + info
        s.panel(top - 1, W - RW, 14, RW, "WORLD VIEW")
        for i, l in enumerate(globe(5, time.time() - s.t0)): s.put(top + i + 1, W - RW + 3, l, curses.color_pair(C))
        s.panel(top + 13, W - RW, bot - top - 11, RW, "STATUS")
        s.put(top + 14, W - RW + 2, "JOB   " + ("RUNNING ●" if s.running else "idle"), curses.color_pair(G if s.running else M))
        s.put(top + 15, W - RW + 2, f"LINES {len(s.out)}")
        s.put(top + 16, W - RW + 2, "nmap  " + ("ada" if __import__("shutil").which("nmap") else "bawaan"))
        for i, l in enumerate(LOGO[:4]): s.put(top + 18 + i, W - RW + 5, l, red) if top + 18 + i < bot else None
        # tengah: terminal
        s.panel(top - 1, LW, bot - top + 3, CW, "TERMINAL")
        rows = bot - top; lines = list(s.out); end = len(lines) - s.scroll; vis = lines[max(0, end - rows):end]
        for i, l in enumerate(vis):
            a = curses.color_pair(R) if l.startswith("[x]") or l.startswith("PERINGATAN") else curses.color_pair(G) if "open" in l or "FOUND" in l or " UP " in l else 0
            s.put(top + i, LW + 2, l[:CW - 4], a)
        s.put(bot, LW + 2, f"{s.user}@brocode:~$ {s.buf}█"[:CW - 4], mag | curses.A_BOLD)
        # bawah: keyboard virtual
        ky = H - 6; s.panel(ky, 0, 6, W, "KEYBOARD")
        for i, row in enumerate(KEYS):
            x = (W - len(row)) // 2
            for j, ch in enumerate(row):
                hit = ch != " " and ch == s.lastkey[0] and time.time() - s.lastkey[1] < 0.25
                s.put(ky + 1 + i, x + j, ch, (red | curses.A_REVERSE) if hit else mag)
        s.scr.refresh()

def main(scr):
    curses.curs_set(0); curses.start_color(); curses.use_default_colors()
    for i, c in ((M, curses.COLOR_MAGENTA), (R, curses.COLOR_RED), (G, curses.COLOR_GREEN),
                 (C, curses.COLOR_CYAN), (Y, curses.COLOR_YELLOW)): curses.init_pair(i, c, -1)
    app = App(scr); app.boot(); scr.timeout(80)
    try:
        while True:
            app.update(); app.draw(); k = scr.getch()
            if k != -1 and k != curses.KEY_RESIZE: app.key(k)
    except (SystemExit, KeyboardInterrupt): pass

if __name__ == "__main__":
    curses.wrapper(main)
