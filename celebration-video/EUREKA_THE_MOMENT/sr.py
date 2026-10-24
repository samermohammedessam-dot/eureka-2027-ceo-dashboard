"""AI upscaling for the 720x1264 Promoat masters (Real-ESRGAN realesr-general-x4v3, CPU).

Each frame is super-resolved x4 then resampled to x2 (1440x2528): a clean master that the 16:9
framing can crop from with ~1.3x enlargement instead of ~2.7x.
  python3 sr.py <in.mp4> <out.mp4> [--t0 S --t1 S] [--denoise 0.5]
Needs torch (CPU) on PYTHONPATH and the weights in $SR_WEIGHTS (realesr-general-x4v3.pth).
"""
import os
import subprocess
import sys

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F


class SRVGGNetCompact(nn.Module):
    """The compact Real-ESRGAN network (architecture as published with realesr-general-x4v3)."""

    def __init__(self, num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4):
        super().__init__()
        self.upscale = upscale
        self.body = nn.ModuleList([nn.Conv2d(num_in_ch, num_feat, 3, 1, 1), nn.PReLU(num_parameters=num_feat)])
        for _ in range(num_conv):
            self.body.append(nn.Conv2d(num_feat, num_feat, 3, 1, 1))
            self.body.append(nn.PReLU(num_parameters=num_feat))
        self.body.append(nn.Conv2d(num_feat, num_out_ch * upscale * upscale, 3, 1, 1))
        self.upsampler = nn.PixelShuffle(upscale)

    def forward(self, x):
        out = x
        for m in self.body:
            out = m(out)
        out = self.upsampler(out)
        return out + F.interpolate(x, scale_factor=self.upscale, mode='nearest')


def load_model():
    w = os.environ.get('SR_WEIGHTS', 'realesr-general-x4v3.pth')
    net = SRVGGNetCompact()
    sd = torch.load(w, map_location='cpu')
    net.load_state_dict(sd.get('params', sd), strict=True)
    return net.eval()


def probe(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries',
                          'stream=width,height,r_frame_rate', '-of', 'csv=p=0', path],
                         capture_output=True, text=True).stdout.strip().split(',')
    num, den = out[2].split('/')
    return int(out[0]), int(out[1]), float(num) / float(den)


@torch.no_grad()
def upscale_frame(net, rgb, tile=360):
    """x4 inference in overlapping horizontal bands (bounded memory), then x2 output via area resample."""
    h, w, _ = rgb.shape
    x = torch.from_numpy(rgb).permute(2, 0, 1)[None].float() / 255
    out = torch.zeros(1, 3, h * 4, w * 4)
    pad = 16
    for y0 in range(0, h, tile):
        a, b = max(0, y0 - pad), min(h, y0 + tile + pad)
        y = net(x[:, :, a:b])
        ta, tb = (y0 - a) * 4, (y0 - a + min(tile, h - y0)) * 4
        out[:, :, y0 * 4:(y0 + min(tile, h - y0)) * 4] = y[:, :, ta:tb]
    out = F.interpolate(out.clamp(0, 1), size=(h * 2, w * 2), mode='area')
    return (out[0].permute(1, 2, 0).numpy() * 255 + 0.5).astype(np.uint8)


def main():
    src, dst = sys.argv[1], sys.argv[2]
    t0 = float(sys.argv[sys.argv.index('--t0') + 1]) if '--t0' in sys.argv else 0.0
    t1 = float(sys.argv[sys.argv.index('--t1') + 1]) if '--t1' in sys.argv else None
    torch.set_num_threads(int(os.environ.get('SR_THREADS', os.cpu_count() or 4)))
    net = load_model()
    w, h, fps = probe(src)
    cut = ['-ss', str(t0)] + (['-to', str(t1)] if t1 else [])
    dec = subprocess.Popen(['ffmpeg', '-v', 'error'] + cut + ['-i', src, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w * 2}x{h * 2}',
                            '-r', f'{fps}', '-i', '-', '-c:v', 'libx264', '-crf', '12', '-preset', 'slow',
                            '-pix_fmt', 'yuv420p', dst], stdin=subprocess.PIPE)
    n = 0
    while True:
        buf = dec.stdout.read(w * h * 3)
        if len(buf) < w * h * 3:
            break
        enc.stdin.write(upscale_frame(net, np.frombuffer(buf, np.uint8).reshape(h, w, 3)).tobytes())
        n += 1
        if n % 24 == 0:
            print(f'{os.path.basename(src)}: {n} frames', flush=True)
    enc.stdin.close()
    enc.wait()
    print('wrote', dst, n, 'frames')


if __name__ == '__main__':
    main()
