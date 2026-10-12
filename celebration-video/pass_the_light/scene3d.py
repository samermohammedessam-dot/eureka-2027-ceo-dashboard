"""Small 3-D software renderer (perspective camera, prisms, emissive quads, window lights, depth fog)
plus the two PASS THE LIGHT environments built with it:

  * City of Excellence — a real 3-D night city on a grid, ten landmark towers that light up
    from the base to the crown, an aerial camera, and a golden relay comet with light paths.
  * Corridor of light — a hospital corridor with luminous ceiling panels, glass wall light,
    a glossy floor (mirrored reflections) and a bright doorway at the end.

Units are 'world units' (~decimetres). Rendering is supersampled 1.5x then downsampled.
"""
import functools
import math

import numpy as np
from PIL import Image, ImageDraw

W, H = 1920, 1080
SS = 1.5
SW, SH = int(W * SS), int(H * SS)
NEAR = 4.0


# ------------------------------------------------------------------ camera
class Cam:
    def __init__(self, pos, yaw=0.0, pitch=0.0, fov_deg=50.0):
        self.pos = np.asarray(pos, np.float64)
        self.yaw, self.pitch = yaw, pitch
        self.f = (W / 2) / math.tan(math.radians(fov_deg) / 2)

    def view(self, P):
        P = np.asarray(P, np.float64)
        d = P - self.pos
        cy, sy = math.cos(self.yaw), math.sin(self.yaw)
        x = d[..., 0] * cy - d[..., 2] * sy
        z = d[..., 0] * sy + d[..., 2] * cy
        y = d[..., 1]
        cp, sp = math.cos(self.pitch), math.sin(self.pitch)
        y2 = y * cp + z * sp
        z2 = -y * sp + z * cp
        return np.stack([x, y2, z2], -1)

    def proj(self, V):
        """view coords -> screen coords (final 1920x1080 space)."""
        z = np.maximum(V[..., 2], 1e-6)
        return np.stack([W / 2 + V[..., 0] / z * self.f, H / 2 - V[..., 1] / z * self.f], -1)

    def screen(self, P):
        V = self.view(P)
        return self.proj(V), V[..., 2]

    def horizon_y(self):
        return H / 2 - math.tan(self.pitch) * self.f


def clip_near(V):
    """Sutherland-Hodgman against z >= NEAR. V: (n,3) view-space polygon."""
    out = []
    n = len(V)
    for i in range(n):
        a, b = V[i], V[(i + 1) % n]
        ina, inb = a[2] >= NEAR, b[2] >= NEAR
        if ina:
            out.append(a)
        if ina != inb:
            t = (NEAR - a[2]) / (b[2] - a[2])
            out.append(a + (b - a) * t)
    return np.array(out) if len(out) >= 3 else None


def poly_screen(cam, P):
    V = clip_near(cam.view(P))
    if V is None:
        return None, None
    S = cam.proj(V) * SS
    return [tuple(p) for p in S], float(V[:, 2].mean())


def fogged(col, depth, fog_col, fog_dist):
    k = 1 - math.exp(-depth / fog_dist)
    return tuple(int(max(0, min(255, c * (1 - k) + fc * k))) for c, fc in zip(col, fog_col))


