"""Eureka x GAHAR celebration film — procedural renderer (numpy + Pillow -> FFmpeg).

Usage:
  python3 render.py stills 5 15 30 70 80 88     # PNG stills to build/stills
  python3 render.py video [--out build/final.mp4]   # full 90 s Full-HD MP4
Assets are read from assets/manifest.json (see README.md).
"""
import functools
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

import timeline as T

W, H, FPS = T.W, T.H, T.FPS
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.environ.get('EUREKA_ASSETS', os.path.join(HERE, 'assets'))
BUILD = os.path.join(HERE, 'build')

# Eureka brand (from the CEO dashboard theme): navy #1a2b4c, gold #c9a24b
NAVY = np.array([0x1a, 0x2b, 0x4c], np.float32) / 255
DEEP = np.array([0x04, 0x08, 0x16], np.float32) / 255
GOLD = np.array([0xc9, 0xa2, 0x4b], np.float32) / 255
GOLD_HI = np.array([1.0, 0.86, 0.55], np.float32)
WARM_WHITE = np.array([1.0, 0.95, 0.85], np.float32)
IVORY = np.array([0.98, 0.95, 0.88], np.float32)


# ------------------------------------------------------------------ easing
def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def seg(t, a, b):
    return clamp01((t - a) / (b - a))


def ease_out(x):
    return 1 - (1 - x) ** 3


def ease_io(x):
    return x * x * (3 - 2 * x)


def ease_back(x, s=1.7):
    x -= 1
    return 1 + x * x * ((s + 1) * x + s)


def window(t, a, b, c, d):
    return seg(t, a, b) * (1 - seg(t, c, d))


def lerp(a, b, x):
    return a + (b - a) * x


# ------------------------------------------------------------------ assets
def load_manifest():
    with open(os.path.join(ASSETS, 'manifest.json')) as f:
        m = json.load(f)
    p = lambda r: os.path.join(ASSETS, r)
    m['eureka_logo'] = p(m['eureka_logo'])
    m['team_photos'] = [p(x) for x in m.get('team_photos', [])]
    for inst in m['institutions']:
        inst['logo'] = p(inst['logo'])
        inst['photos'] = [p(x) for x in inst.get('photos', [])]
    return m


M = None


def manifest():
    global M
    if M is None:
        M = load_manifest()
    return M


@functools.lru_cache(maxsize=256)
def photo(path, maxside=2400):
    im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    s = maxside / max(im.size)
    if s < 1:
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    return im


def photo_pool():
    """Team photos first, then institution photos – used by the montages."""
    m = manifest()
    pool = list(m['team_photos'])
    extra = [p for inst in m['institutions'] for p in inst['photos']]
    return pool + [p for p in extra if p not in pool]


@functools.lru_cache(maxsize=64)
def logo_image(path):
    """Load a logo and trim its empty margins (transparent or flat background)."""
    im = Image.open(path)
    im = ImageOps.exif_transpose(im).convert('RGBA')
    a = np.asarray(im)
    if a[..., 3].min() < 250:
        mask = a[..., 3] > 12
        bg = None
    else:
        corners = np.concatenate([a[:4, :4, :3].reshape(-1, 3), a[:4, -4:, :3].reshape(-1, 3),
                                  a[-4:, :4, :3].reshape(-1, 3), a[-4:, -4:, :3].reshape(-1, 3)])
        bg = np.median(corners, axis=0)
        mask = np.abs(a[..., :3].astype(int) - bg).max(axis=2) > 24
    ys, xs = np.nonzero(mask)
    if len(xs):
        pad = 4
        im = im.crop((max(0, xs.min() - pad), max(0, ys.min() - pad),
                      min(im.width, xs.max() + pad + 1), min(im.height, ys.max() + pad + 1)))
    return im, (None if bg is None else tuple(int(c) for c in bg))


# ------------------------------------------------------------------ text
FONT_FILES = {'cinzel': 'Cinzel.ttf', 'playfair': 'PlayfairItalic.ttf', 'mont': 'Montserrat.ttf'}


@functools.lru_cache(maxsize=None)
def font(name, size, weight=None):
    f = ImageFont.truetype(os.path.join(HERE, 'fonts', FONT_FILES[name]), size)
    if weight:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


def gold_ramp(h, style):
    y = np.linspace(0, 1, h)[:, None]
    if style == 'gold':
        stops = [(0, (1.00, 0.95, 0.76)), (0.38, (0.93, 0.78, 0.42)), (0.52, (0.74, 0.55, 0.20)),
                 (0.66, (0.86, 0.68, 0.32)), (1, (1.0, 0.90, 0.62))]
    elif style == 'ivory':
        stops = [(0, (1, 0.98, 0.94)), (1, (0.95, 0.90, 0.80))]
    else:
        stops = [(0, (1, 1, 1)), (1, (1, 1, 1))]
    xs = [s[0] for s in stops]
    return np.concatenate([np.interp(y, xs, [s[1][c] for s in stops]) for c in range(3)], axis=1)


class Layer:
    """RGBA sprite + optional additive glow mask, composited at a centre point."""

    def __init__(self, rgba, glow=None):
        self.rgba = rgba
        self.glow = glow
        self.w, self.h = rgba.size


@functools.lru_cache(maxsize=None)
def text_layer(text, fname='cinzel', size=60, weight=None, tracking=0, style='gold', glow=10):
    f = font(fname, size, weight)
    asc, desc = f.getmetrics()
    if tracking:
        widths = [f.getlength(c) for c in text]
        total = sum(widths) + tracking * (len(text) - 1)
    else:
        total = f.getlength(text)
    pad = int(size * 0.25) + glow * 3
    w, h = int(total) + 2 * pad, asc + desc + 2 * pad
    mask = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(mask)
    if tracking:
        x = pad
        for c, cw in zip(text, widths):
            d.text((x, pad), c, font=f, fill=255)
            x += cw + tracking
    else:
        d.text((pad, pad), text, font=f, fill=255)
    ramp = np.zeros((h, 3), np.float32)
    ramp[pad:pad + asc + desc] = gold_ramp(asc + desc, style)
    ramp[:pad] = ramp[pad]
    ramp[pad + asc + desc:] = ramp[pad + asc + desc - 1]
    rgb = (np.broadcast_to(ramp[:, None, :], (h, w, 3)) * 255).astype(np.uint8)
    rgba = Image.fromarray(np.dstack([rgb, np.asarray(mask)]), 'RGBA')
    g = mask.filter(ImageFilter.GaussianBlur(glow)) if glow else None
    return Layer(rgba, g)


