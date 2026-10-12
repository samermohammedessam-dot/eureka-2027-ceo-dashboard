"""PASS THE LIGHT — 16:9 preview v3 with the real C3 footage (~17 s).

 0.0-2.3   3-D corridor of light, Eureka logo reveal -> corner
 2.3-7.0   C3 shot A: he reviews, closes the folder (the golden light ignites ON the folder), stands
 7.0-8.9   C3 shot B: he walks the glass corridor; the light travels with the folder in his hand
 8.9-9.5   the light lifts off the folder and flies into the city (gentle golden dissolve)
 9.5-17    3-D City of Excellence: the light reaches milestone 01; tower ignites; logo + GAHAR card

Composition: the vertical footage at full height, feathered softly into the 3-D environment
(no frame borders, no blurred duplicate, no heavy crop); negative space carries title + light.
"""
import functools
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import poc2 as P2  # noqa: E402
from poc2 import R, S, W, H, FPS, add_light, bloom, composite, ease_io, ease_out, lerp, radial, seg, splat, \
    text_layer, tonemap, vignette  # noqa: E402

CLIP = os.path.join(HERE, 'clips', 'C3_file_pass.mp4')
BUILD = P2.BUILD
DUR = 17.0
A_IN, A_OUT = 0.2, 4.9          # clip times used for shot A
B_IN, B_OUT = 5.0, 6.9          # clip times used for shot B (before the over-close camera)
T_A = 2.3
T_B = T_A + (A_OUT - A_IN)      # 7.0
T_LIFT = T_B + (B_OUT - B_IN)   # 8.9
P2.T_CITY = T_LIFT + 0.6        # 9.5
P2.T_ARRIVE = P2.T_CITY + 4.2   # 13.7
IGNITE_CLIP = 2.55              # folder closes
T_IGNITE = T_A + IGNITE_CLIP - A_IN

# folder position in normalised clip coordinates (from the gridded frame study)
FOLDER_A = [(2.4, 0.50, 0.80), (2.8, 0.53, 0.80), (3.2, 0.56, 0.81), (3.8, 0.58, 0.84)]
FOLDER_B = [(5.0, 0.54, 0.58), (5.2, 0.54, 0.60), (5.6, 0.52, 0.65), (6.0, 0.555, 0.77), (6.4, 0.69, 0.83), (6.9, 0.66, 0.92)]

CX = 1270  # where the actor stands in the 16:9 frame


def interp(keys, ct):
    ts = [k[0] for k in keys]
    return float(np.interp(ct, ts, [k[1] for k in keys])), float(np.interp(ct, ts, [k[2] for k in keys]))


@functools.lru_cache(maxsize=1)
def frames():
    d = os.path.join(BUILD, 'c3_frames')
    os.makedirs(d, exist_ok=True)
    if not os.listdir(d):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', CLIP, '-vf', f'fps={FPS},scale=1080:1920',
                        '-q:v', '2', os.path.join(d, 'f%04d.jpg')], check=True)
    return [os.path.join(d, f) for f in sorted(os.listdir(d))]


def clip_img(ct):
    fr = frames()
    return Image.open(fr[min(len(fr) - 1, max(0, int(round(ct * FPS))))]).convert('RGB')


@functools.lru_cache(maxsize=4)
def feather(w, h, f=170):
    x = np.arange(w, dtype=np.float32)
    a = np.clip(np.minimum(x, w - 1 - x) / f, 0, 1)
    a = a * a * (3 - 2 * a)
    y = np.arange(h, dtype=np.float32)
    b = np.clip(np.minimum(y, h - 1 - y) / 40, 0, 1)
    return (b[:, None] * a[None, :])[..., None]


