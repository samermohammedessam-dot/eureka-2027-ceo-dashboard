"""EUREKA — THE MOMENT · FROM DISCOVERY TO IMPACT (135 s, 1920x1080, 30 fps).

  python3 moment_film.py stills 3 9 14 ...
  python3 moment_film.py cut [t0 t1]      # rough cut / master -> EUREKA_THE_MOMENT_FINAL.mp4

Timeline (s)
  0-17     THE DISCOVERY        Archimedes plate (Promoat, AI-upscaled window), "Eureka!", golden light from the water
  17-30    DISCOVERY TO PURPOSE golden ripples -> geometry -> blueprint -> a hospital builds itself -> Eureka logo   VO1
  30-50    WHO WE ARE           medical-director panel + real Eureka team photographs                        VO2
  50-75    WHAT WE DO           seven services: actor panel + real photo + typography
  75-105   OUR IMPACT           eight achievement counters integrated with real healthcare imagery
  105-125  PEOPLE & PARTNERSHIP parallax gallery of real photographs, then the partner logos                   VO3
  125-135  THE FUTURE           a golden light travels through the institutions into the Eureka logo        VO4
Figures are the ones supplied by Eureka (to be confirmed before the final export).
Archimedes is shown as an artistic interpretation of the legend.
"""
import functools
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'EUREKA_THE_POWER_OF_TEN'))
sys.path.insert(0, ROOT)
os.environ.setdefault('EUREKA_ASSETS', os.path.join(ROOT, 'assets_dl'))
import film as PF  # noqa: E402  (POWER OF TEN helpers: transparent logo, cards, glow)
import render as R  # noqa: E402
import stage as ST  # noqa: E402
from render import composite, ease_io, ease_out, lerp, seg, text_layer, tonemap  # noqa: E402

W, H, FPS = 1920, 1080, 30
DUR = 135.0
BUILD = os.path.join(ROOT, 'build', 'moment')
PLATES = os.path.join(BUILD, 'plates')
GOLD = np.array([1.0, 0.80, 0.48], np.float32)
WARM = np.array([1.0, 0.9, 0.75], np.float32)
NAVY = np.array([0.020, 0.035, 0.075], np.float32)
A = os.path.join(ROOT, 'assets_dl') + '/'

T_PURPOSE, T_WHO, T_WHAT, T_IMPACT, T_PEOPLE, T_FUTURE = 17.0, 30.0, 50.0, 75.0, 105.0, 125.0
VO_AT = {'vo1': 19.7, 'vo2': 31.4, 'vo3': 106.2, 'vo4': 126.0}
EUREKA_AT = 13.10          # the voiced insert (its own lip-synced audio) starts here

FIGURES = [  # (value, suffix, label, visual) — supplied by Eureka, subject to confirmation
    (45, '+', 'HEALTHCARE PROJECTS', ('photo', A + 'added/new8.jpg')),
    (10, '', 'GAHAR ACCREDITATION ACHIEVEMENTS', ('logos', None)),
    (5, '', 'INTERNATIONAL ACCREDITATIONS', ('photo', A + 'GIC/WhatsApp Image 2026-10-11 at 16.16.23.jpeg')),
    (4, '', 'COUNTRIES', ('points', 4)),
    (7, '', 'EGYPTIAN GOVERNORATES', ('points', 7)),
    (1200, '+', 'HEALTHCARE PROFESSIONALS TRAINED', ('photo', A + 'Smouha/WhatsApp Image 2026-10-11 at 16.05.58.jpeg')),
    (6500, '+', 'TRAINING HOURS', ('photo', A + 'added/new6.jpg')),
    (5, '', 'TURNKEY PROJECTS', ('photo', A + 'added/new2.jpg')),
]

SERVICES = [  # (title lines, descriptor, actor panel, real photo)
    (('HEALTHCARE ACCREDITATION', '& QUALITY'), 'Accreditation readiness, patient safety and quality systems',
     ('H2_accreditation', 0.4), A + 'city/WhatsApp Image 2026-10-11 at 15.52.30.jpeg'),
    (('HEALTHCARE STRATEGY', '& MANAGEMENT'), 'Strategic plans, governance and performance management',
     ('H3_strategy', 4.3), A + 'city/WhatsApp Image 2026-10-11 at 16.16.25 (2).jpeg'),
    (('OPERATIONAL', 'DEVELOPMENT'), 'Efficient processes, patient flow and clinical operations',
     ('H6_operations', 0.5), A + 'GIC/WhatsApp Image 2026-10-11 at 16.16.24.jpeg'),
    (('TURNKEY HEALTHCARE', 'PROJECTS'), 'From concept and design to opening day',
     ('H5_turnkey', 0.5), A + 'city/WhatsApp Image 2026-10-11 at 16.16.24 (1).jpeg'),
    (('ORGANIZATIONAL', 'DEVELOPMENT & HR'), 'Structures, people and leadership that last',
     ('H7_orgdev', 2.8), A + 'EUREKA/WhatsApp Image 2026-10-11 at 15.52.28.jpeg'),
    (('HEALTHCARE TRAINING', '& EDUCATION'), 'Building skills and confidence across every team',
     ('H4_training', 0.4), A + 'Smouha/WhatsApp Image 2026-10-11 at 16.05.58.jpeg'),
    (('BUSINESS', 'DEVELOPMENT'), 'Growth strategies, partnerships and new services',
     ('H8_business', 0.5), A + 'EUREKA/e0e19773-3a8c-4b37-95d9-19d1f130c5b0.jpg'),
]

TEAM = [A + 'EUREKA/WhatsApp Image 2026-10-11 at 15.52.16.jpeg', A + 'added/new5.jpg', A + 'added/new1.jpg']


