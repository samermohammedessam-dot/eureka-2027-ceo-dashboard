"""THE POWER OF TEN — the awards-stage environment.

A dark, prestigious venue rendered procedurally with a real perspective camera:
glossy reflective floor, an architectural back wall of light slats, a central platform with a gold
rim, ten pedestals in an arc (one per accreditation achievement) and moving volumetric spotlights.
All light is built on quarter-resolution light maps and composited additively.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1920, 1080
LW, LH = W // 4, H // 4
_ly, _lx = np.mgrid[0:LH, 0:LW].astype(np.float32) * 4

NAVY_TOP = np.array([0.012, 0.022, 0.055], np.float32)
NAVY_MID = np.array([0.055, 0.085, 0.17], np.float32)
GOLD = np.array([1.0, 0.80, 0.48], np.float32)
WHITE = np.array([1.0, 0.95, 0.88], np.float32)


class Cam:
    def __init__(self, pos, look, fov=48.0):
        self.pos = np.asarray(pos, np.float64)
        d = np.asarray(look, np.float64) - self.pos
        self.yaw = math.atan2(d[0], d[2])
        self.pitch = math.atan2(-d[1], math.hypot(d[0], d[2]))  # positive = looking down
        self.f = (W / 2) / math.tan(math.radians(fov) / 2)

    def view(self, P):
        d = np.asarray(P, np.float64) - self.pos
        cy, sy = math.cos(self.yaw), math.sin(self.yaw)
        x = d[..., 0] * cy - d[..., 2] * sy
        z = d[..., 0] * sy + d[..., 2] * cy
        y = d[..., 1]
        cp, sp = math.cos(self.pitch), math.sin(self.pitch)
        return np.stack([x, y * cp + z * sp, -y * sp + z * cp], -1)

    def screen(self, P):
        V = self.view(P)
        z = np.maximum(V[..., 2], 1e-3)
        return np.stack([W / 2 + V[..., 0] / z * self.f, H / 2 - V[..., 1] / z * self.f], -1), V[..., 2]

    def horizon(self):
        return H / 2 - math.tan(self.pitch) * self.f


# ------------------------------------------------------------------ layout
N = 10
PLAT_RX, PLAT_RZ, PLAT_H = 1000.0, 520.0, 36.0


def pedestal(k):
    """Ten achievement positions on an arc across the back of the platform."""
    a = math.radians(-66 + 132 * k / (N - 1))
    return np.array([760 * math.sin(a), PLAT_H, 120 + 330 * math.cos(a)])


def lightmap_up(m):
    return np.asarray(Image.fromarray(m.astype(np.float32), 'F').resize((W, H), Image.BILINEAR))


def add(cv, m, color, gain):
    if gain > 0.002:
        cv += lightmap_up(m)[..., None] * (color * gain)


def cone(apex, target, w0, w1):
    """Volumetric beam between two screen points (quarter-res map)."""
    ax, ay = apex
    tx, ty = target
    dx, dy = tx - ax, ty - ay
    L2 = dx * dx + dy * dy + 1e-6
    t = ((_lx - ax) * dx + (_ly - ay) * dy) / L2
    px, py = ax + t * dx, ay + t * dy
    d = np.sqrt((_lx - px) ** 2 + (_ly - py) ** 2)
    w = w0 + (w1 - w0) * np.clip(t, 0, 1)
    inside = np.clip(t, 0, 1.05)
    return np.exp(-(d / w) ** 2) * (inside > 0) * (0.35 + 0.65 * (1 - np.clip(t, 0, 1))) * np.clip(1.08 - t, 0, 1) * 4


def pool(cam, P, r):
    """Elliptical light pool on the floor/platform (projected circle)."""
    S, z = cam.screen(P)
    if z < 10:
        return np.zeros((LH, LW), np.float32)
    rx = r * cam.f / z
    ry = rx * max(0.18, math.sin(cam.pitch + 0.08) + 0.12)
    return np.exp(-(((_lx - S[0]) / rx) ** 2 + ((_ly - S[1]) / ry) ** 2) * 1.6)


def render_stage(cam, t, lit=None, spots=(), wall=1.0, dim=1.0):
    """lit: list of 10 values 0..1 (pedestal beams). spots: [(apex_world, target_world, intensity)]."""
    lit = lit if lit is not None else [0.0] * N
    hy = cam.horizon()
    y = np.arange(H, dtype=np.float32)[:, None, None]
    sky = NAVY_TOP + (NAVY_MID - NAVY_TOP) * np.clip((y - (hy - 700)) / 700, 0, 1) ** 1.5
    floor = NAVY_MID * (1.0 - 0.8 * np.clip((y - hy) / 700, 0, 1) ** 0.7)  # meets the sky without a seam
    cv = np.where(y < hy, sky, floor).astype(np.float32) * np.ones((1, W, 1), np.float32)
    cv = cv.copy()
    # back wall: vertical architectural light slats (+ their floor reflections)
    m = Image.new('L', (LW, LH), 0)
    md = ImageDraw.Draw(m)
    for x in np.arange(-3000, 3001, 190):
        for sgn, gain in ((1, 1.0), (-1, 0.25)):
            (x0, y0), z0 = cam.screen((x, 60 * sgn, 1700))
            (x1, y1), z1 = cam.screen((x, 1500 * sgn, 1700))
            if z0 > 10:
                fall = math.exp(-abs(x) / 2200)
                md.line([(x0 / 4, y0 / 4), (x1 / 4, y1 / 4)], fill=int(140 * gain * fall), width=1)
    m = np.asarray(m.filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
    add(cv, m, np.array([0.55, 0.65, 0.95], np.float32), 0.9 * wall)
    (wx, wy), _ = cam.screen((0, 700, 1700))
    add(cv, np.exp(-(((_lx - wx) / 900) ** 2 + ((_ly - wy) / 420) ** 2)), GOLD, 0.22 * wall)
    # the platform: dark glass disc with a gold rim and its reflection
    ang = np.linspace(0, 2 * math.pi, 96)
    rim = np.stack([PLAT_RX * np.cos(ang), np.full_like(ang, PLAT_H), PLAT_RZ * np.sin(ang) + 260], -1)
    side = rim.copy()
    side[:, 1] = 0
    S_top, z_top = cam.screen(rim)
    S_bot, _ = cam.screen(side)
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if (z_top > 10).all():
        d.polygon([tuple(p) for p in S_bot], fill=(8, 13, 28, 255))
        d.polygon([tuple(p) for p in S_top], fill=(18, 28, 56, 255))
    arr = np.asarray(layer, np.float32) / 255
    a = arr[..., 3:4]
    cv = cv * (1 - a) + arr[..., :3] * a
    rim_m = Image.new('L', (LW, LH), 0)
    ImageDraw.Draw(rim_m).line([(p[0] / 4, p[1] / 4) for p in S_top] + [(S_top[0][0] / 4, S_top[0][1] / 4)], fill=255, width=1)
    rim_m = np.asarray(rim_m.filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255
    add(cv, rim_m, GOLD, 0.9)
    # pedestals: glowing rings; lit ones get a column of light and a pool
    for k in range(N):
        P = pedestal(k)
        S, z = cam.screen(P)
        if z < 10:
            continue
        r = 60 * cam.f / z
        ring = np.exp(-((np.sqrt(((_lx - S[0]) / 1.0) ** 2 + ((_ly - S[1]) / 0.32) ** 2) - r) / (2.5 + r * 0.06)) ** 2)
        add(cv, ring, GOLD, 0.35 + 0.9 * lit[k])
        if lit[k] > 0.01:
            (tx, ty), _ = cam.screen(P + np.array([0, 1600, 0]))
            col = np.exp(-((_lx - S[0]) / (r * 0.55 + 3)) ** 2) * np.clip((S[1] - _ly) / max(1, S[1] - ty), 0, 1) ** 0.3 * (_ly < S[1])
            col *= np.exp(-np.clip(S[1] - _ly, 0, None) / 900)
            add(cv, col, WHITE * 0.6 + GOLD * 0.4, 0.75 * lit[k])
            add(cv, pool(cam, P, 170), GOLD, 0.6 * lit[k])
    # moving spotlights from the truss
    for apex_w, target_w, inten in spots:
        if inten <= 0.01:
            continue
        A, za = cam.screen(apex_w)
        T, zt = cam.screen(target_w)
        if zt < 10:
            continue
        w1 = 260 * cam.f / zt
        add(cv, cone(A, T, 10, w1), WHITE * 0.7 + GOLD * 0.3, 0.32 * inten)
        add(cv, pool(cam, target_w, 260), WHITE * 0.6 + GOLD * 0.4, 0.55 * inten)
    # glossy floor: soft vertical reflection of everything bright above the horizon line
    hy_i = int(hy)
    if 0 < hy_i < H - 2:
        n = min(hy_i, H - hy_i)
        src = cv[hy_i - n:hy_i][::-1]
        small = Image.fromarray((np.clip(src, 0, 1) * 255).astype(np.uint8)).resize((W // 8, max(1, n // 8)))
        blur = np.asarray(small.filter(ImageFilter.GaussianBlur(2)).resize((W, n)), np.float32) / 255
        cv[hy_i:hy_i + n] += blur * np.linspace(0.22, 0.0, n)[:, None, None]
    return cv * dim


# ------------------------------------------------------------------ truss spot helpers
def spot(k_or_xyz, t, phase=0.0, inten=1.0, sweep=0.0):
    """A truss spotlight aimed at a pedestal index or a world point, with a gentle sweep."""
    target = pedestal(k_or_xyz) if isinstance(k_or_xyz, (int, np.integer)) else np.asarray(k_or_xyz, np.float64)
    target = target + np.array([sweep * 260 * math.sin(t * 0.9 + phase), 0, 0])
    apex = np.array([target[0] * 0.4 + 500 * math.sin(phase), 1650, -300])
    return apex, target, inten
