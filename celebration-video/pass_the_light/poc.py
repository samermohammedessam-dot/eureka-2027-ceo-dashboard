"""PASS THE LIGHT — 16:9 proof-of-concept composition (~13 s).

The vertical Promoat clip becomes a 'door of light' inside a stylised corridor of light:
relay light arrives -> the door opens -> the actor's moment plays inside it (with a floor
reflection) -> the door widens to full 16:9 as he walks forward -> hand-off to the City of
Excellence. Permanent Eureka logo top-right from 2.4 s to the end.

  python3 poc.py stills 1 3 6 9.5 12        # PNG stills
  python3 poc.py video [clip.mp4]           # build/ptl_poc.mp4 (stand-in if no clip given)
"""
import functools
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ.setdefault('EUREKA_ASSETS', os.path.join(os.path.dirname(HERE), 'assets_dl'))
import render as R  # noqa: E402
import city_film as CF  # noqa: E402
from render import (GOLD, GOLD_HI, NAVY, DEEP, WARM_WHITE, W, H, add_light, bloom, composite, ease_io,
                    ease_out, flash, lerp, radial, seg, splat, text_layer, tonemap, vignette, Layer)  # noqa: E402

FPS = 30
DUR = 13.0
BUILD = os.path.join(os.path.dirname(HERE), 'build', 'ptl')
CLIP = None  # path of the Promoat clip (vertical); None -> stand-in

# timeline
LOGO_IN, LOGO_TO_CORNER = 0.4, 1.7
DOOR_OPEN = (2.4, 3.3)
CLIP_START = 3.3
CLIP_LEN = 5.0
WIDEN = (CLIP_START + CLIP_LEN - 1.2, CLIP_START + CLIP_LEN + 0.2)
CITY = (CLIP_START + CLIP_LEN + 0.2, DUR)

DOOR_C = (1250, 500)
DOOR_H = 820
DOOR_W = int(DOOR_H * 9 / 16)


# ------------------------------------------------------------------ corridor of light
@functools.lru_cache(maxsize=1)
def corridor():
    """Stylised premium corridor: converging ceiling light lines, glass wall panels, glossy floor."""
    S = 1.15
    w, h = int(W * S), int(H * S)
    vp = (w * 0.47, h * 0.47)
    img = Image.new('RGB', (w, h), (0, 0, 0))
    d = ImageDraw.Draw(img)
    # base gradient
    a = np.zeros((h, w, 3), np.float32)
    y = np.linspace(0, 1, h)[:, None, None]
    a[:] = DEEP + (NAVY * 1.25 - DEEP) * np.exp(-((y - 0.47) / 0.32) ** 2)
    base = Image.fromarray((a * 255).astype(np.uint8))
    lines = Image.new('L', (w, h), 0)
    ld = ImageDraw.Draw(lines)
    panels = Image.new('L', (w, h), 0)
    pd = ImageDraw.Draw(panels)
    walls = Image.new('L', (w, h), 0)
    wd = ImageDraw.Draw(walls)
    # receding frames of the corridor (ceiling light panels, glass wall light strips)
    for j in range(0, 16):
        f0, f1 = 1 / (1 + j * 0.36), 1 / (1 + (j + 0.55) * 0.36)
        def rect(f):
            return (vp[0] - vp[0] * f, vp[1] - vp[1] * f, vp[0] + (w - vp[0]) * f, vp[1] + (h - vp[1]) * f)
        a0, a1 = rect(f0), rect(f1)
        # luminous ceiling panel (trapezoid between two depths, central 44 %)
        def lerpx(r, q):
            return r[0] + (r[2] - r[0]) * q
        pd.polygon([(lerpx(a0, 0.28), a0[1]), (lerpx(a0, 0.72), a0[1]), (lerpx(a1, 0.72), a1[1]), (lerpx(a1, 0.28), a1[1])],
                   fill=int(255 * f0 ** 0.35))
        # glass wall light strips (vertical, both sides)
        for side in (0, 2):
            x = a0[side]
            wd.line((x, a0[1] + (a0[3] - a0[1]) * 0.08, x, a0[3] - (a0[3] - a0[1]) * 0.2), fill=int(200 * f0 ** 0.5), width=max(1, int(7 * f0)))
        # door-frame outline
        ld.rectangle(a0, outline=int(60 * f0), width=max(1, int(3 * f0)))
    P = np.asarray(panels, np.float32) / 255
    Wl = np.asarray(walls, np.float32) / 255
    Lg = np.asarray(lines, np.float32) / 255
    soft = lambda m, r: np.asarray(Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), np.float32) / 255
    light = P * 0.9 + soft(P, 14) * 0.9 + Wl * 0.7 + soft(Wl, 10) * 1.0 + Lg * 0.5
    # glossy floor: mirrored, blurred, dimmed copy of the upper half below the vanishing line
    vy = int(vp[1])
    up = light[:vy][::-1]
    n = min(up.shape[0], h - vy)
    refl = soft(up[:n], 7) * np.linspace(0.55, 0.05, n)[:, None]
    light[vy:vy + n] += refl
    cool = np.array([0.78, 0.86, 1.0], np.float32)
    out = np.asarray(base, np.float32) / 255 * 0.8 + light[..., None] * cool * 0.42
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    out += np.exp(-(((xx - vp[0]) / 300) ** 2 + ((yy - vp[1]) / 200) ** 2))[..., None] * np.array([1.0, 0.8, 0.52]) * 0.6
    return np.clip(out, 0, 2).astype(np.float32), S


