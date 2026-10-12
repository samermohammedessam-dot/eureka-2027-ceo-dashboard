"""EUREKA — THE POWER OF TEN (105 s, 1920x1080, 30 fps).

  python3 film.py stills 4 8 13 18 22 ...
  python3 film.py preview          # 0-22 s: opening + stage + first achievement
  python3 film.py video            # full film -> EUREKA_THE_POWER_OF_TEN_FINAL.mp4

Timeline (s) — reveals lock to a 0.6 s beat (100 BPM)
  0-10    A NIGHT WORTH CELEBRATING   darkness, golden pulse, spotlights, Eureka reveal, title
  10-16.6 TEN LIGHTS                  the platform from above, ten waiting positions
  16.6-76.6 THE ACHIEVEMENT REVEALS   10 x 6 s, four rotating compositions
  76.6-89.2 THE PEOPLE                a camera journey through the real photographs
  89.2-98 THE GRAND REVEAL            the breath, the pulse, the giant 10
  98-105  THE EUREKA FINALE
"""
import functools
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('EUREKA_ASSETS', os.path.join(ROOT, 'assets_dl'))
import render as R  # noqa: E402  (shared helpers: text, logo cards, photos, particles)
import stage as ST  # noqa: E402
from render import Layer, composite, ease_back, ease_io, ease_out, lerp, seg, splat, text_layer, tonemap  # noqa: E402

W, H, FPS = 1920, 1080, 30
DUR = 105.0
BUILD = os.path.join(ROOT, 'build', 'pot')
GOLD = np.array([1.0, 0.80, 0.48], np.float32)
WARM = np.array([1.0, 0.9, 0.75], np.float32)

T_STAGE = 10.0
T_MS = 16.6
SLOT = 6.0
IGN = 0.6                 # ignition inside a slot (on the beat)
T_PEOPLE = T_MS + 10 * SLOT   # 76.6
T_DROP = 89.2
T_HIT = 90.4
T_END = 98.0
INSTS = None


def insts():
    global INSTS
    if INSTS is None:
        INSTS = R.manifest()['institutions']
    return INSTS


def radial(x, y, r):
    return np.exp(-(((ST._lx - x) ** 2 + (ST._ly - y) ** 2) / (r * r)))


def glow(cv, x, y, r, col, g):
    ST.add(cv, radial(x, y, r), col, g)


# ------------------------------------------------------------------ Eureka (transparent logo)
@functools.lru_cache(maxsize=None)
def eureka_rgba():
    im = Image.open(R.manifest()['eureka_logo']).convert('RGB')
    a = np.asarray(im, np.float32) / 255
    alpha = np.clip((1 - a.min(axis=2)) / 0.18, 0, 1)
    rgb = (a - (1 - alpha[..., None])) / np.maximum(alpha[..., None], 1e-3)
    img = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), alpha]) * 255).astype(np.uint8), 'RGBA')
    return img.crop(img.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox())


@functools.lru_cache(maxsize=None)
def eureka_layer(width, halo=0.45):
    lg = eureka_rgba()
    h = int(width * lg.height / lg.width)
    lg = lg.resize((width, h), Image.LANCZOS)
    m = int(width * 0.35)
    canvas = Image.new('RGBA', (width + 2 * m, h + 2 * m), (0, 0, 0, 0))
    a = lg.getchannel('A').filter(ImageFilter.MaxFilter(9 if width > 300 else 7))
    hl = Image.new('L', canvas.size, 0)
    hl.paste(a, (m, m))
    hl = hl.filter(ImageFilter.GaussianBlur(width * 0.07))
    g = Image.new('RGBA', canvas.size, (250, 244, 228, 0))
    g.putalpha(hl.point(lambda v: int(min(255, v * halo))))
    canvas.alpha_composite(g)
    canvas.alpha_composite(lg, (m, m))
    return Layer(canvas, None)


CORNER = (W - 40 - 176 / 2 - 10, 72)


def corner_logo(cv, o=1.0):
    if o > 0.01:
        composite(cv, eureka_layer(176, 1.15), *CORNER, 1.0, o, glow=0)


# ------------------------------------------------------------------ shared pieces
def plate(inst, w=700, h=370):
    return R.inst_card(inst, w, h)


def seal(d):
    return R.seal_layer(d)


def name_of(inst):
    return f"{inst['name']}  ·  {inst['branch']}" if inst.get('branch') else inst['name']


