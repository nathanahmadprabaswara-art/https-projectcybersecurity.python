#!/usr/bin/env python3
"""
GHOST ENGINE // Terminal Visual Engine
Demo visual murni (kosmetik) untuk terminal: matrix rain, boot sequence,
globe ASCII, wireframe 3D, torus, panel kode & hex yang bergulir.
Semua data bersifat simulasi/acak. Tidak ada koneksi jaringan.

Jalankan : python3 ghost_engine.py
Keluar   : tekan q atau Ctrl+C
Setelah intro selesai (atau tekan Enter untuk lewati), muncul menu OSINT
(terintegrasi di file ini): tool pasif berbasis domain/IP. Gunakan hanya pada target
milikmu atau yang kamu punya izin untuk dianalisis.
Ubah nama: edit variabel NAME di bawah (pisahkan dua kata dengan spasi).
Ukuran terminal disarankan >= 100x30. Tanpa dependensi (hanya stdlib).
"""
import curses
import json
import locale
import math
import os
import random
import re
import socket
import ssl
import struct
import threading
import time
import types
import urllib.error
import urllib.request

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

    def draw(self, scr, oy=0, ox=0, only_even=True):
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
                    safe(scr, oy + yy, ox + x, random.choice(glyphs), a)


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


# ====================================================================
# OSINT TOOLKIT (pasif, hanya domain/IP). Gunakan hanya pada target milikmu
# atau yang kamu punya izin untuk dianalisis.
# Tiap tool: fungsi(target) -> list baris. Awalan: '## ' judul, '+ ' baik,
# '! ' peringatan, '- ' info redup. Daftarkan tool baru di list TOOLS.
# ====================================================================
UA = "Mozilla/5.0 (compatible; ghost-engine-osint/1.0)"
TIMEOUT = 8

DOMAIN_RE = re.compile(r"^(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")


# ------------------------------------------------------------ validasi
def clean_target(s):
    s = s.strip().lower()
    s = re.sub(r"^[a-z][a-z0-9+.-]*://", "", s)
    s = re.split(r"[/?#]", s)[0]
    s = s.split("@")[-1]
    if s.count(":") == 1:
        s = s.split(":")[0]
    return s.rstrip(".")


def is_domain(s):
    return bool(DOMAIN_RE.match(s))


def is_ip(s):
    for fam in (socket.AF_INET, socket.AF_INET6):
        try:
            socket.inet_pton(fam, s)
            return True
        except (OSError, ValueError):
            pass
    return False


def validate(tool, raw):
    t = clean_target(raw)
    if not t:
        raise ValueError("Target kosong")
    if tool["accepts"] == "domain":
        if not is_domain(t):
            raise ValueError("Masukkan nama domain, mis. example.com")
    elif not (is_domain(t) or is_ip(t)):
        raise ValueError("Masukkan domain atau alamat IP")
    return t


# ------------------------------------------------------------ DNS (UDP murni)
QTYPES = {"A": 1, "NS": 2, "CNAME": 5, "MX": 15, "TXT": 16, "AAAA": 28}


def _resolvers():
    try:
        with open("/etc/resolv.conf") as f:
            for line in f:
                p = line.split()
                if len(p) > 1 and p[0] == "nameserver" and ":" not in p[1]:
                    yield p[1]
    except OSError:
        pass
    yield "1.1.1.1"
    yield "8.8.8.8"


def _build_query(name, qtype):
    hdr = struct.pack(">HHHHHH", random.randint(0, 65535), 0x0100, 1, 0, 0, 0)
    q = b"".join(bytes([len(p)]) + p.encode("idna") for p in name.split(".")) + b"\0"
    return hdr + q + struct.pack(">HH", qtype, 1)


