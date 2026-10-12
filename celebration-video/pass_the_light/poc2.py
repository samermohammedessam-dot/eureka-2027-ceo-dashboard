"""PASS THE LIGHT — improved 16:9 proof of concept (~15 s), real 3-D environments.

 0.0-2.6  3-D corridor of light, camera dolly; transparent Eureka logo reveal -> top-right corner
 2.0-3.4  the golden relay light travels down the corridor and opens a doorway anchored in 3-D
 3.4-5.9  C2 inside the doorway (0.6x interpolated slow motion, never frozen) + voice
 5.9-7.0  the doorway widens into a full-frame shot
 7.0-15   flash -> aerial over the 3-D City of Excellence; the relay comet crosses the city,
          leaves a light path, reaches milestone 01; the tower ignites base -> crown;
          the institution's real logo + GAHAR seal appear on a glass card tied to the tower.

  python3 poc2.py stills 1 4 6.5 9 12 14
  python3 poc2.py video clips/C2_lets_make_it_happen.mp4
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
sys.path.insert(0, os.path.dirname(HERE))
os.environ.setdefault('EUREKA_ASSETS', os.path.join(os.path.dirname(HERE), 'assets_dl'))
import render as R  # noqa: E402
import scene3d as S  # noqa: E402
from render import (GOLD, GOLD_HI, WARM_WHITE, W, H, Layer, add_light, bloom, composite, ease_io, ease_out, flash,
                    lerp, radial, seg, splat, text_layer, tonemap, vignette)  # noqa: E402

FPS = 30
DUR = 15.0
BUILD = os.path.join(os.path.dirname(HERE), 'build', 'ptl')
CLIP = os.environ.get('PTL_CLIP')
SLOW = 0.6

T_LOGO = (0.3, 1.3)
T_CORNER = (1.6, 2.4)
T_DOOR = (2.6, 3.4)
T_CLIP = 3.4
CLIP_LEN = 1.5 / SLOW                     # 2.5 s
T_WIDEN = (T_CLIP + CLIP_LEN - 0.4, T_CLIP + CLIP_LEN + 0.7)
T_CITY = T_WIDEN[1] + 0.05                # ~6.75
T_ARRIVE = T_CITY + 4.2


# ------------------------------------------------------------------ Eureka logo, transparent
@functools.lru_cache(maxsize=None)
def eureka_rgba():
    """The authentic logo with its white background keyed out (colours un-premultiplied)."""
    im = Image.open(R.manifest()['eureka_logo']).convert('RGB')
    a = np.asarray(im, np.float32) / 255
    alpha = np.clip((1 - a.min(axis=2)) / 0.18, 0, 1)            # distance from white
    rgb = (a - (1 - alpha[..., None])) / np.maximum(alpha[..., None], 1e-3)
    rgba = np.dstack([np.clip(rgb, 0, 1), alpha])
    img = Image.fromarray((rgba * 255).astype(np.uint8), 'RGBA')
    return img.crop(img.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox())


@functools.lru_cache(maxsize=None)
def eureka_layer(width):
    """Transparent logo + a soft luminous backlight (no box) so the navy lettering reads on dark scenes."""
    lg = eureka_rgba()
    h = int(width * lg.height / lg.width)
    lg = lg.resize((width, h), Image.LANCZOS)
    m = int(width * 0.35)
    canvas = Image.new('RGBA', (width + 2 * m, h + 2 * m), (0, 0, 0, 0))
    # feathered warm-white backlight following the logo's own shape
    a = lg.getchannel('A').filter(ImageFilter.MaxFilter(9 if width > 300 else 7))
    halo = Image.new('L', canvas.size, 0)
    halo.paste(a, (m, m))
    halo = halo.filter(ImageFilter.GaussianBlur(width * 0.07))
    glow = Image.new('RGBA', canvas.size, (250, 244, 228, 0))
    glow.putalpha(halo.point(lambda v: int(min(255, v * (0.45 if width > 300 else 1.6)))))
    canvas.alpha_composite(glow)
    canvas.alpha_composite(lg, (m, m))
    return Layer(canvas, None)


def eureka(cv, t):
    big = eureka_layer(560)
    bug = eureka_layer(176)       # ~9 % of frame width
    corner = (W - 40 - 176 / 2 - 10, 34 + bug.h / 2 - 30)
    if t < T_CORNER[0]:
        q = seg(t, *T_LOGO)
        add_light(cv, radial(W / 2, H / 2 - 30, 420), GOLD, 0.12 * q)
        composite(cv, big, W / 2, H / 2 - 30, lerp(0.94, 1.0, ease_out(q)), ease_io(q), glow=0,
                  shine=seg(t, 0.9, 1.6) if 0.9 < t < 1.6 else None)
        return
    m = ease_io(seg(t, *T_CORNER))
    if m < 1:
        composite(cv, big, lerp(W / 2, corner[0], m), lerp(H / 2 - 30, corner[1], m), lerp(1.0, 176 / 560, m), 1.0, glow=0)
    else:
        composite(cv, bug, *corner, 1.0, 1.0, glow=0)


# ------------------------------------------------------------------ corridor + doorway
DOOR3D = (95, 0, 900, 170)   # x centre, floor y, z depth, door width (9:16 tall)


def cor_cam(t):
    return S.Cam((0, 150, -120 + 70 * t), yaw=0.0, pitch=0.02, fov_deg=62)


def corridor(cv, t):
    cam = cor_cam(t)
    img = S.render_corridor(cam)
    # soften the glossy floor reflection
    hy = int(cam.horizon_y())
    if 0 < hy < H:
        low = Image.fromarray((np.clip(img[hy:], 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5))
        img[hy:] = img[hy:] * 0.45 + np.asarray(low, np.float32) / 255 * 0.55
    cv[:] = img
    # halos of the ceiling panels and the doorway at the end
    for z in np.arange(0, 3200, 260):
        sp, zz = cam.screen((0, 299, z + 60))
        if zz > 10:
            add_light(cv, radial(sp[0], sp[1], 90 * 500 / zz + 20), np.array([0.8, 0.86, 1.0]), 0.10)
    sp, zz = cam.screen((0, 115, 3199))
    if zz > 10:
        add_light(cv, radial(sp[0], sp[1], 260), np.array([1.0, 0.8, 0.5]), 0.55)
    return cam


def door_rect(cam):
    x, y0, z, w = DOOR3D
    h = w * 16 / 9
    (x0, y_top), _ = cam.screen((x - w / 2, y0 + h, z))
    (x1, y_bot), _ = cam.screen((x + w / 2, y0, z))
    return x0, y_top, x1 - x0, y_bot - y_top


@functools.lru_cache(maxsize=1)
def clip_frames():
    tmp = os.path.join(BUILD, 'c2_slow')
    os.makedirs(tmp, exist_ok=True)
    if not os.listdir(tmp):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', CLIP, '-vf',
                        f'minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:vsbmc=1,setpts={1 / SLOW:.4f}*PTS,fps={FPS},scale=1080:1920',
                        os.path.join(tmp, 'f%04d.jpg')], check=True)
    return [os.path.join(tmp, f) for f in sorted(os.listdir(tmp))]


def clip_frame(u):
    fr = clip_frames()
    return Image.open(fr[min(len(fr) - 1, max(0, int(u * FPS)))]).convert('RGB')


def doorway(cv, t, cam):
    if t < T_DOOR[0] or t > T_CITY + 0.5:
        return
    open_q = ease_out(seg(t, *T_DOOR))
    widen = ease_io(seg(t, *T_WIDEN))
    rx, ry, rw, rh = door_rect(cam) if cam is not None else (0, 0, W, H)
    rw_open = rw * open_q
    x0 = lerp(rx + (rw - rw_open) / 2, 0, widen)
    y0 = lerp(ry, 0, widen)
    iw = max(2, int(lerp(rw_open, W, widen)))
    ih = max(2, int(lerp(rh, H, widen)))
    fr = clip_frame(max(0.0, t - T_CLIP))
    fw, fh = fr.size
    ar = iw / ih
    cw_, ch_ = (fh * ar, fh) if fw / fh > ar else (fw, fw / ar)
    fy = fh * lerp(0.5, 0.36, widen)
    top = max(0, min(fh - ch_, fy - ch_ / 2))
    arr = np.asarray(fr.resize((iw, ih), Image.BICUBIC, box=(fw / 2 - cw_ / 2, top, fw / 2 + cw_ / 2, top + ch_)), np.float32) / 255
    alpha = min(1.0, seg(t, T_DOOR[0], T_DOOR[1] + 0.2) * 1.5) * (1 - seg(t, T_CITY - 0.05, T_CITY + 0.45))
    r = R.region(int(x0), int(y0), iw, ih)
    if r:
        cv[r[0]] = cv[r[0]] * (1 - alpha) + arr[r[1]] * alpha
    edge = (1 - widen) * alpha
    if edge > 0.01:  # luminous door frame: thin gold edges + spill on the floor
        m = np.zeros((R.LH, R.LW), np.float32)
        X0, Y0, X1, Y1 = x0 / 4, y0 / 4, (x0 + iw) / 4, (y0 + ih) / 4
        lx, ly = R._lx / 4, R._ly / 4
        inx, iny = (lx >= X0) & (lx <= X1), (ly >= Y0) & (ly <= Y1)
        dx = np.minimum(np.abs(lx - X0), np.abs(lx - X1))
        dy = np.minimum(np.abs(ly - Y0), np.abs(ly - Y1))
        m += np.exp(-(dx / 1.0) ** 2) * iny + np.exp(-(dy / 1.0) ** 2) * inx
        add_light(cv, m, GOLD_HI, 0.8 * edge)
        add_light(cv, np.exp(-(((R._lx - (x0 + iw / 2)) / (iw * 0.9)) ** 2 + ((R._ly - (y0 + ih + 40)) / 60) ** 2)),
                  np.array([1.0, 0.78, 0.45]), 0.45 * edge)


def relay_corridor(cv, t, cam):
    """The relay light comes down the corridor from the bright doorway at the end to the side door."""
    a, b = 1.9, T_DOOR[0] + 0.1
    if not (a <= t <= b + 0.25):
        return
    start = np.array([0, 140, 3100.0])
    x, y0, z, w = DOOR3D
    end = np.array([x, y0 + w * 16 / 9 * 0.55, z])
    for k in range(30, -1, -1):
        q = ease_io(max(0, seg(t, a, b) - k * 0.012))
        p = start + (end - start) * q + np.array([0, 60 * math.sin(math.pi * q), 0])
        sp, zz = cam.screen(p)
        if zz < 5:
            continue
        sz = max(1.0, 2600 / zz)
        splat(cv, sp[0], sp[1], sz * (2.2 if k == 0 else 1.0), 1.4 if k == 0 else 0.55 * (1 - k / 31))
        if k == 0:
            add_light(cv, radial(sp[0], sp[1], 30 + 9000 / zz), np.array([1.0, 0.72, 0.36]), 0.55)


# ------------------------------------------------------------------ City of Excellence
def city_cam(u):
    _, land, route = S.city()
    x0, z0 = route[0]
    q = ease_io(min(1.0, u / 7.5))
    pos = (lerp(x0 - 1400, x0 - 640, q), lerp(1500, 720, q), lerp(z0 - 3600, z0 - 1700, q))
    return S.Cam(pos, yaw=lerp(0.32, 0.28, q), pitch=lerp(0.30, 0.20, q), fov_deg=52)


def comet_path(q):
    _, land, _ = S.city()
    L = land[0]
    p0 = np.array([L['x'] - 1600, 900, L['z'] - 2500])
    p1 = np.array([L['x'], L['spire'] + 30, L['z']])
    return S.bez3(p0, p1, q, lift=380)


def city(cv, t):
    u = t - T_CITY
    cam = city_cam(u)
    _, land, _ = S.city()
    L = land[0]
    arr = max(0.0, t - T_ARRIVE)
    lvl = ease_out(min(1.0, arr / 0.6))
    sweep = ease_io(min(1.0, arr / 1.1))
    img, _ = S.render_city(cam, [lvl] + [0.0] * 9, sweeps=[sweep] + [1.0] * 9)
    cv[:] = img
    # horizon haze glow
    # the relay comet with a ribbon trail and the light path it leaves behind
    qn = ease_io(seg(t, T_CITY + 0.4, T_ARRIVE))
    pts = []
    for k in range(0, 60):
        q = max(0.0, qn - k * 0.008)
        sp, zz = cam.screen(comet_path(q))
        if zz > 5:
            pts.append((sp, zz, k))
    for sp, zz, k in pts[::-1]:
        sz = max(1.0, 3500 / zz)
        splat(cv, sp[0], sp[1], sz * (2.4 if k == 0 else 0.9), 1.6 if k == 0 else 0.55 * (1 - k / 60))
    path = Image.new('L', (R.LW, R.LH), 0)
    pd = ImageDraw.Draw(path)
    trail = [cam.screen(comet_path(q)) for q in np.linspace(0, qn, 40)]
    trail = [tuple(p / 4) for p, z in trail if z > 5]
    if len(trail) > 1:
        pd.line(trail, fill=170, width=1)
        add_light(cv, np.asarray(path.filter(ImageFilter.GaussianBlur(1.0)), np.float32) / 255, GOLD_HI, 0.6)
    if pts and qn < 1:
        sp = pts[0][0]
        add_light(cv, radial(sp[0], sp[1], 70 + 60000 / pts[0][1]), np.array([1.0, 0.7, 0.34]), 0.6)
    # arrival: crown light, beam, burst
    (cx, cy), cz = cam.screen((L['x'], L['spire'], L['z']))
    if arr > 0:
        flash(cv, 0.55 * math.exp(-arr / 0.18), cx, cy, 500)
        add_light(cv, radial(cx, cy, 120), GOLD_HI, 0.9 * lvl)
        beam = np.exp(-((R._lx - cx) / 22) ** 2) * np.clip((cy - R._ly) / 500, 0, 1) * np.exp(-np.clip(cy - R._ly, 0, None) / 700)
        add_light(cv, beam, GOLD_HI, 0.5 * lvl)
        R.firework(cv, t, T_ARRIVE, cx, cy - 20, 3, n=46, life=1.3, speed=330)
    return cam, (cx, cy)


def milestone_card(cv, t, anchor):
    """Glass card tied to the lit tower by a thin gold leader line: real logo + GAHAR seal."""
    arr = t - T_ARRIVE - 0.35
    if arr <= 0:
        return
    inst = R.manifest()['institutions'][0]
    q = ease_out(min(1.0, arr / 0.5))
    ax, ay = anchor
    cx, cy = min(W - 380, ax + 470), max(330, min(H - 330, ay + 170))
    # leader line from tower crown to the card
    m = Image.new('L', (R.LW, R.LH), 0)
    ImageDraw.Draw(m).line([(ax / 4, ay / 4), ((cx - 300) / 4, cy / 4)], fill=int(200 * q), width=1)
    add_light(cv, np.asarray(m.filter(ImageFilter.GaussianBlur(0.6)), np.float32) / 255, GOLD_HI, 0.7)
    # frosted glass panel
    pw, ph = 600, 420
    x0, y0 = int(cx - pw / 2), int(cy - ph / 2 + 30 * (1 - q))
    r = R.region(x0, y0, pw, ph)
    if r:
        cv[r[0]] = cv[r[0]] * (1 - 0.55 * q) + np.array([0.05, 0.08, 0.17]) * 0.55 * q
        cv[r[0]][:2] += GOLD_HI * 0.6 * q
    seal = R.seal_layer(92)
    composite(cv, seal, cx, y0 + 70, 0.7 + 0.3 * ease_out(q), q, glow=0.4)
    composite(cv, R.inst_card(inst, 440, 230), cx, y0 + 215, 0.8 + 0.2 * ease_out(q), q, glow=0.25)
    if inst.get('branch'):
        composite(cv, text_layer(inst['branch'], 'playfair', 38, 600, 0, 'gold', 6), cx, y0 + 352, 1.0, q, glow=0.4)
    composite(cv, text_layer('GAHAR ACCREDITATION  ·  MILESTONE 01', 'mont', 19, 600, 5, 'gold', 3), cx, y0 + 395, 1.0, q, glow=0.3)


def frame(t):
    cv = np.zeros((H, W, 3), np.float32)
    cam = None
    if t < T_CITY:
        cam = corridor(cv, t)
        cv *= ease_io(seg(t, 0.0, 0.9)) * (0.5 + 0.5 * seg(t, T_CORNER[0], T_DOOR[0]))
        relay_corridor(cv, t, cam)
        doorway(cv, t, cam)
        flash(cv, 1.3 * seg(t, T_CITY - 0.25, T_CITY) ** 2)
    else:
        ccam, anchor = city(cv, t)
        flash(cv, 1.1 * math.exp(-(t - T_CITY) / 0.25))
        tq = seg(t, T_CITY + 0.8, T_CITY + 1.6)
        composite(cv, text_layer('EXCELLENCE IS NEVER ACHIEVED ALONE.', 'cinzel', 50, 700, 5, 'gold', 10), W / 2, 905,
                  lerp(1.05, 1.0, ease_out(tq)), ease_io(tq) * (1 - seg(t, T_ARRIVE - 0.3, T_ARRIVE + 0.2)), glow=0.8)
        milestone_card(cv, t, anchor)
    bloom(cv, 0.30, 0.78)
    cv *= vignette(0.45)
    eureka(cv, t)
    cv *= 1 - seg(t, DUR - 0.5, DUR)
    return tonemap(cv)


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
    os.makedirs(os.path.join(BUILD, 'poc2_chunks'), exist_ok=True)
    clip_frames()
    nf = int(DUR * FPS)
    jobs = [(a, min(nf, a + 30), os.path.join(BUILD, 'poc2_chunks', f'c{a:04d}.mp4')) for a in range(0, nf, 30)]
    with Pool(4) as p:
        list(p.imap(_chunk, jobs))
    lst = os.path.join(BUILD, 'poc2_chunks', 'list.txt')
    open(lst, 'w').writelines(f"file '{j[2]}'\n" for j in jobs)
    silent = os.path.join(BUILD, 'poc2_video.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', silent], check=True)
    music = os.path.join(BUILD, 'poc2_music.wav')
    subprocess.run([sys.executable, os.path.join(HERE, 'poc_music.py'), music, str(DUR)], check=True)
    dly = int((T_CLIP + 0.5) * 1000)
    filt = (f'[2:a]aresample=48000,aformat=channel_layouts=stereo,volume=1.6,adelay={dly}|{dly},apad,asplit=2[d1][d2];'
            f'[1:a][d1]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[m];'
            f'[m][d2]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', silent, '-i', music, '-i', CLIP, '-filter_complex', filt,
                    '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-t', str(DUR),
                    '-movflags', '+faststart', out], check=True)
    print('wrote', out)


if __name__ == '__main__':
    if sys.argv[1] == 'video' and len(sys.argv) > 2:
        CLIP = os.path.abspath(sys.argv[2])
    elif CLIP is None:
        CLIP = os.path.join(HERE, 'clips', 'C2_lets_make_it_happen.mp4')
    os.environ['PTL_CLIP'] = CLIP
    if sys.argv[1] == 'stills':
        for s in sys.argv[2:]:
            Image.fromarray(frame(float(s))).save(os.path.join(BUILD, f'poc2_{float(s):05.2f}.png'))
    else:
        render_video(os.path.join(BUILD, 'ptl_poc2.mp4'))