def title_block(cv, inst, k, x, y, q, scale=1.0, align_w=900):
    """Institution name (white) + gold accent line + 'GAHAR ACCREDITATION · ACHIEVEMENT 0k'."""
    o = ease_io(q)
    if o <= 0.01:
        return
    zx = np.exp(-((np.arange(W) - x) / (align_w * 0.62)) ** 4)
    zy = np.exp(-((np.arange(H) - (y + 34 * scale)) / (95 * scale)) ** 4)
    cv *= (1 - 0.5 * o * zy[:, None] * zx[None, :])[..., None]
    yy = y
    for ln in R.fit_text_lines(name_of(inst), 'cinzel', int(60 * scale), 700, align_w, 3, 'ivory', 6):
        composite(cv, ln, x, yy + 10 * (1 - ease_out(q)), 1.0, o, glow=0.25)
        yy += ln.h * 0.6
    lw = int(300 * scale * ease_out(seg(q, 0.3, 1.0)))
    if lw > 2:
        cv[int(yy + 14):int(yy + 16), int(x - lw / 2):int(x + lw / 2)] += GOLD * 0.9 * o
    sub = text_layer(f'GAHAR ACCREDITATION  ·  ACHIEVEMENT {k + 1:02d}', 'mont', int(24 * scale), 600, 6, 'gold', 4)
    composite(cv, sub, x, yy + 46 * scale, min(1.0, align_w * 0.95 / sub.w), o, glow=0.35)


def reveal_plate(cv, inst, x, y, u, s=1.0, w=700, h=370, seal_pos=None, seal_d=170):
    """Logo plate arrival: rises with a gold light sweep; GAHAR seal follows. Restrained glow."""
    q = seg(u, 0.0, 0.55)
    if q <= 0:
        return
    sc = s * (0.82 + 0.18 * ease_back(q))
    composite(cv, plate(inst, w, h), x, y + 40 * (1 - ease_out(q)), sc, seg(u, 0, 0.18), glow=0.18,
              shine=seg(u, 0.25, 1.05) if 0.25 < u < 1.05 else None)
    if u < 0.9:  # gold sparkle burst at the moment of reveal (no white flash)
        R.firework(cv, u, 0.08, x, y - h * sc * 0.45, 7 + hash(inst['name']) % 50, n=36, life=1.0, speed=360)
    if seal_pos:
        qs = seg(u, 0.35, 0.8)
        composite(cv, seal(seal_d), *seal_pos, (0.7 + 0.3 * ease_back(qs)) * s, qs, glow=0.25)


@functools.lru_cache(maxsize=48)
def framed(path, w, h, border=6):
    """Real photo with a slim gold frame + soft shadow, as an RGBA layer (faces untouched)."""
    arr = R.photo_crop(path, w, h, 0.5, seed=hash(path) % 97, zoom=0.0)
    card = np.zeros((h + 2 * border, w + 2 * border, 4), np.float32)
    card[..., :3] = (0.86, 0.72, 0.42)
    card[..., 3] = 1
    card[border:border + h, border:border + w, :3] = arr
    img = Image.fromarray((card * 255).astype(np.uint8), 'RGBA')
    m = 46
    out = Image.new('RGBA', (img.width + 2 * m, img.height + 2 * m), (0, 0, 0, 0))
    sh = Image.new('L', out.size, 0)
    ImageDraw.Draw(sh).rectangle((m + 10, m + 18, m + img.width + 10, m + img.height + 18), fill=170)
    out.paste(Image.new('RGBA', out.size, (0, 0, 0, 255)), (0, 0), sh.filter(ImageFilter.GaussianBlur(18)))
    out.alpha_composite(img, (m, m))
    return Layer(out, None)


def photo_box(path, maxw, maxh):
    """Frame size that keeps whole people in view: contain portraits, cover landscapes."""
    if R.is_portrait(path, 1.15):
        return R.contain(path, maxw, maxh)
    return maxw, maxh


def kb_photo(cv, path, x, y, w, h, p, seed, o=1.0, border=True):
    """Large real photograph with a slow cinematic push (Ken Burns) and gold hairline."""
    arr = R.photo_crop(path, int(w), int(h), p, seed=seed, zoom=0.07)
    R.draw_photo(cv, arr, int(x - w / 2), int(y - h / 2), o, border=3 if border else 0, shadow=0.7,
                 border_color=GOLD * 0.95)


# ------------------------------------------------------------------ the stage camera
def stage_cam_opening(t):
    q = ease_io(seg(t, 1.2, 9.5))
    return ST.Cam((0, lerp(160, 620, q), lerp(-900, -2400, q)), (0, lerp(120, 200, q), 300), 46)


def stage_cam_high(t):
    q = ease_io(seg(t, T_STAGE, T_MS + 0.6))
    return ST.Cam((lerp(0, -200, q), lerp(900, 1600, q), lerp(-2200, -1500, q)), (0, 0, 320), 50)