def actor_layer(cv, t):
    """Composite the footage at full height, feathered into the environment; return geometry."""
    if t < T_A - 0.3 or t > P2.T_CITY + 0.2:
        return None
    if t < T_B:
        ct = A_IN + (t - T_A)
        push = 1.0 + 0.035 * seg(t, T_A, T_B)
    else:
        ct = min(B_OUT, B_IN + (t - T_B))
        push = 1.03 + 0.03 * seg(t, T_B, T_LIFT)
    ct = max(A_IN, ct)
    h = int(H * push)
    w = int(h * 9 / 16)
    img = np.asarray(clip_img(ct).resize((w, h), Image.BICUBIC), np.float32) / 255
    # gentle grade towards the film's palette: lift blacks to navy, keep skin tones natural
    img = img * 0.94 + np.array([0.01, 0.02, 0.05])
    x0, y0 = int(CX - w / 2), int(H / 2 - h / 2)
    fade = seg(t, T_A - 0.3, T_A + 0.35) * (1 - seg(t, T_LIFT + 0.2, P2.T_CITY + 0.2))
    a = feather(w, h) * fade
    r = R.region(x0, y0, w, h)
    if r:
        cv[r[0]] = cv[r[0]] * (1 - a[r[1]]) + img[r[1]] * a[r[1]]
    return x0, y0, w, h, ct


def environment(cv, t):
    cam = S.Cam((0, 150, -120 + 70 * t), yaw=0.2, pitch=0.02, fov_deg=62)  # vanishing point in the open space
    img = S.render_corridor(cam)
    cv[:] = img * 0.75
    # warm key light from the actor's side (matches the sunrise in the footage)
    add_light(cv, radial(CX + 120, 380, 700), np.array([1.0, 0.72, 0.4]), 0.18 * seg(t, T_A - 0.3, T_A + 0.6))
    return cam


def folder_light(cv, t, geo):
    if geo is None:
        return None
    x0, y0, w, h, ct = geo
    if t < T_B:
        if ct < IGNITE_CLIP - 0.05:
            return None
        nx, ny = interp(FOLDER_A, ct)
        k = ease_out(seg(t, T_IGNITE, T_IGNITE + 0.5)) * (1 - 0.55 * seg(ct, 3.4, 4.6))
    else:
        nx, ny = interp(FOLDER_B, ct)
        k = 0.55 + 0.25 * seg(t, T_B, T_B + 0.6)
    x, y = x0 + nx * w, y0 + ny * h
    add_light(cv, radial(x, y, 130), np.array([1.0, 0.74, 0.38]), 0.55 * k)
    splat(cv, x, y, 5, 1.1 * k)
    g = np.random.default_rng(int(t * 30))
    for _ in range(int(10 * k)):
        a = g.uniform(0, 1)
        splat(cv, x + g.normal(0, 22), y - a * 70, 1, 0.7 * (1 - a) * k)
    if abs(t - T_IGNITE) < 0.4:  # the moment of ignition
        add_light(cv, radial(x, y, 260), np.array([1.0, 0.8, 0.5]), 0.5 * math.exp(-abs(t - T_IGNITE) / 0.12))
    return x, y


def lift_off(cv, t, start):
    """The light leaves the folder and arcs out of frame, towards the city."""
    if not (T_LIFT - 0.15 <= t <= P2.T_CITY) or start is None:
        return
    q = ease_io(seg(t, T_LIFT - 0.15, P2.T_CITY))
    for k in range(26, -1, -1):
        qq = max(0.0, q - k * 0.014)
        x = lerp(start[0], -120, qq)
        y = lerp(start[1], 140, qq) - 260 * math.sin(math.pi * qq)
        splat(cv, x, y, 3 + (7 if k == 0 else 0), 1.5 if k == 0 else 0.6 * (1 - k / 27))
    x = lerp(start[0], -120, q)
    y = lerp(start[1], 140, q) - 260 * math.sin(math.pi * q)
    add_light(cv, radial(x, y, 150), np.array([1.0, 0.72, 0.36]), 0.55)