def fit_text_lines(text, fname, size, weight, maxw, tracking=0, style='gold', glow=8, min_size=30):
    """Shrink, then wrap to two lines if needed, so long institution names stay readable."""
    s = size
    while s > min_size and text_layer(text, fname, s, weight, tracking, style, glow).w > maxw:
        s -= 2
    if text_layer(text, fname, s, weight, tracking, style, glow).w <= maxw:
        return [text_layer(text, fname, s, weight, tracking, style, glow)]
    words = text.split()
    best = None
    for k in range(1, len(words)):
        a, b = ' '.join(words[:k]), ' '.join(words[k:])
        mw = max(text_layer(a, fname, size, weight, tracking, style, glow).w,
                 text_layer(b, fname, size, weight, tracking, style, glow).w)
        if best is None or mw < best[0]:
            best = (mw, a, b)
    s = size
    while s > min_size and max(text_layer(x, fname, s, weight, tracking, style, glow).w for x in best[1:]) > maxw:
        s -= 2
    return [text_layer(x, fname, s, weight, tracking, style, glow) for x in best[1:]]


# ------------------------------------------------------------------ compositing
def region(x0, y0, w, h):
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if X0 >= X1 or Y0 >= Y1:
        return None
    return (slice(Y0, Y1), slice(X0, X1)), (slice(Y0 - y0, Y1 - y0), slice(X0 - x0, X1 - x0))


def composite(cv, layer, cx, cy, scale=1.0, opacity=1.0, glow=1.0, glow_color=GOLD_HI, shine=None, rot=0.0):
    if opacity <= 0.002 or scale <= 0.01:
        return
    img, g = layer.rgba, layer.glow
    if abs(scale - 1) > 1e-3:
        size = (max(1, round(layer.w * scale)), max(1, round(layer.h * scale)))
        rs = Image.LANCZOS if scale < 1 else Image.BICUBIC
        img = img.resize(size, rs)
        if g is not None:
            g = g.resize(size, Image.BILINEAR)
    if rot:
        img = img.rotate(rot, Image.BICUBIC, expand=True)
        if g is not None:
            g = g.rotate(rot, Image.BICUBIC, expand=True)
    w, h = img.size
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    r = region(x0, y0, w, h)
    if r is None:
        return
    dst, src = r
    arr = np.asarray(img, np.float32)[src] / 255
    a = arr[..., 3:4] * opacity
    rgb = arr[..., :3]
    if shine is not None:  # moving diagonal highlight across the glyphs
        hh, ww = a.shape[:2]
        xx = np.arange(ww)[None, :] + np.arange(hh)[:, None] * 0.5
        band = np.exp(-((xx - shine * (ww + hh)) / (0.06 * ww + 20)) ** 2)[..., None]
        rgb = np.minimum(1.6, rgb + band * 0.9)
    if g is not None and glow > 0:
        ga = np.asarray(g, np.float32)[src][..., None] / 255
        cv[dst] += ga * glow_color * (glow * opacity * 0.9)
    cv[dst] = cv[dst] * (1 - a) + rgb * a


def add_light(cv, lowres, color, gain=1.0):
    """Upsample a quarter-res light map and add it."""
    if gain <= 0.002:
        return
    up = np.asarray(Image.fromarray(lowres.astype(np.float32), 'F').resize((W, H), Image.BILINEAR))
    cv += up[..., None] * (color * gain)


LW, LH = W // 4, H // 4
_ly, _lx = np.mgrid[0:LH, 0:LW].astype(np.float32) * 4


def radial(cx, cy, radius):
    d2 = ((_lx - cx) ** 2 + (_ly - cy) ** 2) / (radius ** 2)
    return np.exp(-d2)


def rays(cx, cy, t, n=18, speed=0.12, sharp=6, reach=900):
    th = np.arctan2(_ly - cy, _lx - cx)
    r = np.sqrt((_lx - cx) ** 2 + (_ly - cy) ** 2)
    a = (0.5 + 0.5 * np.cos(n * th + t * speed * 2 * np.pi)) ** sharp
    b = (0.5 + 0.5 * np.cos(int(n * 0.6) * th - t * speed * 1.3 * 2 * np.pi + 1.0)) ** sharp
    return (0.65 * a + 0.45 * b) * np.exp(-r / reach) * np.clip(r / 60, 0, 1)


def spotlight(ox, oy, ang, width=0.13, reach=1500):
    dx, dy = _lx - ox, _ly - oy
    th = np.arctan2(dy, dx)
    d = np.angle(np.exp(1j * (th - ang)))
    r = np.sqrt(dx * dx + dy * dy)
    return np.exp(-(d / width) ** 2) * np.exp(-r / reach) * (0.3 + 0.7 * np.clip(r / 300, 0, 1))


def streak(t01, angle=-0.35, width=0.08):
    """Diagonal light band sweeping across the frame, t01 in [0,1]."""
    u = (_lx * math.cos(angle) + _ly * math.sin(angle)) / W
    c = lerp(-0.4, 1.4, t01)
    return np.exp(-((u - c) / width) ** 2)


@functools.lru_cache(maxsize=None)
def bg_navy():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((x - W / 2) / W) ** 2 + ((y - H * 0.45) / H) ** 2)
    k = np.clip(1 - d * 1.5, 0, 1)[..., None] ** 1.5
    return DEEP + (NAVY * 1.15 - DEEP) * k


