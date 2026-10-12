"""EUREKA — PASS THE LIGHT · The People Behind Excellence (120 s rough cut).

  python3 ptl_film.py stills 3 15 40 100 110 118
  python3 ptl_film.py video                  # -> build/ptl/EUREKA_PASS_THE_LIGHT_roughcut.mp4

Timeline (s)
  0-10    THE BEGINNING   Eureka reveal -> C1 ("Ready?") -> C2 ("Let's make it happen.") -> C6 walk
  10-24   PEOPLE          C4 nurse safety check, C5 assessment, C4 nurses' station  (+ narration 1)
  24-32   PASS THE LIGHT  C3 folder closes -> light ignites -> walk -> light lifts into the city
  32-92   TEN JOURNEYS    10 x 6 s milestone reveals (milestones.py)
  92-104  TOGETHER        real photo montage, "Every light tells a story" / "Together, we made it possible"
  104-115 THE 10          city converges -> giant 10, ten logos, GAHAR seal (+ narration 2)
  115-120 FINALE          Eureka logo, "Together, We Raise the Standard."
"""
import functools
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import milestones as MS  # noqa: E402
import poc2 as P2  # noqa: E402
from poc2 import R, S  # noqa: E402
from render import (GOLD, GOLD_HI, W, H, add_light, bloom, composite, ease_back, ease_io, ease_out, lerp, radial, seg,
                    splat, text_layer, tonemap, vignette)  # noqa: E402

FPS = 30
DUR = 120.0
BUILD = P2.BUILD
CLIPS = os.path.join(HERE, 'clips')
OUT = os.path.join(BUILD, 'EUREKA_PASS_THE_LIGHT_roughcut.mp4')

T_MS = 32.0          # milestones start
T_TOGETHER = 92.0
T_DROP = 104.0
T_HIT = 106.4
T_FINALE = 115.0


# ------------------------------------------------------------------ footage
@functools.lru_cache(maxsize=None)
def frames(name, slow=1.0):
    d = os.path.join(BUILD, 'frames', f'{name}_{slow:.2f}')
    os.makedirs(d, exist_ok=True)
    if not os.listdir(d):
        vf = f'fps={FPS},scale=1080:1920'
        if slow != 1.0:
            vf = f'minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:vsbmc=1,setpts={1 / slow:.4f}*PTS,' + vf
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(CLIPS, f'{name}.mp4'), '-vf', vf, '-q:v', '2',
                        os.path.join(d, 'f%04d.jpg')], check=True)
    return [os.path.join(d, f) for f in sorted(os.listdir(d))]


def clip_img(name, ct, slow=1.0):
    fr = frames(name, slow)
    return Image.open(fr[min(len(fr) - 1, max(0, int(round(ct * FPS))))]).convert('RGB')


@functools.lru_cache(maxsize=4)
def feather(w, h, f=180):
    x = np.arange(w, dtype=np.float32)
    a = np.clip(np.minimum(x, w - 1 - x) / f, 0, 1)
    a = a * a * (3 - 2 * a)
    y = np.arange(h, dtype=np.float32)
    b = np.clip(np.minimum(y, h - 1 - y) / 30, 0, 1)
    return (b[:, None] * a[None, :])[..., None]


def light_space(cv, t, warm=0.0, seed=0):
    """Elegant deep-navy space with drifting bokeh and a soft light leak (no repeated corridor)."""
    cv[:] = R.bg_navy() * 0.85
    add_light(cv, radial(W * (0.25 + 0.1 * math.sin(t * 0.3 + seed)), H * 0.3, 700), np.array([1.0, 0.72, 0.4]), 0.10 + 0.12 * warm)
    add_light(cv, radial(W * 0.85, H * 0.8, 600), np.array([0.35, 0.55, 1.0]), 0.08)
    R.DUST.draw(cv, t + seed * 5, 0.55)