def _read_name(data, off):
    labels, jumped, end, hops = [], False, off, 0
    while True:
        n = data[off]
        if n == 0:
            off += 1
            break
        if n & 0xC0 == 0xC0:
            ptr = ((n & 0x3F) << 8) | data[off + 1]
            if not jumped:
                end = off + 2
            jumped = True
            off = ptr
            hops += 1
            if hops > 20:
                raise ValueError("loop kompresi DNS")
            continue
        labels.append(data[off + 1:off + 1 + n].decode("ascii", "replace"))
        off += 1 + n
    return ".".join(labels), (end if jumped else off)


class NXDomain(OSError):
    pass


def _parse_response(data):
    rcode = struct.unpack(">H", data[2:4])[0] & 0xF
    if rcode == 3:
        raise NXDomain("domain tidak ditemukan (NXDOMAIN)")
    if rcode != 0:
        raise OSError(f"resolver membalas galat (rcode {rcode})")
    qd, an = struct.unpack(">HH", data[4:8])
    off = 12
    for _ in range(qd):
        _, off = _read_name(data, off)
        off += 4
    out = []
    for _ in range(an):
        _, off = _read_name(data, off)
        rtype, _, ttl, rlen = struct.unpack(">HHIH", data[off:off + 10])
        off += 10
        rd = data[off:off + rlen]
        if rtype == 1 and rlen == 4:
            out.append(("A", socket.inet_ntoa(rd), ttl))
        elif rtype == 28 and rlen == 16:
            out.append(("AAAA", socket.inet_ntop(socket.AF_INET6, rd), ttl))
        elif rtype in (2, 5):
            n, _ = _read_name(data, off)
            out.append(("NS" if rtype == 2 else "CNAME", n, ttl))
        elif rtype == 15:
            pref = struct.unpack(">H", rd[:2])[0]
            n, _ = _read_name(data, off + 2)
            out.append(("MX", f"{pref} {n}", ttl))
        elif rtype == 16:
            txt, i = b"", 0
            while i < len(rd):
                ln = rd[i]
                txt += rd[i + 1:i + 1 + ln]
                i += 1 + ln
            out.append(("TXT", txt.decode("utf-8", "replace"), ttl))
        off += rlen
    return out


def dns_query(name, rtype):
    pkt, last = _build_query(name, QTYPES[rtype]), None
    for srv in _resolvers():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(3)
            s.sendto(pkt, (srv, 53))
            data, _ = s.recvfrom(4096)
            s.close()
            return _parse_response(data)
        except NXDomain:
            raise
        except Exception as e:  # noqa: BLE001
            last = e
    raise OSError(f"DNS gagal: {last}")


def tool_dns(t):
    out = [f"## DNS RECORDS: {t}"]
    for rt in ("A", "AAAA", "CNAME", "NS", "MX", "TXT"):
        try:
            rows = [r for r in dns_query(t, rt) if r[0] == rt]
        except NXDomain as e:
            return out + [f"! {e}"]
        except OSError as e:
            out.append(f"! {rt}: {e}")
            continue
        if not rows:
            out.append(f"- {rt:<5} (kosong)")
        for _, val, ttl in rows:
            out.append(f"{rt:<6}{val}   (ttl {ttl})")
    out.append("")
    out.append("## EMAIL POLICY")
    try:
        txt = [r[1] for r in dns_query(t, "TXT")]
        spf = [x for x in txt if x.lower().startswith("v=spf1")]
        out.append(("+ SPF   : " + spf[0]) if spf else "! SPF   : tidak ditemukan")
        dm = [r[1] for r in dns_query("_dmarc." + t, "TXT") if "dmarc" in r[1].lower()]
        out.append(("+ DMARC : " + dm[0]) if dm else "! DMARC : tidak ditemukan")
    except OSError as e:
        out.append(f"! {e}")
    return out


# ------------------------------------------------------------ WHOIS
WHOIS_KEYS = {
    "domain name", "registrar", "registrar url", "creation date", "created",
    "updated date", "last updated", "registry expiry date", "registrar registration expiration date",
    "expiry date", "expires", "name server", "nserver", "domain status", "status", "dnssec",
    "netname", "country", "orgname", "org-name", "organization", "descr", "cidr", "inetnum",
    "netrange", "route", "origin", "originas", "nettype",
}


