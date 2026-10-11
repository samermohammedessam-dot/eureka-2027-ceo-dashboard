"""EUREKA — Lighting the City of Excellence (90 s, 1920x1080).

A procedural night city with ten landmark towers. A torch-like flame flies from tower to
tower; each tower lights up and reveals the institution's authentic logo + its own photos.
Finale: the ten lights converge into a giant gold "10".

  python3 city_film.py world                 # build the city layers once (build/city/)
  python3 city_film.py stills 5 20 70 80     # PNG stills
  python3 city_film.py video                 # final MP4 (EUREKA_10_GAHAR_CELEBRATION.mp4)
Assets: EUREKA_ASSETS=<folder with manifest.json> (see README.md).
"""
import functools
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import city_timeline as C
import render as R
from render import (DEEP, GOLD, GOLD_HI, NAVY, WARM_WHITE, H, W, Confetti, Dust, Layer, add_light, bloom,
                    clamp01, composite, ease_back, ease_io, ease_out, firework, flash, inst_card, lerp,
                    radial, rays, seal_layer, seg, splat, text_layer, tonemap, vignette)

FPS = 30
HERE = os.path.dirname(os.path.abspath(__file__))
CITY = os.path.join(HERE, 'build', 'city')
OUT_NAME = 'EUREKA_10_GAHAR_CELEBRATION.mp4'

# ------------------------------------------------------------------ world geometry
HY = 2400                 # waterline row inside the layer images
LH_ = 2600                # layer height
MARGIN = 2800             # extra width either side so the widest shots never run out of city
LX = [900 + 420 * i for i in range(C.N)]      # landmark x (world)
START_X = 480                                  # the torch cauldron
CITY_CX = (LX[0] + LX[-1]) / 2
WORLD_W = LX[-1] + 700
DESIGNS = ['spire', 'dome', 'sail', 'stepped', 'twin', 'spire', 'dome', 'stepped', 'sail', 'twin']
HEIGHTS = [600, 520, 580, 560, 610, 540, 560, 620, 570, 590]
PAR_FAR = 0.55


def landmark_polys(design, h):
    """Polygons (relative to base centre, y up = negative) and the crown point."""
    if design == 'spire':
        return [[(-55, 0), (55, 0), (55, -0.78 * h), (12, -0.93 * h), (-12, -0.93 * h), (-55, -0.78 * h)],
                [(-3, -0.93 * h), (3, -0.93 * h), (1, -h), (-1, -h)]], (0, -h)
    if design == 'dome':
        dome = [(math.cos(a) * 62, -0.80 * h - math.sin(a) * 0.17 * h) for a in np.linspace(0, math.pi, 24)]
        return [[(-115, 0), (115, 0), (115, -0.42 * h), (-115, -0.42 * h)],
                [(-62, -0.42 * h), (62, -0.42 * h), (62, -0.80 * h)] + dome + [(-62, -0.80 * h)]], (0, -0.97 * h)
    if design == 'sail':
        curve = [(lerp(95, -60, s) + 70 * math.sin(s * math.pi) * (1 - s), -s * 0.95 * h) for s in np.linspace(0, 1, 30)]
        return [[(-70, 0)] + curve + [(-70, -0.95 * h)], [(-70, -0.95 * h), (-66, -h), (-62, -0.95 * h)]], (-66, -h)
    if design == 'stepped':
        return [[(-90, 0), (90, 0), (90, -0.52 * h), (-90, -0.52 * h)],
                [(-68, -0.52 * h), (68, -0.52 * h), (68, -0.76 * h), (-68, -0.76 * h)],
                [(-44, -0.76 * h), (44, -0.76 * h), (44, -0.92 * h), (-44, -0.92 * h)],
                [(-20, -0.92 * h), (20, -0.92 * h), (6, -h), (-6, -h)]], (0, -h)
    # twin towers with a sky bridge
    return [[(-95, 0), (-25, 0), (-25, -0.94 * h), (-60, -h), (-95, -0.94 * h)],
            [(25, 0), (95, 0), (95, -0.84 * h), (60, -0.9 * h), (25, -0.84 * h)],
            [(-25, -0.56 * h), (25, -0.56 * h), (25, -0.60 * h), (-25, -0.60 * h)]], (-60, -h)


def crown(i):
    _, (cx, cy) = landmark_polys(DESIGNS[i], HEIGHTS[i])
    return LX[i] + cx, HY + cy


def draw_windows(draw, mask_img, x0, y0, x1, y1, rng, p_lit, lit_col, cell=(9, 14), win=(4, 8)):
    m = np.asarray(mask_img)
    for y in range(int(y0) + 6, int(y1) - 4, cell[1]):
        for x in range(int(x0) + 5, int(x1) - 3, cell[0]):
            if 0 <= y < m.shape[0] and 0 <= x < m.shape[1] and m[y, x] and m[min(y + win[1], m.shape[0] - 1), x]:
                if rng.random() < p_lit:
                    a = rng.uniform(0.45, 1.0)
                    c = tuple(int(v * a) for v in lit_col)
                    draw.rectangle((x, y, x + win[0] - 1, y + win[1] - 1), fill=c + (255,))