def draw_corridor(cv, t):
    img, S = corridor()
    z = 1.0 + 0.06 * (t / DUR)          # slow dolly in
    sw, sh = W / z * S / S, H / z
    h, w = img.shape[:2]
    cx, cy = w / 2 + 30 * math.sin(t * 0.2), h / 2
    x0, y0 = int(cx - W / (2 * z) * 1), int(cy - H / (2 * z))
    crop = img[max(0, y0):y0 + int(H / z), max(0, x0):x0 + int(W / z)]
    im = Image.fromarray((np.clip(crop, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
    cv[:] = np.asarray(im, np.float32) / 255


# ------------------------------------------------------------------ the clip
@functools.lru_cache(maxsize=None)
def standin_frame():
    """Stand-in until the real C2 clip arrives: Actor 2's free character portrait, marked STAND-IN."""
    sheet = Image.open(os.path.join(HERE, 'cast', 'karim.jpg')).convert('RGB')
    face = sheet.crop((0, 0, sheet.width // 2, sheet.height // 2))
    face = ImageOps.fit(face, (1080, 1920), Image.LANCZOS, centering=(0.5, 0.35))
    d = ImageDraw.Draw(face)
    f = R.font('mont', 64, 700)
    d.rectangle((0, 1700, 1080, 1800), fill=(150, 20, 20))
    d.text((540, 1750), 'STAND-IN  ·  awaiting C2', font=f, fill='white', anchor='mm')
    return face


def clip_frame(u):
    """Vertical RGB PIL frame of the actor clip at clip-time u (seconds)."""
    if CLIP:
        idx = min(len(clip_frames()) - 1, max(0, int(u * FPS)))
        return clip_frames()[idx]
    img = standin_frame()
    z = 1 + 0.03 * u
    w, h = img.size
    return img.crop((int(w * (1 - 1 / z) / 2), int(h * (1 - 1 / z) / 2), int(w * (1 + 1 / z) / 2), int(h * (1 + 1 / z) / 2)))


@functools.lru_cache(maxsize=1)
def clip_frames():
    tmp = os.path.join(BUILD, 'clip_frames')
    os.makedirs(tmp, exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', CLIP, '-vf', f'fps={FPS},scale=1080:1920', os.path.join(tmp, 'f%04d.jpg')], check=True)
    return [Image.open(os.path.join(tmp, f)).convert('RGB') for f in sorted(os.listdir(tmp))]


def door(cv, t):
    """The vertical clip as a glowing door of light; widens to full 16:9 at the end."""
    if t < DOOR_OPEN[0] or t >= CITY[0] + 0.6:
        return
    open_q = ease_out(seg(t, *DOOR_OPEN))
    widen = ease_io(seg(t, *WIDEN))
    u = max(0.0, t - CLIP_START)
    frame = clip_frame(u)
    # geometry: door rect lerps to full frame
    dw = lerp(DOOR_W * open_q, W, widen)
    dh = lerp(DOOR_H, H, widen)
    cx = lerp(DOOR_C[0], W / 2, widen)
    cy = lerp(DOOR_C[1], H / 2, widen)
    x0, y0 = int(cx - dw / 2), int(cy - dh / 2)
    iw, ih = max(2, int(dw)), max(2, int(dh))
    # source crop: full vertical frame -> centre 16:9 band as the door widens (cover fit)
    fw, fh = frame.size
    ar = iw / ih
    if fw / fh > ar:
        cw_, ch_ = fh * ar, fh
    else:
        cw_, ch_ = fw, fw / ar
    fy = fh * lerp(0.5, 0.42, widen)  # keep the face in the upper-middle of the widescreen crop
    box = (fw / 2 - cw_ / 2, max(0, min(fh - ch_, fy - ch_ / 2)), fw / 2 + cw_ / 2, 0)
    box = (box[0], box[1], box[2], box[1] + ch_)
    img = frame.resize((iw, ih), Image.BICUBIC, box=box)
    arr = np.asarray(img, np.float32) / 255
    if not CLIP:
        arr *= 0.92
    # pre-door light
    reveal = seg(t, DOOR_OPEN[0], DOOR_OPEN[1] + 0.3)
    alpha = min(1.0, reveal * 1.6) * (1 - seg(t, CITY[0], CITY[0] + 0.6))
    r = R.region(x0, y0, iw, ih)
    if r:
        cv[r[0]] = cv[r[0]] * (1 - alpha) + arr[r[1]] * alpha
    # floor reflection
    if widen < 0.98:
        rh = int(min(H - (y0 + ih), ih * 0.35))
        if rh > 4:
            refl = arr[::-1][:rh] * np.linspace(0.32, 0, rh)[:, None, None] * (1 - widen) * alpha
            rr = R.region(x0, y0 + ih + 6, iw, rh)
            if rr:
                cv[rr[0]] += refl[rr[1]]
    # door frame: thin gold light edges + halo, fade as it widens
    edge = (1 - widen) * alpha
    if edge > 0.01:
        m = np.zeros((R.LH, R.LW), np.float32)
        X0, Y0, X1, Y1 = x0 / 4, y0 / 4, (x0 + iw) / 4, (y0 + ih) / 4
        inside_x = (R._lx / 4 >= X0) & (R._lx / 4 <= X1)
        inside_y = (R._ly / 4 >= Y0) & (R._ly / 4 <= Y1)
        dx = np.minimum(np.abs(R._lx / 4 - X0), np.abs(R._lx / 4 - X1))
        dy = np.minimum(np.abs(R._ly / 4 - Y0), np.abs(R._ly / 4 - Y1))
        m += np.exp(-(dx / 1.2) ** 2) * inside_y + np.exp(-(dy / 1.2) ** 2) * inside_x
        add_light(cv, m, GOLD_HI, 0.9 * edge)
        add_light(cv, radial(cx, cy, 520) * 0.6, np.array([1.0, 0.75, 0.4]), 0.25 * edge)
    if DOOR_OPEN[0] < t < DOOR_OPEN[1] + 0.25:
        flash(cv, 0.3 * math.sin(math.pi * seg(t, DOOR_OPEN[0], DOOR_OPEN[1] + 0.25)) * (1 - reveal), DOOR_C[0], DOOR_C[1], 420)


def relay_light(cv, t):
    """The golden relay light: travels in from the left and opens the door."""
    a, b = 1.3, DOOR_OPEN[0] + 0.15
    if a <= t <= b + 0.3:
        q = ease_io(seg(t, a, b))
        for k in range(24, -1, -1):
            qq = max(0, q - k * 0.012)
            x = lerp(-60, DOOR_C[0], qq)
            y = lerp(760, DOOR_C[1] + DOOR_H / 2 - 40, qq) - 120 * math.sin(math.pi * qq)
            splat(cv, x, y, 2 + (6 if k == 0 else 0), (1.3 if k == 0 else 0.5 * (1 - k / 25)))
        if t <= b:
            x = lerp(-60, DOOR_C[0], q)
            y = lerp(760, DOOR_C[1] + DOOR_H / 2 - 40, q) - 120 * math.sin(math.pi * q)
            add_light(cv, radial(x, y, 140), np.array([1.0, 0.72, 0.35]), 0.5)


DUST = R.Dust(140, 77, rise=30)


def city_handoff(cv, t):
    """Hand-off to the City of Excellence: wide aerial, the light flies to the first tower."""
    u = t - CITY[0]
    cam = (CF.LX[0] + 640 + 60 * u, 0.52 + 0.025 * u, 840)  # tower 1 stays left-of-centre
    CF.draw_city(cv, 30.0, cam, bright=1.0, all_lit=0.0)
    x0, y0 = CF.LX[0] - 1500, CF.HY - 700
    x1, y1 = CF.hover(0)
    q = ease_io(seg(u, 0.3, 3.4))
    for k in range(26, -1, -1):
        qq = max(0, q - k * 0.01)
        p = CF.bez((x0, y0), (x1, y1), qq)
        sx, sy = CF.to_screen(*p, cam)
        splat(cv, sx, sy, 3 + (8 if k == 0 else 0), 1.6 if k == 0 else 0.7 * (1 - k / 27))
        if k == 0:
            add_light(cv, radial(sx, sy, 150), np.array([1.0, 0.72, 0.35]), 0.6)
    if q >= 0.99:
        sx, sy = CF.to_screen(*CF.crown(0), cam)
        lvl = seg(u, 3.4, 3.8)
        add_light(cv, radial(sx, sy, 160), GOLD_HI, 0.9 * lvl + 0.8 * math.exp(-(u - 3.4) / 0.25))
        R.firework(cv, t, CITY[0] + 3.4, sx, sy - 30, 5, n=40, life=1.2, speed=300)
    tq = seg(u, 1.0, 1.8)
    composite(cv, text_layer('EXCELLENCE IS NEVER ACHIEVED ALONE.', 'cinzel', 54, 700, 5, 'gold', 10), W / 2, 930,
              lerp(1.06, 1.0, ease_out(tq)), ease_io(tq) * (1 - seg(u, 4.2, 4.7)), glow=0.8)


# ------------------------------------------------------------------ Eureka branding
@functools.lru_cache(maxsize=None)
def corner_bug(width=176):
    """Permanent corner logo: the authentic Eureka logo on a crisp white badge with a fine gold edge."""
    logo, _ = R.logo_image(R.manifest()['eureka_logo'])
    pad = int(width * 0.08)
    inner = width - 2 * pad
    lh = int(inner * logo.height / logo.width)
    card = Image.new('RGBA', (width + 16, lh + 2 * pad + 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((8, 8, 8 + width, 8 + lh + 2 * pad), 10, fill=(255, 255, 255, 236), outline=(214, 180, 100, 255), width=2)
    card.alpha_composite(logo.resize((inner, lh), Image.LANCZOS), (8 + pad, 8 + pad))
    sh = Image.new('L', card.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((8, 8, 8 + width, 8 + lh + 2 * pad), 10, fill=255)
    return Layer(card, sh.filter(ImageFilter.GaussianBlur(8)))


def eureka(cv, t):
    """Large opening reveal, then it flies to the top-right corner and stays (W*0.09 wide)."""
    big = R.eureka_layer(520, 360)
    bug = corner_bug()
    corner = (W - 48 - bug.w / 2, 40 + bug.h / 2)
    if t < LOGO_TO_CORNER:
        q = seg(t, LOGO_IN, LOGO_IN + 0.8)
        composite(cv, big, W / 2, H / 2 - 20, lerp(0.92, 1.0, ease_out(q)), ease_io(q), glow=0.5)
        return
    m = ease_io(seg(t, LOGO_TO_CORNER, LOGO_TO_CORNER + 0.7))
    if m < 1:
        s = lerp(1.0, bug.w / big.w, m)
        composite(cv, big, lerp(W / 2, corner[0], m), lerp(H / 2 - 20, corner[1], m), s, 1.0, glow=0.5 * (1 - m))
    else:
        composite(cv, bug, *corner, 1.0, 1.0, glow=0.0)


def frame(t):
    cv = np.zeros((H, W, 3), np.float32)
    if t < CITY[0]:
        draw_corridor(cv, t)
        cv *= ease_io(seg(t, 0, 0.8)) * (0.45 if t < LOGO_TO_CORNER + 0.4 else lerp(0.45, 1.0, seg(t, LOGO_TO_CORNER + 0.4, DOOR_OPEN[0])))
        DUST.draw(cv, t, 0.6)
        relay_light(cv, t)
        door(cv, t)
    else:
        city_handoff(cv, t)
        door(cv, t)  # fades out over the city
    bloom(cv, 0.22, 0.85)
    cv *= vignette(0.4)
    eureka(cv, t)  # branding sits above grading, always crisp
    cv *= 1 - seg(t, DUR - 0.5, DUR)
    return tonemap(cv)


def render_video(out):
    os.makedirs(BUILD, exist_ok=True)
    silent = os.path.join(BUILD, 'poc_video.mp4')
    pr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '15',
                           '-pix_fmt', 'yuv420p', silent], stdin=subprocess.PIPE)
    for f in range(int(DUR * FPS)):
        pr.stdin.write(frame(f / FPS).tobytes())
    pr.stdin.close()
    pr.wait()
    music = os.path.join(BUILD, 'poc_music.wav')
    subprocess.run([sys.executable, os.path.join(HERE, 'poc_music.py'), music], check=True)
    inputs = ['-i', silent, '-i', music]
    if CLIP:  # actor's dialogue, placed when the door clip plays; music ducks under it
        inputs += ['-i', CLIP]
        filt = (f'[2:a]adelay={int(CLIP_START * 1000)}|{int(CLIP_START * 1000)},apad[d];'
                f'[1:a][d]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[m];'
                f'[m][d]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]')
        amap = ['-filter_complex', filt, '-map', '0:v', '-map', '[a]']
    else:
        amap = ['-map', '0:v', '-map', '1:a']
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, *amap, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k',
                    '-t', str(DUR), '-movflags', '+faststart', out], check=True)
    print('wrote', out)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'stills'
    if cmd == 'stills':
        os.makedirs(BUILD, exist_ok=True)
        for s in sys.argv[2:]:
            Image.fromarray(frame(float(s))).save(os.path.join(BUILD, f'poc_{float(s):05.2f}.png'))
    else:
        if len(sys.argv) > 2:
            CLIP = os.path.abspath(sys.argv[2])
        render_video(os.path.join(BUILD, 'ptl_poc.mp4'))
