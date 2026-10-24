"""16:9 test cut of the Promoat A1 clip (9:16) — no stretching, no side panels.

The tall frame is scaled to full width and a 16:9 window travels inside it, following the action:
his contemplative face -> the crown as he lowers it; then the clip's own close-up of the water.
Adds a gentle grade, fine grain and the authentic Eureka corner logo.
  python3 a1_test.py <A1.mp4> <out.mp4>
"""
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'EUREKA_THE_POWER_OF_TEN'))
os.environ.setdefault('EUREKA_ASSETS', os.path.join(HERE, '..', 'assets_dl'))

SRC, OUT = sys.argv[1], sys.argv[2]
BUILD = os.path.dirname(os.path.abspath(OUT))
CUT = 6.88          # Promoat's internal cut to the water close-up
IN = 0.6            # skip the dark fade-in


def logo_png():
    import film  # the POWER OF TEN helpers: keyed, transparent authentic logo
    lg = film.eureka_rgba()
    w = 176
    lg = lg.resize((w, int(w * lg.height / lg.width)))
    p = os.path.join(BUILD, 'eureka_corner.png')
    lg.save(p)
    return p


def ytrack(keys):
    """ffmpeg expression: piecewise-linear crop top (fraction of scaled height) over time t."""
    (t0, y0), rest = keys[0], keys[1:]
    expr = f'{y0}'
    for (ta, ya), (tb, yb) in zip(keys, rest):
        expr = f'if(gte(t,{ta}),{ya}+({yb}-{ya})*min(1,(t-{ta})/{tb - ta}),{expr})'
    return expr


def main():
    logo = logo_png()
    # scaled to 1920 wide -> about 3371 tall; crop top in pixels = fraction * ih
    a = ytrack([(0, 0.04), (1.5, 0.10), (3.2, 0.42), (5.0, 0.55), (CUT - IN, 0.63)])
    b = ytrack([(0, 0.44), (10, 0.36)])
    grade = 'eq=contrast=1.04:saturation=1.06:gamma=0.98,unsharp=5:5:0.55:5:5:0.0,noise=alls=5:allf=t'
    fc = (f"[0:v]trim={IN}:{CUT},setpts=PTS-STARTPTS,scale=1920:-2:flags=lanczos,"
          f"crop=1920:1080:0:'({a})*ih',{grade}[va];"
          f"[0:v]trim={CUT + 0.04}:10.0,setpts=PTS-STARTPTS,scale=1920:-2:flags=lanczos,"
          f"crop=1920:1080:0:'({b})*ih',{grade}[vb];"
          f"[va][vb]concat=n=2:v=1:a=0,fps=30,fade=in:0:12[v];"
          f"[1:v]format=rgba,colorchannelmixer=aa=0.92[lg];[v][lg]overlay=W-w-44:30[o]")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', SRC, '-i', logo, '-filter_complex', fc,
                    '-map', '[o]', '-an', '-c:v', 'libx264', '-crf', '17', '-preset', 'slow',
                    '-pix_fmt', 'yuv420p', OUT], check=True)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