@functools.lru_cache(maxsize=None)
def vignette(strength=0.55):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    d = ((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2
    return (1 - strength * np.clip(d / 2, 0, 1) ** 1.2)[..., None]


def bloom(cv, strength=0.45, thresh=0.7):
    small = np.asarray(Image.fromarray(np.clip(cv * 255, 0, 255).astype(np.uint8)).reduce(4), np.float32) / 255
    bright = np.clip(small - thresh, 0, None) / (1 - thresh)
    im = Image.fromarray((np.clip(bright, 0, 1) * 255).astype(np.uint8))
    a = np.asarray(im.filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR), np.float32) / 255
    b = np.asarray(im.filter(ImageFilter.GaussianBlur(22)).resize((W, H), Image.BILINEAR), np.float32) / 255
    cv += (a * 0.6 + b * 0.8) * strength


def tonemap(cv):
    x = np.maximum(cv, 0)
    k = 0.82
    out = np.where(x < k, x, k + (1 - k) * np.tanh((x - k) / (1 - k)))
    return (out * 255 + 0.5).astype(np.uint8)


# ------------------------------------------------------------------ photos
def kb_box(img, w, h, p, seed, zoom=0.14):
    rnd = np.random.default_rng(seed)
    iw, ih = img.size
    ar = w / h
    if iw / ih > ar:
        bw, bh = ih * ar, ih
    else:
        bw, bh = iw, iw / ar
    zin = seed % 2 == 0
    z = lerp(1.0, 1 + zoom, p) if zin else lerp(1 + zoom, 1.0, p)
    cw, ch = bw / z, bh / z
    dx0, dx1 = rnd.uniform(-1, 1, 2)
    dy0, dy1 = rnd.uniform(-0.6, 0.3, 2)  # bias upwards: people's faces live in the upper half
    q = ease_io(p)
    cx = iw / 2 + lerp(dx0, dx1, q) * (iw - cw) / 2
    cy = ih / 2 + lerp(dy0, dy1, q) * (ih - ch) / 2
    cx = min(max(cx, cw / 2), iw - cw / 2)
    cy = min(max(cy, ch / 2), ih - ch / 2)
    return (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)


def photo_crop(path, w, h, p=0.0, seed=0, zoom=0.14):
    img = photo(path)
    out = img.resize((w, h), Image.BILINEAR, box=kb_box(img, w, h, p, seed, zoom), reducing_gap=2.0)
    return np.asarray(out, np.float32) / 255


@functools.lru_cache(maxsize=None)
def shadow_mask(w, h, blur=22, spread=10):
    pad = blur * 3
    m = Image.new('L', (w + 2 * pad, h + 2 * pad), 0)
    ImageDraw.Draw(m).rectangle((pad - spread // 2, pad + spread, pad + w + spread // 2, pad + h + spread * 2), fill=255)
    return np.asarray(m.filter(ImageFilter.GaussianBlur(blur)), np.float32) / 255, pad


def draw_photo(cv, arr, x, y, opacity=1.0, border=3, shadow=0.7, border_color=GOLD_HI):
    h, w = arr.shape[:2]
    if shadow:
        sm, pad = shadow_mask(w, h)
        r = region(x - pad, y - pad, sm.shape[1], sm.shape[0])
        if r:
            cv[r[0]] *= 1 - (sm[r[1]] * shadow * opacity)[..., None]
    r = region(x, y, w, h)
    if r is None:
        return
    cv[r[0]] = cv[r[0]] * (1 - opacity) + arr[r[1]] * opacity
    if border:
        for (xx, yy, ww, hh) in [(x - border, y - border, w + 2 * border, border), (x - border, y + h, w + 2 * border, border),
                                 (x - border, y, border, h), (x + w, y, border, h)]:
            rr = region(xx, yy, ww, hh)
            if rr:
                cv[rr[0]] = cv[rr[0]] * (1 - opacity) + border_color * opacity


def flash(cv, amount, cx=W / 2, cy=H / 2, radius=1100, color=WARM_WHITE):
    if amount > 0.003:
        add_light(cv, radial(cx, cy, radius) * 0.6 + 0.4, color, amount)


# ------------------------------------------------------------------ logo plaques
@functools.lru_cache(maxsize=None)
def plaque(path, w, h, pad_frac=0.11, radius=22, frame=4):
    """Luminous white card with a gold frame. The authentic logo sits inside, untouched,
    so every partner logo stays readable on any background."""
    logo, bg = logo_image(path)
    fill = bg if bg is not None and sum(bg) < 600 else (255, 255, 255)
    m = 40
    card = Image.new('RGBA', (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((m, m, m + w, m + h), radius, fill=(222, 186, 104, 255))
    d.rounded_rectangle((m + frame, m + frame, m + w - frame, m + h - frame), radius - 3, fill=fill + (255,))
    inset = 9 + frame
    d.rounded_rectangle((m + inset, m + inset, m + w - inset, m + h - inset), max(4, radius - 10),
                        outline=(201, 162, 75, 200), width=1)
    pad = int(min(w, h) * pad_frac) + inset
    bw, bh = w - 2 * pad, h - 2 * pad
    s = min(bw / logo.width, bh / logo.height)
    lw, lh = max(1, int(logo.width * s)), max(1, int(logo.height * s))
    lg = logo.resize((lw, lh), Image.LANCZOS)
    card.alpha_composite(lg, (m + (w - lw) // 2, m + (h - lh) // 2))
    glow = Image.new('L', card.size, 0)
    ImageDraw.Draw(glow).rounded_rectangle((m, m, m + w, m + h), radius, fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    return Layer(card, glow)


@functools.lru_cache(maxsize=None)
def eureka_layer(width):
    logo, bg = logo_image(manifest()['eureka_logo'])
    a = np.asarray(logo, np.float32) / 255
    if bg is None:
        lum = (a[..., :3] @ [0.3, 0.59, 0.11])[a[..., 3] > 0.5].mean()
        if lum > 0.42:  # light logo with transparency: shows directly over the navy, with a gold halo
            s = width / logo.width
            lg = logo.resize((int(logo.width * s), int(logo.height * s)), Image.LANCZOS)
            m = 60
            c = Image.new('RGBA', (lg.width + 2 * m, lg.height + 2 * m), (0, 0, 0, 0))
            c.alpha_composite(lg, (m, m))
            return Layer(c, c.getchannel('A').filter(ImageFilter.GaussianBlur(24)))
    h = int(width * logo.height / logo.width * 1.0 + width * 0.16)
    return plaque(manifest()['eureka_logo'], width + int(width * 0.16), h, pad_frac=0.08, radius=28, frame=5)


# ------------------------------------------------------------------ particles
@functools.lru_cache(maxsize=None)
def sprite(r):
    s = int(r * 3) + 1
    y, x = np.mgrid[-s:s + 1, -s:s + 1].astype(np.float32)
    d2 = (x * x + y * y) / (r * r)
    core = np.exp(-d2 * 2.5)
    halo = np.exp(-d2 * 0.5) * 0.35
    return (core[..., None] * WARM_WHITE + halo[..., None] * GOLD_HI).astype(np.float32)


def splat(cv, x, y, r, amount):
    sp = sprite(max(1, int(r)))
    s = sp.shape[0] // 2
    rr = region(int(x) - s, int(y) - s, sp.shape[1], sp.shape[0])
    if rr:
        cv[rr[0]] += sp[rr[1]] * amount


class Dust:
    """Drifting gold dust + bokeh."""

    def __init__(self, n, seed, rise=40, sizes=(1, 4)):
        g = np.random.default_rng(seed)
        self.x = g.uniform(0, W, n)
        self.y = g.uniform(0, H, n)
        self.vx = g.normal(0, 8, n)
        self.vy = -g.uniform(0.3, 1.0, n) * rise
        self.r = g.uniform(*sizes, n) ** 1.0
        self.r[g.random(n) < 0.08] *= 3.2  # a few big soft bokeh discs
        self.ph = g.uniform(0, 2 * np.pi, n)
        self.fr = g.uniform(0.6, 2.4, n)

    def draw(self, cv, t, amount=1.0):
        if amount <= 0.01:
            return
        x = (self.x + self.vx * t) % W
        y = (self.y + self.vy * t) % H
        tw = 0.55 + 0.45 * np.sin(self.ph + t * self.fr * 2 * np.pi)
        for xi, yi, ri, ti in zip(x, y, self.r, tw):
            a = amount * ti * (0.9 if ri < 5 else 0.18)
            splat(cv, xi, yi, ri, a)


class Converge:
    """Particles rushing into a single point (the breath before the climax)."""

    def __init__(self, n, seed, cx, cy):
        g = np.random.default_rng(seed)
        ang = g.uniform(0, 2 * np.pi, n)
        rad = g.uniform(500, 1300, n)
        self.x0, self.y0 = cx + np.cos(ang) * rad, cy + np.sin(ang) * rad * 0.7
        self.cx, self.cy = cx, cy
        self.d = g.uniform(0, 0.35, n)
        self.r = g.uniform(1, 3, n)

    def draw(self, cv, p):
        for x0, y0, d, r in zip(self.x0, self.y0, self.d, self.r):
            q = clamp01((p - d) / (1 - d))
            if q <= 0 or q >= 1:
                continue
            e = q ** 2.2
            splat(cv, lerp(x0, self.cx, e), lerp(y0, self.cy, e), r, 0.9 * math.sin(q * math.pi) ** 0.5)


CONF_COLORS = np.array([(232, 196, 106), (201, 162, 75), (255, 233, 176), (247, 242, 228),
                        (176, 136, 52), (240, 214, 140), (38, 58, 104)], np.float32)


class Confetti:
    """Gold confetti with linear-drag physics, flutter and 3-D flip shading."""

    def __init__(self, n, seed, t0, mode='rain'):
        g = np.random.default_rng(seed)
        self.t0 = t0
        if mode == 'rain':
            self.x0 = g.uniform(-50, W + 50, n)
            self.y0 = g.uniform(-1300, -20, n)
            self.vx0 = g.normal(0, 30, n)
            self.vy0 = g.uniform(0, 80, n)
        else:  # cannons from the two bottom corners
            side = g.random(n) < 0.5
            self.x0 = np.where(side, g.uniform(-20, 80, n), g.uniform(W - 80, W + 20, n))
            self.y0 = g.uniform(H - 40, H + 40, n)
            self.vx0 = np.where(side, 1, -1) * g.uniform(250, 1100, n)
            self.vy0 = -g.uniform(1300, 2300, n)
        self.k = 2.0
        self.vt = g.uniform(120, 220, n)
        self.sw = g.uniform(10, 40, n)
        self.sf = g.uniform(0.5, 1.6, n)
        self.rot = g.uniform(0, 2 * np.pi, n)
        self.rs = g.normal(0, 4, n)
        self.flip = g.uniform(3, 10, n)
        self.w = g.uniform(9, 18, n)
        self.h = g.uniform(5, 9, n)
        ci = g.choice(len(CONF_COLORS), n, p=[.22, .2, .18, .14, .1, .12, .04])
        self.col = CONF_COLORS[ci]
        self.ph = g.uniform(0, 2 * np.pi, n)

    def draw(self, cv, t, opacity=1.0):
        dt = t - self.t0
        if dt < 0 or opacity <= 0.01:
            return
        e = 1 - np.exp(-self.k * dt)
        x = self.x0 + self.vx0 / self.k * e + self.sw * np.sin(self.ph + dt * self.sf * 2 * np.pi)
        y = self.y0 + (self.vy0 - self.vt) / self.k * e + self.vt * dt
        vis = (x > -30) & (x < W + 30) & (y > -30) & (y < H + 30)
        if not vis.any():
            return
        layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        rot = self.rot + self.rs * dt
        fl = np.cos(self.ph + self.flip * dt)
        for i in np.nonzero(vis)[0]:
            hw, hh = self.w[i] / 2, self.h[i] / 2 * max(0.12, abs(fl[i]))
            c, s = math.cos(rot[i]), math.sin(rot[i])
            pts = [(x[i] + c * px - s * py, y[i] + s * px + c * py) for px, py in
                   ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]
            shade = 0.55 + 0.45 * abs(fl[i]) + (0.35 if fl[i] > 0.85 else 0)
            col = np.clip(self.col[i] * shade, 0, 255).astype(int)
            d.polygon(pts, fill=(int(col[0]), int(col[1]), int(col[2]), int(255 * opacity)))
        bbox = layer.getbbox()
        if not bbox:
            return
        arr = np.asarray(layer.crop(bbox), np.float32) / 255
        sl = (slice(bbox[1], bbox[3]), slice(bbox[0], bbox[2]))
        a = arr[..., 3:4]
        cv[sl] = cv[sl] * (1 - a) + arr[..., :3] * 1.15 * a


def firework(cv, t, t0, cx, cy, seed, n=70, life=2.0, speed=520):
    dt = t - t0
    if dt < 0 or dt > life:
        return
    g = np.random.default_rng(seed)
    ang = g.uniform(0, 2 * np.pi, n)
    sp = speed * g.uniform(0.55, 1.0, n)
    fade_ = (1 - dt / life) ** 1.6
    k = 2.6
    for a, s in zip(ang, sp):
        for j, lag in enumerate((0, 0.035, 0.07, 0.11)):
            tt = max(0.0, dt - lag)
            e = (1 - math.exp(-k * tt)) / k
            x = cx + math.cos(a) * s * e
            y = cy + math.sin(a) * s * e + 60 * tt * tt
            splat(cv, x, y, 2 if j == 0 else 1, fade_ * (1.0 if j == 0 else 0.45 / j) * 0.9)
    if dt < 0.25:
        splat(cv, cx, cy, 14, (1 - dt / 0.25) * 1.2)


# ------------------------------------------------------------------ scenes
DUST = Dust(220, 1, rise=35)
DUST_FAST = Dust(160, 2, rise=120, sizes=(1, 3))
CONF_RAIN = Confetti(420, 11, T.S5[0] - 0.2, 'rain')
CONF_CANNON = Confetti(380, 12, T.S5[0], 'cannon')
CONF_RAIN2 = Confetti(260, 13, T.S5[0] + 3.0, 'rain')
CONVERGE = Converge(160, 21, W / 2, 400)


def scene1(cv, t):
    """THE SPARK OF EXCELLENCE (0-10)."""
    cv[:] = bg_navy() * (0.35 + 0.65 * seg(t, 0.0, 3.0))
    sweep = t * 0.35
    L = (spotlight(260, H + 80, -1.15 + 0.35 * math.sin(sweep), 0.11) +
         spotlight(W - 260, H + 80, -1.99 - 0.35 * math.sin(sweep + 0.6), 0.11) +
         0.6 * spotlight(W / 2, -120, math.pi / 2 + 0.25 * math.sin(sweep * 1.3), 0.08))
    add_light(cv, L, GOLD_HI, 0.55 * seg(t, 0.4, 3.0))
    add_light(cv, radial(W / 2, 400, 420), GOLD, 0.45 * seg(t, 2.6, 4.2))
    DUST.draw(cv, t, seg(t, 0.2, 2.0))
    lay = eureka_layer(620)
    p = seg(t, 2.9, 4.6)
    if p > 0:
        composite(cv, lay, W / 2, 400, lerp(0.9, 1.0, ease_out(p)), ease_io(p), glow=0.55 * p)
    tl = text_layer('Excellence Worth Celebrating.', 'playfair', 72, 500, 0, 'gold', 10)
    q = seg(t, 5.8, 7.0)
    composite(cv, tl, W / 2, 770 + 18 * (1 - ease_out(q)), 1.0, ease_io(q), glow=0.8,
              shine=seg(t, 7.2, 8.6) if 7.2 < t < 8.6 else None)
    line_w = int(520 * ease_out(seg(t, 6.2, 7.4)))
    if line_w > 2:
        cv[700:702, W // 2 - line_w // 2:W // 2 + line_w // 2] += GOLD_HI * 0.9
    flash(cv, 1.4 * seg(t, 9.55, 10.0) ** 2)


S2_TEXTS = [('Great Achievements.', 10.25, 13.25), ('Extraordinary People.', 13.45, 16.45),
            ('One Shared Vision.', 16.65, 19.75)]


def scene2(cv, t):
    """THE PEOPLE BEHIND THE SUCCESS (10-20): beat-synced montage, a cut every 2 beats."""
    pool = photo_pool()
    k = int((t - 10) // 1.0)
    u = (t - 10) - k
    if k % 4 == 3 and len(pool) >= 3:  # triptych panels sliding in
        cv[:] = bg_navy() * 0.6
        pw, gap = 600, 24
        x0 = (W - 3 * pw - 2 * gap) // 2
        for j in range(3):
            path = pool[(k * 3 + j) % len(pool)]
            q = ease_out(seg(u, j * 0.08, j * 0.08 + 0.35))
            arr = photo_crop(path, pw, 900, u, seed=k * 7 + j, zoom=0.08)
            draw_photo(cv, arr, x0 + j * (pw + gap), 90 + int((1 - q) * (300 if j % 2 else -300)), q * 0.92)
    else:
        path = pool[k % len(pool)]
        cv[:] = photo_crop(path, W, H, (t - 10 - k + 0.15) / 1.3, seed=k * 3 + 1, zoom=0.12)
    cv *= 0.58 * vignette(0.7)
    add_light(cv, radial(lerp(-200, W + 200, u), 200 + 300 * (k % 2), 520), np.array([1.0, 0.62, 0.25]), 0.22)
    flash(cv, 0.4 * math.exp(-u / 0.09))
    DUST_FAST.draw(cv, t, 0.6)
    for text, a, b in S2_TEXTS:
        if a - 0.05 < t < b:
            q = seg(t, a, a + 0.45)
            o = q * (1 - seg(t, b - 0.3, b))
            lay = text_layer(text.upper(), 'cinzel', 88, 700, 6, 'gold', 12)
            band = slice(H // 2 - 120, H // 2 + 140)
            cv[band] *= 1 - 0.35 * o
            composite(cv, lay, W / 2, H / 2 + 10, lerp(1.08, 1.0, ease_out(q)), o, glow=0.9,
                      shine=seg(t, a + 0.5, a + 1.6) if a + 0.5 < t < a + 1.6 else None)
    flash(cv, 1.5 * seg(t, 19.7, 20.0) ** 2)


def scene3_title(cv, t):
    cv[:] = bg_navy()
    u = t - 20
    add_light(cv, rays(W / 2, 470, t, n=16), GOLD_HI, 0.5 * (0.45 + 0.55 * math.exp(-u / 0.8)))
    flash(cv, 1.2 * math.exp(-u / 0.25))
    DUST.draw(cv, t, 0.9)
    q1 = seg(u, 0.15, 0.8)
    composite(cv, text_layer('CELEBRATING OUR PARTNERS', 'cinzel', 100, 700, 8, 'gold', 14), W / 2, 460,
              lerp(1.12, 1.0, ease_out(q1)), ease_io(q1), glow=1.0, shine=seg(u, 1.0, 2.2) if 1.0 < u < 2.2 else None)
    lw = int(900 * ease_out(seg(u, 0.6, 1.5)))
    if lw > 2:
        cv[548:550, W // 2 - lw // 2:W // 2 + lw // 2] += GOLD_HI
    q2 = seg(u, 1.0, 1.7)
    composite(cv, text_layer('Honouring every journey to GAHAR accreditation', 'playfair', 50, 400, 0, 'ivory', 6),
              W / 2, 615 + 14 * (1 - ease_out(q2)), 1.0, ease_io(q2), glow=0.3)
    add_light(cv, streak(seg(u, 3.55, 4.0)), GOLD_HI, 0.9 * (u > 3.5))


def institution_slot(cv, t, i, inst):
    """Reusable showcase template: logo burst -> logo to the side -> 2-4 photos."""
    u = t - T.INSTITUTION_STARTS[i]
    photos = inst['photos'][:4]
    side = -1 if i % 2 == 0 else 1  # which side the logo moves to
    variant = i % 3
    # background: the institution's own photo, deeply blurred & tinted navy
    cv[:] = inst_bg(i) * (1 + 0.15 * math.exp(-u / 0.6))
    hero_c = (W / 2, 450)
    side_c = (W / 2 + side * 470, 470)
    mv = ease_io(seg(u, 1.25, 1.75))
    cx, cy = lerp(hero_c[0], side_c[0], mv), lerp(hero_c[1], side_c[1], mv)
    add_light(cv, rays(cx, cy, t, n=14, reach=700), GOLD_HI, 0.6 * math.exp(-u / 0.7) + 0.16)
    flash(cv, 0.75 * math.exp(-u / 0.12), cx, cy, 700)
    DUST.draw(cv, t, 0.75)
    # photos (other side)
    if photos:
        area_w, area_h = 900, 620
        ax = int(W / 2 - side * 470 - area_w / 2)
        ay = int(H / 2 - area_h / 2) + 10
        n = len(photos)
        starts = {1: [1.5], 2: [1.5, 2.75], 3: [1.5, 2.25, 3.0], 4: [1.5, 2.0, 2.5, 3.0]}[n]
        if variant == 0:
            single_gallery(cv, u, photos, starts, ax, ay, area_w, area_h, i)
        elif variant == 1:
            stack_gallery(cv, u, photos, starts, ax, ay, area_w, area_h, i)
        else:
            panel_gallery(cv, u, photos, starts, ax, ay, area_w, area_h, i, side)
    # logo plaque (drawn last: always on top and fully readable)
    pl = plaque(inst['logo'], 760, 430)
    sc = (0.55 + 0.45 * ease_back(seg(u, 0.0, 0.55))) * lerp(1.0, 0.82, mv)
    composite(cv, pl, cx, cy, sc, seg(u, 0.0, 0.18), glow=0.35 + 0.5 * math.exp(-u / 0.4))
    tag = text_layer(f'GAHAR ACCREDITATION  ·  {i + 1:02d}', 'mont', 26, 600, 6, 'gold', 4)
    q = seg(u, 0.3, 0.7)
    composite(cv, tag, cx, cy - 430 * sc / 2 - 52, 1.0, ease_io(q), glow=0.5)
    lines = fit_text_lines(inst['name'].upper(), 'cinzel', 50, 700, 720 if mv < 0.5 else 640, 3, 'gold', 8)
    q = seg(u, 0.4, 0.85)
    y = cy + 430 * sc / 2 + 62
    for ln in lines:
        composite(cv, ln, cx, y + 14 * (1 - ease_out(q)), 1.0, ease_io(q), glow=0.6)
        y += ln.h * 0.62
    # exit: light streak sweeps across, hand-off flash
    add_light(cv, streak(seg(u, 3.6, 4.0), angle=-0.35 if i % 2 else -2.8), GOLD_HI, 1.0 * (u > 3.55))
    flash(cv, 0.6 * seg(u, 3.85, 4.0) ** 2)


def single_gallery(cv, u, photos, starts, ax, ay, aw, ah, i):
    for j, s in enumerate(starts):
        end = starts[j + 1] + 0.3 if j + 1 < len(starts) else 4.2
        if not (s <= u < end):
            continue
        q = ease_out(seg(u, s, s + 0.35))
        o = q if j == 0 else seg(u, s, s + 0.3)
        arr = photo_crop(photos[j], aw, ah, seg(u, s, 4.0), seed=i * 11 + j, zoom=0.1)
        draw_photo(cv, arr, ax + int((1 - q) * 60 * (-1) ** i), ay, o)
        flash(cv, 0.35 * math.exp(-(u - s) / 0.1), ax + aw / 2, ay + ah / 2, 600)


ANGLES = [-5.0, 4.0, -2.5, 6.0]
OFFS = [(-110, -50), (90, 30), (-40, 70), (120, -60)]


def stack_gallery(cv, u, photos, starts, ax, ay, aw, ah, i):
    pw, ph = 600, 400
    for j, s in enumerate(starts):
        if u < s:
            continue
        q = ease_out(seg(u, s, s + 0.32))
        arr = photo_crop(photos[j], pw, ph, 0.0, seed=i * 13 + j, zoom=0.0)
        fr = 16  # ivory print border + gold hairline
        card = np.empty((ph + 2 * fr, pw + 2 * fr, 4), np.float32)
        card[..., :3] = IVORY
        card[..., 3] = 1
        card[fr - 2:fr + ph + 2, fr - 2:fr + pw + 2, :3] = GOLD_HI
        card[fr:fr + ph, fr:fr + pw, :3] = arr
        img = Image.fromarray((card * 255).astype(np.uint8), 'RGBA')
        sh = Image.new('L', img.size, 0)
        ImageDraw.Draw(sh).rectangle((0, 0, img.width, img.height), fill=150)
        lay = Layer(img, None)
        cx = ax + aw / 2 + OFFS[j][0]
        cy = ay + ah / 2 + OFFS[j][1] - (1 - q) * 120
        sc = lerp(1.25, 1.0, q)
        composite(cv, lay, cx + 14, cy + 22, sc, 0.45 * q, glow=0, rot=ANGLES[j])  # soft drop shadow
        composite(cv, lay, cx, cy, sc, q, glow=0, rot=ANGLES[(j + i) % 4])
        flash(cv, 0.3 * math.exp(-(u - s) / 0.1), cx, cy, 500)


def panel_gallery(cv, u, photos, starts, ax, ay, aw, ah, i, side):
    n = len(photos)
    gap = 16
    if n == 4:
        boxes = [(ax + c * (aw // 2 + gap // 2), ay + r * (ah // 2 + gap // 2), aw // 2 - gap // 2, ah // 2 - gap // 2)
                 for r in range(2) for c in range(2)]
    else:
        pw = (aw - (n - 1) * gap) // n
        boxes = [(ax + k * (pw + gap), ay, pw, ah) for k in range(n)]
    for j, (s, (bx, by, bw, bh)) in enumerate(zip(starts, boxes)):
        if u < s:
            continue
        q = ease_out(seg(u, s, s + 0.4))
        reveal = max(1, int(bh * q))
        arr = photo_crop(photos[j], bw, bh, seg(u, s, 4.2), seed=i * 17 + j, zoom=0.1)
        if j % 2 == 0:
            draw_photo(cv, arr[:reveal], bx, by, 1.0, shadow=0.5)
        else:
            draw_photo(cv, arr[bh - reveal:], bx, by + bh - reveal, 1.0, shadow=0.5)
        flash(cv, 0.3 * math.exp(-(u - s) / 0.1), bx + bw / 2, by + bh / 2, 400)


@functools.lru_cache(maxsize=12)
def inst_bg(i):
    inst = manifest()['institutions'][i]
    src = photo(inst['photos'][0]) if inst['photos'] else logo_image(inst['logo'])[0].convert('RGB')
    small = ImageOps.fit(src, (480, 270), Image.BILINEAR).filter(ImageFilter.GaussianBlur(10))
    arr = np.asarray(small.resize((W, H), Image.BILINEAR), np.float32) / 255
    return (arr * 0.32 + NAVY * 0.45) * vignette(0.75)


# --------------------------------------------------------------- scene 4
GRID_C, GRID_R, TW, TH, GAP = 7, 6, 300, 200, 14
BIG_W, BIG_H = GRID_C * (TW + GAP) + GAP, GRID_R * (TH + GAP) + GAP
_g = np.random.default_rng(5)
TILE_ORDER = _g.permutation(GRID_C * GRID_R)


@functools.lru_cache(maxsize=None)
def tile(path):
    return photo_crop(path, TW, TH, 0.5, seed=hash(path) % 97, zoom=0.0)


def tile_image(k, t):
    pool = photo_pool()
    period = 0.5 if t < 72 else 0.25
    n = int(max(0, t - 64) / period)
    base = k * 5
    # every tick a few tiles change image
    changes = sum(1 for m in range(n) if (m * 7 + k * 3) % 11 < 3)
    return pool[(base + changes * 13) % len(pool)], ((n * 7 + k * 3) % 11 < 3) and n > 0


def scene4(cv, t):
    """THE CELEBRATION BUILDS (64-77): moving mosaic, hero cuts, the silence."""
    if t >= 76.0:
        cv[:] = DEEP * 0.4
        p = seg(t, 76.0, 77.0)
        CONVERGE.draw(cv, p)
        splat(cv, W / 2, 400, 4 + 18 * p ** 3, 0.3 + 1.4 * p ** 2)
        return
    big = np.zeros((BIG_H, BIG_W, 3), np.float32) + DEEP
    for k in range(GRID_C * GRID_R):
        c, r = k % GRID_C, k // GRID_C
        appear = 64 + list(TILE_ORDER).index(k) * 0.07
        q = ease_out(seg(t, appear, appear + 0.35))
        if q <= 0:
            continue
        path, changed = tile_image(k, t)
        arr = tile(path)
        fw = max(2, int(TW * q))
        if fw < TW:
            arr = np.asarray(Image.fromarray((arr * 255).astype(np.uint8)).resize((fw, TH)), np.float32) / 255
        x = GAP + c * (TW + GAP) + (TW - fw) // 2
        y = GAP + r * (TH + GAP)
        big[y:y + TH, x:x + fw] = arr
        period = 0.5 if t < 72 else 0.25
        ph = ((t - 64) % period) / period
        if changed:
            big[y:y + TH, x:x + fw] += WARM_WHITE * 0.5 * math.exp(-ph * period / 0.08)
    # camera: slow push-in + drift
    p = seg(t, 64, 76)
    z = lerp(1.0, 1.18, ease_io(p))
    vw, vh = W / z, H / z
    cx = min(max(BIG_W / 2 + math.sin(p * 2.2) * 90, vw / 2), BIG_W - vw / 2)
    cy = min(max(BIG_H / 2 + math.cos(p * 1.7) * 60, vh / 2), BIG_H - vh / 2)
    box = (cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2)
    img = Image.fromarray((np.clip(big, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR, box=box)
    cv[:] = np.asarray(img, np.float32) / 255
    hero = 66.0 <= t < 70.0
    dim = 1.0 - 0.6 * window(t, 65.8, 66.1, 75.8, 76.0)
    cv *= dim * vignette(0.6)
    if hero:
        step = 1.0 if t < 68 else 0.5
        k = int((t - 66) / step)
        u = (t - 66) - k * step
        pool = photo_pool()
        path = pool[(k * 5 + 2) % len(pool)]
        arr = photo_crop(path, 1120, 680, u / step, seed=k + 40, zoom=0.08)
        q = ease_out(seg(u, 0, 0.18))
        draw_photo(cv, arr, (W - 1120) // 2, (H - 680) // 2 + int((1 - q) * 40), 1.0, border=4)
        flash(cv, 0.3 * math.exp(-u / 0.08))
    add_light(cv, streak((t - 64) % 2 / 2, angle=-0.4), GOLD_HI, 0.25)
    DUST_FAST.draw(cv, t, 0.8)
    if t >= 70.0:
        q = seg(t, 70.0, 70.6)
        o = q * (1 - seg(t, 75.6, 75.95))
        cv[H // 2 - 130:H // 2 + 130] *= 1 - 0.45 * o
        composite(cv, text_layer('TOGETHER WE ACHIEVED MORE.', 'cinzel', 92, 700, 6, 'gold', 14), W / 2, H / 2,
                  lerp(1.1, 1.0, ease_out(q)) + 0.03 * seg(t, 70.6, 75.8), o, glow=1.1,
                  shine=seg(t, 71.0, 72.4) if 71 < t < 72.4 else None)
    beat = ((t - 64) % 0.5) / 0.5
    flash(cv, 0.12 * math.exp(-beat * 0.5 / 0.08) * (t > 66))


# --------------------------------------------------------------- scene 5
def ring_positions():
    """Five logos on an arc at each side of the giant 10."""
    pos = []
    for side in (-1, 1):
        for k in range(5):
            y = 140 + k * 200
            x = W / 2 + side * (690 + 70 * math.cos((k - 2) / 2 * 1.2))
            pos.append((x, y))
    # pop order: alternate sides top to bottom
    order = [0, 5, 1, 6, 2, 7, 3, 8, 4, 9]
    return [pos[o] for o in order]


def scene5(cv, t):
    """THE GRAND REVEAL (77-85)."""
    u = t - 77
    cv[:] = bg_navy() * 0.9
    beat = (u % 0.5) / 0.5
    add_light(cv, rays(W / 2, 400, t, n=22, speed=0.05, sharp=5, reach=1100), GOLD_HI,
              0.42 + 0.2 * math.exp(-beat * 4) + 0.6 * math.exp(-u / 0.5))
    add_light(cv, radial(W / 2, 400, 520), GOLD, 0.3)
    cv[650:900] *= 0.55 + 0.45 * np.abs(np.linspace(-1, 1, 250))[:, None, None] ** 2  # calm band behind the title
    # shockwave ring
    rp = ease_out(seg(u, 0, 0.9))
    if 0 < rp < 1:
        d = np.sqrt((_lx - W / 2) ** 2 + (_ly - 400) ** 2)
        add_light(cv, np.exp(-((d - rp * 1500) / 50) ** 2), WARM_WHITE, 1.2 * (1 - rp))
    DUST.draw(cv, t, 1.0)
    for (fx, fy, ft, fs) in [(470, 250, 77.25, 1), (1450, 230, 77.5, 2), (960, 120, 79.0, 3),
                             (330, 520, 81.0, 4), (1590, 520, 83.0, 5), (960, 160, 84.0, 6)]:
        firework(cv, t, ft, fx, fy, fs)
    CONF_RAIN.draw(cv, t)  # confetti behind the logos and the number: logos are never covered
    CONF_CANNON.draw(cv, t)
    CONF_RAIN2.draw(cv, t)
    # the 10
    ten = text_layer('10', 'cinzel', 640, 900, 0, 'gold', 30)
    q = seg(u, 0, 0.55)
    pulse = 1 + 0.015 * math.exp(-beat * 5) * (u > 0.6)
    shine = None
    for a in (0.7, 3.2, 5.7):
        if a < u < a + 0.9:
            shine = seg(u, a, a + 0.9)
    composite(cv, ten, W / 2, 360, lerp(1.6, 1.0, ease_out(q)) * pulse, seg(u, 0, 0.12),
              glow=0.8 + 0.4 * math.exp(-beat * 4), shine=shine)
    q1, q2 = seg(u, 0.8, 1.3), seg(u, 1.05, 1.55)
    composite(cv, text_layer('GAHAR ACCREDITATION', 'cinzel', 70, 700, 10, 'gold', 12), W / 2,
              720 + 20 * (1 - ease_out(q1)), 1.0, ease_io(q1), glow=0.9)
    composite(cv, text_layer('ACHIEVEMENTS', 'cinzel', 70, 700, 22, 'gold', 12), W / 2,
              812 + 20 * (1 - ease_out(q2)), 1.0, ease_io(q2), glow=0.9)
    lw = int(560 * ease_out(seg(u, 1.2, 2.0)))
    if lw > 2:
        cv[870:872, W // 2 - lw // 2:W // 2 + lw // 2] += GOLD_HI
    # partner logos pop in around the number, one per half beat
    insts = manifest()['institutions']
    for k, ((x, y), inst) in enumerate(zip(ring_positions(), insts)):
        s = 1.0 + k * 0.45
        if u < s:
            continue
        q = seg(u, s, s + 0.32)
        y += 6 * math.sin(t * 1.6 + k)
        composite(cv, plaque(inst['logo'], 300, 168, pad_frac=0.08, radius=16, frame=3), x, y,
                  0.5 + 0.5 * ease_back(q), seg(u, s, s + 0.12), glow=0.3 + 0.9 * math.exp(-(u - s) / 0.25))
        if u - s < 0.2:
            splat(cv, x, y - 95, 10, 0.8 * (1 - (u - s) / 0.2))
    flash(cv, 1.8 * math.exp(-u / 0.16))
    flash(cv, 1.0 * seg(t, 84.7, 85.0) ** 2)


def scene6(cv, t):
    """THE GRAND FINALE (85-90)."""
    u = t - 85
    cv[:] = bg_navy()
    add_light(cv, rays(W / 2, 360, t, n=16, speed=0.04, reach=900), GOLD_HI, 0.35)
    add_light(cv, radial(W / 2, 360, 480), GOLD, 0.35)
    DUST.draw(cv, t, 1.0)
    CONF_RAIN2.draw(cv, t, 1 - seg(u, 2.5, 4.5))
    lay = eureka_layer(640)
    q = seg(u, 0.0, 1.0)
    composite(cv, lay, W / 2, 360, lerp(0.92, 1.0, ease_out(q)), ease_io(seg(u, 0, 0.4)), glow=0.55)
    q1 = seg(u, 0.6, 1.3)
    composite(cv, text_layer('To Our Partners & Teams — Thank You.', 'playfair', 62, 500, 0, 'ivory', 8),
              W / 2, 660 + 14 * (1 - ease_out(q1)), 1.0, ease_io(q1), glow=0.4)
    q2 = seg(u, 1.5, 2.2)
    composite(cv, text_layer('TOGETHER, WE RAISE THE STANDARD.', 'cinzel', 66, 700, 6, 'gold', 12),
              W / 2, 790 + 14 * (1 - ease_out(q2)), 1.0, ease_io(q2), glow=1.0,
              shine=seg(u, 2.4, 3.4) if 2.4 < u < 3.4 else None)
    flash(cv, 1.3 * math.exp(-u / 0.2))
    cv *= 1 - seg(t, 89.0, 89.95)


# --------------------------------------------------------------- frame
def frame(t):
    cv = np.zeros((H, W, 3), np.float32)
    if t < T.S2[0]:
        scene1(cv, t)
    elif t < T.S3[0]:
        scene2(cv, t)
    elif t < T.INSTITUTION_STARTS[0]:
        scene3_title(cv, t)
    elif t < T.S4[0]:
        i = min(T.N_INSTITUTIONS - 1, int((t - T.INSTITUTION_STARTS[0]) // T.SLOT))
        institution_slot(cv, t, i, manifest()['institutions'][i])
    elif t < T.S5[0]:
        scene4(cv, t)
    elif t < T.S6[0]:
        scene5(cv, t)
    else:
        scene6(cv, t)
    photo_scene = T.S2[0] <= t < T.S2[1] or T.INSTITUTION_STARTS[0] <= t < 76.0
    bloom(cv, 0.18 if photo_scene else 0.32, 0.85 if photo_scene else 0.78)
    if not (76.0 <= t < 77.0):
        cv *= vignette(0.35)
    return tonemap(cv)


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
    os.makedirs(os.path.join(BUILD, 'chunks'), exist_ok=True)
    nf = int(T.DURATION * FPS)
    jobs = [(a, min(nf, a + chunk), os.path.join(BUILD, 'chunks', f'c{a:05d}.mp4')) for a in range(0, nf, chunk)]
    with Pool(workers) as p:
        for k, path in enumerate(p.imap(render_chunk, jobs)):
            print(f'chunk {k + 1}/{len(jobs)}', flush=True)
    lst = os.path.join(BUILD, 'chunks', 'list.txt')
    with open(lst, 'w') as f:
        f.writelines(f"file '{os.path.abspath(j[2])}'\n" for j in jobs)
    master = os.path.join(BUILD, 'master.mp4')
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst,
                    '-c', 'copy', master], check=True)
    score = os.path.join(BUILD, 'score.wav')
    if not os.path.exists(score):
        subprocess.run([sys.executable, os.path.join(HERE, 'music.py'), score], check=True)
    # final delivery encode: two-pass H.264 High, ~8.5 Mbps (fits under 100 MB), AAC 256k
    base = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', master, '-i', score,
            '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-profile:v', 'high',
            '-b:v', '8300k', '-maxrate', '14M', '-bufsize', '20M', '-pix_fmt', 'yuv420p', '-g', '60',
            '-r', str(FPS), '-t', str(T.DURATION)]
    plog = os.path.join(BUILD, 'x264pass')
    subprocess.run(base + ['-pass', '1', '-passlogfile', plog, '-an', '-f', 'mp4', '/dev/null'], check=True)
    subprocess.run(base + ['-pass', '2', '-passlogfile', plog, '-c:a', 'aac', '-b:a', '256k',
                           '-movflags', '+faststart', out], check=True)
    print('wrote', out)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'stills'
    if cmd == 'stills':
        d = os.path.join(BUILD, 'stills')
        os.makedirs(d, exist_ok=True)
        for s in sys.argv[2:]:
            Image.fromarray(frame(float(s))).save(os.path.join(d, f't{float(s):05.2f}.png'))
            print('still', s, flush=True)
    elif cmd == 'video':
        out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(BUILD, 'final.mp4')
        render_video(out)