# ------------------------------------------------------------------ plates (memmaps)
@functools.lru_cache(maxsize=None)
def plate(name):
    p = os.path.join(PLATES, f'{name}.npy')
    return np.load(p, mmap_mode='r') if os.path.exists(p) else None


def plate_frame(name, t):
    p = plate(name)
    if p is None:
        return None
    return np.asarray(p[int(np.clip(t * 24, 0, len(p) - 1))], np.float32) / 255


def grade_warm(img, amt=1.0):
    """Gentle golden-hour grade: lifted warmth, soft contrast."""
    g = img * np.array([1.04, 1.0, 0.92], np.float32) * (1 - 0.06 * amt) + 0.012 * amt
    return np.clip(g, 0, 1)


def panel(cv, name, t, x, y, scale=1.0, o=1.0):
    """A 9:16 actor clip as a full-height cinematic panel (616x1080 at scale 1: no enlargement)."""
    fr = plate_frame(name, t)
    if fr is None or o <= 0.01:
        return
    if abs(scale - 1) > 1e-3:
        fr = np.asarray(Image.fromarray((fr * 255).astype(np.uint8)).resize(
            (int(fr.shape[1] * scale), int(fr.shape[0] * scale)), Image.LANCZOS), np.float32) / 255
    R.draw_photo(cv, fr, int(x - fr.shape[1] / 2), int(y - fr.shape[0] / 2), o, border=2, shadow=0.8,
                 border_color=GOLD * 0.9)


def photo_full(cv, path, p, seed, o=1.0, dim=1.0, zoom=0.10):
    arr = R.photo_crop(path, W, H, p, seed=seed, zoom=zoom) * dim
    cv[:] = cv * (1 - o) + arr * o


def text(cv, s, x, y, size=60, font='cinzel', style='ivory', o=1.0, track=6, glow=0.25, weight=700, shine=None, scale=1.0):
    if o > 0.01:
        composite(cv, text_layer(s, font, size, weight, track, style, 8), x, y, scale, o, glow=glow, shine=shine)


def hline(cv, x, y, w, o, col=GOLD):
    w = int(w)
    if w > 2 and o > 0.01:
        cv[int(y):int(y) + 2, int(x - w / 2):int(x + w / 2)] += col * 0.9 * o


def quiet(cv, x, y, rx, ry, k):
    zx = np.exp(-((np.arange(W) - x) / rx) ** 4)
    zy = np.exp(-((np.arange(H) - y) / ry) ** 4)
    cv *= (1 - k * zy[:, None] * zx[None, :])[..., None]


def side_gradient(cv, side, k=0.8, width=0.62):
    x = np.linspace(0, 1, W, dtype=np.float32)
    g = np.clip((width - (x if side == 'left' else 1 - x)) / width, 0, 1) ** 1.4
    cv *= (1 - k * g)[None, :, None]


def streak_wipe(cv, u, col=GOLD, gain=0.5):
    if 0 < u < 1:
        ST.add(cv, R.streak(u, angle=-0.3, width=0.06), col, gain * math.sin(math.pi * u))


# ------------------------------------------------------------------ 1  THE DISCOVERY
@functools.lru_cache(maxsize=1)
def arch_meta():
    p = os.path.join(PLATES, 'arch.json')
    return json.load(open(p)) if os.path.exists(p) else None


EUREKA_CUT = 1.45          # use only the first, strongest-looking "Eureka!" (the water thrown skyward)
T_GOLD = EUREKA_AT + EUREKA_CUT


def arch_time(t):
    """Film time -> plate time: the voiced insert is cut after the first shout, then the water close-up."""
    if t < T_GOLD:
        return t
    m = arch_meta()
    w0, w1 = (m['edl'][-1][0], m['edl'][-1][1]) if m else (15.7, 16.76)
    return min(w0 + (t - T_GOLD), w1 - 0.01)