def actor(cv, name, ct, cx, fade, push0=1.0, push1=1.04, prog=0.0, slow=1.0, grade_warm=0.0):
    """Vertical footage at full height, feathered into the environment (no borders, no blurred copy)."""
    push = lerp(push0, push1, prog)
    h = int(H * push)
    w = int(h * 9 / 16)
    img = np.asarray(clip_img(name, ct, slow).resize((w, h), Image.BICUBIC), np.float32) / 255
    img = img * 0.95 + np.array([0.01, 0.02, 0.05])
    if grade_warm:
        img = img * (1 + grade_warm * np.array([0.10, 0.03, -0.08]))
    x0, y0 = int(cx - w / 2), int(H / 2 - h / 2)
    a = feather(w, h) * fade
    r = R.region(x0, y0, w, h)
    if r:
        cv[r[0]] = cv[r[0]] * (1 - a[r[1]]) + img[r[1]] * a[r[1]]
    return x0, y0, w, h


def cine_crop(cv, name, ct, fade, fy=0.45, zoom=1.0, grade_warm=0.0):
    """Full-frame cinematic crop for medium-wide action shots (used briefly)."""
    im = clip_img(name, ct)
    fw, fh = im.size
    cw = fw / zoom
    ch = cw * 9 / 16
    top = max(0, min(fh - ch, fh * fy - ch / 2))
    arr = np.asarray(im.resize((W, H), Image.BICUBIC, box=(fw / 2 - cw / 2, top, fw / 2 + cw / 2, top + ch)), np.float32) / 255
    if grade_warm:
        arr = arr * (1 + grade_warm * np.array([0.12, 0.04, -0.10]))
    cv[:] = cv * (1 - fade) + arr * fade


def caption(cv, text, x, y, q, size=78, sub=None):
    o = ease_io(q)
    if o <= 0.01:
        return
    composite(cv, text_layer(text, 'cinzel', size, 700, 10, 'gold', 12), x, y + 14 * (1 - ease_out(q)), 1.0, o, glow=0.7)
    if sub:
        composite(cv, text_layer(sub, 'playfair', 42, 500, 0, 'ivory', 6), x, y + size * 0.95, 1.0, o, glow=0.3)


def shot_light_transition(cv, t, at, dur=0.35):
    q = seg(t, at - dur, at + dur)
    if 0 < q < 1:
        add_light(cv, R.streak(q, angle=-0.3), GOLD_HI, 0.7 * math.sin(math.pi * q))


# ------------------------------------------------------------------ scenes
def s1_beginning(cv, t):
    if t < 2.8:  # Eureka opening over a dawn city
        cam = S.Cam((S.city()[2][0][0] - 900, 1300 - 80 * t, S.city()[2][0][1] - 3800 + 120 * t), yaw=0.3, pitch=0.24, fov_deg=52)
        img, _ = S.render_city(cam, [0.0] * 10)
        cv[:] = img * (0.35 + 0.25 * seg(t, 0, 2.8))
        cv *= ease_io(seg(t, 0, 0.9))
        return
    if t < 4.1:  # C1: picks up the plan, looks to her colleague   ("Ready?")
        light_space(cv, t, 0.6)
        actor(cv, 'C1_ready', 0.0 + (t - 2.8), 1250, seg(t, 2.8, 3.1), prog=seg(t, 2.8, 4.1))
        return
    if t < 6.6:  # C2 (0.6x): he looks up and smiles   ("Let's make it happen.")
        light_space(cv, t, 0.8, seed=1)
        actor(cv, 'C2_lets_make_it_happen', t - 4.1, 680, seg(t, 4.1, 4.4), prog=seg(t, 4.1, 6.6), slow=0.6)
        shot_light_transition(cv, t, 4.1)
        return
    # C6: walk through the sunlit atrium to the doors -> cinematic full-frame
    light_space(cv, t, 1.0, seed=2)
    ct = 0.2 + (t - 6.6)
    cine_crop(cv, 'C6_door_walk', ct, seg(t, 6.6, 7.0), fy=0.5, zoom=1.0, grade_warm=0.8)
    shot_light_transition(cv, t, 6.6)
    if t > 9.4:
        add_light(cv, radial(W / 2, H * 0.45, 800) * 0.6 + 0.4, np.array([1.0, 0.85, 0.6]), 0.9 * seg(t, 9.4, 10.0) ** 2)


