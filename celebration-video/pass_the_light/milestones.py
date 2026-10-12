"""Milestone reveal component for PASS THE LIGHT.

Each verified accreditation milestone = 6.0 s:
  0.0-1.2  City of Excellence beat: the relay light travels from the previous tower to this one;
           the tower ignites (the city is the storytelling transition, not the hero)
  1.2-6.0  The celebration stage: the institution's real photos as a moving, graded backdrop;
           large logo plate + the authentic GAHAR seal arrive with a light burst; 2-3 real photos
           float in at different depths on a drifting 2.5-D camera. Three layouts rotate and each
           stage takes its accent colour from the institution's own logo.
"""
import functools
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ.setdefault('EUREKA_ASSETS', os.path.join(os.path.dirname(HERE), 'assets_dl'))
import render as R  # noqa: E402
import scene3d as S  # noqa: E402
from render import (GOLD_HI, W, H, Layer, add_light, composite, ease_back, ease_io, ease_out, lerp, radial, seg, splat,
                    text_layer, vignette)  # noqa: E402

SLOT = 6.0
CITY_BEAT = 1.2


# ------------------------------------------------------------------ accents & assets
@functools.lru_cache(maxsize=None)
def accent(i):
    """Dominant saturated colour of the institution's logo (0..1 RGB) — gives every stage its own tint."""
    inst = R.manifest()['institutions'][i]
    if not inst['logo']:
        return np.array([0.85, 0.7, 0.4])
    im, _ = R.logo_image(inst['logo'])
    a = np.asarray(im.convert('RGBA').resize((120, 120)), np.float32) / 255
    rgb, al = a[..., :3].reshape(-1, 3), a[..., 3].reshape(-1)
    sat = rgb.max(1) - rgb.min(1)
    m = (al > 0.5) & (sat > 0.25) & (rgb.max(1) > 0.25)
    if m.sum() < 20:
        return np.array([0.85, 0.7, 0.4])
    c = np.median(rgb[m], axis=0)
    return c / max(c.max(), 1e-3)


@functools.lru_cache(maxsize=64)
def framed(path, w, h):
    """A real photo in a slim ivory frame with a gold hairline, as an RGBA layer (no retouching)."""
    arr = R.photo_crop(path, w, h, 0.5, seed=hash(path) % 97, zoom=0.0)
    fr = 12
    card = np.zeros((h + 2 * fr, w + 2 * fr, 4), np.float32)
    card[..., :3] = (0.97, 0.95, 0.9)
    card[..., 3] = 1
    card[fr - 2:fr + h + 2, fr - 2:fr + w + 2, :3] = (0.86, 0.72, 0.42)
    card[fr:fr + h, fr:fr + w, :3] = arr
    img = Image.fromarray((card * 255).astype(np.uint8), 'RGBA')
    m = 40
    out = Image.new('RGBA', (img.width + 2 * m, img.height + 2 * m), (0, 0, 0, 0))
    sh = Image.new('L', out.size, 0)
    ImageDraw.Draw(sh).rectangle((m + 8, m + 14, m + img.width + 8, m + img.height + 14), fill=150)
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    out.paste(Image.new('RGBA', out.size, (0, 0, 0, 255)), (0, 0), sh)
    out.alpha_composite(img, (m, m))
    return Layer(out, None)


def photos_of(inst):
    p = list(inst['photos'][:3])
    return p


# ------------------------------------------------------------------ city beat
def city_cam_for(i, q):
    _, land, route = S.city()
    L = land[i]
    prev = land[i - 1] if i > 0 else {'x': L['x'] - 900, 'z': L['z'] - 900}
    # camera travels alongside the light: from behind the previous tower towards this one
    tx, tz = lerp(prev['x'], L['x'], 0.55 + 0.45 * q), lerp(prev['z'], L['z'], 0.55 + 0.45 * q)
    side = -1 if i % 2 == 0 else 1
    cx, cz = tx + side * 620, tz - 1250
    cy = 560 - 60 * q
    yaw = math.atan2(L['x'] - cx, L['z'] - cz)
    return S.Cam((cx, cy, cz), yaw=yaw, pitch=0.16, fov_deg=52)


