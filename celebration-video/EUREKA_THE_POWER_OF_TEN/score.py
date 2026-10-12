"""THE POWER OF TEN — original 105 s orchestral score (synthesised, royalty-free, no voice).

Structure follows film.py's timeline:
  0.0-16.6  anticipation: darkness drone, golden pulse, three spotlight hits, the Eureka reveal
  16.6-76.6 ten achievements: a rising 100 BPM pulse, an award accent at every ignition
  76.6-89.2 the people: emotional strings + piano, accelerating
  89.2-90.4 near-silence with a reverse swell
  90.4-98   the grand "10": full brass and drums
  98-105    the Eureka finale and a warm resolution
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import music as M  # noqa: E402

DUR = 105.0
M.N = int(M.SR * DUR)
N = M.N
from music import (Bus, boom, brass, celesta, crash, kick, mf, piano, riser, shaker, snare,  # noqa: E402
                   spiccato, strings_pad, timpani, tom)

B = 0.6                     # one beat at 100 BPM
T_STAGE, T_MS, SLOT, IGN = 10.0, 16.6, 6.0, 0.6
T_PEOPLE, T_DROP, T_HIT, T_END = 76.6, 89.2, 90.4, 98.0
GRID0 = T_MS % B            # the beat grid is anchored on the first achievement

CH = {'D': [50, 54, 57], 'A': [45, 49, 52], 'Bm': [47, 50, 54], 'G': [43, 47, 50],
      'F#m': [42, 45, 49], 'Em': [40, 43, 47]}
MOTIF = [74, 69, 74, 78]    # the "power of ten" motif: D5 A4 D5 F#5


def reverse_swell(dur):
    x = crash(dur)[::-1].copy()
    return x * np.linspace(0.2, 1, len(x)) ** 2


def whoosh(dur=0.9):
    x = riser(dur)
    n = len(x)
    return x * np.concatenate([np.ones(n - n // 6), np.linspace(1, 0, n // 6)])


def chord_at(t):
    """Harmony map for the whole film."""
    if t < T_STAGE:
        return 'D' if t < 6.4 else 'G'
    if t < T_MS:
        return ['Bm', 'G', 'A'][min(2, int((t - T_STAGE) / 2.4))]
    if t < T_PEOPLE:
        k = int((t - T_MS) / SLOT)
        half = int((t - T_MS - k * SLOT) / 3.0)
        prog = [('D', 'A'), ('Bm', 'G'), ('D', 'A'), ('Em', 'A'), ('Bm', 'F#m'),
                ('G', 'A'), ('D', 'A'), ('Bm', 'G'), ('Em', 'A'), ('G', 'A')]
        return prog[min(k, 9)][half]
    if t < T_DROP:
        return ['Bm', 'G', 'D', 'A'][int((t - T_PEOPLE) / 3.15) % 4]
    if t < T_END:
        return ['D', 'Bm', 'G', 'A'][int((t - T_HIT) / 1.9) % 4]
    return 'G' if 101.0 <= t < 102.6 else 'D'


def chord_spans(t0, t1, step):
    t = t0
    while t < t1 - 0.05:
        d = min(step, t1 - t)
        yield t, d, chord_at(t + 0.01)
        t += step


def compose():
    pad, strs, brs, bell, perc, fx, low = (Bus(n) for n in ['pad', 'str', 'brass', 'bell', 'perc', 'fx', 'low'])
    post = Bus('post')

    # ---------------------------------------------------------- 0-16.6 anticipation
    drone = strings_pad(mf(26), 10.5, 260)
    low.add(0.0, drone * np.linspace(0, 1, len(drone)) ** 0.7, 0.40)
    perc.add(0.9, boom(3.2), 0.55)                       # the golden pulse
    perc.add(0.9, timpani(mf(38), 2.0), 0.35)
    for t, f in [(1.5, 33), (2.3, 36), (3.2, 38)]:       # three spotlights snap on
        perc.add(t, timpani(mf(f), 1.4), 0.40)
        perc.add(t, tom(70, 0.7), 0.30)
        fx.add(t, crash(1.2), 0.035)
    fx.add(2.0, riser(1.6), 0.13)
    perc.add(3.6, boom(3.5), 0.55)                       # Eureka reveal
    fx.add(3.6, crash(3.5), 0.09)
    for j, m in enumerate([74, 78, 81, 86, 90, 93]):
        bell.add(3.65 + 0.11 * j, celesta(mf(m), 2.4), 0.12)
    for t, d, c in chord_spans(3.6, T_STAGE, 2.8):
        for j, m in enumerate(CH[c] + [CH[c][1] + 12]):
            pad.add(t, strings_pad(mf(m + 12), d + 0.4, 1400 + 120 * t), 0.075, pan=(j - 1.5) * 0.4)
        low.add(t, strings_pad(mf(CH[c][0] - 12), d + 0.4, 420), 0.25)
    for t, m in [(4.4, 66), (4.8, 69), (5.4, 74), (6.4, 78), (7.2, 76), (8.0, 74)]:
        bell.add(t, piano(mf(m)), 0.26)
    perc.add(5.4, timpani(mf(38), 1.6), 0.30)            # title lands
    for j, m in enumerate(MOTIF):                        # subtitle: the motif, softly
        bell.add(6.4 + 0.3 * j, celesta(mf(m + 12), 1.8), 0.10)
    fx.add(T_STAGE - 1.4, riser(1.4), 0.15)              # into the stage
    perc.add(T_STAGE, boom(2.6), 0.40)
    fx.add(T_STAGE, crash(2.4), 0.06)

    # ---------------------------------------------------------- 10-16.6 the stage, pulse begins
    for t, d, c in chord_spans(T_STAGE, T_MS, 2.4):
        for j, m in enumerate(CH[c] + [CH[c][1] + 12]):
            pad.add(t, strings_pad(mf(m + 12), d + 0.3, 1800), 0.08, pan=(j - 1.5) * 0.4)
        low.add(t, strings_pad(mf(CH[c][0] - 12), d + 0.3, 500), 0.25)
    t = T_STAGE + GRID0
    while t < T_MS - 0.05:
        c = chord_at(t)
        k = int(round((t - T_STAGE) / (B / 2)))
        ramp = (t - T_STAGE) / (T_MS - T_STAGE)
        strs.add(t, spiccato(mf(CH[c][0] + (12 if k % 2 else 0))), 0.06 + 0.06 * ramp, pan=-0.3)
        t += B / 2
    fx.add(T_MS - 1.8, riser(1.8), 0.18)

    # ---------------------------------------------------------- 16.6-76.6 ten achievements
    for k in range(10):
        s = T_MS + SLOT * k
        ign = s + IGN
        lift = k / 9                                      # the progression keeps rising
        for t, d, c in chord_spans(s, s + SLOT, 3.0):
            for j, m in enumerate(CH[c] + [CH[c][1] + 12]):
                pad.add(t, strings_pad(mf(m + 12), d + 0.3, 1900 + 900 * lift), 0.07 + 0.02 * lift,
                        pan=(j - 1.5) * 0.4)
            low.add(t, strings_pad(mf(CH[c][0] - 12), d + 0.3, 520), 0.26)
            if k >= 5:                                    # brass joins for the second half
                for j, m in enumerate(CH[c]):
                    brs.add(t, brass(mf(m + 12), d), 0.035 + 0.03 * lift, pan=(j - 1) * 0.3)
        # pulse: spiccato eighths, kick, backbeat and shaker layered in as it builds
        t = s
        while t < s + SLOT - 0.05:
            c = chord_at(t)
            j = int(round((t - T_MS) / (B / 2)))
            strs.add(t, spiccato(mf(CH[c][0] + 12 + (7 if j % 4 == 2 else 0) + (12 if j % 2 else 0))),
                     0.10 + 0.05 * lift, pan=0.3 if j % 2 else -0.3)
            beat = j % 2 == 0
            if k >= 1 and beat:
                perc.add(t, kick(), 0.20 + 0.08 * lift)
            if k >= 3 and beat and (j // 2) % 2 == 1:
                perc.add(t, snare(), 0.10 + 0.05 * lift)
            if k >= 2:
                perc.add(t, shaker(), 0.035 + 0.02 * lift, pan=0.4)
            t += B / 2
        # the ignition: impact + award accent + the motif on celesta
        perc.add(ign, boom(2.4), 0.42 + 0.12 * lift)
        perc.add(ign, timpani(mf(38), 1.6), 0.32)
        fx.add(ign, crash(2.6), 0.05 + 0.03 * lift)
        fx.add(ign - 0.55, riser(0.55), 0.10)
        for j, m in enumerate(MOTIF):
            bell.add(ign + 0.08 + 0.15 * j, celesta(mf(m + (12 if k % 2 else 0)), 1.8), 0.11)
        bell.add(ign + 0.7, piano(mf(MOTIF[k % 4] - 12)), 0.18)
        if k < 9:                                         # streak transition whoosh
            fx.add(s + SLOT - 0.75, whoosh(0.9), 0.14)

    # ---------------------------------------------------------- 76.6-89.2 the people (emotional, accelerating)
    perc.add(T_PEOPLE, boom(3.0), 0.40)
    fx.add(T_PEOPLE, crash(3.0), 0.06)
    for t, d, c in chord_spans(T_PEOPLE, T_DROP, 3.15):
        u = (t - T_PEOPLE) / (T_DROP - T_PEOPLE)
        for j, m in enumerate(CH[c] + [CH[c][1] + 12, CH[c][2] + 12]):
            pad.add(t, strings_pad(mf(m + 12), d + 0.4, 2200 + 1600 * u), 0.08 + 0.03 * u,
                    pan=(j - 2) * 0.35)
        low.add(t, strings_pad(mf(CH[c][0] - 12), d + 0.4, 600), 0.28)
        for j, m in enumerate(CH[c]):
            brs.add(t, brass(mf(m + 12), d), 0.05 + 0.04 * u, pan=(j - 1) * 0.3)
    melody = [(0.0, 78), (0.6, 76), (1.2, 74), (1.8, 76), (3.15, 74), (3.75, 73), (4.35, 71), (4.95, 74),
              (6.3, 74), (6.9, 76), (7.5, 78), (8.1, 81), (9.45, 81), (9.75, 83), (10.05, 85), (10.35, 86)]
    for dt, m in melody:
        bell.add(T_PEOPLE + dt, piano(mf(m)), 0.28)
    t = T_PEOPLE
    while t < T_DROP - 0.05:
        u = (t - T_PEOPLE) / (T_DROP - T_PEOPLE)
        step = B / 2 if u < 0.6 else B / 4               # the pulse doubles as it accelerates
        c = chord_at(t)
        j = int(round((t - T_PEOPLE) / (B / 4)))
        strs.add(t, spiccato(mf(CH[c][0] + 12 + (12 if j % 2 else 0))), 0.11 + 0.06 * u,
                 pan=0.3 if j % 2 else -0.3)
        if j % 4 == 0:
            perc.add(t, kick(), 0.26 + 0.08 * u)
        if j % 8 == 4:
            perc.add(t, snare(), 0.14 + 0.06 * u)
        if u > 0.75 and j % 2 == 0:
            perc.add(t, tom(90 + 60 * u), 0.10 + 0.12 * u)
        t += step
    fx.add(T_DROP - 3.0, riser(3.0), 0.22)

    # ---------------------------------------------------------- 89.2-90.4 silence + reverse swell (bypasses the arc)
    post.add(T_DROP + 0.05, strings_pad(mf(26), 1.2, 200), 0.08)
    sw = reverse_swell(T_HIT - T_DROP)
    post.add(T_HIT - len(sw) / M.SR, sw, 0.30)

    # ---------------------------------------------------------- 90.4-98 the grand "10"
    perc.add(T_HIT, boom(4.0), 0.75)
    perc.add(T_HIT, timpani(mf(38), 2.4), 0.50)
    perc.add(T_HIT, kick(), 0.45)
    fx.add(T_HIT, crash(4.0), 0.14)
    for t, d, c in chord_spans(T_HIT, T_END, 1.9):
        for j, m in enumerate(CH[c] + [CH[c][1] + 12, CH[c][2] + 12]):
            pad.add(t, strings_pad(mf(m + 12), d + 0.4, 4200), 0.10, pan=(j - 2) * 0.35)
        for j, m in enumerate(CH[c] + [CH[c][0] + 12]):
            brs.add(t, brass(mf(m + 12), d + 0.1, 2600), 0.10, pan=(j - 1.5) * 0.3)
        low.add(t, strings_pad(mf(CH[c][0] - 12), d + 0.4, 700), 0.32)
    for j, m in enumerate(MOTIF):                        # the motif on full brass
        brs.add(T_HIT + 0.3 + 0.6 * j, brass(mf(m - 12), 0.9 if j < 3 else 2.4, 3000), 0.16)
    t = T_HIT + B / 2
    while t < T_END - 0.05:
        j = int(round((t - T_HIT) / (B / 2)))
        c = chord_at(t)
        strs.add(t, spiccato(mf(CH[c][0] + 12 + (12 if j % 2 else 0))), 0.14, pan=0.3 if j % 2 else -0.3)
        if j % 2 == 0:
            perc.add(t, kick(), 0.34)
        if j % 4 == 2:
            perc.add(t, snare(), 0.20)
        perc.add(t, shaker(), 0.05, pan=0.4)
        t += B / 2
    for dt in (1.9, 3.8, 5.7):
        perc.add(T_HIT + dt, timpani(mf(38), 1.4), 0.30)
        fx.add(T_HIT + dt, crash(2.0), 0.05)
    fx.add(T_END - 1.6, riser(1.6), 0.18)

    # ---------------------------------------------------------- 98-105 Eureka finale + resolution
    perc.add(T_END, boom(4.5), 0.60)
    perc.add(T_END, timpani(mf(38), 2.6), 0.42)
    fx.add(T_END, crash(4.5), 0.11)
    for j, m in enumerate([74, 78, 81, 86, 90, 93, 98]):
        bell.add(T_END + 0.1 + 0.12 * j, celesta(mf(m), 3.0), 0.12)
    for t, d in [(T_END, 3.0), (101.0, 1.6), (102.6, 2.4)]:
        c = chord_at(t + 0.01)
        for j, m in enumerate(CH[c] + [CH[c][1] + 12, CH[c][2] + 12]):
            pad.add(t, strings_pad(mf(m + 12), d + 1.2, 2600), 0.10, pan=(j - 2) * 0.35)
        for j, m in enumerate(CH[c]):
            brs.add(t, brass(mf(m + 12), d + 0.4, 1800), 0.08, pan=(j - 1) * 0.3)
        low.add(t, strings_pad(mf(CH[c][0] - 12), d + 1.2, 500), 0.30)
    for t, m in [(99.2, 78), (99.8, 81), (100.4, 86), (101.6, 83), (102.6, 86)]:
        bell.add(t, piano(mf(m)), 0.24)
    perc.add(102.6, timpani(mf(38), 2.0), 0.22)          # "TOGETHER, WE RAISE THE STANDARD."
    for j, m in enumerate(MOTIF):
        bell.add(102.7 + 0.25 * j, celesta(mf(m + 12), 2.2), 0.10)
    return [pad, strs, brs, bell, perc, fx, low], post


if __name__ == '__main__':
    out = sys.argv[1]
    arc = ([0, T_STAGE, T_MS, T_PEOPLE, T_DROP - 0.1, T_DROP + 0.05, T_HIT - 0.02, T_HIT, T_END, 101, DUR],
           [-11, -9, -7, -3.5, -1, -32, -32, 0, 0, -2, -4])
    x = M.mix(*compose(), arc=arc)
    M.write_wav(out, x)
    print('wrote', out)
