#!/usr/bin/env python3
"""BroCode - eDEX-UI style hacker terminal. Dibuat oleh Nathan.
Jalankan: python3 brocode.py   (terminal minimal 100x30)"""
import curses, time, math, os, socket, threading, queue, platform, shlex
from collections import deque
import tools, fx, random

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

def fmt_up(s):
    s = int(s); return f"{s//86400}d {s%86400//3600:02d}:{s%3600//60:02d}:{s%60:02d}"

def level(p): return G if p < 50 else Y if p < 80 else R
def bar(p, w):
    n = int(w * p / 100); return "▰" * n, "▱" * (w - n)
SPIN = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

ALIASES = {"nmap":"1","port":"2","ports":"2","discover":"3","host":"3","dns":"4","whois":"5","geo":"6",
 "ip":"6","headers":"7","http":"7","ssl":"8","tls":"8","sub":"9","subdomain":"9","phish":"a","phishing":"a",
 "user":"b","username":"b","trace":"c","traceroute":"c"}
M, R, G, C, Y = 1, 2, 3, 4, 5   # color pairs

class App:
    def __init__(s, scr):
        s.scr = scr; s.out = deque(maxlen=3000); s.q = queue.Queue(); s.buf = ""; s.hist = []; s.hi = 0
        s.scroll = 0; s.running = False; s.stop = False; s.glow = {}; s.t0 = time.time(); s.frame = 0
        s.up = deque([0] * 60, 60); s.down = deque([0] * 60, 60); s.prev = None; s.stats = sysinfo(); s.lt = 0
        s.user = os.environ.get("USER", "operator"); s.host = socket.gethostname()
        s.cur = None; s.n = 0; s.active = ""; s.glitch_until = 0; s.has_nmap = bool(__import__("shutil").which("nmap"))
        s.out.extend(["Ketik 'help' untuk daftar perintah. Contoh: nmap scanme.nmap.org",
                      "PERINGATAN: pakai hanya pada target milikmu / dengan izin tertulis.", ""])

    # ---- util gambar ----
    def put(s, y, x, txt, attr=0):
        H, W = s.scr.getmaxyx()
        if 0 <= y < H and 0 <= x < W:
            try: s.scr.addstr(y, x, txt[:W - x - (1 if y == H - 1 else 0)], attr)
            except curses.error: pass

    def panel(s, y, x, h, w, title, hot=False):
        t = time.time() - s.t0; pulse = curses.A_BOLD if math.sin(t * 2 + x * .1) > 0 else curses.A_DIM
        a = curses.color_pair(R if hot else M) | pulse
        s.put(y, x, "┌─", a); s.put(y, x + w - 1, "┐", a)
        s.put(y, x + 4 + len(title), "─" * max(0, w - len(title) - 5), a)
        pos = int(t * 6) % (len(title) + 8)           # sorot yang berjalan di judul
        for i, ch in enumerate(" " + title + " "):
            hl = abs(i - pos) < 2
            s.put(y, x + 2 + i, ch, curses.color_pair(C if hl else M) | curses.A_BOLD)
        for i in range(1, h - 1): s.put(y + i, x, "│", a); s.put(y + i, x + w - 1, "│", a)
        s.put(y + h - 1, x, "└" + "─" * (w - 2) + "┘", a)

    # ---- boot cinematic ----
    def boot(s):
        scr = s.scr; H, W = scr.getmaxyx(); rain = fx.Rain(W, H); scr.timeout(0)
        def frame(lines_done, logo_p, prog):
            scr.erase(); rain.step()
            for y, x, ch, k in rain.cells():
                s.put(y, x, ch, curses.color_pair(G if k == 0 else M) | (curses.A_BOLD if k < 2 else curses.A_DIM))
            ly = H // 2 - 9
            for i, l in enumerate(LOGO):
                txt = l if logo_p >= 1 else fx.glitch(l, 1 - logo_p)
                s.put(ly + i, (W - len(l)) // 2, txt, curses.color_pair(R) | curses.A_BOLD)
            bx = (W - 54) // 2
            for i, l in enumerate(BOOT[:lines_done]):
                ok = i < lines_done - 1; s.put(H // 2 - 3 + i, bx - 1, " " * 56)
                s.put(H // 2 - 3 + i, bx, f"[{time.strftime('%H:%M:%S')}] " + l.format(user=s.user), curses.color_pair(G if ok else Y))
                if ok: s.put(H // 2 - 3 + i, bx + 50, "OK", curses.color_pair(G) | curses.A_BOLD)
            n = int(44 * prog); s.put(H // 2 + 9, bx, "█" * n + "░" * (44 - n) + f" {int(prog*100):3d}%", curses.color_pair(M) | curses.A_BOLD)
            scr.refresh(); time.sleep(0.035)
        for step in range(len(BOOT) + 1):
            for sub in range(4): frame(step, min(1, (step * 4 + sub) / 14), (step * 4 + sub) / (len(BOOT) * 4 + 4))
        for _ in range(10): frame(len(BOOT), 1, 1.0)
        # transisi: UI tersapu dari atas ke bawah
        scr.timeout(40)
        for i in range(1, 21): s.frame_ui(reveal=i / 20); time.sleep(0.02)

    # ---- data ----
    def update(s):
        now = time.time(); s.frame += 1
        if now - s.lt >= 1:
            st = sysinfo()
            if s.prev and st[2]: s.up.append(st[2] - s.prev[2]); s.down.append(st[3] - s.prev[3])
            elif not st[2]: s.up.append(random.randint(0, 3000)); s.down.append(random.randint(0, 9000))
            s.prev = st; s.stats = st; s.lt = now
        if random.random() < .006: s.glitch_until = now + .15
        # typewriter: anggaran karakter per frame, naik kalau antrean menumpuk
        budget = 30 + 12 * s.q.qsize()
        while budget > 0:
            if s.cur is None:
                try: item = s.q.get_nowait()
                except queue.Empty: break
                if item is None: s.running = False; s.out.append("── selesai ──"); continue
                s.cur, s.n = item, 0
            take = min(budget, len(s.cur) - s.n); s.n += take; budget -= max(take, 1)
            if s.n >= len(s.cur): s.out.append(s.cur); s.cur = None; s.scroll = 0

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
        s.running, s.stop = True, False; s.active = t[0]
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
            s.glow["ENTER"] = time.time()
            if s.buf.strip(): s.hist.append(s.buf); s.hi = len(s.hist); s.run(s.buf.strip())
            s.buf = ""
        elif k in (curses.KEY_BACKSPACE, 127, 8): s.buf = s.buf[:-1]; s.glow["BKSP"] = time.time()
        elif k == curses.KEY_UP and s.hist: s.hi = max(0, s.hi - 1); s.buf = s.hist[s.hi]
        elif k == curses.KEY_DOWN and s.hist:
            s.hi = min(len(s.hist), s.hi + 1); s.buf = s.hist[s.hi] if s.hi < len(s.hist) else ""
        elif k == curses.KEY_PPAGE: s.scroll += 5
        elif k == curses.KEY_NPAGE: s.scroll = max(0, s.scroll - 5)
        elif k == 3 and s.running: s.stop = True
        elif 32 <= k < 127:
            s.buf += chr(k); s.glow["SPACE" if k == 32 else chr(k).upper()] = time.time()

    # ---- render ----
    def cell_attr(s, kind):
        return {0: curses.color_pair(M) | curses.A_DIM, 1: curses.color_pair(C) | curses.A_BOLD,
                2: curses.color_pair(M), 3: curses.A_DIM, 4: curses.color_pair(R) | curses.A_BOLD,
                5: curses.color_pair(G) | curses.A_BOLD}[kind]

    def blit(s, y, x, cells):
        for j, row in enumerate(cells):
            for i, (ch, k) in enumerate(row):
                if ch != " ": s.put(y + j, x + i, ch, s.cell_attr(k))

    def header(s, W, now):
        t = now - s.t0; pos = int(t * 40) % (W + 20)
        for x in range(W): s.put(0, x, "━" if abs(x - pos) < 10 else "─", curses.color_pair(C if abs(x - pos) < 10 else M) | curses.A_DIM)
        title = " ◉ " + (fx.glitch("BROCODE", .4) if now < s.glitch_until else "BROCODE") + " "
        s.put(0, 1, title, curses.color_pair(R) | curses.A_BOLD)
        clk = time.strftime(" %H:%M:%S ") if int(t * 2) % 2 else time.strftime(" %H %M %S ")
        s.put(0, W // 2 - 5, clk, curses.color_pair(C) | curses.A_BOLD); s.put(0, W // 2 + 7, time.strftime(" %a %d %b %Y "), curses.color_pair(M))
        s.put(0, W - len(s.host) - len(s.user) - 5, f" {s.user}@{s.host} ", curses.color_pair(G))

    def gauge(s, y, x, label, p, w):
        on, off = bar(p, w)
        s.put(y, x, label); s.put(y, x + 4, on, curses.color_pair(level(p)) | curses.A_BOLD)
        s.put(y, x + 4 + len(on), off, curses.color_pair(M) | curses.A_DIM); s.put(y, x + 5 + w, f"{p:3.0f}%")

    def frame_ui(s, reveal=1.0):
        s.draw(); H, W = s.scr.getmaxyx(); cut = int(H * reveal)
        if reveal < 1:
            for y in range(cut, H): s.scr.move(y, 0); s.scr.clrtoeol()
            s.put(cut, 0, "▀" * (W - 1), curses.color_pair(C) | curses.A_BOLD)
        s.scr.refresh()

    def draw(s):
        s.scr.erase(); H, W = s.scr.getmaxyx(); now = time.time(); t = now - s.t0
        if H < 28 or W < 90: s.put(0, 0, f"Perbesar terminal (min 90x28), sekarang {W}x{H}"); return
        LW = RW = 28; CW = W - LW - RW; top, bot = 2, H - 9
        mag = curses.color_pair(M); cpu, mem, _, _, up = s.stats
        s.header(W, now)
        # kiri
        s.panel(top - 1, 0, 8, LW, "SYSTEM")
        s.put(top, 2, f"OS   {platform.system()} {platform.release()[:14]}"); s.put(top + 1, 2, f"UP   {fmt_up(up)}")
        s.gauge(top + 2, 2, "CPU ", cpu, 11); s.gauge(top + 3, 2, "RAM ", mem, 11)
        s.put(top + 4, 2, f"PY   {platform.python_version()}   CORES {os.cpu_count()}")
        s.panel(top + 7, 0, 7, LW, "NETWORK TRAFFIC")
        s.put(top + 8, 2, "UP ", curses.color_pair(G)); s.put(top + 8, 5, fx.spark(s.up, LW - 8), curses.color_pair(G) | curses.A_BOLD)
        s.put(top + 9, 2, "DN ", curses.color_pair(C)); s.put(top + 9, 5, fx.spark(s.down, LW - 8), curses.color_pair(C) | curses.A_BOLD)
        s.put(top + 10, 2, f"↑{s.up[-1]/1024:6.1f}K/s  ↓{s.down[-1]/1024:6.1f}K/s", mag)
        mh = bot - (top + 14) + 2; s.panel(top + 14, 0, mh, LW, "TOOLS", hot=s.running)
        for i, (k, n, *_ ) in enumerate(tools.TOOLS[:mh - 2]):
            on = s.running and s.active == k
            s.put(top + 15 + i, 2, ("▶ " if on else "  ") + f"[{k}] {n}" + (" " + SPIN[int(t * 12) % 10] if on else ""),
                  curses.color_pair(R if on else Y) | (curses.A_BOLD if on else 0))
        # kanan
        s.panel(top - 1, W - RW, 13, RW, "WORLD VIEW"); s.blit(top, W - RW + 2, fx.globe(5, t))
        sh = bot - 12; s.panel(top + 12, W - RW, sh, RW, "STATUS", hot=s.running)
        s.put(top + 13, W - RW + 2, "JOB   " + (SPIN[int(t * 12) % 10] + " RUNNING" if s.running else "● idle"), curses.color_pair(R if s.running else G) | curses.A_BOLD)
        s.put(top + 14, W - RW + 2, f"LINES {len(s.out)}   NMAP {'ada' if s.has_nmap else 'bawaan'}")
        if sh >= 13: s.blit(top + 15, W - RW + 7, fx.radar(3, t))
        # tengah
        s.panel(top - 1, LW, bot - top + 3, CW, "TERMINAL", hot=s.running)
        rows = bot - top; lines = list(s.out)
        if s.cur is not None: lines.append(s.cur[:s.n] + "▌")
        wd = CW - 4; wr = []
        for l in lines[-(rows * 3):]:
            wr.extend([l[i:i + wd] for i in range(0, max(len(l), 1), wd)])
        end = len(wr) - s.scroll; vis = wr[max(0, end - rows):end]
        for i, l in enumerate(vis):
            a = (curses.color_pair(R) if l.startswith(("[x]", "PERINGATAN")) else curses.color_pair(Y) if l.lstrip().startswith("[+") or l.startswith("[!]")
                 else curses.color_pair(G) if any(w in l for w in ("open", "FOUND", " UP ", "[OK]")) else curses.color_pair(C) | curses.A_BOLD if l.startswith(("Skor", "Scanning", "──")) else 0)
            s.put(top + i, LW + 2, l[:CW - 4], a)
        s.put(bot, LW + 2, f"{s.user}@brocode:~$ ", curses.color_pair(R) | curses.A_BOLD)
        s.put(bot, LW + 2 + len(s.user) + 12, s.buf[-(CW - len(s.user) - 20):] + ("█" if int(t * 2.5) % 2 else " "), mag | curses.A_BOLD)
        s.keyboard(H, W, now)

    def keyboard(s, H, W, now):
        ky = H - 7; s.panel(ky, 0, 7, W, "KEYBOARD")
        def attr(name):
            age = now - s.glow.get(name, 0)
            if age < .12: return curses.color_pair(R) | curses.A_BOLD | curses.A_REVERSE
            if age < .35: return curses.color_pair(R) | curses.A_BOLD
            if age < .7: return curses.color_pair(Y)
            return curses.color_pair(M)
        for i, row in enumerate(KEYS):
            ks = row.split(); x = (W - len(ks) * 4) // 2 + i * 2
            for j, ch in enumerate(ks): s.put(ky + 1 + i, x + j * 4, f"[{ch}]", attr(ch))
        x = (W - 52) // 2 - 4
        s.put(ky + 5, x, "[BKSP]", attr("BKSP")); s.put(ky + 5, x + 7, "[" + "SPACE".center(30) + "]", attr("SPACE")); s.put(ky + 5, x + 40, "[ENTER]", attr("ENTER"))

def main(scr):
    curses.curs_set(0); curses.start_color(); curses.use_default_colors()
    for i, c in ((M, curses.COLOR_MAGENTA), (R, curses.COLOR_RED), (G, curses.COLOR_GREEN),
                 (C, curses.COLOR_CYAN), (Y, curses.COLOR_YELLOW)): curses.init_pair(i, c, -1)
    app = App(scr); app.boot(); scr.timeout(40)
    try:
        while True:
            app.update(); app.frame_ui(); k = scr.getch()
            if k != -1 and k != curses.KEY_RESIZE: app.key(k)
    except (SystemExit, KeyboardInterrupt): pass

if __name__ == "__main__":
    curses.wrapper(main)