def city_beat(cv, u, i, n_lit_before):
    """u in [0, CITY_BEAT]. The light flies from tower i-1 to tower i; tower i ignites."""
    q = ease_io(min(1.0, u / 0.95))
    cam = city_cam_for(i, q)
    _, land, _ = S.city()
    lit = [1.0 if k < n_lit_before else 0.0 for k in range(len(land))]
    arr = max(0.0, u - 0.95)
    lit[i] = ease_out(min(1.0, arr / 0.25))
    sweeps = [1.0] * len(land)
    sweeps[i] = ease_io(min(1.0, arr / 0.25))
    img, _ = S.render_city(cam, lit, sweeps=sweeps)
    cv[:] = img
    L = land[i]
    p1 = np.array([L['x'], L['spire'] + 30, L['z']])
    if i > 0:
        P = land[i - 1]
        p0 = np.array([P['x'], P['spire'] + 30, P['z']])
    else:
        p0 = p1 + np.array([-1400, 500, -1600])
    for k in range(40, -1, -1):  # comet + ribbon
        qq = max(0.0, q - k * 0.012)
        sp, zz = cam.screen(S.bez3(p0, p1, qq, lift=300))
        if zz > 5:
            sz = max(1.0, 3500 / zz)
            splat(cv, sp[0], sp[1], sz * (2.4 if k == 0 else 0.9), 1.6 if k == 0 else 0.55 * (1 - k / 40))
    sp, zz = cam.screen(p1)
    if q < 1:
        hp, hz = cam.screen(S.bez3(p0, p1, q, lift=300))
        if hz > 5:
            add_light(cv, radial(hp[0], hp[1], 60 + 50000 / hz), np.array([1.0, 0.7, 0.34]), 0.6)
    if arr > 0:
        add_light(cv, radial(sp[0], sp[1], 140), GOLD_HI, 0.9 * lit[i] + 0.8 * math.exp(-arr / 0.15))
        beam = np.exp(-((R._lx - sp[0]) / 24) ** 2) * np.clip((sp[1] - R._ly) / 500, 0, 1) * np.exp(-np.clip(sp[1] - R._ly, 0, None) / 700)
        add_light(cv, beam, GOLD_HI, 0.5 * lit[i])
    return sp