def build_world():
    os.makedirs(CITY, exist_ok=True)
    rng = np.random.default_rng(42)
    # ---- far skyline (parallax), hazy blue silhouettes
    fw = int(WORLD_W * PAR_FAR + 2 * MARGIN)
    far = Image.new('RGBA', (fw, LH_), (0, 0, 0, 0))
    d = ImageDraw.Draw(far)
    x = 0
    while x < fw:
        w = int(rng.uniform(40, 130))
        h = int(rng.uniform(70, 300) * (1 + 0.5 * math.sin(x / 700)))
        col = (24, 36, 66, 255)
        d.rectangle((x, HY - h, x + w, HY), fill=col)
        if rng.random() < 0.15:
            d.line((x + w // 2, HY - h, x + w // 2, HY - h - rng.uniform(20, 60)), fill=col, width=3)
        for yy in range(HY - h + 8, HY - 4, 12):
            for xx in range(x + 5, x + w - 4, 9):
                if rng.random() < 0.09:
                    d.rectangle((xx, yy, xx + 2, yy + 4), fill=(150, 130, 100, 200))
        x += w + int(rng.uniform(-10, 15))
    # atmospheric haze towards the waterline
    a = np.asarray(far).astype(np.float32)
    yy = np.arange(LH_)[:, None]
    haze = np.clip((yy - (HY - 300)) / 300, 0, 1)
    a[..., :3] = a[..., :3] * (1 - 0.35 * haze[..., None]) + np.array([60, 70, 105]) * 0.35 * haze[..., None]
    Image.fromarray(a.astype(np.uint8), 'RGBA').save(os.path.join(CITY, 'far.png'))

    # ---- main city: generic buildings + ten landmarks (unlit) + cauldron
    mw = WORLD_W + 2 * MARGIN
    main = Image.new('RGBA', (mw, LH_), (0, 0, 0, 0))
    d = ImageDraw.Draw(main)
    x = 0
    keep_out = [(LX[i] + MARGIN - 150, LX[i] + MARGIN + 150) for i in range(C.N)]
    while x < mw:
        w = int(rng.uniform(50, 140))
        h = int(rng.uniform(110, 360))
        if any(a0 < x + w and x < a1 for a0, a1 in keep_out):
            h = int(h * 0.55)
        top = (14, 24, 46, 255)
        d.rectangle((x, HY - h, x + w, HY), fill=top)
        d.line((x, HY - h, x + w, HY - h), fill=(40, 54, 88, 255), width=2)
        if rng.random() < 0.2:
            d.line((x + w // 3, HY - h, x + w // 3, HY - h - rng.uniform(25, 70)), fill=top, width=3)
        x += w + int(rng.uniform(4, 22))
    # windows on generic buildings (vectorised pass)
    arr = np.asarray(main).copy()
    solid = arr[..., 3] > 0
    gy, gx = np.mgrid[HY - 380:HY - 6, 0:mw]
    win = ((gx % 9) < 4) & ((gy % 14) < 8)
    cellid = (gx // 9) * 1000 + (gy // 14)
    rnd = np.random.default_rng(7).random(cellid.max() + 1)[cellid]
    lit = win & (rnd < 0.13) & solid[HY - 380:HY - 6]
    bright = 0.4 + 0.6 * np.random.default_rng(9).random(cellid.max() + 1)[cellid]
    sub = arr[HY - 380:HY - 6]
    col = np.array([255, 196, 120], np.float32)
    sub[lit, :3] = (col[None, :] * bright[lit][:, None]).astype(np.uint8)
    arr[HY - 380:HY - 6] = sub
    main = Image.fromarray(arr, 'RGBA')
    d = ImageDraw.Draw(main)
    # cauldron: an obelisk on a stepped dais
    cx = START_X + MARGIN
    d.rectangle((cx - 90, HY - 40, cx + 90, HY), fill=(20, 30, 56, 255))
    d.rectangle((cx - 60, HY - 70, cx + 60, HY - 40), fill=(24, 36, 64, 255))
    d.polygon([(cx - 22, HY - 70), (cx + 22, HY - 70), (cx + 12, HY - 300), (cx - 12, HY - 300)], fill=(30, 44, 76, 255))
    d.polygon([(cx - 30, HY - 300), (cx + 30, HY - 300), (cx + 18, HY - 322), (cx - 18, HY - 322)], fill=(201, 162, 75, 255))
    # landmarks
    for i in range(C.N):
        polys, _ = landmark_polys(DESIGNS[i], HEIGHTS[i])
        bx = LX[i] + MARGIN
        for state in ('unlit', 'lit'):
            pad = 70
            x0 = int(min(p[0] for poly in polys for p in poly)) - pad
            x1 = int(max(p[0] for poly in polys for p in poly)) + pad
            y1 = int(min(p[1] for poly in polys for p in poly)) - pad
            sw, sh = x1 - x0, -y1 + 10
            spr = Image.new('RGBA', (sw, sh), (0, 0, 0, 0))
            m = Image.new('L', (sw, sh), 0)
            md = ImageDraw.Draw(m)
            for poly in polys:
                md.polygon([(p[0] - x0, p[1] + sh - 10) for p in poly], fill=255)
            ma = np.asarray(m, np.float32) / 255
            yy = np.linspace(0, 1, sh)[:, None]
            if state == 'unlit':
                base = np.array([16, 28, 56]) + np.array([14, 18, 30]) * (1 - yy[..., None])
            else:
                base = np.array([46, 44, 52]) + np.array([150, 118, 60]) * (1 - yy[..., None]) ** 2
            # vertical facade shading (rounded look)
            xx = np.linspace(-1, 1, sw)[None, :, None]
            shade = 0.75 + 0.35 * np.cos(xx * 1.4)
            rgb = np.clip(base * shade, 0, 255)
            spr = Image.fromarray(np.dstack([rgb, ma * 255]).astype(np.uint8), 'RGBA')
            sd = ImageDraw.Draw(spr)
            draw_windows(sd, m, 0, 0, sw, sh - 10, np.random.default_rng(100 + i),
                         0.10 if state == 'unlit' else 0.82,
                         (210, 160, 100) if state == 'unlit' else (255, 232, 170))
            if state == 'lit':
                # gold rim + crown glow, baked with a soft halo
                edge = m.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(3))
                halo = m.filter(ImageFilter.GaussianBlur(26))
                sa = np.asarray(spr).astype(np.float32)
                e = np.asarray(edge, np.float32)[..., None] / 255
                hl = np.asarray(halo, np.float32)[..., None] / 255 * (1 - ma[..., None])
                sa[..., :3] = sa[..., :3] * (1 - e) + np.array([255, 220, 140]) * e
                sa[..., 3:] = np.maximum(sa[..., 3:], e * 255)
                # halo outside the building: additive-looking warm glow
                glow_rgb = np.array([255, 196, 96], np.float32)
                ga = hl * 0.55
                sa[..., :3] = (sa[..., :3] * (sa[..., 3:] / 255) + glow_rgb * ga) / np.maximum(sa[..., 3:] / 255 + ga, 1e-3)
                sa[..., 3:] = np.clip(sa[..., 3:] + ga * 255, 0, 255)
                spr = Image.fromarray(sa.astype(np.uint8), 'RGBA')
                spr.save(os.path.join(CITY, f'lit{i}.png'))
                with open(os.path.join(CITY, f'lit{i}.txt'), 'w') as f:
                    f.write(f'{bx + x0} {HY - sh + 10}')
            else:
                main.alpha_composite(spr, (bx + x0, HY - sh + 10))
    main.save(os.path.join(CITY, 'main.png'))
    print('world built', main.size, far.size)


@functools.lru_cache(maxsize=None)
def world():
    far = Image.open(os.path.join(CITY, 'far.png')).convert('RGBA')
    main = Image.open(os.path.join(CITY, 'main.png')).convert('RGBA')
    lits = []
    for i in range(C.N):
        spr = Image.open(os.path.join(CITY, f'lit{i}.png')).convert('RGBA')
        x, y = (int(v) for v in open(os.path.join(CITY, f'lit{i}.txt')).read().split())
        lits.append((spr, spr.getchannel('A'), x, y))
    return far, main, lits


@functools.lru_cache(maxsize=None)
def sky():
    y = np.linspace(0, 1, H)[:, None, None]
    top = np.array([0.012, 0.022, 0.06])
    hor = np.array([0.10, 0.14, 0.27])
    s = top + (hor - top) * y ** 1.6
    rng = np.random.default_rng(3)
    img = np.broadcast_to(s, (H, W, 3)).astype(np.float32).copy()
    n = 900
    xs, ys = rng.integers(0, W, n), (rng.random(n) ** 1.6 * H * 0.75).astype(int)
    img[ys, xs] += rng.uniform(0.15, 0.7, n)[:, None] * np.array([0.9, 0.92, 1.0])
    return img


# ------------------------------------------------------------------ camera & torch
def smooth(a, b, x):
    return lerp(a, b, ease_io(clamp01(x)))


def camera(t):
    """(cx world, zoom, horizon row on screen)"""
    wide = (CITY_CX - 120, 0.40, 860)
    if t < C.S2[0]:
        return CITY_CX, lerp(0.36, 0.40, t / 10), 880
    if t < 14.6:
        return lerp(CITY_CX, wide[0], seg(t, 10, 14.6)), 0.40, lerp(880, 860, seg(t, 10, 13))
    if t < C.SLOT0:
        q = seg(t, 14.6, C.SLOT0 + 0.3)
        return smooth(wide[0], START_X + 700, q), smooth(0.40, 0.78, q), smooth(860, 830, q)
    if t < C.S4[0]:
        i = min(C.N - 1, int((t - C.SLOT0) // C.SLOT))
        u = t - C.SLOT_STARTS[i]
        x_prev = (START_X + 700) if i == 0 else LX[i - 1]
        z_prev = 0.78 if i == 0 else 1.1
        if u < C.ARRIVE:
            q = u / C.ARRIVE
            z = smooth(z_prev, 1.03, q) - 0.12 * math.sin(math.pi * q)  # aerial lift during the flight
            return smooth(x_prev, LX[i], q), z, 820
        return LX[i], lerp(1.03, 1.1, seg(u, C.ARRIVE, C.SLOT)), 820
    q = seg(t, C.S4[0], C.S4[0] + 3.4)
    if t < C.S4[0] + 3.4:
        return smooth(LX[-1], wide[0], q), smooth(1.1, 0.40, q) , smooth(820, 860, q)
    return wide[0], lerp(0.40, 0.43, seg(t, C.S4[0] + 3.4, 90)), 860


def to_screen(x, y, cam, par=1.0):
    cx, z, hs = cam
    return (x - cx * par) * z + W / 2, (y - HY) * z + hs


def bez(p0, p1, q):
    c = ((p0[0] + p1[0]) / 2, min(p0[1], p1[1]) - 260)
    return ((1 - q) ** 2 * p0[0] + 2 * (1 - q) * q * c[0] + q * q * p1[0],
            (1 - q) ** 2 * p0[1] + 2 * (1 - q) * q * c[1] + q * q * p1[1])


CAULDRON = (START_X, HY - 345)


def hover(i):
    x, y = crown(i)
    return x, y - 70


def torch_pos(t):
    if t < C.SLOT0:
        return CAULDRON
    if t >= C.S4[0]:
        return hover(C.N - 1)
    i = min(C.N - 1, int((t - C.SLOT0) // C.SLOT))
    u = t - C.SLOT_STARTS[i]
    p0 = CAULDRON if i == 0 else hover(i - 1)
    if u < C.ARRIVE:
        return bez(p0, hover(i), ease_io(u / C.ARRIVE))
    x, y = hover(i)
    return x, y + 6 * math.sin(t * 3)


def lit_level(i, t):
    if t < C.ARRIVALS[i]:
        return 0.0
    return ease_out(seg(t, C.ARRIVALS[i], C.ARRIVALS[i] + 0.45))


# ------------------------------------------------------------------ city render
def layer_view(img, cam, par, extra=None):
    cx, z, hs = cam
    ox = MARGIN
    vw, vh = W / z, H / z
    wx0 = cx * par + ox - vw / 2
    wy0 = HY - hs / z
    X0, Y0 = int(math.floor(wx0)) - 1, int(math.floor(wy0)) - 1
    X1, Y1 = int(math.ceil(wx0 + vw)) + 2, int(math.ceil(wy0 + vh)) + 2
    crop = img.crop((X0, Y0, X1, Y1))
    if extra:
        for spr, alpha, sx, sy, lvl in extra:
            if lvl <= 0.01:
                continue
            m = alpha if lvl >= 0.99 else alpha.point(lambda a, l=lvl: int(a * l))
            crop.paste(spr, (sx - X0, sy - Y0), m)
    return crop.resize((W, H), Image.BILINEAR, box=(wx0 - X0, wy0 - Y0, wx0 - X0 + vw, wy0 - Y0 + vh))


def over(cv, rgba_img, gain=1.0):
    a = np.asarray(rgba_img, np.float32) / 255
    al = a[..., 3:4]
    cv[:] = cv * (1 - al) + a[..., :3] * al * gain


def draw_city(cv, t, cam, bright=1.0, all_lit=None):
    far, main, lits = world()
    cv[:] = sky()
    cx, z, hs = cam
    hs = int(hs)
    # warm horizon glow behind the city
    add_light(cv, np.exp(-((R._ly - hs + 40) / 160) ** 2), np.array([0.9, 0.62, 0.3]), 0.22)
    over(cv, layer_view(far, cam, PAR_FAR), 0.9)
    lv = [(spr, a, x, y, (all_lit if all_lit is not None else lit_level(i, t))) for i, (spr, a, x, y) in enumerate(lits)]
    over(cv, layer_view(main, cam, 1.0, lv))
    # crown beacons and lit-tower beams
    for i in range(C.N):
        x, y = crown(i)
        sx, sy = to_screen(x, y, cam)
        if -200 < sx < W + 200:
            lvl = lv[i][4]
            pulse = 0.5 + 0.5 * math.sin(t * 2.4 + i)
            splat(cv, sx, sy, max(2, 5 * z), (0.35 + 0.25 * pulse) * (1 - lvl) + lvl * 1.2)
            if lvl > 0:
                beam = np.exp(-((R._lx - sx) / (16 + 10 * z)) ** 2) * np.clip((sy - R._ly) / 700, 0, 1) * np.exp(-np.clip(sy - R._ly, 0, None) / 900)
                add_light(cv, beam, GOLD_HI, 0.45 * lvl)
                add_light(cv, radial(sx, sy, 90 * z + 40), GOLD_HI, 0.5 * lvl)
    # water: rippled reflection below the horizon
    h = H - hs
    if h > 0:
        src = cv[max(0, hs - h):hs][::-1]
        if src.shape[0] < h:
            src = np.concatenate([src, np.repeat(src[-1:], h - src.shape[0], 0)])
        r = np.arange(h)
        dx = (np.sin(r * 0.45 + t * 2.6) * (1.5 + r * 0.03)).astype(int)
        idx = (np.arange(W)[None, :] + dx[:, None]) % W
        refl = np.take_along_axis(src, idx[..., None].repeat(3, 2), axis=1)
        fade = (0.42 * np.exp(-r / (h * 0.9)))[:, None, None]
        water = np.array([0.02, 0.035, 0.08]) * (1 + r / h)[:, None, None]
        cv[hs:] = refl * fade + water
        cv[hs:hs + 2] += GOLD_HI * 0.08
    cv *= bright


def golden_paths(cv, t, cam, upto, gain=0.55, flow=False):
    """Glowing arcs connecting the cauldron and every tower reached so far."""
    if upto < 0:
        return
    im = Image.new('L', (R.LW, R.LH), 0)
    d = ImageDraw.Draw(im)
    pts_all = []
    prev = CAULDRON
    for i in range(upto + 1):
        pts = [to_screen(*bez(prev, hover(i), q), cam) for q in np.linspace(0, 1, 28)]
        d.line([(x / 4, y / 4) for x, y in pts], fill=200, width=1)
        pts_all.append(pts)
        prev = hover(i)
    m = np.asarray(im.filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
    add_light(cv, m, GOLD_HI, gain)
    if flow:  # sparks travelling along the paths
        for k, pts in enumerate(pts_all):
            for j in range(3):
                q = ((t * 0.5 + j / 3 + k * 0.13) % 1) * (len(pts) - 1)
                a, b = pts[int(q)], pts[min(len(pts) - 1, int(q) + 1)]
                f = q - int(q)
                splat(cv, lerp(a[0], b[0], f), lerp(a[1], b[1], f), 3, 0.9)


TRAIL_N = 26


def draw_torch(cv, t, cam, scale=1.0, intensity=1.0):
    if intensity <= 0.01:
        return
    z = cam[1]
    for k in range(TRAIL_N, 0, -1):  # trail
        tt = t - k * 0.022
        sx, sy = to_screen(*torch_pos(tt), cam)
        f = (1 - k / TRAIL_N)
        splat(cv, sx, sy, max(1, 6 * f * z), 0.55 * f * f * intensity)
    sx, sy = to_screen(*torch_pos(t), cam)
    s = scale * (0.7 + 0.5 * z)
    add_light(cv, radial(sx, sy, 160 * s), np.array([1.0, 0.7, 0.32]), 0.55 * intensity)
    for j in range(7):  # flame tongues
        fl = math.sin(t * 17 + j * 1.7) * 0.5 + math.sin(t * 29 + j) * 0.3
        splat(cv, sx + fl * 5 * s, sy - j * 7 * s, max(1, (11 - j * 1.3) * s), (0.9 - j * 0.1) * intensity)
    splat(cv, sx, sy, max(2, 7 * s), 1.4 * intensity)
    g = np.random.default_rng(int(t * 30))
    for _ in range(6):  # sparks shed by the flame
        a = g.uniform(0, 1)
        splat(cv, sx + g.normal(0, 14) * s, sy - a * 60 * s, 1, 0.6 * (1 - a) * intensity)


# ------------------------------------------------------------------ overlays
DUST = Dust(160, 31, rise=25)
SPARK = Dust(120, 32, rise=90, sizes=(1, 3))
CONF_RAIN = Confetti(240, 41, C.HIT - 0.2, 'rain')
CONF_CANNON = Confetti(200, 42, C.HIT, 'cannon')
CONF_RAIN2 = Confetti(160, 43, C.HIT + 3.0, 'rain')


def eureka_logo():
    return R.eureka_layer(520, 330)


def scene_beginning(cv, t):
    cam = camera(t)
    draw_city(cv, t, cam, bright=0.25 + 0.75 * ease_io(seg(t, 0.2, 5.0)))
    cv *= seg(t, 0, 1.2)
    DUST.draw(cv, t, seg(t, 0.5, 3))
    p = seg(t, 2.2, 4.0)
    fo = 1 - seg(t, 9.2, 9.95)  # titles dissolve into the spark scene
    composite(cv, eureka_logo(), W / 2, 250, lerp(0.9, 1.0, ease_out(p)), ease_io(p) * fo, glow=0.5 * p)
    q1 = seg(t, 4.4, 5.6)
    composite(cv, text_layer('EUREKA', 'cinzel', 118, 700, 34, 'gold', 14), W / 2, 495 + 16 * (1 - ease_out(q1)),
              1.0, ease_io(q1) * fo, glow=0.9, shine=seg(t, 5.6, 7.0) if 5.6 < t < 7.0 else None)
    q2 = seg(t, 5.6, 6.8)
    composite(cv, text_layer('Lighting the City of Excellence', 'playfair', 60, 500, 0, 'ivory', 8), W / 2,
              595 + 12 * (1 - ease_out(q2)), 1.0, ease_io(q2) * fo, glow=0.4)
    lw = int(560 * ease_out(seg(t, 5.4, 6.6)) * fo)
    if lw > 2:
        cv[548:550, W // 2 - lw // 2:W // 2 + lw // 2] += GOLD_HI * 0.9
    return cam


def scene_spark(cv, t):
    cam = camera(t)
    draw_city(cv, t, cam)
    DUST.draw(cv, t, 0.8)
    # the ignition
    ig = seg(t, C.IGNITE, C.IGNITE + 0.9)
    sx, sy = to_screen(*CAULDRON, cam)
    if t >= C.IGNITE:
        u = t - C.IGNITE
        flash(cv, 0.9 * math.exp(-u / 0.25), sx, sy, 500)
        add_light(cv, rays(sx, sy, t, n=14, reach=500), GOLD_HI, 0.5 * math.exp(-u / 0.8) + 0.08)
        draw_torch(cv, t, cam, scale=lerp(0.3, 1.2, ease_out(ig)), intensity=ease_out(ig))
    # text
    q = seg(t, 11.2, 12.2)
    o = q * (1 - seg(t, 16.6, 17.4))
    composite(cv, text_layer('Every Great Achievement Begins With a Spark', 'playfair', 66, 500, 0, 'gold', 10),
              W / 2, 190 + 14 * (1 - ease_out(q)), 1.0, ease_io(o), glow=0.6)
    return cam


def slot_overlays(ov, t, i, inst):
    u = t - C.SLOT_STARTS[i]
    a = C.ARRIVE
    photos = inst['photos'][:3]
    # left: logo card + markers
    pcx, pcy = 470, 430
    q = seg(u, a + 0.1, a + 0.55)
    card = inst_card(inst, 620, 350)
    sc = 0.6 + 0.4 * ease_back(q)
    composite(ov, card, pcx, pcy, sc, seg(u, a + 0.1, a + 0.25), glow=0.4 + 0.8 * math.exp(-(u - a) / 0.4))
    seal = seal_layer(104)
    qs = seg(u, a + 0.35, a + 0.75)
    if seal:
        composite(ov, seal, pcx, pcy - 175 * sc - 64, 0.6 + 0.4 * ease_back(qs), qs, glow=0.5)
    qn = seg(u, a + 0.45, a + 0.9)
    y = pcy + 175 * sc + 58
    if inst.get('branch'):
        composite(ov, text_layer(inst['branch'], 'playfair', 52, 600, 0, 'gold', 8), pcx, y + 12 * (1 - ease_out(qn)),
                  1.0, ease_io(qn), glow=0.6)
        y += 50
    else:
        for ln in R.fit_text_lines(inst['name'], 'cinzel', 46, 700, 640, 3, 'gold', 8):
            composite(ov, ln, pcx, y + 12 * (1 - ease_out(qn)), 1.0, ease_io(qn), glow=0.6)
            y += ln.h * 0.6
    qm = seg(u, a + 0.6, a + 1.0)
    composite(ov, text_layer(f'GAHAR ACCREDITATION  ·  MILESTONE {i + 1:02d}', 'mont', 22, 600, 5, 'gold', 4),
              pcx, y + 22, 1.0, ease_io(qm), glow=0.4)
    # right: 2-3 photos from this institution's own folder
    ax, ay, aw, ah = 1080, 200, 780, 540
    if photos:
        n = len(photos)
        starts = {1: [1.6], 2: [1.6, 2.7], 3: [1.6, 2.35, 3.1]}[n]
        v = i % 3
        if v == 0:
            R.single_gallery(ov, u, photos, starts, ax, ay, aw, ah, i)
        elif v == 1:
            R.stack_gallery(ov, u, photos, starts, ax, ay, aw, ah, i)
        else:
            R.panel_gallery(ov, u, photos, starts, ax, ay, aw, ah, i, 1)
    elif seal:  # no photos supplied: the accreditation seal takes the stage
        qq = seg(u, a + 0.5, a + 1.0)
        composite(ov, seal_layer(300), ax + aw / 2, ay + ah / 2, 0.6 + 0.4 * ease_back(qq), qq, glow=0.7)


def scene_milestones(cv, t):
    i = min(C.N - 1, int((t - C.SLOT0) // C.SLOT))
    u = t - C.SLOT_STARTS[i]
    cam = camera(t)
    show = seg(u, C.ARRIVE, C.ARRIVE + 0.4) * (1 - seg(u, C.SLOT - 0.5, C.SLOT - 0.05))
    draw_city(cv, t, cam, bright=1 - 0.28 * show)
    golden_paths(cv, t, cam, i if u >= C.ARRIVE else i - 1)
    if u < C.ARRIVE:  # path being drawn by the flame
        pts = [to_screen(*bez(CAULDRON if i == 0 else hover(i - 1), hover(i), q), cam)
               for q in np.linspace(0, ease_io(u / C.ARRIVE), 20)]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            splat(cv, x1, y1, 2, 0.5)
    DUST.draw(cv, t, 0.6)
    draw_torch(cv, t, cam, intensity=1.0 - 0.45 * show)
    if u >= C.ARRIVE:  # arrival: the tower lights up
        sx, sy = to_screen(*crown(i), cam)
        du = u - C.ARRIVE
        flash(cv, 0.8 * math.exp(-du / 0.14), sx, sy, 600)
        add_light(cv, rays(sx, sy, t, n=16, reach=650), GOLD_HI, 0.55 * math.exp(-du / 0.6))
        firework(cv, t, C.ARRIVALS[i], sx, sy - 40, 100 + i, n=40, life=1.2, speed=320)
    if show > 0.01:
        ov = cv.copy()
        slot_overlays(ov, t, i, R.manifest()['institutions'][i])
        cv[:] = cv * (1 - show) + ov * show
    return cam


S4_TEXTS = [('Every Light Tells a Story', C.S4[0] + 1.2, C.S4[0] + 6.4),
            ('Together, We Made It Possible', C.S4[0] + 6.8, C.DROP - 0.15)]


@functools.lru_cache(maxsize=None)
def montage_pool():
    m = R.manifest()
    pool = list(m['team_photos'])
    for inst in m['institutions']:
        pool += [p for p in inst['photos'] if p not in pool]
    pool += [p for p in m.get('extra_photos', []) if p not in pool]
    return pool


def floating_photos(cv, t):
    """Two rows of framed photos drifting across the night sky (parallax)."""
    pool = montage_pool()
    t0 = C.S4[0] + 2.0
    if t < t0:
        return
    o = seg(t, t0, t0 + 0.8) * (1 - seg(t, C.DROP - 0.4, C.DROP))
    for row, (y, ph, speed, gap, off) in enumerate([(205, 230, 120, 40, 0), (470, 190, 75, 34, 7)]):
        pw = int(ph * 1.45)
        step = pw + gap
        shift = (t - t0) * speed + W * 0.55  # rows enter already partly filled, drifting right -> left
        k_lo = max(0, int((shift - W - 20 - pw) // step))
        for k in range(k_lo, int(shift // step) + 2):
            xx = int(W + 20 + k * step - shift)
            if -pw - 20 < xx < W + 20:
                path = pool[(k + off) % len(pool)]
                arr = R.photo_crop(path, pw, ph, 0.5, seed=k, zoom=0.0)
                R.draw_photo(cv, arr, xx, y - ph // 2, o, border=3, shadow=0.6)


def scene_alive(cv, t):
    cam = camera(t)
    draw_city(cv, t, cam, all_lit=1.0)
    golden_paths(cv, t, cam, C.N - 1, gain=0.75, flow=True)
    DUST.draw(cv, t, 0.9)
    SPARK.draw(cv, t, 0.5)
    pull = seg(t, C.S4[0], C.S4[0] + 0.6)
    flash(cv, 0.5 * math.exp(-(t - C.MUSIC_S4) / 0.2) * (t > C.MUSIC_S4))
    draw_torch(cv, t, cam, intensity=1 - pull)
    floating_photos(cv, t)
    for text, a, b in S4_TEXTS:
        if a - 0.05 < t < b:
            q = seg(t, a, a + 0.6)
            o = q * (1 - seg(t, b - 0.4, b))
            cv[620:760] *= 1 - 0.45 * o
            composite(cv, text_layer(text.upper(), 'cinzel', 70, 700, 6, 'gold', 12), W / 2, 690,
                      lerp(1.08, 1.0, ease_out(q)), o, glow=1.0, shine=seg(t, a + 0.7, a + 2.0) if a + 0.7 < t < a + 2 else None)
    return cam


def ring_positions():
    pos = []
    for side in (-1, 1):
        for k in range(5):
            pos.append((W / 2 + side * (690 + 70 * math.cos((k - 2) / 2 * 1.2)), 140 + k * 200))
    order = [0, 5, 1, 6, 2, 7, 3, 8, 4, 9]
    return [pos[o] for o in order]


TEN_C = (W / 2, 360)


def scene_grand(cv, t):
    cam = camera(t)
    dim = 0.55 if t < C.HIT else 0.38
    draw_city(cv, t, cam, bright=dim, all_lit=1.0)
    golden_paths(cv, t, cam, C.N - 1, gain=0.35)
    if t < C.HIT:  # energy flows from the ten towers to the centre
        p = seg(t, C.DROP, C.HIT)
        for i in range(C.N):
            sx, sy = to_screen(*crown(i), cam)
            for j in range(14):
                q = (p * 1.6 - j * 0.045)
                if 0 < q < 1:
                    e = q ** 1.6
                    c = ((sx + TEN_C[0]) / 2, min(sy, TEN_C[1]) - 220)
                    x = (1 - e) ** 2 * sx + 2 * (1 - e) * e * c[0] + e * e * TEN_C[0]
                    y = (1 - e) ** 2 * sy + 2 * (1 - e) * e * c[1] + e * e * TEN_C[1]
                    splat(cv, x, y, 3 if j == 0 else 2, 1.0 - j * 0.06)
            splat(cv, sx, sy, 6, 0.8 * (1 - p))
        splat(cv, *TEN_C, 4 + 26 * p ** 3, 0.3 + 1.5 * p ** 2)
        add_light(cv, radial(*TEN_C, 60 + 300 * p ** 2), GOLD_HI, 0.6 * p ** 2)
        return cam
    u = t - C.HIT
    beat = (u % C.BEAT) / C.BEAT
    add_light(cv, rays(*TEN_C, t, n=22, speed=0.05, sharp=5, reach=1100), GOLD_HI,
              0.38 + 0.18 * math.exp(-beat * 4) + 0.6 * math.exp(-u / 0.5))
    add_light(cv, radial(*TEN_C, 520), GOLD, 0.3)
    rp = ease_out(seg(u, 0, 0.9))
    if 0 < rp < 1:
        dd = np.sqrt((R._lx - TEN_C[0]) ** 2 + (R._ly - TEN_C[1]) ** 2)
        add_light(cv, np.exp(-((dd - rp * 1500) / 50) ** 2), WARM_WHITE, 1.1 * (1 - rp))
    cv[650:900] *= 0.55 + 0.45 * np.abs(np.linspace(-1, 1, 250))[:, None, None] ** 2
    DUST.draw(cv, t, 1.0)
    for (fx, fy, ft, fs) in [(470, 250, C.HIT + 0.2, 1), (1450, 230, C.HIT + 0.45, 2), (960, 110, C.HIT + 2.2, 3),
                             (330, 520, C.HIT + 4.4, 4), (1590, 520, C.HIT + 6.0, 5)]:
        firework(cv, t, ft, fx, fy, fs, n=60)
    CONF_RAIN.draw(cv, t)
    CONF_CANNON.draw(cv, t)
    CONF_RAIN2.draw(cv, t)
    ten = text_layer('10', 'cinzel', 640, 900, 0, 'gold', 30)
    q = seg(u, 0, 0.55)
    shine = None
    for a in (0.7, 3.2, 5.7):
        if a < u < a + 0.9:
            shine = seg(u, a, a + 0.9)
    composite(cv, ten, *TEN_C, lerp(1.6, 1.0, ease_out(q)) * (1 + 0.015 * math.exp(-beat * 5) * (u > 0.6)),
              seg(u, 0, 0.12), glow=0.8 + 0.4 * math.exp(-beat * 4), shine=shine)
    q1, q2 = seg(u, 0.8, 1.3), seg(u, 1.05, 1.55)
    composite(cv, text_layer('GAHAR ACCREDITATION', 'cinzel', 70, 700, 10, 'gold', 12), W / 2,
              720 + 20 * (1 - ease_out(q1)), 1.0, ease_io(q1), glow=0.9)
    composite(cv, text_layer('ACHIEVEMENTS', 'cinzel', 70, 700, 22, 'gold', 12), W / 2,
              812 + 20 * (1 - ease_out(q2)), 1.0, ease_io(q2), glow=0.9)
    lw = int(560 * ease_out(seg(u, 1.2, 2.0)))
    if lw > 2:
        cv[870:872, W // 2 - lw // 2:W // 2 + lw // 2] += GOLD_HI
    seal = seal_layer(150)
    if seal and u > 2.4:
        qs = seg(u, 2.4, 2.8)
        composite(cv, seal, W / 2, 972, 0.6 + 0.4 * ease_back(qs), qs, glow=0.5 + 0.8 * math.exp(-(u - 2.4) / 0.3))
    for k, ((x, y), inst) in enumerate(zip(ring_positions(), R.manifest()['institutions'])):
        s = 1.0 + k * 0.45
        if u < s:
            continue
        q = seg(u, s, s + 0.32)
        y += 6 * math.sin(t * 1.6 + k)
        composite(cv, inst_card(inst, 300, 168, pad_frac=0.08, radius=16, frame=3), x, y,
                  0.5 + 0.5 * ease_back(q), seg(u, s, s + 0.12), glow=0.3 + 0.9 * math.exp(-(u - s) / 0.25))
        if inst.get('branch'):
            composite(cv, R.branch_tag(inst['branch']), x, y + 84, 1.0, seg(u, s + 0.1, s + 0.35), glow=0)
        if u - s < 0.2:
            splat(cv, x, y - 95, 10, 0.8 * (1 - (u - s) / 0.2))
    flash(cv, 1.8 * math.exp(-u / 0.16))
    flash(cv, 0.9 * seg(t, C.FINALE - 0.3, C.FINALE) ** 2)
    return cam


def scene_finale(cv, t):
    u = t - C.FINALE
    cam = camera(t)
    draw_city(cv, t, cam, bright=0.55, all_lit=1.0)
    golden_paths(cv, t, cam, C.N - 1, gain=0.4, flow=True)
    add_light(cv, rays(W / 2, 330, t, n=16, speed=0.04, reach=900), GOLD_HI, 0.25)
    DUST.draw(cv, t, 1.0)
    CONF_RAIN2.draw(cv, t, 1 - seg(u, 2.0, 4.0))
    q = seg(u, 0.0, 1.0)
    composite(cv, R.eureka_layer(640, 420), W / 2, 330, lerp(0.92, 1.0, ease_out(q)), ease_io(seg(u, 0, 0.4)), glow=0.55)
    q2 = seg(u, 0.8, 1.5)
    cv[640:790] *= 1 - 0.4 * q2
    composite(cv, text_layer('TOGETHER, WE RAISE THE STANDARD.', 'cinzel', 72, 700, 6, 'gold', 12),
              W / 2, 715 + 14 * (1 - ease_out(q2)), 1.0, ease_io(q2), glow=1.0,
              shine=seg(u, 1.8, 2.8) if 1.8 < u < 2.8 else None)
    flash(cv, 1.2 * math.exp(-u / 0.2))
    cv *= 1 - seg(t, 89.0, 89.95)
    return cam


def frame(t):
    cv = np.zeros((H, W, 3), np.float32)
    if t < C.S2[0]:
        scene_beginning(cv, t)
    elif t < C.SLOT0:
        scene_spark(cv, t)
    elif t < C.S4[0]:
        scene_milestones(cv, t)
    elif t < C.DROP:
        scene_alive(cv, t)
    elif t < C.FINALE:
        scene_grand(cv, t)
    else:
        scene_finale(cv, t)
    bloom(cv, 0.3, 0.8)
    cv *= vignette(0.35)
    return tonemap(cv)


# ------------------------------------------------------------------ output
def render_chunk(args):
    a, b, path = args
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
           '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '12',
           '-pix_fmt', 'yuv420p', path]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(a, b):
        pr.stdin.write(frame(f / FPS).tobytes())
    pr.stdin.close()
    pr.wait()
    return path


def render_video(out, workers=4, chunk=90):
    build = os.path.join(HERE, 'build')
    cdir = os.path.join(build, 'city_chunks')
    os.makedirs(cdir, exist_ok=True)
    nf = int(C.DURATION * FPS)
    jobs = [(a, min(nf, a + chunk), os.path.join(cdir, f'c{a:05d}.mp4')) for a in range(0, nf, chunk)]
    with Pool(workers) as p:
        for k, _ in enumerate(p.imap(render_chunk, jobs)):
            print(f'chunk {k + 1}/{len(jobs)}', flush=True)
    lst = os.path.join(cdir, 'list.txt')
    with open(lst, 'w') as f:
        f.writelines(f"file '{os.path.abspath(j[2])}'\n" for j in jobs)
    master = os.path.join(build, 'city_master.mp4')
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst,
                    '-c', 'copy', master], check=True)
    score = os.path.join(build, 'city_score.wav')
    if not os.path.exists(score):
        subprocess.run([sys.executable, os.path.join(HERE, 'music_city.py'), score], check=True)
    base = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', master, '-i', score, '-map', '0:v', '-map', '1:a',
            '-c:v', 'libx264', '-preset', 'slow', '-profile:v', 'high', '-b:v', '8300k', '-maxrate', '14M',
            '-bufsize', '20M', '-pix_fmt', 'yuv420p', '-g', '60', '-r', str(FPS), '-t', str(C.DURATION)]
    plog = os.path.join(build, 'x264city')
    subprocess.run(base + ['-pass', '1', '-passlogfile', plog, '-an', '-f', 'mp4', '/dev/null'], check=True)
    subprocess.run(base + ['-pass', '2', '-passlogfile', plog, '-c:a', 'aac', '-b:a', '256k',
                           '-movflags', '+faststart', out], check=True)
    print('wrote', out)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'stills'
    if cmd == 'world':
        build_world()
    elif cmd == 'stills':
        d = os.path.join(HERE, 'build', 'city_stills')
        os.makedirs(d, exist_ok=True)
        for s in sys.argv[2:]:
            Image.fromarray(frame(float(s))).save(os.path.join(d, f't{float(s):05.2f}.png'))
            print('still', s, flush=True)
    elif cmd == 'video':
        render_video(os.path.join(HERE, OUT_NAME))