# ------------------------------------------------------------------ prisms (buildings)
class Prism:
    """Footprint polygon (counter-clockwise, x/z) extruded from y0 to y1."""

    def __init__(self, foot, y0, y1, base_col, rng, win=True, win_dx=16, win_dy=20, lit_p=0.22, landmark=-1, bands=False):
        self.foot = np.asarray(foot, np.float64)
        self.y0, self.y1 = y0, y1
        self.col = base_col
        self.landmark = landmark
        self.center = np.array([self.foot[:, 0].mean(), (y0 + y1) / 2, self.foot[:, 1].mean()])
        self.faces = []
        n = len(self.foot)
        for i in range(n):
            a, b = self.foot[i], self.foot[(i + 1) % n]
            edge = b - a
            L = float(np.hypot(*edge))
            nrm = np.array([edge[1], 0, -edge[0]]) / max(L, 1e-6)  # outward for CCW
            quad = np.array([[a[0], y0, a[1]], [b[0], y0, b[1]], [b[0], y1, b[1]], [a[0], y1, a[1]]])
            wins = None
            if win and L > 20 and (y1 - y0) > 30:
                us = np.arange(win_dx / 2, L - win_dx / 3, win_dx)
                vs = np.arange(y0 + 12, y1 - 8, win_dy)
                uu, vv = np.meshgrid(us, vs)
                uu, vv = uu.ravel(), vv.ravel()
                pts = np.stack([a[0] + edge[0] / L * uu, vv, a[1] + edge[1] / L * uu], -1) + nrm * 0.6
                r = rng.random(len(pts))
                if bands:  # glass towers: whole floors lit, reading as horizontal light bands
                    rows = np.round((vv - y0) / win_dy).astype(int)
                    r = rng.random(rows.max() + 1)[rows] * 0.92 + r * 0.08
                bright = rng.uniform(0.45, 1.0, len(pts))
                hfrac = (vv - y0) / max(1, y1 - y0)
                wins = (pts, r, bright, hfrac)
            shade = 0.55 + 0.45 * abs(nrm[0] * 0.8 + nrm[2] * 0.35)
            self.faces.append((quad, nrm, wins, shade))
        self.top = np.array([[p[0], y1, p[1]] for p in self.foot])


def draw_prism(draw, cam, pr, env, lit=0.0, lit_sweep=1.0, gold=(255, 214, 140), win_points=None):
    eye = cam.pos
    fog_col, fog_dist = env['fog'], env['fog_dist']
    items = []
    for quad, nrm, wins, shade in pr.faces:
        c = quad.mean(0)
        if np.dot(nrm, eye - c) <= 0:
            continue
        items.append((np.linalg.norm(c - eye), quad, wins, shade))
    items.sort(key=lambda x: -x[0])
    base = pr.col
    for dist, quad, wins, shade in items:
        V = cam.view(quad)
        if (V[:, 2] < NEAR).all():
            continue
        depth = float(V[:, 2].mean())
        col = tuple(c * shade for c in base)
        if lit > 0:
            col = tuple(c * (1 - 0.55 * lit) + g * 0.26 * lit * shade for c, g in zip(col, gold))
        # three horizontal bands: facades read darker at street level, lighter towards the sky
        bands = 3 if depth < 4500 else 1
        for k in range(bands):
            f0, f1 = k / bands, (k + 1) / bands
            sub = quad.copy()
            sub[0, 1] = sub[1, 1] = quad[0, 1] + (quad[2, 1] - quad[0, 1]) * f0
            sub[2, 1] = sub[3, 1] = quad[0, 1] + (quad[2, 1] - quad[0, 1]) * f1
            pts, dd = poly_screen(cam, sub)
            if pts is None:
                continue
            g = 0.72 + 0.5 * (f0 + f1) / 2 if bands > 1 else 1.0
            draw.polygon(pts, fill=fogged(tuple(c * g for c in col), dd, fog_col, fog_dist))
        # roof-edge highlight
        e = cam.view(quad[2:4])
        if (e[:, 2] > NEAR).all():
            sp = cam.proj(e) * SS
            draw.line([tuple(sp[0]), tuple(sp[1])], fill=fogged(tuple(min(255, c * 2.2 + 18) for c in col), depth, fog_col, fog_dist), width=1)
        if wins is not None and depth < env['win_dist']:
            P, r, bright, hfrac = wins
            if lit > 0:
                on = (r < env['lit_p']) | ((hfrac < lit_sweep) & (r < 0.86 * lit))
            else:
                on = r < env['lit_p']
            if not on.any():
                continue
            S, Z = cam.screen(P[on])
            ok = Z > NEAR
            b = bright[on][ok]
            if lit > 0:
                warm = np.where((hfrac[on][ok] < lit_sweep), 1.0, 0.0)
            else:
                warm = np.zeros(ok.sum())
            win_points.append((S[ok] * SS, Z[ok], b, warm, depth))
    if pr.top is not None and eye[1] > pr.y1:
        pts, depth = poly_screen(cam, pr.top)
        if pts:
            col = tuple(c * 0.75 for c in base)
            draw.polygon(pts, fill=fogged(col, depth, fog_col, fog_dist))