S2_SHOTS = [  # (start, end, clip, clip_in, x)
    (10.0, 14.6, 'C4_safety_check', 0.4, 1260),
    (14.6, 19.2, 'C5_assessment_plan', 0.4, 660),
    (19.2, 24.0, 'C4_safety_check', 5.3, 1260),
]


def s2_people(cv, t):
    for a, b, name, cin, x in S2_SHOTS:
        if a <= t < b:
            light_space(cv, t, 0.5, seed=int(a))
            actor(cv, name, cin + (t - a), x, seg(t, a, a + 0.35), prog=seg(t, a, b))
            shot_light_transition(cv, t, a)
            if a == 10.0:
                add_light(cv, radial(W / 2, H / 2, 900) * 0.6 + 0.4, np.array([1.0, 0.85, 0.6]), 0.8 * math.exp(-(t - 10.0) / 0.3))
    # the people the narration speaks of: one quiet line of text in the open space
    for a, b, text, x in [(11.2, 14.4, 'PEOPLE WHO BELIEVE', 560), (15.6, 19.0, 'TEAMS WHO WORK', 1300),
                          (20.2, 23.6, 'PARTNERS IN EXCELLENCE', 560)]:
        if a <= t < b:
            caption(cv, text, x, 520, seg(t, a, a + 0.6) * (1 - seg(t, b - 0.4, b)), size=58)


FOLDER_A = [(2.4, 0.50, 0.80), (2.8, 0.53, 0.80), (3.2, 0.56, 0.81), (3.8, 0.58, 0.84)]
FOLDER_B = [(5.0, 0.54, 0.58), (5.2, 0.54, 0.60), (5.6, 0.52, 0.65), (6.0, 0.555, 0.77), (6.4, 0.69, 0.83), (6.9, 0.66, 0.92)]


def _folder(keys, ct, geo):
    x0, y0, w, h = geo
    ts = [k[0] for k in keys]
    return x0 + float(np.interp(ct, ts, [k[1] for k in keys])) * w, y0 + float(np.interp(ct, ts, [k[2] for k in keys])) * h


