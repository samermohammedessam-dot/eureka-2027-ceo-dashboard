"""EUREKA — THE MOMENT v2 (about 139 s, 1920x1080, 30 fps). Timeline in tl.py.

  python3 moment_v2.py stills 20 45 ...
  python3 moment_v2.py cut [t0 t1]     # -> EUREKA_THE_MOMENT_v2_FINAL.mp4 (+ cached chunks in build/moment/chunks_v2)

Revision: no narration, a visual bridge from Archimedes' problem to healthcare's, services shown only with
relevant actor footage (no unrelated photos), a longer ten-GAHAR moment with iVein branch labels, and an
institutional wall built only from the approved uploaded logos (assets_logos/logos.json).
"""
import functools
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import moment_film as M  # noqa: E402  (approved scenes and helpers)
import tl  # noqa: E402
from moment_film import (GOLD, NAVY, WARM, H, W, FPS, PF, R, ST, composite, draw_lines, ease_io, ease_out,  # noqa: E402
                         grade_warm, hline, lerp, panel, plate, quiet, seg, text, text_layer, tonemap)

DUR = tl.DUR

_plate_frame = M.plate_frame


def _plate_frame_v2(name, t):
    """Inside the shout, use the wide re-performance (same audio) when its upscaled plate exists."""
    if name == 'arch' and tl.EUREKA_AT <= t < tl.T_GOLD and plate('A4w_win') is not None:
        return _plate_frame('A4w_win', t - tl.EUREKA_AT)
    return _plate_frame(name, t)


M.plate_frame = _plate_frame_v2
BUILD = M.BUILD
LOGOS = os.path.join(M.ROOT, 'assets_logos')
STEEL = np.array([0.45, 0.62, 0.85], np.float32)

SERVICES = [  # title lines, descriptor, two actor panels (clip, in-point); a new clip replaces its fallback if present
    (('HEALTHCARE STRATEGY', '& BUSINESS DEVELOPMENT'), 'Strategy, growth and the decisions that shape institutions',
     [('H3_strategy', 4.3), ('H8_business', 0.5)]),
    (('ACCREDITATION', '& QUALITY EXCELLENCE'), 'Accreditation readiness, patient safety and clinical governance',
     [('H2_accreditation', 0.4), ('Q2_quality@0.3|H2_accreditation@4.6', 0)]),
    (('TURNKEY', 'HEALTHCARE PROJECTS'), 'From planning and design to operational readiness and launch',
     [('T2_turnkey@0.4|H5_turnkey@5.0', 0), ('H5_turnkey', 0.5)]),
    (('TRAINING &', 'ORGANIZATIONAL DEVELOPMENT'), 'Skills, leadership and teams built for excellence',
     [('H4_training', 0.4), ('H7_orgdev', 2.8)]),
    (('OPERATIONS &', 'PERFORMANCE IMPROVEMENT'), 'Patient journeys, clinical workflow and efficient service delivery',
     [('H6_operations', 0.5), ('O2_operations@0.3|H6_operations@5.2', 0)]),
]


def clip(spec, c0=0.0):
    """'NEW@in|FALLBACK@in' -> (clip, in-point): the new clip if its plate exists, else the approved fallback."""
    opts = []
    for part in spec.split('|'):
        name, _, at = part.partition('@')
        opts.append((name, float(at) if at else c0))
    for name, at in opts:
        if plate(name) is not None:
            return name, at
    return opts[-1]


# ------------------------------------------------------------------ 2  THE BRIDGE (problem -> solution)
@functools.lru_cache(maxsize=1)
def tangle():
    rng = np.random.default_rng(21)
    return [np.cumsum(rng.normal(0, 38, (26, 2)), axis=0) + rng.uniform([120, 160], [900, 920]) for _ in range(26)]