def draw_windows(draw, win_points, cam, env):
    """Window lights: points (far) or small rects (near). Colour = warm interior or gold when lit."""
    fog_dist = env['fog_dist']
    for S, Z, b, warm, depth in win_points:
        fade = np.exp(-Z / (fog_dist * 1.6))
        size = 9.0 * cam.f / np.maximum(Z, 1) * SS
        lum = np.clip(b * fade * 1.25, 0, 1.2)
        base = np.array([255, 196, 120])
        goldc = np.array([255, 236, 175])
        cols = (base[None, :] * (1 - warm[:, None]) + goldc[None, :] * warm[:, None]) * np.clip(lum + 0.35 * warm, 0, 1.3)[:, None]
        cols = np.clip(cols, 0, 255).astype(int)
        small = size < 2.2
        if small.any():
            for c_lv in range(4):  # bucket colours to keep PIL calls few
                m = small & (np.digitize(lum, [0.35, 0.6, 0.8]) == c_lv)
                if m.any():
                    c = tuple(int(v) for v in cols[m].mean(0))
                    draw.point([tuple(p) for p in S[m]], fill=c)
        big = np.nonzero(~small)[0]
        for i in big[:600]:
            x, y = S[i]
            s = size[i]
            draw.rectangle((x - s * 0.35, y - s * 0.5, x + s * 0.35, y + s * 0.5), fill=tuple(cols[i]))


# ------------------------------------------------------------------ the City of Excellence
LANDMARK_N = 10
AVIATION = []  # (x, y, z, phase) red blinking lights on spires