def title(cv, t):
    q = seg(t, T_A + 2.2, T_A + 3.2)
    o = q * (1 - seg(t, T_B + 1.2, T_LIFT))
    if o <= 0.01:
        return
    yy = np.linspace(-1, 1, 300)[:, None, None]
    cv[150:450, 80:960] *= 1 - 0.45 * o * (1 - yy ** 2)  # quiet the ceiling behind the title
    composite(cv, text_layer('PASS THE LIGHT', 'cinzel', 78, 700, 12, 'gold', 12), 520, 250 + 14 * (1 - ease_out(q)),
              1.0, o, glow=0.7, shine=seg(t, T_A + 3.0, T_A + 4.3) if T_A + 3.0 < t < T_A + 4.3 else None)
    lw = int(380 * ease_out(seg(t, T_A + 2.6, T_A + 3.6)) * o)
    if lw > 2:
        cv[318:320, 520 - lw // 2:520 + lw // 2] += R.GOLD_HI * 0.8 * o
    q2 = seg(t, T_A + 2.8, T_A + 3.8)
    composite(cv, text_layer('The People Behind Excellence', 'playfair', 42, 500, 0, 'ivory', 6), 520, 370,
              1.0, ease_io(q2) * o / max(q, 1e-3) * q, glow=0.3)


def frame(t):
    cv = np.zeros((H, W, 3), np.float32)
    if t < P2.T_CITY:
        environment(cv, t)
        cv *= ease_io(seg(t, 0.0, 0.9)) * (0.55 + 0.45 * seg(t, P2.T_CORNER[0], T_A))
        geo = actor_layer(cv, t)
        pos = folder_light(cv, t, geo)
        start = lift_start()
        lift_off(cv, t, start)
        title(cv, t)
        add_light(cv, radial(W / 2, H / 2, 900) * 0.7 + 0.3, np.array([1.0, 0.78, 0.45]), 0.3 * seg(t, P2.T_CITY - 0.4, P2.T_CITY) ** 2)
    else:
        _, anchor = P2.city(cv, t)
        add_light(cv, radial(W / 2, H / 2, 900) * 0.7 + 0.3, np.array([1.0, 0.78, 0.45]), 0.3 * math.exp(-(t - P2.T_CITY) / 0.3))
        tq = seg(t, P2.T_CITY + 0.8, P2.T_CITY + 1.6)
        composite(cv, text_layer('EXCELLENCE IS NEVER ACHIEVED ALONE.', 'cinzel', 50, 700, 5, 'gold', 10), W / 2, 905,
                  lerp(1.05, 1.0, ease_out(tq)), ease_io(tq) * (1 - seg(t, P2.T_ARRIVE - 0.3, P2.T_ARRIVE + 0.2)), glow=0.8)
        P2.milestone_card(cv, t, anchor)
    bloom(cv, 0.26, 0.8)
    cv *= vignette(0.42)
    P2.eureka(cv, t)
    cv *= 1 - seg(t, DUR - 0.5, DUR)
    return tonemap(cv)


@functools.lru_cache(maxsize=1)
def lift_start():
    """Folder position (screen) at the moment the light lifts off — same geometry as actor_layer."""
    ct = B_OUT - 0.16
    push = 1.03 + 0.03 * seg(T_LIFT - 0.16, T_B, T_LIFT)
    h = int(H * push)
    w = int(h * 9 / 16)
    nx, ny = interp(FOLDER_B, ct)
    return CX - w / 2 + nx * w, H / 2 - h / 2 + ny * h


def _chunk(args):
    a, b, path = args
    pr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', path],
                          stdin=subprocess.PIPE)
    for f in range(a, b):
        pr.stdin.write(frame(f / FPS).tobytes())
    pr.stdin.close()
    pr.wait()
    return path


def render_video(out):
    cdir = os.path.join(BUILD, 'poc3_chunks')
    os.makedirs(cdir, exist_ok=True)
    frames()
    nf = int(DUR * FPS)
    jobs = [(a, min(nf, a + 30), os.path.join(cdir, f'c{a:04d}.mp4')) for a in range(0, nf, 30)]
    with Pool(4) as p:
        list(p.imap(_chunk, jobs))
    lst = os.path.join(cdir, 'list.txt')
    open(lst, 'w').writelines(f"file '{j[2]}'\n" for j in jobs)
    silent = os.path.join(BUILD, 'poc3_video.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', silent], check=True)
    music = os.path.join(BUILD, 'poc3_music.wav')
    env = dict(os.environ, PTL_CUTS=f'{T_IGNITE:.2f},{P2.T_CITY:.2f},{P2.T_ARRIVE:.2f}')
    subprocess.run([sys.executable, os.path.join(HERE, 'poc_music.py'), music, str(DUR)], check=True, env=env)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', silent, '-i', music, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                    '-c:a', 'aac', '-b:a', '256k', '-t', str(DUR), '-movflags', '+faststart', out], check=True)
    print('wrote', out)


if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        for s in sys.argv[2:]:
            Image.fromarray(frame(float(s))).save(os.path.join(BUILD, f'poc3_{float(s):05.2f}.png'))
    else:
        render_video(os.path.join(BUILD, 'ptl_poc3.mp4'))