def _whois_raw(server, q):
    with socket.create_connection((server, 43), timeout=TIMEOUT) as s:
        s.sendall((q + "\r\n").encode())
        buf = b""
        while len(buf) < 200000:
            d = s.recv(4096)
            if not d:
                break
            buf += d
    return buf.decode("utf-8", "replace")


def _whois_fields(raw):
    seen, out = set(), []
    for line in raw.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip().lower(), v.strip()
        if k in WHOIS_KEYS and v and "@" not in v and (k, v) not in seen:
            seen.add((k, v))
            out.append(f"{k:<26}{v}")
    return out[:60]


def tool_whois(t):
    raw = _whois_raw("whois.iana.org", t)
    m = re.search(r"^refer:\s*(\S+)", raw, re.M | re.I)
    server = m.group(1) if m else "whois.iana.org"
    raws = [raw]
    if m:
        raws.append(_whois_raw(server, t))
        m2 = re.search(r"^registrar whois server:\s*(\S+)", raws[-1], re.M | re.I)
        if m2 and m2.group(1).lower() != server.lower():
            try:
                raws.append(_whois_raw(m2.group(1), t))
                server = m2.group(1)
            except OSError:
                pass
    fields = []
    for r in reversed(raws):
        fields = _whois_fields(r)
        if len(fields) >= 3:
            break
    out = [f"## WHOIS: {t}", f"- server: {server}"]
    out += fields or ["! Tidak ada field publik yang bisa ditampilkan"]
    out.append("- data kontak pribadi sengaja tidak ditampilkan")
    return out


# ------------------------------------------------------------ HTTP
def _get(url, timeout=TIMEOUT, limit=300000):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        r = e
    try:
        body = r.read(limit)
        status = getattr(r, "status", None) or r.code
        return r.geturl(), status, r.headers, body
    finally:
        r.close()


SEC_HEADERS = [
    ("Strict-Transport-Security", "HSTS"),
    ("Content-Security-Policy", "CSP"),
    ("X-Frame-Options", "Anti-clickjacking"),
    ("X-Content-Type-Options", "No-sniff"),
    ("Referrer-Policy", "Referrer policy"),
    ("Permissions-Policy", "Permissions policy"),
]


def tool_http(t):
    last = None
    for scheme in ("https", "http"):
        try:
            url, status, hdr, _ = _get(f"{scheme}://{t}/", limit=2000)
            break
        except Exception as e:  # noqa: BLE001
            last = e
    else:
        raise OSError(f"Tidak bisa terhubung: {last}")
    out = ["## HTTP RESPONSE", f"URL akhir : {url}", f"Status    : {status}"]
    for h in ("Server", "X-Powered-By", "Via", "Content-Type", "Last-Modified", "X-Generator"):
        if hdr.get(h):
            out.append(f"{h:<10}: {hdr.get(h)}")
    out += ["", "## SECURITY HEADERS"]
    for h, label in SEC_HEADERS:
        if hdr.get(h):
            out.append(f"+ {label:<18} {hdr.get(h)[:80]}")
        elif h == "Strict-Transport-Security" and not url.startswith("https"):
            out.append(f"! {label:<18} tidak relevan (situs tidak memakai HTTPS)")
        else:
            out.append(f"! {label:<18} tidak ada")
    return out


def tool_robots(t):
    out = []
    for path in ("/robots.txt", "/.well-known/security.txt"):
        out.append(f"## {path}")
        try:
            _, status, _, body = _get(f"https://{t}{path}", limit=20000)
            text = body.decode("utf-8", "replace")
            if status == 200 and text.strip() and "<html" not in text[:300].lower():
                out += text.splitlines()[:40]
            else:
                out.append(f"- tidak ada (HTTP {status})")
        except Exception as e:  # noqa: BLE001
            out.append(f"! gagal: {e}")
        out.append("")
    return out