@functools.lru_cache(maxsize=1)
def city():
    rng = np.random.default_rng(2026)
    # the relay route: a gentle S-curve through the city
    route = []
    for i in range(LANDMARK_N):
        z = 1500 + i * 620
        x = 520 * math.sin(i * 0.9) + (i % 2) * 140 - 70
        route.append((x, z))
    prisms = []
    occupied = []
    # landmarks
    kinds = ['tiers', 'octa', 'twin', 'tiers', 'slab', 'octa', 'tiers', 'twin', 'slab', 'octa']
    land_info = []
    for i, (x, z) in enumerate(route):
        k = kinds[i]
        h = 520 + 60 * math.sin(i * 1.7) + (i == LANDMARK_N - 1) * 80
        col = (24, 40, 78)
        parts = []
        if k == 'tiers':
            for j, (s, y0, y1) in enumerate([(70, 0, h * 0.55), (52, h * 0.55, h * 0.82), (34, h * 0.82, h * 0.95)]):
                parts.append(Prism([(x - s, z - s), (x - s, z + s), (x + s, z + s), (x + s, z - s)][::-1], y0, y1, col, rng, landmark=i))
        elif k == 'octa':
            for j, (r, y0, y1) in enumerate([(78, 0, h * 0.7), (56, h * 0.7, h * 0.93)]):
                foot = [(x + r * math.cos(a), z + r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 9)[:-1]]
                parts.append(Prism(foot, y0, y1, col, rng, win_dx=14, landmark=i))
        elif k == 'twin':
            for dx, hh in [(-55, h * 0.95), (55, h * 0.82)]:
                s = 34
                parts.append(Prism([(x + dx - s, z - s), (x + dx - s, z + s), (x + dx + s, z + s), (x + dx + s, z - s)][::-1], 0, hh, col, rng, landmark=i))
            parts.append(Prism([(x - 22, z - 14), (x - 22, z + 14), (x + 22, z + 14), (x + 22, z - 14)][::-1], h * 0.55, h * 0.6, col, rng, win=False, landmark=i))
        else:  # slab with a crown
            parts.append(Prism([(x - 95, z - 40), (x - 95, z + 40), (x + 95, z + 40), (x + 95, z - 40)][::-1], 0, h * 0.86, col, rng, landmark=i))
            parts.append(Prism([(x - 45, z - 25), (x - 45, z + 25), (x + 45, z + 25), (x + 45, z - 25)][::-1], h * 0.86, h * 0.95, col, rng, landmark=i))
        top = max(p.y1 for p in parts)
        land_info.append({'x': x, 'z': z, 'h': top, 'spire': top + 60, 'kind': k})
        prisms += parts
        occupied.append((x, z, 150))
    # generic city blocks
    step = 230
    for gx in np.arange(-2600, 2601, step):
        for gz in np.arange(200, 9200, step):
            if rng.random() < 0.12:
                continue  # plazas
            cx, cz = gx + rng.uniform(-20, 20), gz + rng.uniform(-20, 20)
            if any((cx - ox) ** 2 + (cz - oz) ** 2 < (r + 80) ** 2 for ox, oz, r in occupied):
                continue
            # fewer, lower buildings near the route so the landmarks read
            near = min(math.hypot(cx - x, cz - z) for x, z in route)
            hmax = 80 + min(1.0, near / 900) * 280
            for _ in range(rng.integers(1, 3)):
                sx, sz = rng.uniform(40, 85), rng.uniform(40, 85)
                ox, oz = rng.uniform(-40, 40), rng.uniform(-40, 40)
                h = float(rng.lognormal(math.log(hmax * 0.38), 0.65))
                h = min(h, hmax * 1.3)
                if rng.random() < 0.035 and near > 700:  # occasional distant high-rise
                    h = rng.uniform(330, 520)
                    sx, sz = rng.uniform(35, 55), rng.uniform(35, 55)
                mat = rng.choice(['glass', 'stone', 'plain'], p=[0.3, 0.2, 0.5])
                shade = rng.uniform(0.75, 1.05)
                if mat == 'glass':
                    col = (int(12 * shade), int(30 * shade), int(64 * shade))
                elif mat == 'stone':
                    col = (int(36 * shade), int(32 * shade), int(42 * shade))
                else:
                    col = (int(16 * shade), int(26 * shade), int(50 * shade))
                x0, x1, z0, z1 = cx + ox - sx, cx + ox + sx, cz + oz - sz, cz + oz + sz
                if h > 240 and rng.random() < 0.25:  # octagonal tower
                    r_ = min(sx, sz)
                    foot = [(cx + ox + r_ * math.cos(a_), cz + oz + r_ * math.sin(a_)) for a_ in np.linspace(0, 2 * math.pi, 9)[:-1]]
                    prisms.append(Prism(foot, 0, h, col, rng, win_dx=14, bands=(mat == 'glass')))
                elif h > 200 and rng.random() < 0.4:  # setback tower
                    prisms.append(Prism([(x1, z0), (x1, z1), (x0, z1), (x0, z0)], 0, h * 0.7, col, rng, bands=(mat == 'glass')))
                    k_ = 0.62
                    mx, mz = cx + ox, cz + oz
                    prisms.append(Prism([(mx + sx * k_, mz - sz * k_), (mx + sx * k_, mz + sz * k_), (mx - sx * k_, mz + sz * k_),
                                         (mx - sx * k_, mz - sz * k_)], h * 0.7, h, col, rng, bands=(mat == 'glass')))
                else:
                    prisms.append(Prism([(x1, z0), (x1, z1), (x0, z1), (x0, z0)], 0, h, col, rng, bands=(mat == 'glass')))
                if rng.random() < 0.35:  # rooftop plant room
                    rx, rz = cx + ox + rng.uniform(-sx, sx) * 0.4, cz + oz + rng.uniform(-sz, sz) * 0.4
                    rs = rng.uniform(10, 22)
                    prisms.append(Prism([(rx + rs, rz - rs), (rx + rs, rz + rs), (rx - rs, rz + rs), (rx - rs, rz - rs)], h,
                                        h + rng.uniform(8, 22), tuple(int(c_ * 0.8) for c_ in col), rng, win=False))
                if h > 260 and rng.random() < 0.6:  # spire + aviation light
                    mx, mz = cx + ox, cz + oz
                    top = h + rng.uniform(50, 120)
                    prisms.append(Prism([(mx + 3, mz - 3), (mx + 3, mz + 3), (mx - 3, mz + 3), (mx - 3, mz - 3)], h, top,
                                        (40, 46, 70), rng, win=False))
                    AVIATION.append((mx, top + 3, mz, rng.uniform(0, 6.28)))
    return prisms, land_info, route