def s2_bridge(cv, t):
    u = t - tl.T_BRIDGE
    if u < 2.4 or u > 6.4:
        corner = M.s2_purpose(cv, t)        # ripples + "EUREKA — I have found it"; then geometry -> blueprint -> hospital -> logo
        if u < 2.4:
            cv *= 1 - 0.85 * seg(u, 2.0, 2.4)
        return corner
    # 2.4-6.4: a healthcare leader facing complexity; tangled steel-blue lines; the insight straightens them into gold
    cv[:] = NAVY * 0.9
    insight = seg(u, 4.9, 5.7)
    fade_in = ease_out(seg(u, 2.4, 2.9))
    lead, c0 = clip('C1_insight@0.3|H3_strategy@0.5')
    panel(cv, lead, c0 + (u - 2.4), 1400, 540, 0.9, ease_out(seg(u, 2.4, 2.9)))
    cv[:, 1100:] *= (1 - 0.35 * (1 - insight))                         # cool, uncertain until the insight
    cv[:, 1100:] = cv[:, 1100:] * (1 - 0.25 * (1 - insight)) + cv[:, 1100:].mean(axis=2, keepdims=True) * STEEL * 0.25 * (1 - insight)
    pts, edges, _ = M.geometry_nodes()
    segs = []
    for k, path in enumerate(tangle()):
        n = int(np.clip((u - 2.5) * 10, 2, len(path)))
        ia, ib = edges[k % len(edges)]
        pa, pb = (pts[ia] * np.array([0.52, 1.0]) - [40, 0]), (pts[ib] * np.array([0.52, 1.0]) - [40, 0])
        tgt = pa + (pb - pa) * np.linspace(0, 1, n)[:, None]        # each tangle straightens into one clean connection
        p = path[:n] * (1 - insight) + tgt * insight
        for a, b in zip(p[:-1], p[1:]):
            segs.append((a[0], a[1], b[0], b[1], 0.7))
    col = STEEL * (1 - insight) + GOLD * insight
    cv += draw_lines(segs, 2)[..., None] * col * 0.55 + draw_lines(segs, 6, 5)[..., None] * col * 0.25
    q = seg(u, 2.8, 3.4) * (1 - seg(u, 4.7, 5.1))
    for j, s in enumerate(['COMPLEX DECISIONS', 'OPERATIONAL PRESSURE', 'ACCREDITATION DEMANDS']):
        qq = seg(u, 2.9 + 0.35 * j, 3.4 + 0.35 * j) * (1 - seg(u, 4.7, 5.1))
        text(cv, s, 520, 430 + 70 * j, 34, 'mont', 'ivory', ease_io(qq) * 0.85, 10, 0.1, 600)
    q2 = seg(u, 5.2, 5.8)
    text(cv, 'EVERY CHALLENGE HAS A SOLUTION', 520, 540, 40, 'cinzel', 'gold', ease_io(q2) * (1 - seg(u, 6.1, 6.4)), 8, 0.5)
    PF.glow(cv, 1400, 360, 500, GOLD, 0.55 * math.exp(-max(0, u - 5.0) / 0.4) * (u > 4.9))   # the insight flash, restrained
    cv *= 0.15 + 0.85 * fade_in
    _ = q
    return True


# ------------------------------------------------------------------ 3  WHO WE ARE (10 s)
def s3_who(cv, t):
    u = t - tl.T_WHO
    return M.s3_who(cv, M.T_WHO + u if u < 5 else M.T_WHO + 10 + u)