# ------------------------------------------------------------ TLS
def tool_tls(t, port=443):
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((t, port), timeout=TIMEOUT) as sk:
            with ctx.wrap_socket(sk, server_hostname=t) as ss:
                cert, ver, cipher = ss.getpeercert(), ss.version(), ss.cipher()
    except ssl.SSLCertVerificationError as e:
        return ["## TLS CERTIFICATE", f"! Verifikasi sertifikat gagal: {e.verify_message}"]

    def flat(rdn):
        return {k: v for part in rdn for k, v in part}

    subj, iss = flat(cert.get("subject", ())), flat(cert.get("issuer", ()))
    left = (ssl.cert_time_to_seconds(cert["notAfter"]) - time.time()) / 86400
    out = ["## TLS CERTIFICATE",
           f"Subject   : {subj.get('commonName', '-')}",
           f"Issuer    : {iss.get('organizationName', '-')} ({iss.get('commonName', '-')})",
           f"Berlaku   : {cert['notBefore']}  ->  {cert['notAfter']}",
           (f"+ Sisa masa berlaku {left:.0f} hari" if left > 14 else f"! Sisa masa berlaku {left:.0f} hari"),
           f"Protokol  : {ver}",
           f"Cipher    : {cipher[0]}", "", "## SUBJECT ALT NAMES"]
    sans = [v for k, v in cert.get("subjectAltName", ()) if k == "DNS"]
    out += [f"  {s}" for s in sans[:60]] or ["- (tidak ada)"]
    if len(sans) > 60:
        out.append(f"- ... +{len(sans) - 60} lainnya")
    return out


# ------------------------------------------------------------ subdomain (CT logs)
def tool_subdomains(t):
    _, status, _, body = _get(f"https://crt.sh/?q=%25.{t}&output=json", timeout=30, limit=8_000_000)
    if status != 200:
        raise OSError(f"crt.sh membalas HTTP {status}")
    try:
        rows = json.loads(body)
    except ValueError:
        raise OSError("crt.sh tidak membalas JSON valid (coba lagi sebentar lagi)")
    names = set()
    for row in rows:
        for n in row.get("name_value", "").split("\n"):
            n = n.strip().lower().lstrip("*.")
            if (n == t or n.endswith("." + t)) and is_domain(n):
                names.add(n)
    out = ["## SUBDOMAIN (Certificate Transparency, pasif)", f"- {len(names)} nama unik ditemukan"]
    ordered = sorted(names)
    out += [f"  {n}" for n in ordered[:500]]
    if len(ordered) > 500:
        out.append(f"- ... +{len(ordered) - 500} lainnya tidak ditampilkan")
    return out


# ------------------------------------------------------------ IP / reverse DNS
def tool_ip(t):
    out = ["## IP / REVERSE DNS"]
    if is_ip(t):
        ips = [t]
    else:
        ips = []
        for *_, sa in socket.getaddrinfo(t, None, proto=socket.IPPROTO_TCP):
            if sa[0] not in ips:
                ips.append(sa[0])
    for ip in ips:
        try:
            host = socket.gethostbyaddr(ip)[0]
        except OSError:
            host = "(tidak ada PTR)"
        out.append(f"{ip:<40}{host}")
    out += ["", "- untuk pemilik blok IP / ASN, jalankan tool WHOIS pada IP ini"]
    return out


# ------------------------------------------------------------ laporan gabungan
def tool_report(t):
    out = []
    for name, fn in (("dns", tool_dns), ("whois", tool_whois), ("tls", tool_tls),
                     ("http", tool_http), ("subdomain", tool_subdomains)):
        try:
            out += fn(t)
        except Exception as e:  # noqa: BLE001
            out += [f"## {name.upper()}", f"! {e}"]
        out.append("")
    return out


