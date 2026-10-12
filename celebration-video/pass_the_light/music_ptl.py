"""Original orchestral score for PASS THE LIGHT (120 s), synthesised here: royalty-free.
Builds milestone by milestone (layers added as the achievements accumulate), an impact on every
tower ignition, a breath of silence before the 10, an awards-ceremony climax and a warm resolution."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import music as M  # noqa: E402

DUR = 120.0
M.N = int(M.SR * DUR)
from music import (Bus, boom, brass, celesta, crash, kick, mf, piano, riser, shaker, snare, spiccato,  # noqa: E402
                   strings_pad, timpani, tom)

B = 0.6
T_MS, T_TOG, T_DROP, T_HIT, T_FIN = 32.0, 92.0, 104.0, 106.4, 115.0
IGN = [T_MS + 6 * k + 1.2 for k in range(10)]
CH = {'D': [50, 54, 57], 'A': [45, 49, 52], 'Bm': [47, 50, 54], 'G': [43, 47, 50],
      'E': [52, 56, 59], 'B': [47, 51, 54], 'C#m': [49, 52, 56]}


def chord_at(t):
    if t < T_TOG:
        return ['D', 'A', 'Bm', 'G'][int(max(0, t) // 3.0) % 4]
    if t < T_DROP:
        return ['E', 'B', 'C#m', 'A'][int((t - T_TOG) // 3.0) % 4]
    if t < T_FIN:
        return ['E', 'C#m', 'A', 'B'][min(3, int((t - T_HIT) // 2.4))] if t >= T_HIT else 'E'
    return 'E'


def compose():
    pad, strs, brs, bell, perc, fx, low = (Bus(n) for n in ['pad', 'str', 'brass', 'bell', 'perc', 'fx', 'low'])
    post = Bus('post')
    # pads + bass, chord changes every 3 s (2.4 s in the climax)
    t = 0.0
    while t < DUR - 0.2:
        if T_DROP <= t < T_HIT:
            t = T_HIT
            continue
        n = chord_at(t + 0.01)
        step = 2.4 if T_HIT <= t < T_FIN else 3.0
        if t >= T_FIN:
            step = DUR - t
        d = min(step, DUR - t, (T_DROP - t) if t < T_DROP else 99)
        g = 0.16 + 0.10 * min(1, t / 100)
        for j, m in enumerate(CH[n] + [CH[n][1] + 12]):
            pad.add(t, strings_pad(mf(m + 12), d, 1400 + 22 * t), g * 0.33, pan=(j - 1.5) * 0.35)
        low.add(t, strings_pad(mf(CH[n][0] - 12), d, 600), g * 0.9)
        t += step
    # opening piano + celesta
    for t, m in [(0.4, 66), (1.0, 69), (1.6, 74), (2.8, 73), (4.0, 71), (4.6, 74), (5.2, 78), (6.4, 76), (7.6, 73), (8.8, 74)]:
        bell.add(t, piano(mf(m)), 0.30)
    for k, m in enumerate([86, 90, 93, 98]):
        bell.add(25.1 + 0.08 * k, celesta(mf(m), 2.0), 0.12)  # the folder ignites
    # rhythmic pulse: eighths from 10 s, sixteenths from 24 s
    t = 10.0
    while t < T_DROP - 1e-6:
        n = chord_at(t + 0.01)
        step = B / 2 if t < 24 else B / 4
        k = int(round(t / step))
        r = CH[n][0]
        m = [r, r + 12, CH[n][2], r + 12][k % 4]
        g = 0.10 + 0.08 * min(1, (t - 10) / 80)
        strs.add(t, spiccato(mf(m)), g, pan=-0.35)
        if t > 50:
            strs.add(t, spiccato(mf(m + 12), bright=3600), g * 0.5, pan=0.35)
        t += step
    # drums grow with the milestones
    t = 17.0
    while t < T_DROP - 1e-6:
        beat = int(round((t - 17.0) / B)) % 4
        perc.add(t, kick(), 0.30 if t < T_MS else 0.5)
        level = sum(1 for x in IGN if x <= t)
        if level >= 2 and beat in (1, 3):
            perc.add(t, snare(), 0.18 + 0.02 * level)
        if t >= 24:
            perc.add(t + B / 2, shaker(), 0.08)
        if level >= 8 or t >= T_TOG:
            perc.add(t, tom(80 if beat % 2 else 110), 0.22)
        t += B
    fx.add(29.0, riser(3.0), 0.2)
    perc.add(28.6, boom(), 0.4)
    # every tower ignition: impact
    for k, x in enumerate(IGN):
        perc.add(x, boom(), 0.40 + 0.02 * k)
        perc.add(x, timpani(mf(38)), 0.35)
        fx.add(x, crash(), 0.10 + 0.01 * k)
        fx.add(x - 1.0, riser(1.0), 0.10)
        for j, m in enumerate([86, 90, 93]):
            bell.add(x + 0.05 + 0.07 * j, celesta(mf(m + (k % 3) * 2), 1.4), 0.08)
    # brass from milestone 4, melody from milestone 6
    t = IGN[3] - 1.2
    while t < T_DROP - 0.5:
        n = chord_at(t + 0.01)
        for m in CH[n]:
            brs.add(t, brass(mf(m + 12), 2.4), 0.10 + 0.04 * min(1, (t - 50) / 50))
        t += 3.0
    phrase = [(0, 66, 2), (2, 69, 2), (4, 74, 3), (7, 73, 1), (8, 76, 2), (10, 73, 2), (12, 69, 4),
              (16, 71, 2), (18, 74, 2), (20, 78, 3), (23, 76, 1), (24, 74, 2), (26, 71, 2), (28, 69, 4)]
    e8 = B / 2
    for p0, shift in [(IGN[5] - 1.2, 0), (IGN[5] - 1.2 + 32 * e8, 0), (T_TOG, 2)]:
        for e, m, L in phrase:
            if p0 + e * e8 < T_DROP - 0.4:
                brs.add(p0 + e * e8, brass(mf(m + shift), L * e8 * 0.95, 2800), 0.20, pan=0.15)
                strs.add(p0 + e * e8, strings_pad(mf(m + 12 + shift), L * e8, 3400) * 0.6, 0.18, pan=-0.15)
    # build into the drop
    perc.add(T_TOG, boom(), 0.5)
    fx.add(T_TOG, crash(), 0.14)
    for b in np.arange(T_DROP - 2.4, T_DROP, B / 8):
        perc.add(b, snare(), 0.05 + 0.32 * ((b - T_DROP + 2.4) / 2.4) ** 2)
    fx.add(T_DROP - 5.0, riser(5.0), 0.32)
    # the breath: low pedal + reverse swell (added after the duck)
    post.add(T_DROP, strings_pad(mf(40), T_HIT - T_DROP, 500), 0.25)
    rc = crash(1.2)[::-1].copy()
    post.add(T_HIT - 1.2, rc * np.linspace(0, 1, len(rc)) ** 2, 0.55)
    post.add(T_HIT - 1.6, riser(1.6), 0.3)
    # CLIMAX — awards ceremony
    perc.add(T_HIT, boom(4.0), 0.85)
    fx.add(T_HIT, crash(4.0), 0.30)
    for b in np.arange(T_HIT, T_FIN - 1e-6, B):
        k = int(round((b - T_HIT) / B))
        perc.add(b, kick(), 0.6)
        perc.add(b, timpani(mf(40) if k % 2 == 0 else mf(47), 0.8), 0.30)
        if k % 2 == 1:
            perc.add(b, snare(), 0.32)
        perc.add(b + B / 2, shaker(), 0.12)
    t = T_HIT
    while t < T_FIN - 0.1:
        n = chord_at(t + 0.01)
        for m in CH[n] + [CH[n][0] + 12]:
            brs.add(t, brass(mf(m + 12), min(2.3, T_FIN - t), 2600), 0.20)
        fx.add(t, crash(), 0.10)
        t += 2.4
    climax = [(0, 76, 4), (4, 80, 2), (6, 83, 2), (8, 85, 4), (12, 83, 2), (14, 80, 2), (16, 81, 4), (20, 85, 2), (22, 88, 2), (24, 87, 4)]
    for e, m, L in climax:
        brs.add(T_HIT + e * e8, brass(mf(m - 12), L * e8 * 0.95, 3200), 0.24)
        strs.add(T_HIT + e * e8, strings_pad(mf(m), L * e8, 4200) * 0.6, 0.22)
    for b in np.arange(T_FIN - 1.2, T_FIN, B / 8):
        perc.add(b, timpani(mf(40), 0.4), 0.10 + 0.25 * (b - T_FIN + 1.2))
    # FINALE: warm resolution
    perc.add(T_FIN, boom(4.5), 0.7)
    fx.add(T_FIN, crash(4.8), 0.26)
    for m in [40, 52, 56, 59, 64, 68, 71, 76]:
        pad.add(T_FIN, strings_pad(mf(m), 4.6, 3200), 0.12)
        brs.add(T_FIN, brass(mf(m), 3.6, 2400), 0.10)
    for k, m in enumerate([76, 80, 83, 88, 92]):
        bell.add(T_FIN + 0.5 + k * 0.3, celesta(mf(m), 3.0), 0.18)
    return [pad, strs, brs, bell, perc, fx, low], post


ARC = ([0, 9.9, 10, 23.9, 24, T_MS, 60, T_TOG, T_DROP - 0.05, T_DROP + 0.1, T_HIT - 0.02, T_HIT, DUR],
       [-12, -10, -8.5, -6.5, -5, -4, -3, -1.5, -0.5, -24, -24, 0, 0])

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'ptl_score.wav'
    x = M.mix(*compose(), arc=ARC)
    t = np.arange(M.N) / M.SR
    x *= np.clip((DUR - t) / 2.0, 0, 1)
    M.write_wav(out, x)
    print('wrote', out)