CITY_ENV = {'fog': (30, 40, 74), 'fog_dist': 3300, 'win_dist': 6500, 'lit_p': 0.22}


@functools.lru_cache(maxsize=1)
def sky_gradient():
    return None


def draw_sky(img_arr, cam):
    hy = cam.horizon_y() * SS
    y = np.arange(SH, dtype=np.float32)[:, None]
    t = np.clip((y - (hy - 900 * SS)) / (900 * SS), 0, 1) ** 1.6
    top = np.array([4, 8, 22], np.float32)
    hor = np.array([30, 40, 74], np.float32)          # = fog colour: the city dissolves into the sky
    col = top + (hor - top) * t[..., None]
    warm = np.exp(-((y - hy) / (60 * SS)) ** 2)[..., None] * np.array([40, 26, 10], np.float32)
    ground = np.broadcast_to(hor, (SH, 1, 3))
    img_arr[:] = np.where((y > hy)[..., None], ground + warm, col + warm)
    rng = np.random.default_rng(9)
    n = 700
    xs = rng.integers(0, SW, n)
    ys = (rng.random(n) * max(1, hy - 40 * SS)).astype(int)
    ok = ys < SH
    img_arr[ys[ok], xs[ok]] += rng.uniform(40, 150, ok.sum())[:, None]


def draw_streets(draw, cam):
    """Glowing street grid: lines of amber street lights on the ground."""
    pts_warm = []
    for gx in np.arange(-2600 - 115, 2700, 230):
        z = np.arange(150, 9300, 45)
        P = np.stack([np.full_like(z, gx, dtype=float), np.zeros_like(z, dtype=float), z], -1)
        S, Z = cam.screen(P)
        ok = (Z > NEAR) & (Z < 9000)
        pts_warm.append((S[ok], Z[ok]))
    for gz in np.arange(200 - 115, 9300, 230):
        x = np.arange(-2700, 2700, 45)
        P = np.stack([x, np.zeros_like(x, dtype=float), np.full_like(x, gz, dtype=float)], -1)
        S, Z = cam.screen(P)
        ok = (Z > NEAR) & (Z < 9000)
        pts_warm.append((S[ok], Z[ok]))
    allS = np.concatenate([s for s, _ in pts_warm])
    allZ = np.concatenate([z for _, z in pts_warm])
    fade = np.exp(-allZ / 6000)
    for lv, c in enumerate([(90, 66, 34), (160, 118, 60), (230, 176, 96)]):
        m = np.digitize(fade, [0.35, 0.65]) == lv
        draw.point([tuple(p) for p in allS[m] * SS], fill=c)


def bez3(p0, p1, q, lift=260):
    c = (p0 + p1) / 2 + np.array([0, lift, 0])
    return (1 - q) ** 2 * p0 + 2 * (1 - q) * q * c + q * q * p1


def render_city(cam, lit_levels, sweeps=None):
    """Returns float32 RGB [0..1+] 1920x1080 and the landmark info list."""
    prisms, land, route = city()
    arr = np.zeros((SH, SW, 3), np.float32)
    draw_sky(arr, cam)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(img)
    draw_streets(draw, cam)
    eye = cam.pos
    order = sorted(prisms, key=lambda p: -np.linalg.norm(p.center - eye))
    wins = []
    for pr in order:
        # cheap frustum reject
        sc, z = cam.screen(pr.center)
        if z < -300 or (z > 0 and (sc[0] < -1200 or sc[0] > W + 1200)):
            continue
        lit = lit_levels[pr.landmark] if pr.landmark >= 0 else 0.0
        sweep = sweeps[pr.landmark] if (sweeps is not None and pr.landmark >= 0) else 1.0
        wp = []
        draw_prism(draw, cam, pr, CITY_ENV, lit=lit, lit_sweep=sweep, win_points=wp)
        draw_windows(draw, wp, cam, CITY_ENV)
        if lit > 0.01:  # gold edge light on the landmark silhouette
            for quad, nrm, w_, s_ in pr.faces:
                c = quad.mean(0)
                if np.dot(nrm, eye - c) <= 0:
                    continue
                pts, depth = poly_screen(cam, quad)
                if pts:
                    g = tuple(int(v * lit) for v in (255, 210, 130))
                    draw.line(pts + [pts[0]], fill=g, width=max(1, int(2 * SS)))
    out = np.asarray(img.resize((W, H), Image.LANCZOS), np.float32) / 255
    return out, land


