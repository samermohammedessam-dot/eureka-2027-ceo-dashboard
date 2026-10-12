"""13 s original music bed for the proof of concept (synthesised: royalty-free).
Warm piano + strings, a soft pulse from the door opening, a swell into the city hand-off."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import music as M  # noqa: E402
from music import Bus, boom, celesta, crash, kick, mf, piano, riser, spiccato, strings_pad, timpani  # noqa: E402

DUR = 13.0
M.N = int(M.SR * DUR)
N = M.N
B = 0.55
CH = {'D': [50, 54, 57], 'Bm': [47, 50, 54], 'G': [43, 47, 50], 'A': [45, 49, 52]}
PROG = [(0.0, 'D'), (2.2, 'Bm'), (4.4, 'G'), (6.6, 'A'), (8.8, 'D'), (11.0, 'G')]


def compose():
    pad, strs, bell, perc, fx, low = (Bus(n) for n in ['pad', 'str', 'bell', 'perc', 'fx', 'low'])
    post = Bus('post')
    for t, n in PROG:
        d = min(2.2, DUR - t)
        for j, m in enumerate(CH[n] + [CH[n][1] + 12]):
            pad.add(t, strings_pad(mf(m + 12), d, 1600 + 160 * t), 0.07, pan=(j - 1.5) * 0.35)
        low.add(t, strings_pad(mf(CH[n][0] - 12), d, 500), 0.22)
    for t, m in [(0.3, 66), (0.85, 69), (1.4, 74), (2.5, 73), (3.6, 71), (4.15, 74), (4.7, 78), (5.8, 76),
                 (6.9, 73), (7.45, 76), (8.0, 81), (9.1, 78)]:
        bell.add(t, piano(mf(m)), 0.30)
    t = 2.4
    while t < DUR - 0.3:  # pulse starts as the light opens the door
        n = [c for s, c in PROG if s <= t + 1e-6][-1]
        k = int(round((t - 2.4) / (B / 2)))
        strs.add(t, spiccato(mf(CH[n][0] + (12 if k % 2 else 0))), 0.10 + 0.06 * min(1, (t - 2.4) / 6), pan=-0.3)
        t += B / 2
    for t in np.arange(3.3, DUR - 0.5, 2 * B):
        perc.add(t, kick(), 0.22)
    perc.add(2.4, timpani(mf(38), 1.6), 0.25)
    for k, m in enumerate([86, 90, 93]):
        bell.add(2.45 + 0.07 * k, celesta(mf(m), 1.6), 0.10)
    fx.add(6.8, riser(2.0), 0.18)
    perc.add(8.8, boom(3.0), 0.40)
    fx.add(8.8, crash(3.0), 0.10)
    for k, m in enumerate([74, 78, 81, 86]):
        bell.add(8.9 + 0.14 * k, celesta(mf(m), 2.0), 0.13)
    return [pad, strs, Bus('brass'), bell, perc, fx, low], post


if __name__ == '__main__':
    out = sys.argv[1]
    arc = ([0, 2.3, 2.4, 8.7, 8.8, 13], [-9, -8, -6, -4, -1.5, -1.5])
    x = M.mix(*compose(), arc=arc)
    t = np.arange(N) / M.SR
    x *= np.clip((DUR - t) / 1.2, 0, 1)
    M.write_wav(out, x)
    print('wrote', out)
