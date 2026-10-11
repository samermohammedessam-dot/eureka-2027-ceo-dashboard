"""Original orchestral score for 'Lighting the City of Excellence' (synthesised here: royalty-free).
Reuses the instruments in music.py; structure follows city_timeline.py."""
import os
import sys

import numpy as np

import city_timeline as C
import music as M
from music import (Bus, boom, brass, celesta, crash, kick, mf, piano, riser, shaker, snare,
                   spiccato, strings_pad, timpani, tom)

B = C.BEAT
CH = {'D': (50, [50, 54, 57]), 'Bm': (47, [47, 50, 54]), 'G': (43, [43, 47, 50]), 'A': (45, [45, 49, 52]),
      'E': (52, [52, 56, 59]), 'B': (47, [47, 51, 54]), 'C#m': (49, [49, 52, 56]), 'Asus': (45, [45, 50, 52])}


def bars(start, names):
    return [(start + k * C.BAR, n) for k, n in enumerate(names)]


INTRO = bars(0.4, ['D', 'Bm', 'G', 'A'])
BUILD = bars(9.2, ['D', 'Bm', 'G', 'A', 'Asus'])
RELAY = bars(C.ARRIVALS[0], (['D', 'A', 'Bm', 'G'] * 6)[:20])
ALIVE = bars(C.MUSIC_S4, ['E', 'B', 'C#m', 'A', 'E', 'B'])
CLIMAX = bars(C.HIT, ['E', 'C#m', 'A', 'B'])