TOOLS = [
    {"label": "DNS Records", "func": tool_dns, "accepts": "domain", "example": "example.com",
     "desc": "Record A, AAAA, CNAME, NS, MX, TXT plus pengecekan SPF dan DMARC."},
    {"label": "WHOIS", "func": tool_whois, "accepts": "any", "example": "example.com atau 93.184.216.34",
     "desc": "Registrar, tanggal, name server, status (domain) atau netname/org/CIDR (IP). Data kontak pribadi disaring."},
    {"label": "HTTP & Security Headers", "func": tool_http, "accepts": "domain", "example": "example.com",
     "desc": "Satu request biasa: status, server, dan audit header keamanan."},
    {"label": "TLS Certificate", "func": tool_tls, "accepts": "domain", "example": "example.com",
     "desc": "Penerbit, masa berlaku, versi TLS, dan daftar SAN sertifikat."},
    {"label": "Subdomain (CT Logs)", "func": tool_subdomains, "accepts": "domain", "example": "example.com",
     "desc": "Daftar subdomain dari log Certificate Transparency via crt.sh. Pasif: target tidak disentuh."},
    {"label": "robots & security.txt", "func": tool_robots, "accepts": "domain", "example": "example.com",
     "desc": "Ambil /robots.txt dan /.well-known/security.txt."},
    {"label": "IP / Reverse DNS", "func": tool_ip, "accepts": "any", "example": "example.com atau 93.184.216.34",
     "desc": "Resolusi domain ke IP dan pencarian PTR (reverse DNS)."},
    {"label": "Laporan Lengkap", "func": tool_report, "accepts": "domain", "example": "example.com",
     "desc": "Menjalankan DNS, WHOIS, TLS, HTTP, dan Subdomain berurutan dalam satu laporan."},
]


osint = types.SimpleNamespace(TOOLS=TOOLS, validate=validate)


import textwrap