def s1_discovery(cv, t):
    fr = plate_frame('arch', arch_time(t))
    if fr is not None:
        z = 1 + 0.10 * ease_io(seg(t, T_GOLD + 0.6, T_PURPOSE))         # the camera sinks toward the water
        if z > 1.001:
            cw, ch = int(W / z), int(H / z)
            x0, y0 = (W - cw) // 2, int((H - ch) * 0.62)
            fr = np.asarray(Image.fromarray((fr * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS,
                            box=(x0, y0, x0 + cw, y0 + ch)), np.float32) / 255
        cv[:] = grade_warm(fr)
    cv *= ease_out(seg(t, 0.0, 1.2))
    # caption: the legend, honestly labelled
    q = seg(t, 1.0, 1.8) * (1 - seg(t, 5.2, 6.0))
    quiet(cv, W / 2, 960, 700, 70, 0.45 * q)
    text(cv, 'SYRACUSE  ·  THE LEGEND OF ARCHIMEDES', W / 2, 940, 30, 'mont', 'gold', q, 10, 0.2, 600)
    text(cv, 'An artistic interpretation', W / 2, 985, 22, 'mont', 'ivory', q * 0.8, 4, 0.0, 400)
    # the golden light rising from the water
    g = ease_io(seg(t, T_GOLD, T_GOLD + 1.6))
    if g > 0:
        PF.glow(cv, W / 2, H * 0.62, 260 + 700 * g, GOLD, 0.9 * g)
        for k in range(40):
            rng = np.random.default_rng(k)
            x0, sp = rng.uniform(0.2, 0.8) * W, rng.uniform(140, 380)
            y = H * 0.75 - (t - T_GOLD) * sp - rng.uniform(0, 200)
            if 0 < y < H:
                R.splat(cv, x0 + 30 * math.sin(t * 2 + k), y, rng.uniform(2, 5), 1.2 * g)
    cv[:] = cv * (1 - 0.5 * seg(t, T_PURPOSE - 0.5, T_PURPOSE)) + GOLD * 0.25 * seg(t, T_PURPOSE - 0.5, T_PURPOSE)
    return t > 3.0


# ------------------------------------------------------------------ 2  DISCOVERY TO PURPOSE
def ripple_field(t, cx, cy, t0):
    """Golden concentric ripples on dark water (quarter-res light map)."""
    lx, ly = ST._lx, ST._ly
    dy = (ly - cy) * 2.6
    r = np.sqrt((lx - cx) ** 2 + dy ** 2)
    out = np.zeros_like(r)
    for k in range(7):
        rk = (t - t0 - k * 0.42) * 420
        if rk > 0:
            out += np.exp(-((r - rk) / (6 + rk * 0.02)) ** 2) * math.exp(-rk / 1500)
    return out


@functools.lru_cache(maxsize=1)
def geometry_nodes():
    rng = np.random.default_rng(7)
    pts = []
    for ring, n in [(170, 6), (330, 10), (500, 14)]:
        for k in range(n):
            a = 2 * math.pi * k / n + ring * 0.01
            pts.append((W / 2 + ring * math.cos(a) * 1.6, H / 2 + ring * math.sin(a) * 0.9))
    pts = np.array(pts)
    edges = []
    for i in range(len(pts)):
        d = np.hypot(*(pts - pts[i]).T)
        for j in np.argsort(d)[1:4]:
            if i < j:
                edges.append((i, j))
    return pts, edges, rng.uniform(0, 1, len(edges))


def draw_lines(segs, width=2, blur=0):
    m = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(m)
    for (x0, y0, x1, y1, v) in segs:
        if v > 0.01:
            d.line([(x0, y0), (x1, y1)], fill=int(255 * min(1, v)), width=width)
    if blur:
        m = m.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(m, np.float32) / 255


def blueprint(u):
    """An architectural plan drawing itself (u 0..1): outer walls, wards, corridors, cores."""
    x0, y0, w, h = W / 2 - 620, H / 2 - 300, 1240, 600
    rects = [(0, 0, 1, 1), (0, 0, 0.36, 0.48), (0.36, 0, 0.28, 0.48), (0.64, 0, 0.36, 0.48),
             (0, 0.58, 0.24, 0.42), (0.24, 0.58, 0.26, 0.42), (0.5, 0.58, 0.22, 0.42), (0.72, 0.58, 0.28, 0.42),
             (0.44, 0.48, 0.12, 0.10)]
    segs = []
    for k, (a, b, c, d) in enumerate(rects):
        v = seg(u, k * 0.07, k * 0.07 + 0.35)
        if v <= 0:
            continue
        X0, Y0, X1, Y1 = x0 + a * w, y0 + b * h, x0 + (a + c) * w, y0 + (b + d) * h
        perim = [(X0, Y0, X1, Y0), (X1, Y0, X1, Y1), (X1, Y1, X0, Y1), (X0, Y1, X0, Y0)]
        for j, (p, q_, r_, s_) in enumerate(perim):
            vv = np.clip(v * 4 - j, 0, 1)
            segs.append((p, q_, p + (r_ - p) * vv, q_ + (s_ - q_) * vv, 1.0))
    # door swings and grid ticks
    for k in range(14):
        v = seg(u, 0.45 + k * 0.02, 0.6 + k * 0.02)
        xx = x0 + w * (0.06 + 0.066 * k)
        segs.append((xx, y0 + 0.48 * h, xx, y0 + 0.48 * h + 0.10 * h * v, 0.7))
    return segs


HOSPITAL = [  # (x, z, w, d, floors) blocks of a modern campus, in world units
    (0, 600, 520, 300, 9), (-560, 650, 360, 260, 5), (560, 650, 360, 260, 5),
    (0, 300, 1200, 220, 2), (-300, 980, 300, 220, 4), (320, 980, 300, 220, 6),
]


def hospital(t, u, cam):
    """A wireframe hospital campus assembling floor by floor (u 0..1), with glowing windows."""
    segs, wins = [], []
    for bi, (x, z, w, d, fl) in enumerate(HOSPITAL):
        hgt = fl * 46 * ease_out(seg(u, bi * 0.08, bi * 0.08 + 0.55))
        if hgt < 2:
            continue
        xs, zs = (x - w / 2, x + w / 2), (z - d / 2, z + d / 2)
        corners = [(xx, yy, zz) for yy in (0, hgt) for xx in xs for zz in zs]
        S, Z = cam.screen(np.array(corners, np.float64))
        idx = [(0, 1), (2, 3), (0, 2), (1, 3), (4, 5), (6, 7), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]
        for a, b in idx:
            if Z[a] > 10 and Z[b] > 10:
                segs.append((S[a][0], S[a][1], S[b][0], S[b][1], 1.0))
        for f in range(int(hgt / 46)):
            for k in range(int(w / 60)):
                P = (xs[0] + 30 + k * 60, f * 46 + 23, zs[0])
                (sx, sy), sz = cam.screen(np.array(P, np.float64))
                if sz > 10:
                    wins.append((sx, sy, 0.5 + 0.5 * math.sin(k * 1.7 + f * 2.3 + bi)))
    return segs, wins


def s2_purpose(cv, t):
    u = t - T_PURPOSE
    cv[:] = NAVY * (1 + 0.6 * np.linspace(1, 0, H, dtype=np.float32)[:, None, None])
    # 0-3.2 golden ripples (continuing the water), 2.4-6.6 they become geometry
    rip = ripple_field(t, W / 2, H * 0.58, T_PURPOSE - 0.6) * (1 - seg(u, 2.6, 4.0))
    ST.add(cv, rip, GOLD, 0.9)
    # the name and its meaning, over the golden ripples
    q2 = seg(u, 0.1, 0.9) * (1 - seg(u, 2.4, 3.0))
    quiet(cv, W / 2, 430, 760, 140, 0.4 * q2)
    text(cv, '“EUREKA”', W / 2, 400, 124, 'cinzel', 'gold', ease_io(q2), 18, 0.6,
         shine=seg(u, 0.5, 1.7) if 0.5 < u < 1.7 else None)
    text(cv, 'I HAVE FOUND IT', W / 2, 525, 34, 'mont', 'ivory', ease_io(seg(u, 0.6, 1.3)) * (1 - seg(u, 2.4, 3.0)), 14, 0.2, 600)
    g = seg(u, 2.2, 4.2) * (1 - seg(u, 6.0, 7.2))
    if g > 0:
        pts, edges, rnd = geometry_nodes()
        segs = []
        for (i, j), r in zip(edges, rnd):
            v = seg(g, r * 0.5, r * 0.5 + 0.5)
            p, q = pts[i], pts[j]
            segs.append((p[0], p[1], p[0] + (q[0] - p[0]) * v, p[1] + (q[1] - p[1]) * v, g))
        sharp = draw_lines(segs, 2)
        cv += sharp[..., None] * GOLD * 0.8 + draw_lines(segs, 6, 6)[..., None] * GOLD * 0.5
        for p in pts:
            R.splat(cv, p[0], p[1], 3, 1.4 * g)
    # 5.6-9.4 a blueprint draws itself; 8.4-13 the hospital assembles; 9.5-13 Eureka logo
    b = seg(u, 5.6, 9.0) * (1 - seg(u, 9.0, 10.0))
    if b > 0:
        grid = (((np.arange(W) % 60) < 1)[None, :] | ((np.arange(H) % 60) < 1)[:, None]).astype(np.float32)
        cv += grid[..., None] * np.array([0.25, 0.45, 0.75], np.float32) * 0.10 * b
        segs = blueprint(seg(u, 5.6, 8.8))
        cv += draw_lines(segs, 2)[..., None] * np.array([0.55, 0.78, 1.0], np.float32) * 0.85 * b
        cv += draw_lines(segs, 6, 5)[..., None] * np.array([0.3, 0.55, 0.95], np.float32) * 0.35 * b
    hq = seg(u, 8.4, 11.5)
    if hq > 0:
        a = math.radians(-28 + 22 * seg(u, 8.4, 13.0))
        cam = ST.Cam((1900 * math.sin(a), 520 - 120 * seg(u, 8.4, 13), 620 - 1900 * math.cos(a)), (0, 160, 650), 44)
        segs, wins = hospital(t, hq, cam)
        o = seg(u, 8.4, 9.2) * (1 - 0.55 * seg(u, 9.6, 10.4))
        cv += draw_lines([s[:4] + (o,) for s in segs], 2)[..., None] * GOLD * 0.9
        cv += draw_lines([s[:4] + (o,) for s in segs], 7, 6)[..., None] * GOLD * 0.35
        for (x, y, v) in wins:
            R.splat(cv, x, y, 2.2, 0.55 * v * o * seg(hq, 0.3, 1.0))
        PF.glow(cv, W / 2, H * 0.7, 900, GOLD, 0.15 * o)
    # the Eureka logo, prominently
    q = seg(u, 9.6, 10.6)
    if q > 0:
        quiet(cv, W / 2, 470, 650, 260, 0.6 * q)
        composite(cv, PF.eureka_layer(620, 0.55), W / 2, 450, lerp(0.92, 1.0, ease_out(q)), ease_io(q) * (1 - seg(u, 12.4, 13.0)),
                  glow=0, shine=seg(u, 10.4, 11.6) if 10.4 < u < 11.6 else None)
        PF.glow(cv, W / 2, 450, 800, WARM, 0.5 * math.exp(-max(0, u - 9.6) / 0.35) * (u > 9.6))
    cv *= 1 - 0.85 * seg(u, 12.6, 13.0)
    return not (9.4 < u < 13.0)


# ------------------------------------------------------------------ 3  WHO WE ARE
def s3_who(cv, t):
    u = t - T_WHO
    if u < 5.0:
        cv[:] = NAVY
        photo_full(cv, TEAM[0], seg(u, 0, 6), 3, 1.0, 0.45, 0.06)
        side_gradient(cv, 'left', 0.93, 0.8)
        panel(cv, 'H1_leadership', 0.3 + u * 0.9, 1380, 540, 0.92, ease_out(seg(u, 0.2, 1.0)))
        q = seg(u, 0.6, 1.4)
        text(cv, 'WHO WE ARE', 520, 380, 84, 'cinzel', 'gold', ease_io(q), 14, 0.5)
        hline(cv, 520, 452, 380 * ease_out(seg(u, 1.0, 2.0)), q)
        for k, s in enumerate(['HEALTHCARE CONSULTANTS', 'MEDICAL DIRECTORS', 'QUALITY & ACCREDITATION EXPERTS', 'HEALTHCARE LEADERS']):
            qq = seg(u, 1.6 + 0.45 * k, 2.2 + 0.45 * k)
            text(cv, s, 520, 520 + 58 * k + 10 * (1 - ease_out(qq)), 30, 'mont', 'ivory', ease_io(qq), 8, 0.1, 600)
        streak_wipe(cv, seg(u, 4.4, 5.2))
        return True
    # real Eureka team photographs, full frame (high-resolution originals), slow cinematic moves
    shots = [(5.0, TEAM[1], 'TOGETHER WITH HEALTHCARE LEADERS'), (10.0, TEAM[2], 'ON THE GROUND, IN EVERY DEPARTMENT'),
             (15.0, TEAM[0], 'ONE TEAM  ·  ONE PURPOSE')]
    for k, (a, path, cap) in enumerate(shots):
        if a <= u < a + 5.0 or (k == len(shots) - 1 and u >= a):
            v = u - a
            cv[:] = 0
            photo_full(cv, path, seg(v, 0, 5.0), 11 + k, 1.0, 0.9, 0.10)
            cv[:] = grade_warm(cv, 0.6)
            cv *= 1 - 0.55 * np.clip((np.arange(H)[:, None, None] - 640) / 440, 0, 1)
            q = seg(v, 0.8, 1.6) * (1 - seg(v, 4.2, 4.8))
            text(cv, cap, W / 2, 960, 38, 'cinzel', 'ivory', ease_io(q), 10, 0.25)
            if v < 0.5 and k:
                cv *= ease_out(v / 0.5) * 0.6 + 0.4
            streak_wipe(cv, seg(v, 4.5, 5.2), WARM, 0.35)
    cv *= 1 - seg(t, T_WHAT - 0.4, T_WHAT)
    return True


# ------------------------------------------------------------------ 4  WHAT WE DO
SERV_T0, SERV_DUR = T_WHAT + 1.8, (T_IMPACT - T_WHAT - 1.8) / len(SERVICES)


def s4_what(cv, t):
    u = t - T_WHAT
    if u < 1.8:
        cv[:] = NAVY
        PF.glow(cv, W / 2, H / 2, 700, GOLD, 0.25 * seg(u, 0, 0.8))
        q = seg(u, 0.1, 0.8) * (1 - seg(u, 1.4, 1.8))
        text(cv, 'WHAT WE DO', W / 2, 520, 96, 'cinzel', 'gold', ease_io(q), 18, 0.6, shine=seg(u, 0.4, 1.4) if u > 0.4 else None)
        hline(cv, W / 2, 600, 420 * ease_out(seg(u, 0.4, 1.2)), q)
        return True
    k = min(len(SERVICES) - 1, int((t - SERV_T0) // SERV_DUR))
    v = t - SERV_T0 - k * SERV_DUR
    (l1, l2), desc, (clip, c0), photo = SERVICES[k]
    side = 'right' if k % 2 == 0 else 'left'            # where the actor panel sits
    cv[:] = 0
    photo_full(cv, photo, seg(v, 0, SERV_DUR), 21 + k, 1.0, 0.62, 0.08)
    cv[:] = grade_warm(cv, 0.5)
    side_gradient(cv, 'left' if side == 'right' else 'right', 0.9, 0.78)
    px = 1430 if side == 'right' else 490
    tx = 600 if side == 'right' else 1300
    panel(cv, clip, c0 + v * 1.0, px + (40 if side == 'right' else -40) * (1 - ease_out(seg(v, 0, 0.6))), 540, 0.86,
          ease_out(seg(v, 0.0, 0.5)))
    q = seg(v, 0.25, 0.85)
    text(cv, f'0{k + 1}', tx, 330, 40, 'mont', 'gold', ease_io(q), 10, 0.3, 600)
    quiet(cv, tx, 500, 560, 250, 0.62 * q)
    for j, (ln, yy, a0) in enumerate([(l1, 420, 0.25), (l2, 496, 0.35)]):
        lay = text_layer(ln, 'cinzel', 56, 700, 6, 'ivory', 8)
        qq = seg(v, a0, a0 + 0.6)
        composite(cv, lay, tx, yy + 12 * (1 - ease_out(qq)), min(1.0, 900 / lay.w), ease_io(qq), glow=0.3)
    hline(cv, tx, 572, 300 * ease_out(seg(v, 0.5, 1.2)), q)
    text(cv, desc, tx, 630, 29, 'mont', 'ivory', ease_io(seg(v, 0.7, 1.3)), 2, 0.1, 500)
    fade_out = seg(v, SERV_DUR - 0.35, SERV_DUR)
    streak_wipe(cv, seg(v, SERV_DUR - 0.55, SERV_DUR + 0.2), GOLD, 0.45)
    if k == len(SERVICES) - 1:
        cv *= 1 - fade_out
    return True


# ------------------------------------------------------------------ 5  OUR IMPACT
IMP_T0 = T_IMPACT + 2.2
IMP_DUR = (T_PEOPLE - IMP_T0) / len(FIGURES)


def fmt(n):
    return f'{n:,}'


def counter_value(v, target):
    q = ease_out(seg(v, 0.35, 1.7))
    return int(round(target * q))


def points_constellation(cv, n, v, seed):
    rng = np.random.default_rng(seed)
    pts = [(W * 0.68 + 460 * math.cos(2 * math.pi * k / n + 0.4) * rng.uniform(0.6, 1.0),
            H * 0.48 + 300 * math.sin(2 * math.pi * k / n + 0.4) * rng.uniform(0.6, 1.0)) for k in range(n)]
    segs = []
    for k in range(n):
        a, b = pts[k], pts[(k + 1) % n]
        w = seg(v, 0.4 + 0.12 * k, 0.9 + 0.12 * k)
        segs.append((a[0], a[1], a[0] + (b[0] - a[0]) * w, a[1] + (b[1] - a[1]) * w, 0.8))
    cv += draw_lines(segs, 2)[..., None] * GOLD * 0.6 + draw_lines(segs, 6, 5)[..., None] * GOLD * 0.3
    for k, (x, y) in enumerate(pts):
        on = seg(v, 0.3 + 0.12 * k, 0.6 + 0.12 * k)
        PF.glow(cv, x, y, 60, GOLD, 0.9 * on)
        R.splat(cv, x, y, 5, 2.0 * on)


@functools.lru_cache(maxsize=1)
def ten_cards():
    return [PF.plate(inst, 300, 160) for inst in PF.insts()]


def logos_ring(cv, v):
    for j, ((x, y), card) in enumerate(zip(PF.ring_positions(), ten_cards())):
        q = seg(v, 0.3 + 0.1 * j, 0.8 + 0.1 * j)
        composite(cv, card, x, y, 0.8 * (0.85 + 0.15 * ease_out(q)), ease_io(q), glow=0.12)
    composite(cv, PF.seal(150), W / 2, 930, 1.0, ease_io(seg(v, 1.4, 2.0)), glow=0.2)


def s5_impact(cv, t):
    u = t - T_IMPACT
    if u < 2.2:
        cv[:] = NAVY
        PF.glow(cv, W / 2, H / 2, 900, GOLD, 0.3 * seg(u, 0, 1.0))
        ST.add(cv, R.rays(W / 2, H / 2, t, n=16, speed=0.05, reach=1100), GOLD, 0.18 * seg(u, 0.2, 1.2))
        q = seg(u, 0.2, 0.9) * (1 - seg(u, 1.8, 2.2))
        text(cv, 'OUR IMPACT', W / 2, 500, 110, 'cinzel', 'gold', ease_io(q), 20, 0.7, shine=seg(u, 0.6, 1.6) if u > 0.6 else None)
        text(cv, 'DISCOVERIES TURNED INTO MEASURABLE ACHIEVEMENTS', W / 2, 620, 30, 'mont', 'ivory', ease_io(seg(u, 0.6, 1.2)) * (1 - seg(u, 1.8, 2.2)), 10, 0.1, 600)
        return True
    k = min(len(FIGURES) - 1, int((t - IMP_T0) // IMP_DUR))
    v = t - IMP_T0 - k * IMP_DUR
    val, suf, label, (kind, arg) = FIGURES[k]
    cv[:] = NAVY
    if kind == 'photo':
        # the photograph owns the right of the frame; the achievement owns the dark left
        PX = 760
        arr = grade_warm(R.photo_crop(arg, W - PX, H, seg(v, 0, IMP_DUR), seed=31 + k, zoom=0.10) * 0.78, 0.8)
        ramp = np.clip(np.arange(W - PX, dtype=np.float32) / 380, 0, 1) ** 1.6
        cv[:, PX:] = cv[:, PX:] * (1 - ramp[None, :, None]) + arr * ramp[None, :, None]
    elif kind == 'points':
        PF.glow(cv, W * 0.66, H * 0.48, 800, np.array([0.3, 0.45, 0.8], np.float32), 0.25)
        points_constellation(cv, arg, v, 40 + k)
    elif kind == 'logos':
        PF.glow(cv, W / 2, H / 2, 900, GOLD, 0.22)
        logos_ring(cv, v)
    # light trail sweeping in as the number lands
    ST.add(cv, R.streak(seg(v, 0.1, 1.2), angle=-0.18, width=0.05), GOLD, 0.6 * math.sin(math.pi * seg(v, 0.1, 1.2)))
    n = counter_value(v, val)
    centre = kind == 'logos'
    x = W / 2 if centre else 420
    num_y = 440 if centre else 470
    q = seg(v, 0.2, 0.6)
    s = fmt(n) + (suf if n >= val else '')
    text(cv, s, x, num_y, 190 if not centre else 250, 'cinzel', 'gold', ease_io(q), 6, 0.8,
         shine=seg(v, 1.7, 2.6) if v > 1.7 else None)
    hline(cv, x, num_y + 150, 360 * ease_out(seg(v, 1.2, 1.9)), q)
    ql = seg(v, 0.9, 1.5)
    if centre:
        text(cv, 'GAHAR ACCREDITATION', x, 640, 46, 'cinzel', 'ivory', ease_io(ql), 12, 0.3)
        text(cv, 'ACHIEVEMENTS', x, 705, 46, 'cinzel', 'ivory', ease_io(ql), 12, 0.3)
    else:
        words = label.split(' ')
        mid = (len(words) + 1) // 2 if len(label) > 22 else len(words)
        text(cv, ' '.join(words[:mid]), x, num_y + 210, 38, 'cinzel', 'ivory', ease_io(ql), 8, 0.3)
        if mid < len(words):
            text(cv, ' '.join(words[mid:]), x, num_y + 262, 38, 'cinzel', 'ivory', ease_io(ql), 8, 0.3)
    if 1.6 < v < 2.6:   # the achievement lands: a soft gold burst, no white flash
        R.firework(cv, v, 1.65, x + (0 if centre else 200), num_y - 60, 90 + k, n=40, life=1.0, speed=380)
    cv *= 1 - 0.7 * seg(v, IMP_DUR - 0.3, IMP_DUR) if k < len(FIGURES) - 1 else 1
    return not centre


# ------------------------------------------------------------------ 6  PEOPLE & PARTNERSHIPS
@functools.lru_cache(maxsize=1)
def gallery():
    m = R.manifest()
    pool = [p for p in m['team_photos'] if not R.is_portrait(p, 0.9)]
    for inst in m['institutions']:
        pool += [p for p in inst['photos'] if p not in pool]
    return pool[:30]


def s6_people(cv, t):
    u = t - T_PEOPLE
    if u < 12.0:
        cv[:] = NAVY * 0.8
        pool = gallery()
        rows = [(225, 1.0, 400, 52), (860, 0.92, 400, 40)]   # y, depth, height, speed (the middle band stays clear)
        for r, (y, depth, hh, sp) in enumerate(rows):
            x = -((u * sp) % 10000) - r * 260
            j = r
            while x < W + 400:
                path = pool[(j * 3 + r) % len(pool)]
                ww, hh2 = R.contain(path, int(hh * 1.6), hh)
                if x + ww > -50:
                    arr = R.photo_crop(path, ww, hh2, 0.5, seed=j, zoom=0.0) * (0.55 + 0.45 * depth)
                    R.draw_photo(cv, arr, int(x), int(y - hh2 / 2), ease_out(seg(u, 0, 1.0)), border=2, shadow=0.6,
                                 border_color=GOLD * 0.8)
                x += ww + 34
                j += 3
        cv *= 0.72
        PF.glow(cv, W / 2, 545, 700, GOLD, 0.12 * seg(u, 0.6, 1.6))
        for a, b, s in [(1.0, 5.6, 'BEHIND EVERY ACHIEVEMENT'), (5.8, 11.4, 'EXTRAORDINARY PEOPLE')]:
            q = seg(u, a, a + 0.7) * (1 - seg(u, b - 0.5, b))
            text(cv, s, W / 2, 545, 74, 'cinzel', 'gold', ease_io(q), 14, 0.45)
        cv *= 1 - seg(u, 11.6, 12.0)
        return True
    # trusted partnerships: the real partner logos
    v = u - 12.0
    cv[:] = NAVY
    PF.glow(cv, W / 2, H / 2, 1000, GOLD, 0.18)
    q = seg(v, 0.2, 0.9)
    text(cv, 'TRUSTED PARTNERSHIPS', W / 2, 170, 70, 'cinzel', 'gold', ease_io(q), 14, 0.5)
    hline(cv, W / 2, 228, 380 * ease_out(seg(v, 0.5, 1.2)), q)
    cards = ten_cards()
    for j, card in enumerate(cards):
        cx = W / 2 + ((j % 5) - 2) * 340
        cy = 470 + (j // 5) * 250
        qq = seg(v, 0.7 + 0.18 * j, 1.2 + 0.18 * j)
        composite(cv, card, cx, cy + 20 * (1 - ease_out(qq)), 0.95, ease_io(qq), glow=0.1,
                  shine=seg(v, 1.0 + 0.18 * j, 1.8 + 0.18 * j) if 1.0 + 0.18 * j < v < 1.8 + 0.18 * j else None)
    text(cv, 'A SHARED BELIEF THAT HEALTHCARE CAN ALWAYS BE BETTER', W / 2, 920, 30, 'mont', 'ivory',
         ease_io(seg(v, 3.4, 4.2)) * (1 - seg(v, 7.4, 8.0)), 8, 0.1, 600)
    cv *= 1 - 0.8 * seg(v, 7.6, 8.0)
    return True


# ------------------------------------------------------------------ 7  THE FUTURE
def s7_future(cv, t):
    u = t - T_FUTURE
    cv[:] = NAVY * 0.9
    cards = ten_cards()
    # a golden light travels through the institutions: an arc of the ten real partner logos lit in turn
    travel = seg(u, 0.2, 3.4)
    lx = lerp(-150, W + 150, ease_io(travel))
    out = seg(u, 3.4, 4.4)
    for j, card in enumerate(cards):
        x0 = 205 + j * 168
        y0 = 560 - 70 * math.sin(math.pi * j / 9)
        lit = math.exp(-((x0 - lx) / 140) ** 2)
        seen = seg(lx, x0 - 120, x0 + 60)                  # stays warm once the light has passed
        x, y = lerp(x0, W / 2, ease_io(out)), lerp(y0, 560, ease_io(out))
        composite(cv, card, x, y, 0.52 * (1 + 0.12 * lit) * (1 - 0.5 * out), (0.35 + 0.65 * seen) * (1 - out), glow=0.1 + 0.15 * lit)
        PF.glow(cv, x, y + 70, 110, GOLD, 0.18 * lit * (1 - out))
    if 0 < travel < 1:
        ly = 560 - 70 * math.sin(math.pi * np.clip((lx - 205) / (168 * 9), 0, 1)) + 95   # glides just under the arc
        PF.glow(cv, lx, ly, 120, GOLD, 0.35)
        for k in range(14):                                    # a short comet tail of light particles
            R.splat(cv, lx - k * 26, ly + 4 * math.sin(k + t * 3), 3.2 - k * 0.18, 1.3 * (1 - k / 14))
    PF.glow(cv, W / 2, 520, 160 + 600 * out, GOLD, 1.1 * out * (1 - 0.6 * seg(u, 4.6, 5.4)))
    ST.add(cv, R.rays(W / 2, 420, t, n=20, speed=0.04, reach=1100), GOLD, 0.2 * seg(u, 4.0, 5.0))
    q = seg(u, 4.2, 5.2)
    composite(cv, PF.eureka_layer(600, 0.55), W / 2, 400, lerp(0.9, 1.0, ease_out(q)), ease_io(q), glow=0,
              shine=seg(u, 5.0, 6.2) if 5.0 < u < 6.2 else None)
    q3 = seg(u, 6.2, 7.0)
    text(cv, 'FROM INSIGHT TO IMPACT.', W / 2, 820, 78, 'cinzel', 'ivory', ease_io(q3), 8, 0.6,
         shine=seg(u, 7.0, 8.2) if 7.0 < u < 8.2 else None)
    cv *= 1 - seg(t, DUR - 1.0, DUR)
    return u < 4.0


# ------------------------------------------------------------------ frame + output
def corner_logo(cv, o=1.0):
    """The authentic Eureka logo as a subtle corner brand (about 8% of the frame width), never clipped."""
    lay = PF.eureka_layer(150, 1.0)
    composite(cv, lay, W - 44 - lay.w / 2, 26 + lay.h / 2, 1.0, o, glow=0)


GRAIN = np.random.default_rng(3).normal(0, 1, (8, H // 2, W // 2)).astype(np.float32)


def frame(t):
    cv = np.zeros((H, W, 3), np.float32)
    if t < T_PURPOSE:
        corner = s1_discovery(cv, t)
    elif t < T_WHO:
        corner = s2_purpose(cv, t)
    elif t < T_WHAT:
        corner = s3_who(cv, t)
    elif t < T_IMPACT:
        corner = s4_what(cv, t)
    elif t < T_PEOPLE:
        corner = s5_impact(cv, t)
    elif t < T_FUTURE:
        corner = s6_people(cv, t)
    else:
        corner = s7_future(cv, t)
    R.bloom(cv, 0.22, 0.82)
    cv *= R.vignette(0.32)
    g = GRAIN[int(t * FPS) % 8]
    cv += np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None] * 0.012
    if corner:
        corner_logo(cv, 0.92)
    return tonemap(cv)


def _chunk(args):
    a, b, path = args
    tmp = path + '.part.mp4'
    pr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', tmp],
                          stdin=subprocess.PIPE)
    for f in range(a, b):
        pr.stdin.write(frame(f / FPS).tobytes())
    pr.stdin.close()
    pr.wait()
    os.replace(tmp, path)
    return path


def mix_audio(t0, t1, out):
    """Score + lip-synced 'Eureka!' (from the voiced Promoat insert) + narration, with ducking."""
    au = os.path.join(BUILD, 'audio')
    music = os.path.join(BUILD, 'moment_score.wav')
    if not os.path.exists(music):
        subprocess.run([sys.executable, os.path.join(HERE, 'score_moment.py'), music], check=True)
    ins = ['-i', music, '-ss', '0', '-i', os.path.join(BUILD, 'A4_eureka_voiced.mp4')]
    for k in ('vo1', 'vo2', 'vo3', 'vo4'):
        ins += ['-i', os.path.join(au, f'{k}.wav')]
    vo = [f'[{i + 2}:a]adelay={int(VO_AT[k] * 1000)}|{int(VO_AT[k] * 1000)},volume=1.25[{k}]' for i, k in enumerate(['vo1', 'vo2', 'vo3', 'vo4'])]
    eu = f'[1:a]atrim=0:{EUREKA_CUT + 0.05},afade=out:st={EUREKA_CUT - 0.1}:d=0.15,asetpts=PTS-STARTPTS,highpass=f=90,aecho=0.8:0.6:60|140:0.25|0.15,volume=1.5,adelay={int(EUREKA_AT * 1000)}|{int(EUREKA_AT * 1000)}[eu]'
    fc = ';'.join(vo + [eu, f'[vo1][vo2][vo3][vo4][eu]amix=inputs=5:normalize=0,apad=whole_dur={DUR},asplit[voice][key]',
                        '[0:a][key]sidechaincompress=threshold=0.04:ratio=5:attack=20:release=400[duck]',
                        f'[duck][voice]amix=inputs=2:normalize=0,atrim={t0}:{t1},asetpts=PTS-STARTPTS,alimiter=limit=0.95[a]'])
    subprocess.run(['ffmpeg', '-v', 'error', '-y'] + ins + ['-filter_complex', fc, '-map', '[a]', '-c:a', 'pcm_s16le', out], check=True)


def render(t0, t1, out):
    d = os.path.join(BUILD, 'chunks')        # 1.5 s chunks on a fixed grid, cached: delete a chunk to re-render it
    os.makedirs(d, exist_ok=True)
    a0, a1 = int(t0 * FPS) // 45 * 45, int(t1 * FPS)
    jobs = [(a, min(a1, a + 45), os.path.join(d, f'c{a:05d}_{min(a1, a + 45):05d}.mp4')) for a in range(a0, a1, 45)]
    todo = [j for j in jobs if not os.path.exists(j[2])]
    with Pool(4) as p:
        for k, _ in enumerate(p.imap_unordered(_chunk, todo)):
            print(f'chunk {k + 1}/{len(todo)}', flush=True)
    if os.environ.get('CHUNKS_ONLY'):
        return
    lst = os.path.join(d, 'list.txt')
    open(lst, 'w').writelines(f"file '{j[2]}'\n" for j in jobs)
    silent = os.path.join(d, 'video.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', silent], check=True)
    wav = os.path.join(d, 'mix.wav')
    mix_audio(t0, t1, wav)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', silent, '-i', wav, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '320k',
                    '-shortest', '-movflags', '+faststart', out], check=True)
    print('wrote', out)


if __name__ == '__main__':
    os.makedirs(BUILD, exist_ok=True)
    cmd = sys.argv[1]
    if cmd == 'stills':
        for s in sys.argv[2:]:
            Image.fromarray(frame(float(s))).save(os.path.join(BUILD, f'm_{float(s):06.2f}.png'))
    elif cmd == 'cut':
        t0 = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
        t1 = float(sys.argv[3]) if len(sys.argv) > 3 else DUR
        name = 'EUREKA_THE_MOMENT_FINAL.mp4' if (t0, t1) == (0.0, DUR) else f'moment_{int(t0)}_{int(t1)}.mp4'
        render(t0, t1, os.path.join(HERE if name.endswith('FINAL.mp4') else BUILD, name))