def stage_cam_focus(k, u):
    P = ST.pedestal(k)
    q = ease_io(min(1.0, u / 1.2))
    return ST.Cam((P[0] * 0.55, lerp(1000, 560, q), P[2] - lerp(2000, 1350, q)), (P[0], 220, P[2]), 46)


def lit_levels(t):
    lv = []
    for k in range(10):
        a = T_MS + k * SLOT + IGN
        lv.append(ease_out(seg(t, a - 0.15, a + 0.35)))
    return lv


# ------------------------------------------------------------------ scenes
def s1_opening(cv, t):
    cam = stage_cam_opening(t)
    on1 = ease_out(seg(t, 1.5, 1.8))
    on2 = ease_out(seg(t, 2.3, 2.6))
    spots = [ST.spot((-500, 36, 250), t, 0.0, on1, sweep=0.6), ST.spot((500, 36, 250), t, 2.0, on2, sweep=0.6),
             ST.spot((0, 36, 300), t, 4.0, ease_out(seg(t, 3.2, 3.6)), sweep=0.3)]
    cv[:] = ST.render_stage(cam, t, [0.12 * seg(t, 4, 7)] * 10, spots, wall=seg(t, 2.6, 5.0), dim=1.0)
    cv *= ease_io(seg(t, 0.8, 2.0)) * 0.85 + 0.15 * seg(t, 0.4, 0.8)
    pulse = math.exp(-((t - 0.9) / 0.35) ** 2)  # the first golden pulse in the darkness
    glow(cv, W / 2, H * 0.45, 160 + 200 * pulse, GOLD, 1.2 * pulse)
    splat(cv, W / 2, H * 0.45, 6, 1.4 * pulse)
    R.DUST.draw(cv, t, seg(t, 2.0, 4.0) * 0.7)
    big = eureka_layer(540, 0.5)
    q = seg(t, 3.6, 4.6)
    if t < 9.0:
        composite(cv, big, W / 2, 330, lerp(0.92, 1.0, ease_out(q)), ease_io(q), glow=0,
                  shine=seg(t, 4.4, 5.4) if 4.4 < t < 5.4 else None)
    else:
        m = ease_io(seg(t, 9.0, 9.8))
        composite(cv, big, lerp(W / 2, CORNER[0], m), lerp(330, CORNER[1], m), lerp(1.0, eureka_layer(176, 1.15).w / big.w, m), 1.0, glow=0)
    fo = 1 - seg(t, 9.2, 9.9)
    q1 = seg(t, 5.4, 6.3)
    qz = ease_io(seg(t, 5.0, 6.0)) * fo  # quiet zone so the title never fights the pedestal rings
    zy = np.exp(-((np.arange(H) - 700) / 150) ** 4)
    zx = np.exp(-((np.arange(W) - W / 2) / 900) ** 4)
    cv *= (1 - 0.72 * qz * zy[:, None] * zx[None, :])[..., None]
    composite(cv, text_layer('THE POWER OF TEN', 'cinzel', 104, 700, 18, 'gold', 14), W / 2, 640 + 14 * (1 - ease_out(q1)),
              1.0, ease_io(q1) * fo, glow=0.45, shine=seg(t, 6.4, 7.6) if 6.4 < t < 7.6 else None)
    lw = int(560 * ease_out(seg(t, 6.0, 7.0)) * fo)
    if lw > 2:
        cv[722:724, W // 2 - lw // 2:W // 2 + lw // 2] += GOLD * 0.9
    q2 = seg(t, 6.4, 7.3)
    composite(cv, text_layer('CELEBRATING 10 GAHAR ACCREDITATION ACHIEVEMENTS', 'mont', 30, 600, 7, 'ivory', 4), W / 2, 772,
              1.0, ease_io(q2) * fo, glow=0.2)
    return t >= 9.8


def s2_stage(cv, t):
    cam = stage_cam_high(t)
    lv = lit_levels(t)
    breath = [0.18 + 0.12 * math.sin(t * 2.2 + k) for k in range(10)]
    k0 = ST.pedestal(0)
    sweep_q = ease_io(seg(t, 14.6, T_MS + IGN))
    target = lerp(np.array([0.0, 36, 300]), k0, sweep_q)
    spots = [(np.array([0, 1650, -300]), target, 0.8), ST.spot((-700, 36, 300), t, 1.0, 0.4, sweep=1.0),
             ST.spot((700, 36, 300), t, 3.0, 0.4, sweep=1.0)]
    cv[:] = ST.render_stage(cam, t, [max(a, b) for a, b in zip(lv, breath)], spots)
    R.DUST.draw(cv, t, 0.7)
    for a, b, text, y in [(10.5, 13.4, 'TEN ACHIEVEMENTS', 820), (13.0, 16.2, 'ONE SHARED VISION', 905)]:
        if a <= t < b:
            q = seg(t, a, a + 0.7) * (1 - seg(t, b - 0.4, b))
            composite(cv, text_layer(text, 'cinzel', 72, 700, 14, 'gold', 12), W / 2, y + 12 * (1 - ease_out(q)), 1.0, ease_io(q), glow=0.7)
    return True


# ------------------------------------------------------------------ the achievement reveals
def stage_backdrop(cv, t, k, u, dim=0.42):
    cam = stage_cam_focus(k, u)
    prev = ST.pedestal(k - 1) if k > 0 else np.array([0.0, 36, 300])
    tq = ease_io(min(1.0, u / IGN))
    spots = [(np.array([0, 1650, -300]), lerp(prev, ST.pedestal(k), tq), 1.0),
             ST.spot(k, t, 1.0 + k, 0.35, sweep=0.4)]
    cv[:] = ST.render_stage(cam, t, lit_levels(t), spots) * dim


def comp_hero(cv, t, k, inst, u):
    """V0 — Floating large-format photograph under a spotlight, logo plate to the left."""
    ph = inst['photos']
    a = IGN + 0.15
    reveal_plate(cv, inst, 430, 330, u - a, s=0.86, seal_pos=(430, 600), seal_d=150)
    title_block(cv, inst, k, 430, 720, seg(u, a + 0.5, a + 1.1), scale=0.85, align_w=700)
    if ph:
        q = ease_out(seg(u, a + 0.6, a + 1.3))
        path = ph[0] if (u < 3.6 or len(ph) < 2) else ph[1]
        w, h = photo_box(path, 1020, 780)
        x, y = 1350 + 60 * (1 - q), 540
        glow(cv, x, y - h * 0.3, 700, WARM, 0.18 * q)
        kb_photo(cv, path, x, y, w, h, seg(u, a + 0.6, 6.0), seed=k * 3, o=q)
        if 3.4 < u < 3.8 and len(ph) > 1:
            glow(cv, x, y, 500, WARM, 0.35 * math.sin(math.pi * seg(u, 3.4, 3.8)))


def comp_wall(cv, t, k, inst, u):
    """V1 — Cinematic photo wall; a spotlight travels across the faces; logo above."""
    ph = inst['photos'][:3]
    a = IGN + 0.15
    reveal_plate(cv, inst, 760, 220, u - a, s=0.7, seal_pos=(1180, 220), seal_d=150)
    n = len(ph)
    if n:
        ww = 1800 // max(n, 2) - 40
        hh = 470
        for j, path in enumerate(ph):
            q = ease_out(seg(u, a + 0.5 + 0.25 * j, a + 1.1 + 0.25 * j))
            w, h = photo_box(path, ww, hh)
            cx = W / 2 + (j - (n - 1) / 2) * (ww + 30)
            focus = math.exp(-((u - (a + 1.6 + 1.1 * j)) / 0.9) ** 2)
            kb_photo(cv, path, cx, 650 + 50 * (1 - q), w, h, seg(u, a, 6), seed=k * 5 + j, o=q * (0.75 + 0.25 * focus))
            glow(cv, cx, 560, 320, WARM, 0.22 * focus * q)
    title_block(cv, inst, k, W / 2, 935, seg(u, a + 0.8, a + 1.4), scale=0.7, align_w=1200)


def comp_architect(cv, t, k, inst, u):
    """V2 — Architectural logo reveal on a column of light, then a full-frame people moment."""
    ph = inst['photos']
    a = IGN + 0.1
    full = ease_io(seg(u, 2.4, 3.1)) if ph else 0.0
    if full > 0:
        path = ph[0] if len(ph) < 3 else ph[2]
        if R.is_portrait(path, 1.15):
            w, h = R.contain(path, 1400, 1000)
            kb_photo(cv, path, 1180, 540, w, h, seg(u, 2.4, 6.0), seed=k * 7, o=full, border=True)
        else:
            arr = R.photo_crop(path, W, H, seg(u, 2.4, 6.0), seed=k * 7, zoom=0.08)
            grade = arr * 0.92 * R.vignette(0.55)
            cv[:] = cv * (1 - full) + grade * full
    mv = ease_io(seg(u, 2.3, 3.0))
    x, y = lerp(W / 2, 440, mv), lerp(470, 720, mv)
    s = lerp(1.05, 0.62, mv)
    glow(cv, x, y, 420, GOLD, 0.25 * (1 - mv) * seg(u, a, a + 0.6))
    reveal_plate(cv, inst, x, y, u - a, s=s, seal_pos=(x + 470 * s + 30, y), seal_d=int(lerp(190, 150, mv)))
    if mv < 0.5:
        title_block(cv, inst, k, W / 2, 760, seg(u, a + 0.5, a + 1.1) * (1 - seg(u, 2.0, 2.4)), scale=0.95, align_w=1300)
    else:
        title_block(cv, inst, k, 470, 915, seg(u, 3.0, 3.5), scale=0.62, align_w=760)


def comp_mosaic(cv, t, k, inst, u):
    """V3 — Elegant mosaic of the institution's photographs with a moving spotlight focus."""
    ph = inst['photos'][:4]
    a = IGN + 0.15
    if ph:
        tiles = [(0, 0), (1, 0), (0, 1), (1, 1)][:max(2, len(ph))]
        tw, th = W // 2 - 30, H // 2 - 30
        for j, (cx_, cy_) in enumerate(tiles):
            path = ph[j % len(ph)]
            x = 30 + cx_ * (tw + 30) + tw / 2 - 15
            y = 30 + cy_ * (th + 30) + th / 2 - 15
            q = ease_out(seg(u, a + 0.2 * j, a + 0.7 + 0.2 * j))
            focus = math.exp(-((u - (a + 1.4 + 1.0 * j)) / 0.8) ** 2)
            w, h = photo_box(path, tw, th)
            kb_photo(cv, path, x, y, w, h, seg(u, a, 6), seed=k * 11 + j, o=q * (0.5 + 0.5 * focus))
    # logo in a quiet centre zone, always on top
    zx = np.exp(-((np.arange(W) - W / 2) / 560.0) ** 4)
    zy = np.exp(-((np.arange(H) - 470) / 300.0) ** 4)
    cv *= (1 - 0.6 * seg(u, a, a + 0.5) * zy[:, None] * zx[None, :])[..., None]
    reveal_plate(cv, inst, W / 2 - 110, 420, u - a, s=0.78, seal_pos=(W / 2 + 290, 420), seal_d=150)
    title_block(cv, inst, k, W / 2, 640, seg(u, a + 0.5, a + 1.1), scale=0.8, align_w=1100)


def comp_logo_only(cv, t, k, inst, u):
    """Logo-focused recognition (no photographs supplied): plate + seal under a crown of light."""
    a = IGN + 0.1
    R.DUST.draw(cv, t, 1.0)
    ST.add(cv, R.rays(W / 2, 420, t, n=18, speed=0.05, reach=900), GOLD, 0.35 * seg(u, a, a + 0.6))
    reveal_plate(cv, inst, W / 2 - 150, 420, u - a, s=1.05, seal_pos=(W / 2 + 390, 420), seal_d=230)
    title_block(cv, inst, k, W / 2, 720, seg(u, a + 0.5, a + 1.1), scale=1.0, align_w=1300)


COMPS = [comp_hero, comp_wall, comp_architect, comp_mosaic]


def s3_achievement(cv, t):
    k = min(9, int((t - T_MS) // SLOT))
    u = t - T_MS - k * SLOT
    inst = insts()[k]
    stage_backdrop(cv, t, k, u, dim=lerp(1.0, 0.42, seg(u, IGN, IGN + 0.6)))
    if u >= IGN:
        (COMPS[k % 4] if inst['photos'] else comp_logo_only)(cv, t, k, inst, u)
    # celebration: gold particles that grow with the count of achievements
    R.DUST.draw(cv, t, 0.4 + 0.05 * k)
    # transition: the spotlight whips toward the next achievement
    q = seg(u, SLOT - 0.45, SLOT)
    if q > 0:
        ST.add(cv, R.streak(q, angle=-0.35 if k % 2 else -2.8), GOLD, 0.7)
        cv *= 1 - 0.35 * math.sin(math.pi * q)
    return True


# ------------------------------------------------------------------ the people: a journey through the photographs
@functools.lru_cache(maxsize=1)
def journey():
    m = R.manifest()
    pool = []
    for inst in m['institutions']:
        pool += [p for p in inst['photos'] if p not in pool]
    pool = list(m['team_photos'][:4]) + pool + [p for p in m['team_photos'][4:] if p not in pool]
    rng = np.random.default_rng(10)
    items = []
    for j, p in enumerate(pool[:28]):
        side = -1 if j % 2 == 0 else 1
        items.append((p, side * rng.uniform(380, 620), rng.uniform(-200, 160), 700 + j * 520, rng.uniform(-3, 3)))
    return items


def s4_people(cv, t):
    u = t - T_PEOPLE
    cv[:] = R.bg_navy() * 0.75
    R.DUST.draw(cv, t, 0.8)
    camz = 600 + u * 1080 * (1 + 0.35 * u / 12)        # accelerating
    f = 900
    visible = []
    for p, x, y, z, rot in journey():
        dz = z - camz
        if 120 < dz < 3800:
            visible.append((dz, p, x, y, rot))
    for dz, p, x, y, rot in sorted(visible, key=lambda v: -v[0]):
        s = f / dz
        w0, h0 = photo_box(p, 900, 600)
        sw, sh_ = int(w0 * s), int(h0 * s)
        if sw < 30:
            continue
        lay = framed(p, w0 // 2, h0 // 2)
        fade = min(1.0, (3800 - dz) / 900) * min(1.0, (dz - 120) / 220)
        sx, sy = W / 2 + x * s, H / 2 + y * s
        composite(cv, lay, sx, sy, s * 2, fade, glow=0, rot=rot)
        if dz < 600:  # speed light as a photo passes the camera
            ST.add(cv, radial(sx, sy, 300), WARM, 0.06 * (1 - dz / 600))
    ST.add(cv, R.streak((u * 0.7) % 1, angle=-0.25), GOLD, 0.12)
    for a, b, text in [(T_PEOPLE + 0.8, T_PEOPLE + 5.6, 'BEHIND EVERY ACHIEVEMENT...'),
                       (T_PEOPLE + 6.4, T_DROP - 0.3, 'EXTRAORDINARY PEOPLE.')]:
        if a <= t < b:
            q = seg(t, a, a + 0.7) * (1 - seg(t, b - 0.4, b))
            zy = np.exp(-((np.arange(H) - 540) / 110.0) ** 4)
            cv *= (1 - 0.55 * q * zy)[:, None, None]
            composite(cv, text_layer(text, 'cinzel', 84, 700, 12, 'gold', 14), W / 2, 540 + 14 * (1 - ease_out(q)), 1.0, ease_io(q), glow=0.8)
    if t > T_DROP - 0.5:
        cv *= 1 - seg(t, T_DROP - 0.5, T_DROP)
    return True


# ------------------------------------------------------------------ the grand reveal
CONF_RAIN = R.Confetti(260, 501, T_HIT - 0.2, 'rain')
CONF_CANNON = R.Confetti(240, 502, T_HIT, 'cannon')
CONF_RAIN2 = R.Confetti(160, 503, T_HIT + 3.5, 'rain')
TEN_C = (W / 2, 360)


@functools.lru_cache(maxsize=1)
def ten_3d():
    """A dimensional '10': gold face over a stacked bronze extrusion, cut once and reused."""
    face = text_layer('10', 'cinzel', 560, 900, 0, 'gold', 26)
    a = face.rgba.getchannel('A')
    depth = 22
    w, h = face.rgba.size
    out = Image.new('RGBA', (w + depth, h + depth), (0, 0, 0, 0))
    for d in range(depth, 0, -1):
        c = int(70 + 60 * (1 - d / depth))
        sl = Image.new('RGBA', (w, h), (c + 40, int(c * 0.72), int(c * 0.32), 255))
        out.paste(sl, (d, d), a)
    out.alpha_composite(face.rgba)
    g = Image.new('L', out.size, 0)
    g.paste(face.glow, (0, 0))
    return Layer(out, g)


def ring_positions():
    pos = []
    for side in (-1, 1):
        for j in range(5):
            pos.append((W / 2 + side * (690 + 55 * math.cos((j - 2) / 2 * 1.2)), 250 + j * 190))
    order = [0, 5, 1, 6, 2, 7, 3, 8, 4, 9]
    return [pos[o] for o in order]


def s5_reveal(cv, t):
    cam = ST.Cam((0, 1700, -1700), (0, 0, 320), 52)
    if t < T_HIT:  # the breath: lights converge, darkness, a single golden pulse
        p = seg(t, T_DROP, T_HIT)
        spots = [(np.array([x, 1650, -300]), lerp(ST.pedestal(k), np.array([0.0, 36, 300]), ease_io(p)), 1 - 0.6 * p)
                 for k, x in zip(range(0, 10, 3), (-900, -300, 300, 900))]
        cv[:] = ST.render_stage(cam, t, [1.0] * 10, spots) * (1 - 0.75 * ease_io(p))
        pulse = math.exp(-((t - (T_HIT - 0.25)) / 0.18) ** 2)
        glow(cv, *TEN_C, 120 + 260 * pulse, GOLD, 1.6 * pulse)
        splat(cv, *TEN_C, 4 + 20 * p ** 3, 0.2 + 1.4 * p ** 2)
        return True
    u = t - T_HIT
    beat = (u % 0.6) / 0.6
    cv[:] = ST.render_stage(cam, t, [1.0] * 10, [ST.spot(k, t, k, 0.6, sweep=1.0) for k in (1, 4, 5, 8)]) * 0.45
    ST.add(cv, R.rays(*TEN_C, t, n=24, speed=0.05, sharp=5, reach=1150), GOLD, 0.4 + 0.2 * math.exp(-beat * 4) + 0.7 * math.exp(-u / 0.5))
    rp = ease_out(seg(u, 0, 0.9))
    if 0 < rp < 1:
        dd = np.sqrt((ST._lx - TEN_C[0]) ** 2 + (ST._ly - TEN_C[1]) ** 2)
        ST.add(cv, np.exp(-((dd - rp * 1500) / 50) ** 2), WARM, 1.1 * (1 - rp))
    R.DUST.draw(cv, t, 1.0)
    for (fx, fy, ft, fs) in [(430, 240, T_HIT + 0.25, 1), (1490, 220, T_HIT + 0.5, 2), (960, 90, T_HIT + 2.4, 3),
                             (300, 560, T_HIT + 4.2, 4), (1620, 560, T_HIT + 5.6, 5), (960, 120, T_HIT + 6.6, 6)]:
        R.firework(cv, t, ft, fx, fy, fs, n=70)
    CONF_RAIN.draw(cv, t)
    CONF_CANNON.draw(cv, t)
    CONF_RAIN2.draw(cv, t)
    q = seg(u, 0, 0.55)
    shine = next((seg(u, a, a + 0.9) for a in (0.7, 3.3, 5.9) if a < u < a + 0.9), None)
    composite(cv, ten_3d(), *TEN_C, lerp(1.6, 1.0, ease_out(q)) * (1 + 0.015 * math.exp(-beat * 5) * (u > 0.6)),
              seg(u, 0, 0.12), glow=0.8 + 0.4 * math.exp(-beat * 4), shine=shine)
    zy = np.exp(-((np.arange(H) - 760) / 120.0) ** 4)
    zx = np.exp(-((np.arange(W) - W / 2) / 560.0) ** 4)
    cv *= (1 - 0.5 * seg(u, 0.6, 1.2) * zy[:, None] * zx[None, :])[..., None]
    q1, q2 = seg(u, 0.8, 1.3), seg(u, 1.05, 1.55)
    composite(cv, text_layer('GAHAR ACCREDITATION', 'cinzel', 64, 700, 10, 'gold', 12), W / 2, 715 + 20 * (1 - ease_out(q1)), 1.0, ease_io(q1), glow=0.9)
    composite(cv, text_layer('ACHIEVEMENTS', 'cinzel', 64, 700, 22, 'gold', 12), W / 2, 800 + 20 * (1 - ease_out(q2)), 1.0, ease_io(q2), glow=0.9)
    qs = seg(u, 1.6, 2.1)
    composite(cv, seal(190), W / 2, 950, 0.6 + 0.4 * ease_back(qs), qs, glow=0.5 + 0.8 * math.exp(-max(0, u - 1.6) / 0.3))
    for j, ((x, y), inst) in enumerate(zip(ring_positions(), insts())):
        s = 0.6 + j * 0.3
        if u < s:
            continue
        qk = seg(u, s, s + 0.3)
        y += 5 * math.sin(t * 1.6 + j)
        composite(cv, R.inst_card(inst, 300, 160, pad_frac=0.08, radius=16, frame=3), x, y, 0.5 + 0.5 * ease_back(qk),
                  seg(u, s, s + 0.12), glow=0.15 + 0.6 * math.exp(-(u - s) / 0.25))
        if inst.get('branch'):
            composite(cv, R.branch_tag(inst['branch']), x + (95 if x < W / 2 else -95), y + 80, 1.0, seg(u, s + 0.1, s + 0.35), glow=0)
        if u - s < 0.2:
            splat(cv, x, y - 80, 10, 0.8 * (1 - (u - s) / 0.2))
    glow(cv, W / 2, H / 2, 900, WARM, 1.0 * math.exp(-u / 0.16))
    if t > T_END - 0.6:  # all light flows toward the finale
        cv *= 1 - 0.5 * seg(t, T_END - 0.6, T_END)
    return True


def s6_finale(cv, t):
    u = t - T_END
    cv[:] = R.bg_navy() * 0.85
    R.DUST.draw(cv, t, 1.0)
    ST.add(cv, R.rays(W / 2, 330, t, n=16, speed=0.04, reach=900), GOLD, 0.22 + 0.5 * math.exp(-u / 0.4))
    # light trails converging into the logo
    for j in range(10):
        a0 = j / 10 * 2 * math.pi
        for k in range(12):
            q = ease_io(seg(u, 0.0 + k * 0.02, 0.9 + k * 0.02))
            r = lerp(900, 0, q)
            splat(cv, W / 2 + r * math.cos(a0 + q * 2), 330 + r * 0.55 * math.sin(a0 + q * 2), 2, (1 - k / 12) * (1 - seg(u, 0.85, 1.0)))
    q = seg(u, 0.7, 1.5)
    composite(cv, eureka_layer(560, 0.5), W / 2, 330, lerp(0.9, 1.0, ease_out(q)), ease_io(q), glow=0)
    for j, (text, at) in enumerate([('10 ACHIEVEMENTS.', 1.6), ('ONE VISION.', 2.1), ('ENDLESS POSSIBILITIES.', 2.6)]):
        qq = seg(u, at, at + 0.5) * (1 - seg(u, 4.1, 4.5))
        composite(cv, text_layer(text, 'cinzel', 48, 700, 8, 'ivory', 6), W / 2 + (j - 1) * 520, 690 + 10 * (1 - ease_out(qq)), 1.0, ease_io(qq), glow=0.3)
    q2 = seg(u, 4.4, 5.1)
    composite(cv, text_layer('TOGETHER, WE RAISE THE STANDARD.', 'cinzel', 70, 700, 6, 'gold', 12), W / 2, 700 + 12 * (1 - ease_out(q2)),
              1.0, ease_io(q2), glow=0.9, shine=seg(u, 5.2, 6.2) if 5.2 < u < 6.2 else None)
    glow(cv, W / 2, 330, 700, WARM, 0.7 * math.exp(-max(0, u - 0.8) / 0.3) * (u > 0.8))
    cv *= 1 - seg(t, DUR - 0.8, DUR)
    return False


def frame(t):
    cv = np.zeros((H, W, 3), np.float32)
    if t < T_STAGE:
        corner = s1_opening(cv, t)
    elif t < T_MS:
        corner = s2_stage(cv, t)
    elif t < T_PEOPLE:
        corner = s3_achievement(cv, t)
    elif t < T_DROP:
        corner = s4_people(cv, t)
    elif t < T_END:
        corner = s5_reveal(cv, t)
    else:
        corner = s6_finale(cv, t)
    R.bloom(cv, 0.26, 0.8)
    cv *= R.vignette(0.36)
    if corner:
        corner_logo(cv)
    return tonemap(cv)


# ------------------------------------------------------------------ output
def _chunk(args):
    a, b, path = args
    pr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-pix_fmt', 'yuv420p', path],
                          stdin=subprocess.PIPE)
    for f in range(a, b):
        pr.stdin.write(frame(f / FPS).tobytes())
    pr.stdin.close()
    pr.wait()
    return path


def render(t0, t1, out):
    d = os.path.join(BUILD, f'chunks_{int(t0)}_{int(t1)}')
    os.makedirs(d, exist_ok=True)
    a0, a1 = int(t0 * FPS), int(t1 * FPS)
    jobs = [(a, min(a1, a + 45), os.path.join(d, f'c{a:05d}.mp4')) for a in range(a0, a1, 45)]
    with Pool(4) as p:
        for k, _ in enumerate(p.imap(_chunk, jobs)):
            print(f'chunk {k + 1}/{len(jobs)}', flush=True)
    lst = os.path.join(d, 'list.txt')
    open(lst, 'w').writelines(f"file '{j[2]}'\n" for j in jobs)
    silent = os.path.join(d, 'video.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', silent], check=True)
    music = os.path.join(BUILD, 'pot_score.wav')
    subprocess.run([sys.executable, os.path.join(HERE, 'score.py'), music], check=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', silent, '-ss', str(t0), '-t', str(t1 - t0), '-i', music,
                    '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k',
                    '-af', f'afade=t=out:st={t1 - t0 - 0.8}:d=0.8' if t1 < DUR else 'anull', '-movflags', '+faststart', out], check=True)
    print('wrote', out)


if __name__ == '__main__':
    os.makedirs(BUILD, exist_ok=True)
    cmd = sys.argv[1]
    if cmd == 'stills':
        for s in sys.argv[2:]:
            Image.fromarray(frame(float(s))).save(os.path.join(BUILD, f'f_{float(s):06.2f}.png'))
    elif cmd == 'preview':
        render(0.0, 22.6, os.path.join(BUILD, 'EUREKA_THE_POWER_OF_TEN_preview.mp4'))
    elif cmd == 'video':
        render(0.0, DUR, os.path.join(HERE, 'EUREKA_THE_POWER_OF_TEN_FINAL.mp4'))
