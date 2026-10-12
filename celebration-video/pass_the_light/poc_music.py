"""13 s original music bed for the proof of concept (synthesised: royalty-free).
Warm piano + strings, a soft pulse from the door opening, a swell into the city hand-off."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import music as M  # noqa: E402
from music import Bus, boom, celesta, crash, kick, mf, piano, riser, spiccato, strings_pad, timpani  # noqa: E402

DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 13.0
M.N = int(M.SR * DUR)
N = M.N
B = 0.55
CH = {'D': [50, 54, 57], 'Bm': [47, 50, 54], 'G': [43, 47, 50], 'A': [45, 49, 52]}
PROG = [(0.0, 'D'), (2.2, 'Bm'), (4.4, 'G'), (6.6, 'A'), (8.8, 'D'), (11.0, 'G'), (13.2, 'A'), (15.4, 'D')]


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
    DOOR, CITY, ARRIVE = (float(v) for v in os.environ.get('PTL_CUTS', '2.6,6.75,10.95').split(','))  # cut points
    t = DOOR
    while t < DUR - 0.3:  # pulse starts as the relay light opens the door
        n = [c for s_, c in PROG if s_ <= t + 1e-6][-1]
        k = int(round((t - DOOR) / (B / 2)))
        strs.add(t, spiccato(mf(CH[n][0] + (12 if k % 2 else 0))), 0.09 + 0.07 * min(1, (t - DOOR) / 8), pan=-0.3)
        t += B / 2
    for t in np.arange(CITY, DUR - 0.5, 2 * B):
        perc.add(t, kick(), 0.24)
    perc.add(DOOR, timpani(mf(38), 1.6), 0.25)
    for k, m in enumerate([86, 90, 93]):
        bell.add(DOOR + 0.05 + 0.07 * k, celesta(mf(m), 1.6), 0.10)
    fx.add(CITY - 1.6, riser(1.6), 0.16)
    perc.add(CITY, boom(3.0), 0.38)
    fx.add(CITY, crash(2.5), 0.08)
    fx.add(ARRIVE - 1.4, riser(1.4), 0.14)
    perc.add(ARRIVE, boom(3.0), 0.45)
    perc.add(ARRIVE, timpani(mf(38), 1.8), 0.35)
    fx.add(ARRIVE, crash(3.0), 0.12)
    for k, m in enumerate([74, 78, 81, 86, 90]):
        bell.add(ARRIVE + 0.1 + 0.14 * k, celesta(mf(m), 2.2), 0.13)
    return [pad, strs, Bus('brass'), bell, perc, fx, low], post


if __name__ == '__main__':
    out = sys.argv[1]
    _d, _c, _a = (float(v) for v in os.environ.get('PTL_CUTS', '2.6,6.75,10.95').split(','))
    arc = ([0, _d - 0.1, _d, _c - 0.05, _c, 30], [-9, -8, -6, -4.5, -1.5, -1.5])
    x = M.mix(*compose(), arc=arc)
    t = np.arange(N) / M.SR
    x *= np.clip((DUR - t) / 1.2, 0, 1)
    M.write_wav(out, x)
    print('wrote', out)