def s3_pass_the_light(cv, t):
    if t < 26.4:  # C3 shot A: closes the folder -> the light ignites
        light_space(cv, t, 0.9, seed=3)
        ct = 1.4 + (t - 24.0)
        geo = actor(cv, 'C3_file_pass', ct, 1250, seg(t, 24.0, 24.3), prog=seg(t, 24.0, 26.4))
        shot_light_transition(cv, t, 24.0)
        if ct > 2.5:
            x, y = _folder(FOLDER_A, ct, geo)
            k = ease_out(seg(ct, 2.5, 2.9))
            add_light(cv, radial(x, y, 140), np.array([1.0, 0.74, 0.38]), 0.6 * k)
            splat(cv, x, y, 6, 1.2 * k)
            if ct < 2.9:
                add_light(cv, radial(x, y, 300), np.array([1.0, 0.8, 0.5]), 0.6 * math.sin(math.pi * seg(ct, 2.5, 2.9)))
        caption(cv, 'PASS THE LIGHT', 560, 470, seg(t, 24.6, 25.3), size=84, sub='The People Behind Excellence')
        return
    if t < 28.6:  # C3 shot B: walks with the glowing folder
        light_space(cv, t, 0.9, seed=4)
        ct = min(6.9, 5.0 + (t - 26.4))
        geo = actor(cv, 'C3_file_pass', ct, 1250, 1.0, push0=1.03, push1=1.07, prog=seg(t, 26.4, 28.6))
        x, y = _folder(FOLDER_B, ct, geo)
        add_light(cv, radial(x, y, 120), np.array([1.0, 0.74, 0.38]), 0.5)
        splat(cv, x, y, 5, 1.0)
        caption(cv, 'PASS THE LIGHT', 560, 470, 1 - seg(t, 27.6, 28.3), size=84, sub='The People Behind Excellence')
        if t > 28.0:  # the light lifts off and flies out of frame, towards the city
            q = ease_io(seg(t, 28.0, 28.6))
            for k in range(20, -1, -1):
                qq = max(0.0, q - k * 0.02)
                splat(cv, lerp(x, -100, qq), lerp(y, 120, qq) - 240 * math.sin(math.pi * qq), 3 + (7 if k == 0 else 0),
                      1.4 if k == 0 else 0.5 * (1 - k / 21))
        return
    # 28.6-32: the City of Excellence, ten towers waiting; text
    u = t - 28.6
    _, land, route = S.city()
    cam = S.Cam((route[4][0] - 1700 + 120 * u, 1500 - 60 * u, route[0][1] - 2600 + 160 * u), yaw=0.42, pitch=0.30, fov_deg=55)
    img, _ = S.render_city(cam, [0.0] * 10)
    cv[:] = img
    for L in land:  # ten waiting beacons
        sp, zz = cam.screen((L['x'], L['spire'], L['z']))
        if zz > 5:
            splat(cv, sp[0], sp[1], 3, 0.5 + 0.3 * math.sin(t * 3 + L['x']))
    add_light(cv, radial(W / 2, H / 2, 900) * 0.6 + 0.4, np.array([1.0, 0.82, 0.55]), 0.5 * math.exp(-u / 0.3))
    caption(cv, 'EXCELLENCE IS NEVER ACHIEVED ALONE.', W / 2, 900, seg(t, 29.2, 29.9) * (1 - seg(t, 31.4, 31.9)), size=52)