# ------------------------------------------------------------------ 4  WHAT WE DO: two relevant actor panels per service
def s4_what(cv, t):
    u = t - tl.T_WHAT
    cv[:] = NAVY * 0.85
    grid = (((np.arange(W) % 80) < 1)[None, :] | ((np.arange(H) % 80) < 1)[:, None]).astype(np.float32)
    cv += grid[..., None] * STEEL * 0.035
    PF.glow(cv, 430, 520, 700, GOLD, 0.12)
    if u < 1.5:
        q = seg(u, 0.1, 0.7) * (1 - seg(u, 1.2, 1.5))
        text(cv, 'WHAT WE DO', W / 2, 520, 96, 'cinzel', 'gold', ease_io(q), 18, 0.6, shine=seg(u, 0.3, 1.2) if u > 0.3 else None)
        hline(cv, W / 2, 600, 420 * ease_out(seg(u, 0.3, 1.0)), q)
        return True
    k = min(tl.SV_N - 1, int((t - tl.SV_T0) // tl.SV_DUR))
    v = t - tl.SV_T0 - k * tl.SV_DUR
    (l1, l2), desc, clips = SERVICES[k]
    for j, (spec, c0) in enumerate(clips):
        qq = ease_out(seg(v, 0.05 + 0.25 * j, 0.6 + 0.25 * j))
        x = 1090 + j * 480
        name, at = clip(spec, c0)
        panel(cv, name, at + v, x + 60 * (1 - qq), 585, 0.74, qq)
    q = seg(v, 0.2, 0.8)
    text(cv, f'0{k + 1}', 430, 380, 40, 'mont', 'gold', ease_io(q), 10, 0.3, 600)
    for j, (ln, yy, a0) in enumerate([(l1, 460, 0.2), (l2, 530, 0.32)]):
        lay = text_layer(ln, 'cinzel', 52, 700, 5, 'ivory', 8)
        qq = seg(v, a0, a0 + 0.6)
        composite(cv, lay, 430, yy + 12 * (1 - ease_out(qq)), min(1.0, 720 / lay.w), ease_io(qq), glow=0.3)
    hline(cv, 430, 595, 300 * ease_out(seg(v, 0.5, 1.2)), q)
    lay = text_layer(desc, 'mont', 27, 500, 2, 'ivory', 4)
    composite(cv, lay, 430, 650, min(1.0, 720 / lay.w), ease_io(seg(v, 0.7, 1.3)), glow=0.1)
    M.streak_wipe(cv, seg(v, tl.SV_DUR - 0.5, tl.SV_DUR + 0.2), GOLD, 0.45)
    if k == tl.SV_N - 1:
        cv *= 1 - seg(v, tl.SV_DUR - 0.35, tl.SV_DUR)
    return True


# ------------------------------------------------------------------ 5  OUR IMPACT (the ten GAHAR achievements get the big moment)
@functools.lru_cache(maxsize=1)
def branch_tags():
    return [R.branch_tag(i['branch']) if i.get('branch') else None for i in PF.insts()]


def gahar_ring(cv, v, t):
    cards = M.ten_cards()
    for j, ((x, y), card, tag) in enumerate(zip(PF.ring_positions(), cards, branch_tags())):
        q = seg(v, 0.3 + 0.16 * j, 0.8 + 0.16 * j)
        s = 0.82 * (0.85 + 0.15 * ease_out(q))
        composite(cv, card, x, y, s, ease_io(q), glow=0.12, shine=seg(v, 0.6 + 0.16 * j, 1.4 + 0.16 * j) if 0.6 + 0.16 * j < v < 1.4 + 0.16 * j else None)
        if tag is not None:
            composite(cv, tag, x + 70, y + 60, 0.8, ease_io(q), glow=0)
    composite(cv, PF.seal(160), W / 2, 930, 1.0, ease_io(seg(v, 2.2, 2.8)), glow=0.25)
    ST.add(cv, R.rays(W / 2, 400, t, n=18, speed=0.05, reach=1000), GOLD, 0.16 * seg(v, 1.8, 2.6))


def s5_impact(cv, t):
    u = t - tl.T_IMPACT
    if u < 2.0:
        cv[:] = NAVY
        PF.glow(cv, W / 2, H / 2, 900, GOLD, 0.3 * seg(u, 0, 1.0))
        ST.add(cv, R.rays(W / 2, H / 2, t, n=16, speed=0.05, reach=1100), GOLD, 0.18 * seg(u, 0.2, 1.2))
        q = seg(u, 0.15, 0.8) * (1 - seg(u, 1.6, 2.0))
        text(cv, 'OUR IMPACT', W / 2, 520, 110, 'cinzel', 'gold', ease_io(q), 20, 0.7, shine=seg(u, 0.5, 1.5) if u > 0.5 else None)
        return True
    starts = tl.imp_starts()
    k = max(i for i, s in enumerate(starts) if t >= s)
    v, dur = t - starts[k], tl.IMP_DURS[k]
    val, suf, label, (kind, arg) = M.FIGURES[k]
    cv[:] = NAVY
    if kind == 'photo':
        PX = 760
        arr = grade_warm(R.photo_crop(arg, W - PX, H, seg(v, 0, dur), seed=31 + k, zoom=0.10) * 0.78, 0.8)
        ramp = np.clip(np.arange(W - PX, dtype=np.float32) / 380, 0, 1) ** 1.6
        cv[:, PX:] = cv[:, PX:] * (1 - ramp[None, :, None]) + arr * ramp[None, :, None]
    elif kind == 'points':
        PF.glow(cv, W * 0.66, H * 0.48, 800, np.array([0.3, 0.45, 0.8], np.float32), 0.25)
        M.points_constellation(cv, arg, v, 40 + k)
    else:
        PF.glow(cv, W / 2, H / 2, 900, GOLD, 0.25)
        gahar_ring(cv, v, t)
    ST.add(cv, R.streak(seg(v, 0.1, 1.2), angle=-0.18, width=0.05), GOLD, 0.6 * math.sin(math.pi * seg(v, 0.1, 1.2)))
    centre = kind == 'logos'
    n = M.counter_value(v, val)
    x, num_y = (W / 2, 420) if centre else (420, 470)
    q = seg(v, 0.2, 0.6)
    s = M.fmt(n) + (suf if n >= val else '')
    text(cv, s, x, num_y, 250 if centre else 190, 'cinzel', 'gold', ease_io(q), 6, 0.8, shine=seg(v, 1.7, 2.6) if v > 1.7 else None)
    hline(cv, x, num_y + 150, 360 * ease_out(seg(v, 1.2, 1.9)), q)
    ql = seg(v, 0.9, 1.5)
    if centre:
        text(cv, 'GAHAR ACCREDITATION', x, 630, 46, 'cinzel', 'ivory', ease_io(ql), 12, 0.3)
        text(cv, 'ACHIEVEMENTS', x, 695, 46, 'cinzel', 'ivory', ease_io(ql), 12, 0.3)
    else:
        words = label.split(' ')
        mid = (len(words) + 1) // 2 if len(label) > 22 else len(words)
        text(cv, ' '.join(words[:mid]), x, num_y + 210, 38, 'cinzel', 'ivory', ease_io(ql), 8, 0.3)
        if mid < len(words):
            text(cv, ' '.join(words[mid:]), x, num_y + 262, 38, 'cinzel', 'ivory', ease_io(ql), 8, 0.3)
    if tl.LAND - 0.05 < v < tl.LAND + 1.0:
        R.firework(cv, v, tl.LAND, x + (0 if centre else 200), num_y - 60, 90 + k, n=60 if centre else 40, life=1.0, speed=420 if centre else 380)
    if k < len(starts) - 1:
        cv *= 1 - 0.7 * seg(v, dur - 0.3, dur)
    else:
        cv *= 1 - seg(v, dur - 0.4, dur)
    return not centre


# ------------------------------------------------------------------ 6  PEOPLE (9 s)
def s6_people(cv, t):
    u = t - tl.T_PEOPLE
    return M.s6_people(cv, M.T_PEOPLE + u * 12.0 / 9.0)


# ------------------------------------------------------------------ 7  TRUSTED BY HEALTHCARE LEADERS (approved upload only)
def plaque_card(path, w, h, radius=22, frame=4):
    """Gold-framed card filled with the logo's OWN background colour, so each original logo appears exactly as
    designed (no recolouring, no reshaping; only uniform scaling)."""
    from PIL import ImageDraw, ImageFilter
    logo, bg = R.logo_image(path)
    fill = tuple(bg) if bg is not None else (255, 255, 255)
    m = 40
    card = Image.new('RGBA', (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((m, m, m + w, m + h), radius, fill=(222, 186, 104, 255))
    d.rounded_rectangle((m + frame, m + frame, m + w - frame, m + h - frame), radius - 3, fill=fill + (255,))
    pad = int(min(w, h) * 0.10) + frame + 6
    s = min((w - 2 * pad) / logo.width, (h - 2 * pad) / logo.height)
    lw, lh = max(1, int(logo.width * s)), max(1, int(logo.height * s))
    card.alpha_composite(logo.resize((lw, lh), Image.LANCZOS), (m + (w - lw) // 2, m + (h - lh) // 2))
    glow = Image.new('L', card.size, 0)
    ImageDraw.Draw(glow).rounded_rectangle((m, m, m + w, m + h), radius, fill=255)
    return R.Layer(card, glow.filter(ImageFilter.GaussianBlur(18)))


@functools.lru_cache(maxsize=1)
def wall_logos():
    p = os.path.join(LOGOS, 'logos.json')
    new = json.load(open(p))['logos'] if os.path.exists(p) else []
    new = [(e['name'], os.path.join(LOGOS, e['file'])) for e in new]
    seen, gahar = set(), []
    for inst in PF.insts():                       # the GAHAR institutions, each once (no branch labels here)
        if inst['logo'] and inst['name'] not in seen:
            seen.add(inst['name'])
            gahar.append((inst['name'], inst['logo']))
    return new, gahar


@functools.lru_cache(maxsize=None)
def wall_card(path, w, h):
    return plaque_card(path, w, h)


def wall_panels():
    new, _ = wall_logos()
    return [new[i:i + 5] for i in range(0, len(new), 5)]


def wall_times():
    """(panel starts..., network start, end)."""
    t = tl.T_WALL + tl.WALL_HEAD
    n = max(1, len(wall_panels()))
    dur = float(np.clip((tl.T_FUTURE - t - 6.5) / n, 3.6, 6.0))   # the full network always keeps about 6.5 s
    starts = []
    for _ in wall_panels():
        starts.append(t)
        t += dur
    return starts, t, tl.T_FUTURE, dur


def s7_wall(cv, t):
    u = t - tl.T_WALL
    cv[:] = NAVY
    PF.glow(cv, W / 2, H * 0.55, 1100, GOLD, 0.16)
    ST.add(cv, R.rays(W / 2, -200, t, n=14, speed=0.03, reach=1400), GOLD, 0.06)
    starts, t_net, t_end, pdur = wall_times()
    hq = seg(u, 0.2, 0.9)
    head_o = ease_io(hq) * (1 - seg(t, t_end - 0.5, t_end))
    text(cv, 'TRUSTED BY HEALTHCARE LEADERS', W / 2, 150, 64, 'cinzel', 'gold', head_o, 12, 0.5,
         shine=seg(u, 0.5, 1.6) if 0.5 < u < 1.6 else None)
    hline(cv, W / 2, 205, 420 * ease_out(seg(u, 0.5, 1.2)), head_o)
    for p, logos in enumerate(wall_panels()):
        a = starts[p]
        if not (a - 0.1 <= t < a + pdur):
            continue
        v = t - a
        out = seg(v, pdur - 0.45, pdur)
        n = len(logos)
        pos = [(W / 2 + (j - 1) * 470, 470) for j in range(3)] + [(W / 2 - 235 + (j - 3) * 470, 800) for j in range(3, 5)]
        if n < 5:
            pos = [(W / 2 + (j - (n - 1) / 2) * 470, 600) for j in range(n)]
        for j, ((name, path), (x, y)) in enumerate(zip(logos, pos)):
            qq = seg(v, 0.15 + 0.32 * j, 0.7 + 0.32 * j)
            card = wall_card(path, 400, 270)
            composite(cv, card, x, y + 24 * (1 - ease_out(qq)), 0.96 + 0.04 * ease_out(qq), ease_io(qq) * (1 - out), glow=0.1,
                      shine=seg(v, 0.5 + 0.32 * j, 1.3 + 0.32 * j) if 0.5 + 0.32 * j < v < 1.3 + 0.32 * j else None)
    # the full network: every uploaded logo + the GAHAR institutions (each once), one balanced wide grid
    if t >= t_net - 0.1:
        v = t - t_net
        new, gahar = wall_logos()
        allx = new + gahar
        n = len(allx)
        cols = 6 if n > 15 else 5
        rows = (n + cols - 1) // cols
        cw, ch = (270, 170) if rows > 2 else (320, 200)
        gx, gy = cw + 30, ch + 30
        y0 = 560 - (rows - 1) * gy / 2 + 30
        out = seg(t, t_end - 0.6, t_end)
        for j, (name, path) in enumerate(allx):
            r, c = divmod(j, cols)
            inrow = min(cols, n - r * cols)
            x = W / 2 + (c - (inrow - 1) / 2) * gx
            y = y0 + r * gy
            qq = seg(v, 0.1 + 0.07 * j, 0.5 + 0.07 * j)
            composite(cv, wall_card(path, cw, ch), x, y, 0.9 + 0.1 * ease_out(qq), ease_io(qq) * (1 - out), glow=0.08)
        PF.glow(cv, W / 2, 560, 900, WARM, 0.12 * seg(v, 1.4, 2.6) * (1 - out))
    return False          # the heading owns the top of the frame here


# ------------------------------------------------------------------ 8  FINALE (15 s, final musical peak on the line)
def s8_finale(cv, t):
    u = t - tl.T_FUTURE
    if u < 9.0:
        M.s7_future(cv, M.T_FUTURE + u)
    else:   # hold the final composition, alive: slow rays and shimmer
        M.s7_future(cv, M.T_FUTURE + 8.95)
        ST.add(cv, R.rays(W / 2, 420, t, n=20, speed=0.04, reach=1100), GOLD, 0.06)
    cv *= 1 - seg(t, DUR - 1.4, DUR)
    return u < 4.0


# ------------------------------------------------------------------ frame + output
def frame(t):
    cv = np.zeros((H, W, 3), np.float32)
    if t < tl.T_BRIDGE:
        corner = M.s1_discovery(cv, t)
    elif t < tl.T_WHO:
        corner = s2_bridge(cv, t)
    elif t < tl.T_WHAT:
        corner = s3_who(cv, t)
    elif t < tl.T_IMPACT:
        corner = s4_what(cv, t)
    elif t < tl.T_PEOPLE:
        corner = s5_impact(cv, t)
    elif t < tl.T_WALL:
        corner = s6_people(cv, t)
    elif t < tl.T_FUTURE:
        corner = s7_wall(cv, t)
    else:
        corner = s8_finale(cv, t)
    R.bloom(cv, 0.22, 0.82)
    cv *= R.vignette(0.32)
    g = M.GRAIN[int(t * FPS) % 8]
    cv += np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None] * 0.012
    if corner:
        M.corner_logo(cv, 0.92)
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


def mix_audio(out):
    """Score (with its sound design) + the single lip-synced 'EUREKA!', then hall mastering (two-pass loudnorm)."""
    music = os.path.join(BUILD, 'moment_score_v2.wav')
    subprocess.run([sys.executable, os.path.join(HERE, 'score_v2.py'), music], check=True)
    at = int(tl.EUREKA_AT * 1000)
    eu = (f'[1:a]atrim=0:{tl.EUREKA_CUT + 0.05},afade=out:st={tl.EUREKA_CUT - 0.1}:d=0.15,asetpts=PTS-STARTPTS,'
          f'highpass=f=90,aecho=0.8:0.55:70|160:0.22|0.12,volume=1.7,adelay={at}|{at},apad=whole_dur={DUR}[eu]')
    pre = os.path.join(BUILD, 'mix_v2_pre.wav')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', music, '-i', os.path.join(BUILD, 'A4_eureka_voiced.mp4'), '-filter_complex',
                    eu + f';[0:a][eu]amix=inputs=2:normalize=0,atrim=0:{DUR}[a]', '-map', '[a]', '-ar', '48000', pre], check=True)
    meas = subprocess.run(['ffmpeg', '-v', 'info', '-i', pre, '-af', 'loudnorm=I=-16:TP=-1.5:LRA=14:print_format=json', '-f', 'null', '-'],
                          capture_output=True, text=True).stderr
    js = json.loads(meas[meas.rindex('{'):meas.rindex('}') + 1])
    ln = (f"loudnorm=I=-16:TP=-1.5:LRA=14:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
          f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', pre, '-af', ln + ',aresample=48000', '-c:a', 'pcm_s16le', out], check=True)


def render(t0, t1, out):
    d = os.path.join(BUILD, 'chunks_v2')
    os.makedirs(d, exist_ok=True)
    a0, a1 = int(t0 * FPS) // 45 * 45, int(round(t1 * FPS))
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
    mix_audio(wav)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', silent, '-ss', str(t0), '-t', str(t1 - t0), '-i', wav, '-c:v', 'copy',
                    '-c:a', 'aac', '-b:a', '320k', '-shortest', '-movflags', '+faststart', out], check=True)
    print('wrote', out)


if __name__ == '__main__':
    os.makedirs(BUILD, exist_ok=True)
    cmd = sys.argv[1]
    if cmd == 'stills':
        for s in sys.argv[2:]:
            Image.fromarray(frame(float(s))).save(os.path.join(BUILD, f'v2_{float(s):06.2f}.png'))
    elif cmd == 'cut':
        t0 = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
        t1 = float(sys.argv[3]) if len(sys.argv) > 3 else DUR
        full = (t0, t1) == (0.0, DUR)
        render(t0, t1, os.path.join(HERE, 'EUREKA_THE_MOMENT_v2_FINAL.mp4') if full else os.path.join(BUILD, f'v2_{int(t0)}_{int(t1)}.mp4'))