class Menu:
    """Menu OSINT: mode menu -> input -> running -> result."""

    def __init__(self):
        self.tools = osint.TOOLS if osint else []
        self.entries = [t["label"] for t in self.tools] + ["Putar ulang intro", "Keluar"]
        self.sel = 0
        self.mode = "menu"
        self.buf = ""
        self.lines = []
        self.scroll = 0
        self.msg = ""
        self.token = 0
        self.target = ""
        self.cache = (None, None, [])
        self.globe = Globe()
        self.rain = None
        self.rain_key = None
        self.reveal = 0.0
        self.t_run = 0.0
        self.t_enter = 0.0
        self.geo = (1, 34)

    # ---- logika
    def tool(self):
        return self.tools[self.sel] if self.sel < len(self.tools) else None

    def start_input(self):
        if self.tool():
            self.mode, self.buf, self.msg = "input", "", ""

    def run(self):
        tool = self.tool()
        try:
            self.target = osint.validate(tool, self.buf)
        except ValueError as e:
            self.msg = str(e)
            return
        self.msg = ""
        self.token += 1
        threading.Thread(target=self._worker, args=(self.token, tool, self.target),
                         daemon=True).start()
        self.mode = "running"
        self.t_run = time.time()

    def _worker(self, token, tool, target):
        try:
            res = tool["func"](target)
        except Exception as e:  # noqa: BLE001
            res = [f"## {tool['label'].upper()}", f"! {e}"]
        if token == self.token:
            self.lines, self.scroll, self.reveal, self.mode = res, 0, 0.0, "result"

    def save(self):
        d = os.path.join(os.getcwd(), "osint_reports")
        os.makedirs(d, exist_ok=True)
        safe_t = "".join(c if c.isalnum() or c in ".-" else "_" for c in self.target)
        name = f"{self.tool()['label'].split()[0].lower()}_{safe_t}_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write("\n".join(l[3:] if l.startswith(("## ",)) else l for l in self.lines) + "\n")
        self.msg = f"Tersimpan: osint_reports/{name}"

    def mouse(self, mx, my, bs):
        top, lw = self.geo
        up = bs & getattr(curses, "BUTTON4_PRESSED", 0)
        down = bs & getattr(curses, "BUTTON5_PRESSED", 0)
        if self.mode == "result":
            if up:
                self.scroll = max(0, self.scroll - 3)
            elif down:
                self.scroll += 3
        elif self.mode == "menu":
            if up or down:
                self.sel = (self.sel + (1 if down else -1)) % len(self.entries)
            elif bs & (curses.BUTTON1_CLICKED | curses.BUTTON1_PRESSED):
                i = my - (top + 1)
                if mx < lw and 0 <= i < len(self.entries):
                    self.sel = i
                    return self.handle(10)
        return None

    def handle(self, k):
        """Return None, 'quit', atau 'replay'."""
        if k == curses.KEY_MOUSE:
            try:
                _, mx, my, _, bs = curses.getmouse()
            except curses.error:
                return None
            return self.mouse(mx, my, bs)
        enter = k in (10, 13, curses.KEY_ENTER)
        if self.mode == "menu":
            n = len(self.entries)
            if k in (curses.KEY_UP, ord("k")):
                self.sel = (self.sel - 1) % n
            elif k in (curses.KEY_DOWN, ord("j")):
                self.sel = (self.sel + 1) % n
            elif ord("1") <= k <= ord("9") and k - ord("1") < len(self.tools):
                self.sel = k - ord("1")
                self.start_input()
            elif enter:
                if self.tool():
                    self.start_input()
                elif self.sel == len(self.tools):
                    return "replay"
                else:
                    return "quit"
            elif k in (ord("r"), ord("R")):
                return "replay"
            elif k in (ord("q"), ord("Q")):
                return "quit"
        elif self.mode == "input":
            if k == 27:
                self.mode, self.msg = "menu", ""
            elif enter and self.buf.strip():
                self.run()
            elif k in (curses.KEY_BACKSPACE, 127, 8):
                self.buf = self.buf[:-1]
            elif 32 <= k <= 126 and len(self.buf) < 120:
                self.buf += chr(k)
        elif self.mode == "running":
            if k in (27, ord("q")):
                self.token += 1
                self.mode = "menu"
        elif self.mode == "result":
            if k in (curses.KEY_UP, ord("k")):
                self.scroll = max(0, self.scroll - 1)
            elif k in (curses.KEY_DOWN, ord("j")):
                self.scroll += 1
            elif k == curses.KEY_PPAGE:
                self.scroll = max(0, self.scroll - 10)
            elif k == curses.KEY_NPAGE:
                self.scroll += 10
            elif k == curses.KEY_HOME:
                self.scroll = 0
            elif k in (ord("s"), ord("S")):
                try:
                    self.save()
                except OSError as e:
                    self.msg = f"Gagal menyimpan: {e}"
            elif k in (27, ord("q"), ord("Q"), curses.KEY_BACKSPACE, 127) or enter:
                self.mode, self.msg = "menu", ""
        return None

    # ---- tampilan
    def wrapped(self, width):
        if self.cache[0] is not self.lines or self.cache[1] != width:
            out = []
            for ln in self.lines:
                out += textwrap.wrap(ln, width, subsequent_indent="    ") or [""]
            self.cache = (self.lines, width, out)
        return self.cache[2]

    SCENES = ("globe", "wire", "torus")
    SCENE_TITLES = {"globe": "ORBIT / LIVE", "wire": "GEOMETRY / LIVE", "torus": "RENDER / LIVE"}

    def draw(self, scr, H, W_, t):
        top, ph = 1, H - 4
        lw = max(34, W_ // 3)
        rw = W_ - lw
        self.geo = (top, lw)
        safe(scr, 0, 1, f"{NAME} // OSINT TOOLKIT", col(C, bold=True))
        safe(scr, 0, W_ - 10, time.strftime("%H:%M:%S"), col(C))
        # ---- kiri atas: menu
        menu_h = min(ph, len(self.entries) + 4)
        box(scr, top, 0, menu_h, lw, "MENU")
        blink = int(t * 3) % 2 == 0
        for i, label in enumerate(self.entries):
            is_tool = i < len(self.tools)
            num = f"{i + 1}." if is_tool else ("R." if i == len(self.tools) else "Q.")
            attr = col(G, bold=True) if is_tool else col(C)
            mark = " "
            if i == self.sel:
                attr |= curses.A_REVERSE
                mark = ">" if blink else "»"
            safe(scr, top + 1 + i, 2, f"{mark}{num:<3}{label}".ljust(lw - 4)[:lw - 4], attr)
        safe(scr, top + menu_h - 2, 2, "Pasif. Hanya domain/IP.", col(B, dim=True))
        # ---- kiri bawah: scene 3D hidup
        rem = ph - menu_h
        if rem >= 9:
            scene = "globe" if self.mode == "running" else self.SCENES[self.sel % 3]
            sy = top + menu_h
            box(scr, sy, 0, rem, lw, self.SCENE_TITLES[scene])
            cv = Canvas(lw - 2, rem - 2)
            if scene == "globe":
                self.globe.render(cv, t)
            elif scene == "wire":
                render_wire(cv, t)
            else:
                render_torus(cv, t)
            cv.blit(scr, sy + 1, 1)
        # ---- kanan
        title = {"result": f"HASIL: {self.target}", "running": "MENJALANKAN"}.get(self.mode, "INFO")
        box(scr, top, lw, ph, rw, title)
        inner_w, inner_h = rw - 4, ph - 2
        if self.mode in ("menu", "input"):
            tool = self.tool()
            if tool:
                rows = [("## " + tool["label"].upper()), ""]
                rows += textwrap.wrap(tool["desc"], inner_w)
                rows += ["", "Target : " + ("domain" if tool["accepts"] == "domain" else "domain atau IP"),
                         f"Contoh  : {tool['example']}"]
            else:
                rows = ["## " + self.entries[self.sel].upper()]
            rows += ["", "- Gunakan hanya pada target milikmu atau yang", "- kamu punya izin untuk dianalisis."]
            for i, ln in enumerate(rows[:inner_h]):
                self._line(scr, top + 1 + i, lw + 2, ln, inner_w)
            # hujan matrix mengisi sisa panel
            ry = len(rows) + 1
            rh = inner_h - ry
            if rh >= 3:
                key = (inner_w + 2, rh)
                if self.rain_key != key:
                    self.rain, self.rain_key = Rain(*key), key
                self.rain.draw(scr, top + 1 + ry, lw + 1)
        elif self.mode == "running":
            el = time.time() - self.t_run
            spin = "|/-\\"[int(t * 10) % 4]
            safe(scr, top + 2, lw + 3, f"{spin} {self.tool()['label']} -> {self.target}", col(Y, bold=True))
            bw = max(10, min(40, inner_w - 4))
            pos = int((math.sin(t * 3) * 0.5 + 0.5) * (bw - 6))
            bar = "░" * pos + "█████" + "░" * (bw - 5 - pos)
            safe(scr, top + 4, lw + 3, "[" + bar + "]", col(C, bold=True))
            safe(scr, top + 6, lw + 3, f"Berjalan {el:4.1f} dtk   [Esc] batal", col(C, dim=True))
            for i in range(min(inner_h - 9, 8)):
                hx = " ".join(f"{random.randint(0, 255):02X}" for _ in range(10))
                safe(scr, top + 8 + i, lw + 3, hx[:inner_w - 2], col(G, dim=True))
        else:
            rows = self.wrapped(inner_w)
            self.reveal = min(len(rows), self.reveal + 2.5)  # efek ketik: baris muncul bertahap
            shown = rows[:int(self.reveal) + 1]
            self.scroll = max(0, min(self.scroll, max(0, len(shown) - inner_h)))
            for i, ln in enumerate(shown[self.scroll:self.scroll + inner_h]):
                self._line(scr, top + 1 + i, lw + 2, ln, inner_w)
            if len(rows) > inner_h:
                safe(scr, top, lw + rw - 14,
                     f" {self.scroll + 1}-{min(len(rows), self.scroll + inner_h)}/{len(rows)} ", col(C))
        # ---- prompt + footer
        if self.mode == "input":
            lab = self.tool()["label"]
            safe(scr, H - 2, 1, f"{lab} > ", col(C, bold=True))
            cur = "█" if int(t * 2) % 2 == 0 else " "
            safe(scr, H - 2, 4 + len(lab), (self.buf + cur)[-(W_ - 20):], col(W, bold=True))
        elif self.msg:
            safe(scr, H - 2, 1, self.msg[:W_ - 2], col(Y, bold=True))
        if self.mode == "input" and self.msg:
            safe(scr, H - 1, 1, ("! " + self.msg)[:W_ - 2], col(Y, bold=True))
            return
        hints = {
            "menu": "[↑↓/klik] pilih  [Enter/1-9] jalankan  [R] intro  [Q] keluar",
            "input": "[Enter] jalankan  [Esc] batal",
            "running": "[Esc] batal",
            "result": "[↑↓/PgUp/PgDn/scroll] gulir  [S] simpan  [Esc] kembali",
        }[self.mode]
        safe(scr, H - 1, 1, hints[:W_ - 2], col(G, dim=True))
        safe(scr, H - 1, W_ - 16, f"MODE:{self.mode.upper():<7}", col(G, dim=True))

    @staticmethod
    def _line(scr, y, x, ln, w):
        if ln.startswith("## "):
            safe(scr, y, x, ln[3:][:w], col(C, bold=True) | curses.A_UNDERLINE)
        elif ln.startswith("+ "):
            safe(scr, y, x, ln[:w], col(G, bold=True))
        elif ln.startswith("! "):
            safe(scr, y, x, ln[:w], col(Y, bold=True))
        elif ln.startswith("- "):
            safe(scr, y, x, ln[:w], col(B, dim=True))
        else:
            safe(scr, y, x, ln[:w], col(G))


def main(scr):
    os.environ.setdefault("ESCDELAY", "25")
    locale.setlocale(locale.LC_ALL, "")
    curses.curs_set(0)
    init_colors()
    scr.keypad(True)
    scr.timeout(0)
    try:
        curses.mousemask(curses.BUTTON1_CLICKED | curses.BUTTON1_PRESSED
                         | getattr(curses, "BUTTON4_PRESSED", 0) | getattr(curses, "BUTTON5_PRESSED", 0))
    except curses.error:
        pass
    dash, rain, size = Dash(), None, (0, 0)
    menu = Menu()
    start = time.time()
    in_menu = entered = False
    while True:
        t0 = time.time()
        k = scr.getch()
        if in_menu:
            act = menu.handle(k) if k != -1 else None
            if act == "quit":
                return
            if act == "replay":
                in_menu, entered, start, dash = False, False, time.time(), Dash()
                continue
        elif k in (ord("q"), ord("Q"), 27):
            return
        elif k in (10, 13, 32, curses.KEY_ENTER):
            in_menu = True
        elif k == curses.KEY_MOUSE:
            try:
                curses.getmouse()
            except curses.error:
                pass
        H, W_ = scr.getmaxyx()
        if (H, W_) != size:
            size, rain = (H, W_), Rain(W_, H)
            scr.clear()
        scr.erase()
        t = time.time() - start
        c = t
        if H < 20 or W_ < 70:
            safe(scr, 0, 0, "Perbesar terminal (min 70x20)", col(Y, bold=True))
        elif in_menu or c >= CYCLE:
            in_menu = True
            if not entered:  # transisi: hujan matrix menyapu layar saat masuk menu
                entered, menu.t_enter, rain = True, time.time(), Rain(W_, H)
            menu.draw(scr, H, W_, time.time())
            if time.time() - menu.t_enter < 1.6:
                rain.draw(scr)
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