def s4_milestones(cv, t):
    k = min(9, int((t - T_MS) // MS.SLOT))
    MS.milestone(cv, t - T_MS - k * MS.SLOT, k, R.manifest()['institutions'][k], k)


@functools.lru_cache(maxsize=1)
def montage_pool():
    m = R.manifest()
    pool = list(m['team_photos'])
    for inst in m['institutions']:
        pool += [p for p in inst['photos'][3:] + inst['photos'][:1] if p not in pool]
    return [p for p in pool if not R.is_portrait(p, 1.1)] + [p for p in pool if R.is_portrait(p, 1.1)]


def s5_together(cv, t):
    """Fast, elegant cuts of real photos; full-frame for landscape, feathered for portrait."""
    u = t - T_TOGETHER
    step = 0.95
    k = int(u / step)
    pool = montage_pool()
    path = pool[k % len(pool)]
    q = (u - k * step) / step
    if R.is_portrait(path, 1.1):
        light_space(cv, t, 0.7, seed=k)
        pw, ph = R.contain(path, 1200, 1080)
        arr = R.photo_crop(path, pw, ph, q, seed=k, zoom=0.05)
        x0 = (W - pw) // 2 + (260 if k % 2 else -260)
        a = feather(pw, ph, 120)
        r = R.region(x0, 0, pw, ph)
        cv[r[0]] = cv[r[0]] * (1 - a[r[1]]) + arr[r[1]] * a[r[1]]
    else:
        cv[:] = R.photo_crop(path, W, H, q, seed=k, zoom=0.08) * 0.9
    cv *= vignette(0.6)
    add_light(cv, R.streak(q, angle=-0.3 if k % 2 else -2.8), GOLD_HI, 0.25)
    add_light(cv, radial(W / 2, H / 2, 900) * 0.6 + 0.4, np.array([1.0, 0.85, 0.6]), 0.25 * math.exp(-(u - k * step) / 0.08))
    for a, b, text in [(93.0, 97.6, 'EVERY LIGHT TELLS A STORY.'), (98.4, 103.6, 'TOGETHER, WE MADE IT POSSIBLE.')]:
        if a <= t < b:
            o = seg(t, a, a + 0.6) * (1 - seg(t, b - 0.4, b))
            yy = np.exp(-((np.arange(H) - 900) / 90.0) ** 4)
            cv *= (1 - 0.55 * o * yy)[:, None, None]
            caption(cv, text, W / 2, 900, o, size=70)


CONF_RAIN = R.Confetti(260, 141, T_HIT - 0.2, 'rain')
CONF_CANNON = R.Confetti(220, 142, T_HIT, 'cannon')


def ring_positions():
    pos = []
    for side in (-1, 1):
        for k in range(5):
            pos.append((W / 2 + side * (680 + 60 * math.cos((k - 2) / 2 * 1.2)), 255 + k * 176))  # clear of the corner logo
    order = [0, 5, 1, 6, 2, 7, 3, 8, 4, 9]
    return [pos[o] for o in order]


def s6_the_ten(cv, t):
    _, land, route = S.city()
    cam = S.Cam((route[4][0] - 2300, 2100, route[0][1] - 3400), yaw=0.36, pitch=0.36, fov_deg=55)
    img, _ = S.render_city(cam, [1.0] * 10)
    cv[:] = img * (0.7 if t < T_HIT else 0.38)
    center = (W / 2, 370)
    if t < T_HIT:  # all ten lights stream to the centre
        p = seg(t, T_DROP, T_HIT)
        for L in land:
            sp, zz = cam.screen((L['x'], L['spire'], L['z']))
            for j in range(16):
                q = p * 1.5 - j * 0.04
                if 0 < q < 1:
                    e = q ** 1.6
                    c = ((sp[0] + center[0]) / 2, min(sp[1], center[1]) - 240)
                    x = (1 - e) ** 2 * sp[0] + 2 * (1 - e) * e * c[0] + e * e * center[0]
                    y = (1 - e) ** 2 * sp[1] + 2 * (1 - e) * e * c[1] + e * e * center[1]
                    splat(cv, x, y, 3 if j == 0 else 2, 1.0 - j * 0.05)
            add_light(cv, radial(sp[0], sp[1], 90), GOLD_HI, 0.6 * (1 - p))
        splat(cv, *center, 4 + 26 * p ** 3, 0.3 + 1.5 * p ** 2)
        add_light(cv, radial(*center, 60 + 320 * p ** 2), GOLD_HI, 0.6 * p ** 2)
        return
    u = t - T_HIT
    beat = (u % 0.55) / 0.55
    add_light(cv, R.rays(*center, t, n=22, speed=0.05, sharp=5, reach=1100), GOLD_HI, 0.38 + 0.18 * math.exp(-beat * 4) + 0.6 * math.exp(-u / 0.5))
    rp = ease_out(seg(u, 0, 0.9))
    if 0 < rp < 1:
        dd = np.sqrt((R._lx - center[0]) ** 2 + (R._ly - center[1]) ** 2)
        add_light(cv, np.exp(-((dd - rp * 1500) / 50) ** 2), R.WARM_WHITE, 1.0 * (1 - rp))
    yy = np.exp(-((np.arange(H) - 790) / 130.0) ** 4)
    cv *= (1 - 0.45 * yy)[:, None, None]
    R.DUST.draw(cv, t, 1.0)
    for (fx, fy, ft, fs) in [(470, 250, T_HIT + 0.2, 1), (1450, 230, T_HIT + 0.45, 2), (960, 110, T_HIT + 2.4, 3),
                             (330, 520, T_HIT + 4.6, 4), (1590, 520, T_HIT + 6.2, 5)]:
        R.firework(cv, t, ft, fx, fy, fs, n=60)
    CONF_RAIN.draw(cv, t)
    CONF_CANNON.draw(cv, t)
    ten = text_layer('10', 'cinzel', 600, 900, 0, 'gold', 30)
    q = seg(u, 0, 0.55)
    shine = next((seg(u, a, a + 0.9) for a in (0.7, 3.4, 6.2) if a < u < a + 0.9), None)
    composite(cv, ten, *center, lerp(1.6, 1.0, ease_out(q)) * (1 + 0.015 * math.exp(-beat * 5) * (u > 0.6)), seg(u, 0, 0.12),
              glow=0.8 + 0.4 * math.exp(-beat * 4), shine=shine)
    q1, q2 = seg(u, 0.8, 1.3), seg(u, 1.05, 1.55)
    composite(cv, text_layer('GAHAR ACCREDITATION', 'cinzel', 66, 700, 10, 'gold', 12), W / 2, 735 + 20 * (1 - ease_out(q1)), 1.0, ease_io(q1), glow=0.9)
    composite(cv, text_layer('ACHIEVEMENTS', 'cinzel', 66, 700, 22, 'gold', 12), W / 2, 822 + 20 * (1 - ease_out(q2)), 1.0, ease_io(q2), glow=0.9)
    seal = R.seal_layer(150)
    qs = seg(u, 2.0, 2.4)
    composite(cv, seal, W / 2, 965, 0.6 + 0.4 * ease_back(qs), qs, glow=0.5 + 0.8 * math.exp(-max(0, u - 2.0) / 0.3))
    for k, ((x, y), inst) in enumerate(zip(ring_positions(), R.manifest()['institutions'])):
        s = 0.9 + k * 0.42
        if u < s:
            continue
        qk = seg(u, s, s + 0.32)
        y += 6 * math.sin(t * 1.6 + k)
        composite(cv, R.inst_card(inst, 310, 172, pad_frac=0.08, radius=16, frame=3), x, y, 0.5 + 0.5 * ease_back(qk),
                  seg(u, s, s + 0.12), glow=0.3 + 0.9 * math.exp(-(u - s) / 0.25))
        if inst.get('branch'):
            composite(cv, R.branch_tag(inst['branch']), x, y + 86, 1.0, seg(u, s + 0.1, s + 0.35), glow=0)
    add_light(cv, radial(W / 2, H / 2, 900) * 0.6 + 0.4, np.array([1.0, 0.85, 0.6]), 1.2 * math.exp(-u / 0.18))


def s7_finale(cv, t):
    u = t - T_FINALE
    light_space(cv, t, 0.6, seed=7)
    add_light(cv, R.rays(W / 2, 330, t, n=16, speed=0.04, reach=900), GOLD_HI, 0.22)
    q = seg(u, 0.0, 1.0)
    composite(cv, P2.eureka_layer(600), W / 2, 330, lerp(0.92, 1.0, ease_out(q)), ease_io(seg(u, 0, 0.5)), glow=0)
    caption(cv, 'TOGETHER, WE RAISE THE STANDARD.', W / 2, 730, seg(u, 0.9, 1.6), size=68)
    q3 = seg(u, 1.8, 2.5)
    composite(cv, text_layer('10 Achievements. One Vision. Endless Possibilities.', 'playfair', 44, 500, 0, 'ivory', 6),
              W / 2, 860, 1.0, ease_io(q3), glow=0.3)
    add_light(cv, radial(W / 2, H / 2, 900) * 0.6 + 0.4, np.array([1.0, 0.85, 0.6]), 0.6 * math.exp(-u / 0.25))
    cv *= 1 - seg(t, DUR - 0.9, DUR)


def corner_logo(cv, t):
    """Permanent Eureka branding: big at the opening (P2.eureka), corner throughout, big again at the finale."""
    if t < 2.8:
        P2.eureka(cv, t * (2.4 / 2.8))
    elif t < T_FINALE - 0.3:
        P2.eureka(cv, 99.0)
    elif t < T_FINALE:
        o = 1 - seg(t, T_FINALE - 0.3, T_FINALE)
        tmp = cv.copy()
        P2.eureka(tmp, 99.0)
        cv[:] = cv * (1 - o) + tmp * o


def frame(t):
    cv = np.zeros((H, W, 3), np.float32)
    if t < 10.0:
        s1_beginning(cv, t)
    elif t < 24.0:
        s2_people(cv, t)
    elif t < T_MS:
        s3_pass_the_light(cv, t)
    elif t < T_TOGETHER:
        s4_milestones(cv, t)
    elif t < T_DROP:
        s5_together(cv, t)
    elif t < T_FINALE:
        s6_the_ten(cv, t)
    else:
        s7_finale(cv, t)
    bloom(cv, 0.24, 0.8)
    cv *= vignette(0.38)
    corner_logo(cv, t)
    return tonemap(cv)


# ------------------------------------------------------------------ output
def _chunk(args):
    a, b, path = args
    pr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', path],
                          stdin=subprocess.PIPE)
    for f in range(a, b):
        pr.stdin.write(frame(f / FPS).tobytes())
    pr.stdin.close()
    pr.wait()
    return path


def render_video(out=OUT):
    for name, slow in [('C1_ready', 1.0), ('C2_lets_make_it_happen', 0.6), ('C3_file_pass', 1.0), ('C4_safety_check', 1.0),
                       ('C5_assessment_plan', 1.0), ('C6_door_walk', 1.0)]:
        frames(name, slow)
    d = os.path.join(BUILD, 'film_chunks')
    os.makedirs(d, exist_ok=True)
    nf = int(DUR * FPS)
    jobs = [(a, min(nf, a + 60), os.path.join(d, f'c{a:05d}.mp4')) for a in range(0, nf, 60)]
    with Pool(4) as p:
        for k, _ in enumerate(p.imap(_chunk, jobs)):
            print(f'chunk {k + 1}/{len(jobs)}', flush=True)
    lst = os.path.join(d, 'list.txt')
    open(lst, 'w').writelines(f"file '{j[2]}'\n" for j in jobs)
    silent = os.path.join(BUILD, 'film_video.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', silent], check=True)
    music = os.path.join(BUILD, 'film_music.wav')
    subprocess.run([sys.executable, os.path.join(HERE, 'music_ptl.py'), music], check=True)
    # voices: "Ready?" (Actor 1), "Let's make it happen." (Actor 2, from C2), narration lines 1 and 2
    au = os.path.join(HERE, 'audio')
    v = [('ready.mp3', 0, None, 3.55), (os.path.join(CLIPS, 'C2_lets_make_it_happen.mp4'), 0, None, 4.75),
         ('narration.mp3', 0.0, 8.45, 11.0), ('narration.mp3', 8.6, 12.4, 107.4)]
    inputs, chains, labels = ['-i', silent, '-i', music], [], []
    for k, (f, a, b, at) in enumerate(v):
        inputs += ['-i', f if os.path.isabs(f) else os.path.join(au, f)]
        trim = f'atrim={a}:{b},' if b else ''
        chains.append(f'[{k + 2}:a]{trim}asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,'
                      f'volume=1.7,adelay={int(at * 1000)}|{int(at * 1000)},apad[v{k}]')
        labels.append(f'[v{k}]')
    filt = ';'.join(chains) + f";{''.join(labels)}amix=inputs={len(v)}:normalize=0,asplit=2[vx][vy];" \
        "[1:a][vx]sidechaincompress=threshold=0.02:ratio=5:attack=30:release=500[m];[m][vy]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]"
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', filt, '-map', '0:v', '-map', '[a]',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-t', str(DUR), '-movflags', '+faststart', out], check=True)
    print('wrote', out)


if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        for s in sys.argv[2:]:
            Image.fromarray(frame(float(s))).save(os.path.join(BUILD, f'film_{float(s):06.2f}.png'))
    else:
        render_video()