# ------------------------------------------------------------------ the corridor of light
def corridor_quads():
    q = []
    wdt, hgt, L = 220, 300, 3200
    # walls (glass panels separated by light strips)
    for side in (-1, 1):
        x = side * wdt
        for z in np.arange(-200, L, 200):
            q.append(('wall', np.array([[x, 0, z], [x, 0, z + 190], [x, hgt, z + 190], [x, hgt, z]]), (22, 34, 62), False))
            q.append(('strip', np.array([[x - side * 1, 20, z + 192], [x - side * 1, 20, z + 198], [x - side * 1, hgt - 30, z + 198], [x - side * 1, hgt - 30, z + 192]]), (190, 206, 240), True))
    # ceiling and luminous panels
    q.append(('ceil', np.array([[-wdt, hgt, -200], [wdt, hgt, -200], [wdt, hgt, L], [-wdt, hgt, L]]), (14, 22, 42), False))
    for z in np.arange(0, L, 260):
        q.append(('panel', np.array([[-70, hgt - 1, z], [70, hgt - 1, z], [70, hgt - 1, z + 120], [-70, hgt - 1, z + 120]]), (235, 240, 255), True))
    # end wall with the doorway of light
    q.append(('end', np.array([[-wdt, 0, L], [wdt, 0, L], [wdt, hgt, L], [-wdt, hgt, L]]), (30, 40, 70), False))
    q.append(('door', np.array([[-80, 0, L - 1], [80, 0, L - 1], [80, 230, L - 1], [-80, 230, L - 1]]), (255, 222, 160), True))
    return q


COR_ENV = {'fog': (40, 48, 80), 'fog_dist': 2600}


def render_corridor(cam):
    arr = np.zeros((SH, SW, 3), np.float32)
    hy = cam.horizon_y() * SS
    y = np.arange(SH, dtype=np.float32)[:, None, None]
    arr[:] = np.where(y < hy, np.array([12, 18, 36], np.float32), np.array([16, 22, 40], np.float32))
    img = Image.fromarray(arr.astype(np.uint8))
    d = ImageDraw.Draw(img)
    quads = corridor_quads()
    # floor reflections: mirrored emissive quads, dimmed (glossy floor)
    refl = []
    for kind, P, col, emis in quads:
        if emis:
            M = P.copy()
            M[:, 1] = -M[:, 1]
            pts, depth = poly_screen(cam, M)
            if pts:
                k = 0.22 * math.exp(-depth / 1800)
                refl.append((depth, pts, tuple(int(c * k + 16 * (1 - k)) for c in col)))
    for depth, pts, col in sorted(refl, key=lambda r: -r[0]):
        d.polygon(pts, fill=col)
    items = []
    for kind, P, col, emis in quads:
        pts, depth = poly_screen(cam, P)
        if pts:
            items.append((depth, pts, col, emis, kind))
    items.sort(key=lambda r: -r[0])
    for depth, pts, col, emis, kind in items:
        if emis:
            k = math.exp(-depth / 5000)
            c = tuple(int(v * (0.55 + 0.45 * k)) for v in col)
        else:
            c = fogged(col, depth, COR_ENV['fog'], COR_ENV['fog_dist'])
        d.polygon(pts, fill=c)
    return np.asarray(img.resize((W, H), Image.LANCZOS), np.float32) / 255