# ------------------------------------------------------------------ the celebration stage
def backdrop(cv, u, i, inst, path):
    """Real photo as a moving, darkened, accent-graded backdrop (not blurred, not duplicated)."""
    acc = accent(i)
    arr = R.photo_crop(path, W // 2, H // 2, min(1.0, u / 5.0), seed=i * 7 + 3, zoom=0.10)
    im = Image.fromarray((arr * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6)).resize((W, H), Image.BILINEAR)
    arr = np.asarray(im, np.float32) / 255  # gentle depth-of-field: the backdrop sits behind the logos
    lum = arr @ np.array([0.3, 0.59, 0.11], np.float32)
    graded = arr * 0.24 + lum[..., None] * 0.06 + np.array([0.02, 0.04, 0.10])
    cv[:] = graded * vignette(0.75)
    add_light(cv, radial(W * 0.3, H * 0.35, 900), acc * 0.6 + GOLD_HI * 0.4, 0.22)
    add_light(cv, R.rays(W * 0.32, H * 0.42, u + i, n=14, speed=0.06, reach=900), GOLD_HI, 0.12)


def logo_stage(cv, u, i, inst, home, scale_end, t_move=(1.7, 2.3)):
    """Large logo plate + authentic GAHAR seal; plate moves from centre to its home position."""
    q_in = ease_out(seg(u, 0.15, 0.75))
    mv = ease_io(seg(u, *t_move))
    cx, cy = lerp(W / 2 - 120, home[0], mv), lerp(H / 2 - 40, home[1], mv)
    sc = lerp(1.0, scale_end, mv) * (0.7 + 0.3 * ease_back(seg(u, 0.15, 0.7)))
    plate = R.inst_card(inst, 720, 380)
    composite(cv, plate, cx, cy, sc, seg(u, 0.15, 0.35), glow=0.45 + 0.8 * math.exp(-max(0, u - 0.2) / 0.35),
              shine=seg(u, 0.5, 1.4) if 0.5 < u < 1.4 else None)
    seal = R.seal_layer(210)
    qs = seg(u, 0.55, 1.0)
    sx = cx + (380 + 120) * sc
    composite(cv, seal, sx, cy - 10 * sc, (0.6 + 0.4 * ease_back(qs)) * lerp(1.0, scale_end, mv), qs, glow=0.5)
    qn = seg(u, 0.7, 1.2)
    y = cy + 190 * sc + 52
    name = inst.get('branch') and f"{inst['name']} · {inst['branch']}" or inst['name']
    # soft, feathered quiet zone behind the name for legibility (no hard box)
    zx = np.exp(-((np.arange(W) - (cx + 60 * sc)) / 520.0) ** 4)
    zy = np.exp(-((np.arange(H) - (y + 30)) / 85.0) ** 4)
    cv *= (1 - 0.5 * ease_io(qn) * zy[:, None] * zx[None, :])[..., None]
    for ln in R.fit_text_lines(name, 'cinzel', 58, 700, 900 * max(sc, 0.75), 3, 'gold', 8):
        composite(cv, ln, cx + 60 * sc, y + 10 * (1 - ease_out(qn)), max(0.8, sc), ease_io(qn), glow=0.6)
        y += ln.h * 0.62 * max(0.8, sc)
    composite(cv, text_layer(f'GAHAR ACCREDITATION  ·  MILESTONE {i + 1:02d}', 'mont', 26, 600, 6, 'gold', 4),
              cx + 60 * sc, y + 26, max(0.8, sc), ease_io(seg(u, 0.9, 1.4)), glow=0.4)
    if u < 0.6:  # arrival burst
        add_light(cv, radial(cx, cy, 500), np.array([1.0, 0.82, 0.55]), 0.35 * math.sin(math.pi * seg(u, 0.0, 0.6)))
        R.firework(cv, u, 0.12, cx, cy - 40, 50 + i, n=44, life=1.2, speed=420)


LAYOUTS = {
    # (photo targets: x, y, w, h, rot, depth), logo home, logo scale
    0: ([(1430, 330, 500, 335, -4, 1.0), (1600, 720, 430, 290, 5, 0.8), (1240, 790, 400, 270, -2, 1.2)], (560, 430), 0.92),
    1: ([(470, 820, 400, 265, -3, 1.0), (960, 850, 400, 265, 2, 1.1), (1450, 820, 400, 265, -2, 0.9)], (880, 330), 0.86),
    2: ([(1430, 430, 640, 425, 0, 1.0), (1560, 830, 380, 255, 4, 1.3)], (560, 480), 0.86),
}


def stage(cv, u, i, inst):
    """u in [0, SLOT - CITY_BEAT]."""
    photos = photos_of(inst)
    variant = i % 3
    if photos:
        backdrop(cv, u, i, inst, photos[0] if (variant != 2 or u < 2.4 or len(photos) < 2) else photos[1])
    else:  # logo-only milestone: navy stage with the seal taking the second chair
        cv[:] = R.bg_navy() * 1.05
        add_light(cv, R.rays(W / 2, H / 2, u + i, n=16, speed=0.06, reach=900), GOLD_HI, 0.35)
    cam_drift = 28 * u  # slow lateral 2.5-D camera
    R.DUST.draw(cv, u + i * 3, 0.6)
    targets, home, scale_end = LAYOUTS[variant]
    if not photos:
        home, scale_end = (W / 2 - 120, H / 2 - 40), 1.0
    # floating photos (drawn before the logo; the logo always stays on top and readable)
    if variant == 2 and photos:
        targets = targets[:1] + targets[1:] if len(photos) > 2 else targets[:1]
        use = photos[2:3] if len(photos) > 2 else []
        tg = targets[1:2] if use else []
    else:
        use, tg = photos, targets
    for k, (path, (x, y, w, h, rot, depth)) in enumerate(zip(use, tg)):
        s = 1.75 + k * 0.55
        q = ease_out(seg(u, s, s + 0.6))
        if q <= 0:
            continue
        lay = framed(path, int(w), int(h))
        if variant == 0:
            px = lerp(W + 500, x, q)
            py = y
        elif variant == 1:
            px = x
            py = lerp(H + 400, y, q)
        else:
            px, py = lerp(x + 300, x, q), y
        px -= cam_drift * depth
        py += 6 * math.sin(u * 1.3 + k)
        composite(cv, lay, px, py, lerp(1.12, 1.0, q), min(1.0, q * 1.4), glow=0, rot=rot + 2 * (1 - q))
        if 0 < u - s < 0.25:
            add_light(cv, radial(px, py, 300), np.array([1.0, 0.85, 0.6]), 0.25 * (1 - (u - s) / 0.25))
    logo_stage(cv, u, i, inst, (home[0] - cam_drift * 0.5, home[1]), scale_end)
    # hand-off: light streak whips across before the next city beat
    q = seg(u, SLOT - CITY_BEAT - 0.45, SLOT - CITY_BEAT)
    if q > 0:
        add_light(cv, R.streak(q, angle=-0.35), GOLD_HI, 0.8)


def milestone(cv, t_local, i, inst, n_lit_before):
    """Full 6-second milestone (city beat + stage)."""
    if t_local < CITY_BEAT:
        city_beat(cv, t_local, i, n_lit_before)
        a = seg(t_local, CITY_BEAT - 0.25, CITY_BEAT)
        if a > 0:
            add_light(cv, radial(W / 2, H / 2, 900) * 0.6 + 0.4, np.array([1.0, 0.82, 0.55]), 0.45 * a)
    else:
        u = t_local - CITY_BEAT
        stage(cv, u, i, inst)
        add_light(cv, radial(W / 2, H / 2, 900) * 0.6 + 0.4, np.array([1.0, 0.82, 0.55]), 0.4 * math.exp(-u / 0.2))
