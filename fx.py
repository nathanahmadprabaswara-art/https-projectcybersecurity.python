"""Efek visual BroCode: globe berbenua, radar, matrix rain, glitch."""
import math, random

LAND = {75:[(-110,-70),(-55,-20),(90,110),(130,160)],
 65:[(-168,-60),(-52,-20),(-24,-12),(5,35),(35,180)], 55:[(-165,-55),(-10,-2),(5,60),(60,170)],
 45:[(-125,-60),(-10,40),(40,140)], 35:[(-122,-75),(-10,35),(35,60),(60,130),(130,142)],
 25:[(-110,-80),(-17,35),(35,60),(68,122)], 15:[(-105,-85),(-80,-60),(-17,50),(72,80),(98,110)],
 5:[(-80,-50),(-15,10),(10,50),(95,105),(110,150)], -5:[(-80,-35),(10,40),(100,150)],
 -15:[(-75,-40),(12,50),(130,150)], -25:[(-70,-40),(15,35),(115,153)],
 -35:[(-72,-60),(18,28),(140,150),(172,178)], -45:[(-73,-68),(168,174)], -75:[(-180,180)]}
CITIES = [(-6.2,106.8),(40.7,-74),(51.5,0),(35.7,139.7),(-33.9,151.2),(55.7,37.6),(37.8,-122.4),(1.3,103.8)]
BLOCKS = "▁▂▃▄▅▆▇█"

def is_land(lat, lon):
    row = int(math.floor(lat / 10)) * 10 + 5; lon = (lon + 180) % 360 - 180
    return any(a <= lon <= b for a, b in LAND.get(row, ()))

def spark(vals, w):
    vs = list(vals)[-w:]; mx = max(vs + [1])
    return "".join(BLOCKS[min(7, int(v / mx * 7.99))] if v > 0 else "▁" for v in vs).rjust(w)

def globe(r, t):
    """Return rows of (char, kind): 0 laut,1 darat,2 grid,3 tepi,4 target."""
    h, w, cx, cy, rot = 2 * r + 1, 4 * r + 3, 2 * r + 1, r, t * 18
    g = [[(" ", 0)] * w for _ in range(h)]
    for j in range(h):
        for i in range(w):
            x, y = (i - cx) / (2 * r), (cy - j) / r; d = x * x + y * y
            if d > 1: continue
            z = math.sqrt(1 - d); lat = math.degrees(math.asin(y)); lon = math.degrees(math.atan2(x, z)) + rot
            if d > .88: g[j][i] = ("░", 3)
            elif is_land(lat, lon): g[j][i] = ("█" if z > .55 else "▓", 1)
            elif lon % 30 < 4 or abs(lat % 30) < 3: g[j][i] = ("·", 2)
            else: g[j][i] = ("·", 0)
    if math.sin(t * 4) > -.3:
        for la, lo in CITIES:
            a, b = math.radians(la), math.radians(lo - rot)
            if math.cos(a) * math.cos(b) > .15:
                i, j = int(cx + math.cos(a) * math.sin(b) * 2 * r), int(cy - math.sin(a) * r)
                if 0 <= j < h and 0 <= i < w: g[j][i] = ("◉", 4)
    return g

_BL = [(random.uniform(0, 6.28), random.uniform(.3, .95)) for _ in range(6)]
def radar(r, t):
    h, w, cx, cy, sw = 2 * r + 1, 4 * r + 1, 2 * r, r, (t * 2.2) % 6.283
    g = [[(" ", 0)] * w for _ in range(h)]
    for j in range(h):
        for i in range(w):
            x, y = (i - cx) / 2, cy - j; d = math.hypot(x, y)
            if d > r + .3: continue
            ring = abs(d - r) < .45 or abs(d - r / 2) < .3 or (abs(x) < .3 and d < r) or (abs(y) < .3 and d < r)
            age = (sw - math.atan2(y, x)) % 6.283
            if age < 1.0 and d < r: g[j][i] = ("▒" if age < .3 else "░", 5)
            elif ring: g[j][i] = ("·", 2)
    for a, rd in _BL:
        age = (sw - a) % 6.283
        if age < 3.5:
            i, j = int(cx + math.cos(a) * rd * r * 2), int(cy - math.sin(a) * rd * r)
            if 0 <= j < h and 0 <= i < w: g[j][i] = ("●" if age < 1.5 else "•", 4)
    return g

def glitch(text, p=.25):
    return "".join(random.choice("#%@$&01▓") if c != " " and random.random() < p else c for c in text)

class Rain:
    def __init__(s, w, h): s.w, s.h = w, h; s.d = [random.randint(-h, 0) for _ in range(w)]; s.sp = [random.choice((1, 1, 2)) for _ in range(w)]
    def step(s): s.d = [(y + sp) if y - 8 < s.h else random.randint(-s.h // 2, 0) for y, sp in zip(s.d, s.sp)]
    def cells(s):
        for x in range(s.w):
            for k in range(8):
                y = s.d[x] - k
                if 0 <= y < s.h: yield y, x, random.choice("01アイウエオカキクｱｲｳ#:"), k
