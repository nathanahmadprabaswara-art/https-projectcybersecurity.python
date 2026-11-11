#!/usr/bin/env python3
"""
GHOST ENGINE // Terminal Visual Engine
Demo visual murni (kosmetik) untuk terminal: matrix rain, boot sequence,
globe ASCII, wireframe 3D, torus, panel kode & hex yang bergulir.
Semua data bersifat simulasi/acak. Tidak ada koneksi jaringan.

Jalankan : python3 ghost_engine.py
Keluar   : tekan q atau Ctrl+C
Ubah nama: edit variabel NAME di bawah (pisahkan dua kata dengan spasi).
Ukuran terminal disarankan >= 100x30. Tanpa dependensi (hanya stdlib).
"""
import curses
import locale
import math
import random
import time

NAME = "GHOST ENGINE"
FPS = 30

# Durasi tiap fase (detik)
BOOT, GLOBE, WIRE, TORUS, FINALE = 6, 9, 7, 7, 6
CYCLE = BOOT + GLOBE + WIRE + TORUS + FINALE

G, C, B, W, Y = 1, 2, 3, 4, 5  # nomor color pair

FONT = {
    "A": ".#.|#.#|###|#.#|#.#", "B": "##.|#.#|##.|#.#|##.",
    "C": ".##|#..|#..|#..|.##", "D": "##.|#.#|#.#|#.#|##.",
    "E": "###|#..|##.|#..|###", "F": "###|#..|##.|#..|#..",
    "G": ".##|#..|#.#|#.#|.##", "H": "#.#|#.#|###|#.#|#.#",
    "I": "###|.#.|.#.|.#.|###", "J": "..#|..#|..#|#.#|.#.",
    "K": "#.#|#.#|##.|#.#|#.#", "L": "#..|#..|#..|#..|###",
    "M": "#.#|###|###|#.#|#.#", "N": "###|#.#|#.#|#.#|#.#",
    "O": ".#.|#.#|#.#|#.#|.#.", "P": "##.|#.#|##.|#..|#..",
    "Q": ".#.|#.#|#.#|##.|.##", "R": "##.|#.#|##.|#.#|#.#",
    "S": ".##|#..|.#.|..#|##.", "T": "###|.#.|.#.|.#.|.#.",
    "U": "#.#|#.#|#.#|#.#|###", "V": "#.#|#.#|#.#|#.#|.#.",
    "W": "#.#|#.#|###|###|#.#", "X": "#.#|#.#|.#.|#.#|#.#",
    "Y": "#.#|#.#|.#.|.#.|.#.", "Z": "###|..#|.#.|#..|###",
}

CODE = """class FrameEngine:
    def __init__(self):
        self.queue = deque()
        self.frame = 0
        self.mode = "local"

    def update(self, points):
        self.frame += 1
        for p in points:
            self.queue.append(proj(p))
        return self.frame

engine = FrameEngine()
for frame in scene.frames():
    pts = camera.project(frame)
    engine.update(pts)
    display.commit(engine)

# orbit: simulated links
def link(a, b, t):
    k = slerp(a, b, t)
    return k * (1 + 0.3 * sin(pi * t))
""".splitlines()

LOGS = [
    "node sync", "link established", "packet relayed", "route updated",
    "cache flushed", "handshake ok", "buffer swap", "frame committed",
    "entropy pool refill", "vector normalized", "mesh rebuilt",
]

BOOT_STEPS = [
    "loading kernel modules", "mapping memory regions", "starting render core",
    "building geometry tables", "calibrating projection", "spawning stream threads",
    "linking display buffer", "engine ready",
]


# ---------------------------------------------------------------- utilitas
def safe(scr, y, x, s, attr=0):
    try:
        scr.addstr(y, x, s, attr)
    except curses.error:
        pass


