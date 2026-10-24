"""THE MOMENT — footage plates.

arch   : the Archimedes opening. Each edit segment takes a 16:9 window that travels inside the tall
         720x1264 Promoat master (no stretching, no side panels). The visible window is AI-upscaled
         (Real-ESRGAN x4 -> 1920x1080) and blended with a Lanczos pass so skin stays natural.
panel  : modern scenes as full-height 9:16 panels (720x1264 -> 616x1080: a downscale, so no
         enlargement at all), for the split-screen service compositions.
Plates are stored as raw uint8 memmaps (frames x H x W x 3) at the source 24 fps.

  python3 plates.py arch            # needs torch + SR_WEIGHTS (see sr.py)
  python3 plates.py panels [names]
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'build', 'moment')
OUT = os.path.join(SRC, 'plates')
SFPS = 24
PW, PH = 616, 1080

# Edit decision list for the discovery (film seconds are implied by the running sum of durations).
# keys: (seconds into the segment, crop-top as a fraction of the source height, window width fraction)
ARCH = [
    ('A_discovery', 0.60, 6.88, [(0, 0.04, 1.0), (1.5, 0.10, 1.0), (3.2, 0.42, 1.0), (5.0, 0.55, 1.0), (6.28, 0.63, 1.0)]),
    ('A_discovery', 6.92, 8.94, [(0, 0.44, 1.0), (2.02, 0.41, 0.94)]),
    ('B_realization', 0.40, 3.20, [(0, 0.10, 1.0), (1.2, 0.18, 1.0), (2.8, 0.47, 1.0)]),
    ('B_realization', 6.40, 8.40, [(0, 0.02, 1.0), (2.0, 0.0, 0.92)]),
    ('A4_eureka_voiced', 0.00, 2.60, [(0, 0.17, 1.0), (1.0, 0.13, 1.0), (2.6, 0.12, 0.95)]),
    ('A_discovery', 8.94, 10.0, [(0, 0.41, 0.94), (1.06, 0.40, 0.86)]),
]


def arch_edl():
    """Film-time layout of the plate: [(film_t0, film_t1, segment_index)]."""
    out, t = [], 0.0
    for i, (_, a, b, _) in enumerate(ARCH):
        out.append((t, t + (b - a), i))
        t += b - a
    return out


def decode(path, t0=None, t1=None, scale=None):
    w, h = map(int, subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries',
                                    'stream=width,height', '-of', 'csv=p=0', path],
                                   capture_output=True, text=True).stdout.strip().split(','))
    vf = [f'fps={SFPS}'] + ([f'scale={scale[0]}:{scale[1]}:flags=lanczos'] if scale else [])
    cut = (['-ss', str(t0)] if t0 is not None else []) + (['-to', str(t1)] if t1 is not None else [])
    raw = subprocess.run(['ffmpeg', '-v', 'error'] + cut + ['-i', path, '-vf', ','.join(vf), '-f', 'rawvideo',
                          '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    ow, oh = scale or (w, h)
    return np.frombuffer(raw, np.uint8).reshape(-1, oh, ow, 3)


def interp(keys, u):
    ts = [k[0] for k in keys]
    return float(np.interp(u, ts, [k[1] for k in keys])), float(np.interp(u, ts, [k[2] for k in keys]))


def build_arch():
    sys.path.insert(0, HERE)
    import torch
    import sr
    torch.set_num_threads(os.cpu_count() or 4)
    net = sr.load_model()
    frames = []
    for name, a, b, keys in ARCH:
        src = decode(os.path.join(SRC, f'{name}.mp4'), a, b)
        n = int(round((b - a) * SFPS))
        for j in range(min(n, len(src))):
            fr = src[j]
            H0, W0, _ = fr.shape
            yf, wf = interp(keys, j / SFPS)
            cw = int(W0 * wf) // 2 * 2
            ch = int(cw * 9 / 16) // 2 * 2
            x0 = (W0 - cw) // 2
            y0 = int(np.clip(yf * H0, 0, H0 - ch))
            win = np.ascontiguousarray(fr[y0:y0 + ch, x0:x0 + cw])
            up = sr.upscale_frame(net, win)          # x2 of the window (x4 model, area-resampled)
            ai = np.asarray(Image.fromarray(up).resize((1920, 1080), Image.LANCZOS), np.float32)
            lz = np.asarray(Image.fromarray(win).resize((1920, 1080), Image.LANCZOS), np.float32)
            frames.append(np.clip(0.72 * ai + 0.28 * lz, 0, 255).astype(np.uint8))
            print(f'arch {name} {len(frames)}', flush=True)
    os.makedirs(OUT, exist_ok=True)
    mm = np.lib.format.open_memmap(os.path.join(OUT, 'arch.npy'), 'w+', np.uint8, (len(frames), 1080, 1920, 3))
    for i, f in enumerate(frames):
        mm[i] = f
    mm.flush()
    json.dump({'edl': arch_edl(), 'fps': SFPS, 'frames': len(frames)}, open(os.path.join(OUT, 'arch.json'), 'w'))
    print('arch plate', len(frames), 'frames')


def build_panel(name):
    fr = decode(os.path.join(SRC, f'{name}.mp4'), scale=(PW, PH))
    os.makedirs(OUT, exist_ok=True)
    np.save(os.path.join(OUT, f'{name}.npy'), fr)
    print('panel', name, fr.shape)


if __name__ == '__main__':
    if sys.argv[1] == 'arch':
        build_arch()
    elif sys.argv[1] == 'panels':
        for n in sys.argv[2:]:
            build_panel(n)