def compose():
    pad, strs, brs, bell, perc, fx, low = (Bus(n) for n in ['pad', 'str', 'brass', 'bell', 'perc', 'fx', 'low'])
    post = Bus('post')

    def pads(seq, g, bright, end):
        for k, (t, n) in enumerate(seq):
            d = min(C.BAR, end - t)
            r, notes = CH[n]
            for j, m in enumerate(notes + [notes[1] + 12, notes[2] + 12]):
                pad.add(t, strings_pad(mf(m + 12), d, bright), g * 0.33, pan=(j - 2) * 0.3)
            low.add(t, strings_pad(mf(r - 12), d, 600), g * 0.9)

    pads(INTRO, 0.20, 1400, 9.2)
    pads(BUILD, 0.24, 2000, C.ARRIVALS[0])
    pads(RELAY, 0.22, 2600, C.MUSIC_S4)
    pads(ALIVE, 0.24, 3000, C.DROP)
    pads(CLIMAX, 0.30, 3600, C.FINALE)

    def chord_at(t, seq):
        cur = seq[0][1]
        for s, n in seq:
            if s <= t + 1e-6:
                cur = n
        return CH[cur]

    # celesta arpeggios (8ths)
    t = 1.0
    while t < C.MUSIC_S4:
        seq = INTRO if t < 9.2 else BUILD if t < C.ARRIVALS[0] else RELAY
        _, notes = chord_at(t, seq)
        i = int(round(t / (B / 2)))
        m = [notes[0] + 24, notes[1] + 24, notes[2] + 24, notes[0] + 36][i % 4 if i % 8 < 4 else 3 - i % 4]
        bell.add(t, celesta(mf(m)), (0.16 if t < C.ARRIVALS[0] else 0.07) * (0.6 + 0.4 * min(1, t / 8)), pan=0.4 * np.sin(i))
        t += B / 2
    for t, m in [(2.6, 66), (3.15, 69), (3.7, 74), (4.8, 73), (7.0, 71), (7.55, 74), (8.1, 78), (9.2, 76)]:
        bell.add(t, piano(mf(m)), 0.32)

    # the spark: ignition swell + sparkle
    perc.add(C.IGNITE, timpani(mf(38), 2.0), 0.35)
    fx.add(C.IGNITE, crash(3.0), 0.10)
    for k, m in enumerate([86, 90, 93, 98]):
        bell.add(C.IGNITE + 0.08 * k, celesta(mf(m), 2.0), 0.12)

    # string pulse / spiccato
    for s0, s1, step, g, seq in [(10.3, C.ARRIVALS[0], B / 2, 0.18, BUILD), (C.ARRIVALS[0], C.MUSIC_S4, B / 4, 0.16, RELAY),
                                 (C.MUSIC_S4, C.DROP, B / 4, 0.19, ALIVE)]:
        t = s0
        while t < s1 - 1e-6:
            r, notes = chord_at(t, seq)
            i = int(round((t - s0) / step))
            m = [r, r + 12, notes[2], r + 12][i % 4]
            acc = 1.0 if i % 4 == 0 else 0.7
            strs.add(t, spiccato(mf(m)), g * acc, pan=-0.35)
            strs.add(t, spiccato(mf(m + 12), bright=3600), g * 0.5 * acc, pan=0.35)
            t += step

    # drums
    t = 13.6
    while t < C.ARRIVALS[0] - 1e-6:
        perc.add(t, kick(), 0.32)
        t += 2 * B
    for b in np.arange(C.ARRIVALS[0] - 1.65, C.ARRIVALS[0], B / 4):
        perc.add(b, snare(), 0.06 + 0.25 * (b - C.ARRIVALS[0] + 1.65) / 1.65)
    fx.add(15.8, riser(C.ARRIVALS[0] - 15.8), 0.22)
    for s0, s1, dense in [(C.ARRIVALS[0], C.MUSIC_S4, False), (C.MUSIC_S4, C.DROP - 2.2, True)]:
        b = s0
        while b < s1 - 1e-6:
            beat = int(round((b - s0) / B)) % 4
            perc.add(b, kick(), 0.55)
            if beat in (1, 3):
                perc.add(b, snare(), 0.30)
            perc.add(b + B / 2, shaker(), 0.10)
            if dense:
                perc.add(b + B / 4, shaker(), 0.06); perc.add(b + 3 * B / 4, shaker(), 0.06)
                perc.add(b, tom(80 if beat % 2 else 110), 0.28)
            b += B
    # torch flights: whoosh during each 1.1 s travel, tom pickup into each arrival
    for a in C.ARRIVALS:
        fx.add(a - C.ARRIVE, riser(C.ARRIVE), 0.16)
        for k, dt in enumerate([-0.55, -0.4125, -0.275, -0.1375]):
            perc.add(a + dt, tom(140 - k * 18), 0.30)
    # arrivals = impacts
    for a in C.ARRIVALS + [C.MUSIC_S4]:
        perc.add(a, boom(), 0.55)
        fx.add(a, crash(), 0.15)
        perc.add(a, timpani(mf(38)), 0.4)
    # S4 build to the drop
    for b in np.arange(C.DROP - 2.2, C.DROP, B / 8):
        perc.add(b, snare(), 0.05 + 0.32 * ((b - C.DROP + 2.2) / 2.2) ** 2)
    fx.add(C.DROP - 5.5, riser(5.5), 0.35)

    # brass chords + stabs
    for seq, end, g in [(RELAY, C.MUSIC_S4, 0.16), (ALIVE, C.DROP, 0.2)]:
        for t, n in seq:
            if t >= end:
                continue
            _, notes = CH[n]
            for m in notes:
                brs.add(t, brass(mf(m + 12), C.BAR * 0.7), g * 0.6)
            brs.add(t + 3 * B, brass(mf(notes[1] + 12), 0.4), g * 0.4)

    # heroic melody (eighths = B/2), one phrase per 4 bars
    phrase = [(0, 66, 2), (2, 69, 2), (4, 74, 3), (7, 73, 1), (8, 76, 2), (10, 73, 2), (12, 69, 4),
              (16, 71, 2), (18, 74, 2), (20, 78, 3), (23, 76, 1), (24, 74, 2), (26, 71, 2), (28, 69, 4)]
    e8 = B / 2
    for p0 in np.arange(C.ARRIVALS[0] + 4 * C.BAR, C.MUSIC_S4 - 1, 4 * C.BAR):
        for e, m, L in phrase:
            brs.add(p0 + e * e8, brass(mf(m), L * e8 * 0.95, 2600), 0.20, pan=0.15)
            strs.add(p0 + e * e8, strings_pad(mf(m + 12), L * e8, 3200) * 0.6, 0.20, pan=-0.15)
    for e, m, L in phrase:
        if C.MUSIC_S4 + e * e8 < C.DROP - 0.3:
            brs.add(C.MUSIC_S4 + e * e8, brass(mf(m + 2), L * e8 * 0.95, 3000), 0.24, pan=0.15)
            strs.add(C.MUSIC_S4 + e * e8, strings_pad(mf(m + 14), L * e8, 3600) * 0.6, 0.24)

    # the drop: low pedal + reverse swell into the HIT (added after the duck)
    post.add(C.DROP, strings_pad(mf(40), C.HIT - C.DROP, 500), 0.25)
    post.add(C.DROP + 0.4, strings_pad(mf(64), C.HIT - C.DROP - 0.4, 1800), 0.06)
    rc = crash(1.2)[::-1].copy()
    post.add(C.HIT - 1.2, rc * np.linspace(0, 1, len(rc)) ** 2, 0.55)
    post.add(C.HIT - 1.6, riser(1.6), 0.3)

    # CLIMAX
    perc.add(C.HIT, boom(4.0), 0.85)
    fx.add(C.HIT, crash(4.0), 0.30)
    for b in np.arange(C.HIT, C.FINALE - 1e-6, B):
        k = int(round((b - C.HIT) / B))
        perc.add(b, kick(), 0.6)
        perc.add(b, timpani(mf(40) if k % 2 == 0 else mf(47), 0.8), 0.32)
        if k % 2 == 1:
            perc.add(b, snare(), 0.32)
        perc.add(b + B / 2, shaker(), 0.12)
    for t, _ in CLIMAX[1:]:
        fx.add(t, crash(), 0.14)
    for t, n in CLIMAX:
        _, notes = CH[n]
        d = min(C.BAR, C.FINALE - t) * 0.9
        for m in notes + [notes[0] + 12]:
            brs.add(t, brass(mf(m + 12), d, 2600), 0.20)
    climax_mel = [(0, 76, 4), (4, 80, 2), (6, 83, 2), (8, 85, 4), (12, 83, 2), (14, 80, 2),
                  (16, 81, 4), (20, 85, 2), (22, 88, 2), (24, 87, 4)]
    for e, m, L in climax_mel:
        brs.add(C.HIT + e * e8, brass(mf(m - 12), L * e8 * 0.95, 3200), 0.24)
        strs.add(C.HIT + e * e8, strings_pad(mf(m), L * e8, 4200) * 0.6, 0.22)
    for b in np.arange(C.FINALE - 1.1, C.FINALE, B / 8):
        perc.add(b, timpani(mf(40), 0.4), 0.10 + 0.25 * (b - C.FINALE + 1.1))

    # FINALE: resolution
    perc.add(C.FINALE, boom(4.5), 0.75)
    fx.add(C.FINALE, crash(4.8), 0.28)
    for m in [40, 52, 56, 59, 64, 68, 71, 76]:
        pad.add(C.FINALE, strings_pad(mf(m), 4.2, 3200), 0.12)
        brs.add(C.FINALE, brass(mf(m), 3.2, 2400), 0.10)
    for k, m in enumerate([76, 80, 83, 88, 92]):
        bell.add(C.FINALE + 0.4 + k * 0.275, celesta(mf(m), 3.0), 0.18)
    return [pad, strs, brs, bell, perc, fx, low], post


ARC = ([0, 9.1, 9.2, 18.9, C.ARRIVALS[0], C.MUSIC_S4 - 0.1, C.MUSIC_S4, C.DROP - 0.05, C.DROP + 0.1,
        C.HIT - 0.02, C.HIT, 90], [-11, -9, -7.5, -5, -2.5, -2.5, -1.5, -0.5, -24, -24, 0, 0])


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'build/city_score.wav'
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    M.write_wav(out, M.mix(*compose(), arc=ARC))
    print('wrote', out)