def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(G, curses.COLOR_GREEN, -1)
    curses.init_pair(C, curses.COLOR_CYAN, -1)
    curses.init_pair(B, curses.COLOR_BLUE, -1)
    curses.init_pair(W, curses.COLOR_WHITE, -1)
    curses.init_pair(Y, curses.COLOR_YELLOW, -1)


def col(n, bold=False, dim=False):
    a = curses.color_pair(n)
    if bold:
        a |= curses.A_BOLD
    if dim:
        a |= curses.A_DIM
    return a


def rot(x, y, z, ax, ay):
    x, z = x * math.cos(ay) + z * math.sin(ay), -x * math.sin(ay) + z * math.cos(ay)
    y, z = y * math.cos(ax) - z * math.sin(ax), y * math.sin(ax) + z * math.cos(ax)
    return x, y, z


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.buf = {}
        self.zb = {}

    def put(self, x, y, ch, attr, z=0.0):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            if z >= self.zb.get((x, y), -1e9):
                self.zb[(x, y)] = z
                self.buf[(x, y)] = (ch, attr)

    def line(self, x0, y0, x1, y1, ch, attr, z=0.0):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / max(n, 1)
            self.put(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, ch, attr, z)

    def blit(self, scr, oy, ox):
        for (x, y), (ch, attr) in self.buf.items():
            safe(scr, oy + y, ox + x, ch, attr)


