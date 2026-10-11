"""Generate clearly-marked PLACEHOLDER assets (abstract gradients, no people, no real logos)
so the pipeline can be tested before the real photos/logos are dropped in."""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'build', 'placeholder_assets')
F = lambda s: ImageFont.truetype(os.path.join(HERE, 'fonts', 'Montserrat.ttf'), s)
g = np.random.default_rng(3)


def photo(path, label, hue):
    y, x = np.mgrid[0:1000, 0:1500] / 1000
    base = np.stack([0.25 + 0.5 * hue[0] * (1 - y), 0.25 + 0.4 * hue[1] * x / 1.5, 0.35 + 0.4 * hue[2] * y], -1)
    for _ in range(6):
        cx, cy, r = g.uniform(0, 1.5), g.uniform(0, 1), g.uniform(0.1, 0.35)
        base += 0.25 * np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / r ** 2)[..., None] * g.uniform(0.3, 1, 3)
    im = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.text((750, 470), 'PLACEHOLDER PHOTO', font=F(64), fill=(255, 255, 255), anchor='mm')
    d.text((750, 560), label, font=F(40), fill=(255, 255, 255), anchor='mm')
    im.save(path, quality=90)


def logo(path, label, color):
    im = Image.new('RGBA', (900, 450), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((40, 85, 320, 365), outline=color, width=22)
    d.text((370, 170), 'PARTNER', font=F(80), fill=color)
    d.text((370, 270), label, font=F(80), fill=color)
    im.save(path)


os.makedirs(out, exist_ok=True)
man = {'eureka_logo': 'eureka_logo.png', 'team_photos': [], 'institutions': []}
im = Image.new('RGBA', (1000, 360), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
d.text((500, 140), 'EUREKA', font=F(170), fill=(26, 43, 76), anchor='mm')
d.text((500, 285), 'LOGO PLACEHOLDER', font=F(48), fill=(201, 162, 75), anchor='mm')
im.save(os.path.join(out, 'eureka_logo.png'))
for k in range(12):
    p = f'team_{k:02d}.jpg'
    photo(os.path.join(out, p), f'Team {k + 1}', g.uniform(0.3, 1, 3))
    man['team_photos'].append(p)
names = ['Placeholder Hospital One', 'Placeholder Medical Center Two', 'Placeholder Specialized Hospital Three',
         'Placeholder Hospital Four', 'Placeholder Clinic Five', 'Placeholder Hospital Six',
         'Placeholder Healthcare Seven', 'Placeholder Hospital Eight', 'Placeholder Center Nine',
         'Placeholder Hospital Ten']
for i, n in enumerate(names):
    lp = f'inst{i:02d}_logo.png'
    logo(os.path.join(out, lp), f'{i + 1:02d}', tuple(int(c) for c in g.integers(20, 160, 3)) + (255,))
    ph = []
    for j in range(2 + i % 3):
        p = f'inst{i:02d}_photo{j}.jpg'
        photo(os.path.join(out, p), f'Institution {i + 1} - {j + 1}', g.uniform(0.3, 1, 3))
        ph.append(p)
    man['institutions'].append({'name': n, 'logo': lp, 'photos': ph})
json.dump(man, open(os.path.join(out, 'manifest.json'), 'w'), indent=1)
print('placeholders in', out)
