"""Two-milestone sample (Hope + City Hospital), 12 s, with corner logo and music."""
import os, subprocess, sys
import numpy as np
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import milestones as MS, poc2 as P2, render as R  # noqa: E402

PICK = [1, 3]
DUR = MS.SLOT * len(PICK)
FPS = 30
BUILD = P2.BUILD


def frame(t):
    cv = np.zeros((R.H, R.W, 3), np.float32)
    k = min(len(PICK) - 1, int(t // MS.SLOT))
    i = PICK[k]
    MS.milestone(cv, t - k * MS.SLOT, i, R.manifest()['institutions'][i], i)
    R.bloom(cv, 0.24, 0.8)
    cv *= R.vignette(0.35)
    P2.eureka(cv, 99.0)  # permanent corner logo
    cv *= R.seg(t, 0, 0.3) * (1 - R.seg(t, DUR - 0.4, DUR))
    return R.tonemap(cv)


def chunk(args):
    a, b, path = args
    pr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1920x1080', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    for f in range(a, b):
        pr.stdin.write(frame(f / FPS).tobytes())
    pr.stdin.close(); pr.wait()
    return path


if __name__ == '__main__':
    d = os.path.join(BUILD, 'ms_chunks'); os.makedirs(d, exist_ok=True)
    nf = int(DUR * FPS)
    jobs = [(a, min(nf, a + 30), os.path.join(d, f'c{a:04d}.mp4')) for a in range(0, nf, 30)]
    with Pool(4) as p:
        list(p.imap(chunk, jobs))
    open(os.path.join(d, 'list.txt'), 'w').writelines(f"file '{j[2]}'\n" for j in jobs)
    silent = os.path.join(BUILD, 'ms_video.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', os.path.join(d, 'list.txt'), '-c', 'copy', silent], check=True)
    music = os.path.join(BUILD, 'ms_music.wav')
    subprocess.run([sys.executable, os.path.join(HERE, 'poc_music.py'), music, str(DUR)], check=True,
                   env=dict(os.environ, PTL_CUTS=f'0.2,{MS.CITY_BEAT:.2f},{MS.SLOT + MS.CITY_BEAT:.2f}'))
    out = os.path.join(BUILD, 'ptl_milestone_sample.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', silent, '-i', music, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac',
                    '-b:a', '256k', '-t', str(DUR), '-movflags', '+faststart', out], check=True)
    print('wrote', out)