# ---------------------------------------------------------------- rain
class Rain:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.y = [random.uniform(-h, 0) for _ in range(w)]
        self.v = [random.uniform(0.25, 0.9) for _ in range(w)]
        self.n = [random.randint(5, max(6, h // 2)) for _ in range(w)]

    def draw(self, scr, only_even=True):
        glyphs = "01ABCDEF<>/\\|=+*#%$"
        for x in range(0, self.w - 1, 2 if only_even else 1):
            self.y[x] += self.v[x]
            if self.y[x] - self.n[x] > self.h:
                self.y[x] = random.uniform(-8, 0)
                self.v[x] = random.uniform(0.25, 0.9)
            for k in range(self.n[x]):
                yy = int(self.y[x]) - k
                if 0 <= yy < self.h:
                    if k == 0:
                        a = col(W, bold=True)
                    elif k < 3:
                        a = col(G, bold=True)
                    else:
                        a = col(G, dim=True)
                    safe(scr, yy, x, random.choice(glyphs), a)


# ---------------------------------------------------------------- scene 3D
class Globe:
    def __init__(self):
        self.links = []

    @staticmethod
    def land(lat, lon):
        n = math.sin(2 * lon + 1) + math.cos(3 * lat) + 0.6 * math.sin(3 * lon - 2 * lat)
        return n > 0.55

    @staticmethod
    def sph(lat, lon):
        return (math.cos(lat) * math.cos(lon), math.sin(lat), math.cos(lat) * math.sin(lon))

    def render(self, cv, t):
        cx, cy = cv.w / 2, cv.h / 2
        r = max(3, min(cv.h / 2 - 1, cv.w / 4 - 2))
        ay, ax = t * 0.5, 0.35
        for i in range(36):
            lat = -math.pi / 2 + math.pi * i / 35
            for j in range(72):
                lon = 2 * math.pi * j / 72
                x, y, z = rot(*self.sph(lat, lon), ax, ay)
                px, py = cx + x * r * 2, cy - y * r
                land = self.land(lat, lon)
                if z > 0:
                    if land:
                        cv.put(px, py, "█", col(G, bold=z > 0.5), z)
                    elif (i + j) % 2 == 0:
                        cv.put(px, py, "·", col(C, dim=True), z)
                elif land and (i + j) % 3 == 0:
                    cv.put(px, py, ".", col(B, dim=True), z)
        for k in range(140):  # cincin orbit
            a = 2 * math.pi * k / 140
            x, y, z = rot(math.cos(a) * 1.4, 0, math.sin(a) * 1.4, 0.9, t * 0.2)
            cv.put(cx + x * r * 2, cy - y * r, "." if z < 0 else "o", col(C, dim=z < 0), z + 0.9)
        if random.random() < 0.07 and len(self.links) < 4:
            self.links.append((self.sph(random.uniform(-1.2, 1.2), random.uniform(0, 6.28)),
                               self.sph(random.uniform(-1.2, 1.2), random.uniform(0, 6.28)), t))
        alive = []
        for a, b, born in self.links:
            p = (t - born) / 2.0
            if p > 1:
                continue
            alive.append((a, b, born))
            for s in range(int(p * 30) + 1):
                u = s / 30
                v = [a[m] + (b[m] - a[m]) * u for m in range(3)]
                ln = math.sqrt(sum(c * c for c in v)) or 1
                k = (1 + 0.3 * math.sin(math.pi * u)) / ln
                x, y, z = rot(v[0] * k, v[1] * k, v[2] * k, ax, ay)
                if z > -0.1:
                    cv.put(cx + x * r * 2, cy - y * r, "*", col(Y, bold=True), z + 1)
        self.links = alive


def render_wire(cv, t):
    phi = (1 + 5 ** 0.5) / 2
    base = []
    for a in (-1, 1):
        for b in (-phi, phi):
            base += [(0, a, b), (a, b, 0), (b, 0, a)]
    edges = [(i, j) for i in range(12) for j in range(i + 1, 12)
             if abs(sum((base[i][m] - base[j][m]) ** 2 for m in range(3)) - 4) < 0.01]
    cx, cy = cv.w / 2, cv.h / 2
    s = max(3, min(cv.h / 2 - 1, cv.w / 4 - 2)) / 1.9

    def proj(p, sc, ax, ay):
        x, y, z = rot(*p, ax, ay)
        f = 4 / (4 - z)
        return cx + x * sc * f * 2, cy - y * sc * f, z

    pts = [proj(p, s, t * 0.4, t * 0.7) for p in base]
    for i, j in edges:
        a, b = pts[i], pts[j]
        cv.line(a[0], a[1], b[0], b[1], ".", col(C, dim=True), (a[2] + b[2]) / 2)
    cube = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    cp = [proj(p, s * 0.7, -t * 0.6, -t * 0.5) for p in cube]
    for i in range(8):
        for j in range(i + 1, 8):
            if sum(a != b for a, b in zip(cube[i], cube[j])) == 1:
                cv.line(cp[i][0], cp[i][1], cp[j][0], cp[j][1], "·", col(G), 1)
    for p in pts:
        cv.put(p[0], p[1], "◆", col(W, bold=True), p[2] + 2)
    for p in cp:
        cv.put(p[0], p[1], "■", col(G, bold=True), 3)


def render_torus(cv, t):
    R1, R2, K2 = 1.0, 2.0, 5.0
    K1 = min(cv.h * 0.667, cv.w / 2 / 1.2 * 0.9)
    A, Bb = t * 0.9, t * 0.5
    cA, sA, cB, sB = math.cos(A), math.sin(A), math.cos(Bb), math.sin(Bb)
    cx, cy = cv.w / 2, cv.h / 2
    shades = ".,-~:;=!*#$@"
    th = 0.0
    while th < 6.283:
        ct, st = math.cos(th), math.sin(th)
        ph = 0.0
        while ph < 6.283:
            cp, sp = math.cos(ph), math.sin(ph)
            ccx, ccy = R2 + R1 * ct, R1 * st
            x = ccx * (cB * cp + sA * sB * sp) - ccy * cA * sB
            y = ccx * (sB * cp - sA * cB * sp) + ccy * cA * cB
            z = K2 + cA * ccx * sp + ccy * sA
            L = cp * ct * sB - cA * ct * sp - sA * st + cB * (cA * st - ct * sA * sp)
            ooz = 1 / z
            ch = shades[max(0, min(11, int(L * 8)))] if L > 0 else "."
            a = col(G, bold=True) if L > 0.7 else col(C) if L > 0.2 else col(B, dim=True)
            cv.put(cx + 2 * K1 * x * ooz, cy - K1 * y * ooz, ch, a, ooz)
            ph += 0.05
        th += 0.12


# ---------------------------------------------------------------- panel UI
def box(scr, y, x, h, w, title="", attr=None):
    attr = attr if attr is not None else col(B)
    if h < 3 or w < 6:
        return
    safe(scr, y, x, "┌" + "─" * (w - 2) + "┐", attr)
    safe(scr, y + h - 1, x, "└" + "─" * (w - 2) + "┘", attr)
    for i in range(1, h - 1):
        safe(scr, y + i, x, "│", attr)
        safe(scr, y + i, x + w - 1, "│", attr)
    if title:
        safe(scr, y, x + 2, f" {title} ", col(G, bold=True))


class Dash:
    def __init__(self):
        self.src = []
        self.src_i = 0
        self.hex = [[random.randint(0, 255) for _ in range(8)] for _ in range(64)]
        self.addr = 0x4000
        self.log = []
        self.globe = Globe()
        self.last = 0.0

    def tick(self, t):
        if t - self.last > 0.12:
            self.last = t
            self.src.append(CODE[self.src_i % len(CODE)])
            self.src_i += 1
            self.addr += 8
            if random.random() < 0.6:
                self.log.append(f"{time.strftime('%H:%M:%S')} {random.choice(LOGS)} "
                                f"0x{random.randint(0, 65535):04X}")
        for _ in range(6):
            r = random.randrange(len(self.hex))
            self.hex[r][random.randrange(8)] = random.randint(0, 255)

    def draw(self, scr, H, W_, t, scene):
        self.tick(t)
        lw, rw = max(26, W_ // 4), max(28, W_ // 4)
        cw = W_ - lw - rw
        top, ph = 1, H - 3
        safe(scr, 0, 1, f"{NAME} // TERMINAL VISUAL ENGINE", col(C, bold=True))
        safe(scr, 0, W_ - 10, time.strftime("%H:%M:%S"), col(C))
        # kiri: source
        box(scr, top, 0, ph, lw, "SOURCE / LOCAL")
        for i, ln in enumerate(self.src[-(ph - 2):]):
            s = ln.strip()
            a = col(C, bold=True) if s.startswith(("def", "class")) else \
                col(B, dim=True) if s.startswith("#") else col(G)
            safe(scr, top + 1 + i, 2, ln[:lw - 4], a)
        # tengah: scene
        title = {"globe": "ORBIT / SIMULATED LINKS", "wire": "CORE / GEOMETRY ENGINE",
                 "torus": "RENDER / TORUS"}[scene]
        box(scr, top, lw, ph, cw, title)
        cv = Canvas(cw - 2, ph - 2)
        if scene == "globe":
            self.globe.render(cv, t)
        elif scene == "wire":
            render_wire(cv, t)
        else:
            render_torus(cv, t)
        cv.blit(scr, top + 1, lw + 1)
        # kanan: hex + stream
        rx = lw + cw
        hh = ph // 2
        box(scr, top, rx, hh, rw, "HEX / GENERATOR")
        for i in range(hh - 2):
            row = self.hex[i % len(self.hex)]
            line = f"{(self.addr - 8 * (hh - 2 - i)) & 0xFFFF:04X} " + " ".join(f"{b:02X}" for b in row)
            safe(scr, top + 1 + i, rx + 2, line[:rw - 4], col(G, dim=i % 2 == 0))
        box(scr, top + hh, rx, ph - hh, rw, "STREAM / SIMULATED")
        for i, ln in enumerate(self.log[-(ph - hh - 2):]):
            safe(scr, top + hh + 1 + i, rx + 2, ln[:rw - 4], col(C))
        # footer
        cpu = int(5 + 4 * (1 + math.sin(t)) * 4)
        bar = "█" * (cpu // 4) + "░" * (10 - cpu // 4)
        safe(scr, H - 1, 1, f"MODE:{scene.upper():<6} CPU {bar} {cpu:>2}%  FPS:{FPS}  [q] quit",
             col(G, dim=True))


# ---------------------------------------------------------------- layar penuh
def draw_boot(scr, H, W_, rain, p, t):
    rain.draw(scr)
    bw, bh = min(60, W_ - 4), 12
    y, x = (H - bh) // 2, (W_ - bw) // 2
    for i in range(bh):
        safe(scr, y + i, x, " " * bw)
    box(scr, y, x, bh, bw, "INITIALIZATION SEQUENCE", col(G))
    n = min(len(BOOT_STEPS), int(p * (len(BOOT_STEPS) + 1)))
    for i in range(n):
        ok = i < n - 1 or p >= 1
        safe(scr, y + 2 + i % 6, x + 3,
             f"[{'OK' if ok else '..'}] {BOOT_STEPS[i]}"[:bw - 6], col(G if ok else Y))
    fill = int((bw - 8) * p)
    safe(scr, y + bh - 3, x + 3, "█" * fill + "░" * (bw - 8 - fill), col(C, bold=True))
    safe(scr, y + bh - 2, x + 3, f"{int(p * 100):>3}%", col(W, bold=True))
    t0 = f"{NAME} // TERMINAL VISUAL ENGINE"
    safe(scr, max(0, y - 2), (W_ - len(t0)) // 2, t0, col(C, bold=True))


def draw_finale(scr, H, W_, rain, t):
    rain.draw(scr)
    words = NAME.upper().split()
    sx = 2
    widest = max(sum(4 * sx if True else 0 for _ in w) for w in words)
    if widest > W_ - 2:
        sx = 1
    total_h = len(words) * 6
    y = max(1, (H - total_h) // 2)
    for wd in words:
        wlen = len(wd) * (3 * sx + 1)
        x = max(0, (W_ - wlen) // 2)
        for ch_i, ch in enumerate(wd):
            glyph = FONT.get(ch, "...|...|...|...|...").split("|")
            for ry, rowp in enumerate(glyph):
                for rx, c in enumerate(rowp):
                    if c == "#":
                        safe(scr, y + ry, x + ch_i * (3 * sx + 1) + rx * sx, "█" * sx,
                             col(G, bold=True))
                    else:
                        safe(scr, y + ry, x + ch_i * (3 * sx + 1) + rx * sx, " " * sx)
        y += 6
    msg = "[ SIMULATION COMPLETE ]"
    safe(scr, min(H - 2, y + 1), (W_ - len(msg)) // 2, msg, col(C, bold=True))


def main(scr):
    locale.setlocale(locale.LC_ALL, "")
    curses.curs_set(0)
    init_colors()
    scr.timeout(0)
    dash, rain, size = Dash(), None, (0, 0)
    start = time.time()
    while True:
        t0 = time.time()
        if scr.getch() in (ord("q"), ord("Q"), 27):
            return
        H, W_ = scr.getmaxyx()
        if (H, W_) != size:
            size, rain = (H, W_), Rain(W_, H)
            scr.clear()
        scr.erase()
        t = time.time() - start
        c = t % CYCLE
        if H < 20 or W_ < 70:
            safe(scr, 0, 0, "Perbesar terminal (min 70x20)", col(Y, bold=True))
        elif c < BOOT:
            draw_boot(scr, H, W_, rain, c / BOOT, t)
        elif c < BOOT + GLOBE:
            dash.draw(scr, H, W_, t, "globe")
        elif c < BOOT + GLOBE + WIRE:
            dash.draw(scr, H, W_, t, "wire")
        elif c < BOOT + GLOBE + WIRE + TORUS:
            dash.draw(scr, H, W_, t, "torus")
        else:
            draw_finale(scr, H, W_, rain, t)
        scr.refresh()
        time.sleep(max(0, 1 / FPS - (time.time() - t0)))


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
