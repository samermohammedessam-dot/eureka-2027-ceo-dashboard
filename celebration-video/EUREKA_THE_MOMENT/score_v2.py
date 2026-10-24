"""THE MOMENT v2 — epic cinematic orchestral score with integrated sound design (original, synthesised: royalty-free).

Mystery -> Discovery -> Transformation -> Achievement -> Pride -> Celebration. Cues come from tl.py.
  - a deep, tense opening; a held breath and a clean gap for the "EUREKA!" shout;
  - a huge impact + golden-light shimmer right after the shout;
  - driving 120 BPM ostinato, war-drum toms and brass themes through the services and achievements;
  - the ten GAHAR achievements get a brass fanfare and the biggest hit before the finale;
  - an uplifting build under the institutional wall; a final peak on "FROM INSIGHT TO IMPACT." and a clean resolution.
Sound design (water, whooshes, sub hits, risers, technology shimmer, logo impacts) is mixed in, used selectively.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import music as M  # noqa: E402
import tl  # noqa: E402

DUR = tl.DUR
M.N = int(M.SR * DUR)
SR = M.SR
from music import (Bus, boom, brass, celesta, crash, kick, mf, piano, riser, shaker, snare,  # noqa: E402
                   spiccato, strings_pad, timpani, tom, lowpass, bandpass, highpass)

rng = np.random.default_rng(11)
B = 0.5                                     # 120 BPM in the driving sections
CH = {'Dm': [50, 53, 57], 'Bb': [46, 50, 53], 'F': [41, 45, 48], 'C': [48, 52, 55], 'Gm': [43, 46, 50], 'A': [45, 49, 52],
      'D': [50, 54, 57], 'G': [43, 47, 50], 'Bm': [47, 50, 54], 'Em': [40, 43, 47]}
THEME = [62, 65, 69, 67, 65, 64, 62, 69]   # the heroic theme (D minor), later in D major


# ------------------------------------------------------------------ sound design
def sub_hit(dur=2.2, f0=58, f1=28):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 3.0)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
    return (x * np.minimum(1, t / 0.004)).astype(np.float32)


def whoosh(dur=1.0, up=True):
    n = int(dur * SR)
    noise = rng.standard_normal(n).astype(np.float32)
    out = np.zeros(n, np.float32)
    seg = 10
    for k in range(seg):
        a, b = k * n // seg, (k + 1) * n // seg
        q = k / (seg - 1)
        fc = 300 * (14 ** (q if up else 1 - q))
        out[a:b] = bandpass(noise, fc, min(fc * 2.2, 18000))[a:b]
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** (1.6 if up else 0.8)
    return out * env


def splash(dur=1.6):
    """Water: a broadband wash with a low body, plus random droplets."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    wash = bandpass(rng.standard_normal(n).astype(np.float32), 500, 7000) * np.exp(-t * 2.8) * np.minimum(1, t / 0.02)
    body = lowpass(rng.standard_normal(n).astype(np.float32), 400) * np.exp(-t * 5) * 1.5
    drops = np.zeros(n, np.float32)
    for _ in range(70):
        i = int(rng.uniform(0.05, 0.95) * n)
        f = rng.uniform(900, 3200)
        m = int(0.03 * SR)
        tt = np.arange(m) / SR
        seg = np.sin(2 * np.pi * (f + 4000 * tt) * tt) * np.exp(-tt * 120) * rng.uniform(0.2, 0.7)
        drops[i:i + m] += seg[:max(0, min(m, n - i))]
    return (wash + body + drops * 0.6).astype(np.float32)


def shimmer(dur=3.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = highpass(rng.standard_normal(n).astype(np.float32), 6000) * np.exp(-t * 1.2) * np.minimum(1, t / 0.3)
    return x * 0.5


def tech_blips(t0, bus, count=8, gain=0.05):
    for k in range(count):
        bus.add(t0 + k * 0.125, celesta(mf(rng.choice([86, 89, 93, 98])), 0.25), gain)


def reverse_swell(dur):
    x = crash(dur)[::-1].copy()
    return x * np.linspace(0.2, 1, len(x)) ** 2


# ------------------------------------------------------------------ helpers
def chords(pad, low, brs, t0, t1, prog, step, gain, bright, brass_gain=0.0):
    t, k = t0, 0
    while t < t1 - 0.05:
        c = prog[k % len(prog)]
        d = min(step, t1 - t)
        for j, m in enumerate(CH[c] + [CH[c][1] + 12]):
            pad.add(t, strings_pad(mf(m + 12), d + 0.4, bright), gain, pan=(j - 1.5) * 0.45)
        low.add(t, strings_pad(mf(CH[c][0] - 12), d + 0.4, 520), gain * 3.4)
        if brass_gain:
            for j, m in enumerate(CH[c]):
                brs.add(t, brass(mf(m), d + 0.1, 2200), brass_gain, pan=(j - 1) * 0.3)
        t += step
        k += 1


def ostinato(strs, t0, t1, prog, step_chord, gain):
    t, j = t0, 0
    while t < t1 - 0.03:
        c = prog[int((t - t0) / step_chord) % len(prog)]
        r = CH[c][0] + 12
        m = [r, r + 12, r + 7, r + 12][j % 4]
        strs.add(t, spiccato(mf(m), 0.1, 3600), gain, pan=-0.35 if j % 2 else 0.35)
        t += B / 2
        j += 1


def drums(perc, t0, t1, level, pattern='drive'):
    t, j = t0, 0
    while t < t1 - 0.03:
        if pattern == 'drive':
            if j % 4 == 0:
                perc.add(t, kick(), 0.26 * level)
                perc.add(t, tom(62, 0.7), 0.22 * level)                 # war drum
            if j % 4 == 2:
                perc.add(t, snare(), 0.13 * level)
            if j % 8 == 7:
                perc.add(t, tom(110, 0.4), 0.14 * level)
            perc.add(t, shaker(), 0.025 * level, pan=0.4)
        elif pattern == 'half':
            if j % 8 == 0:
                perc.add(t, kick(), 0.22 * level)
                perc.add(t, tom(58, 0.9), 0.18 * level)
            if j % 8 == 4:
                perc.add(t, snare(), 0.10 * level)
        t += B / 2
        j += 1


def theme(brs, bell, t0, notes, step, gain, major=False, octave=0):
    for k, m in enumerate(notes):
        m = m + (4 if major and m % 12 in (5,) else 0) + octave
        brs.add(t0 + k * step, brass(mf(m), step * 1.6, 2600), gain, pan=0.0)
        bell.add(t0 + k * step, celesta(mf(m + 24), 1.0), gain * 0.25)


def big_hit(perc, fx, post, brs, t, chord='D', size=1.0):
    perc.add(t, boom(3.5), 0.55 * size)
    perc.add(t, timpani(mf(38), 2.0), 0.4 * size)
    fx.add(t, crash(3.5), 0.10 * size)
    post.add(t, sub_hit(2.4), 0.22 * size)
    for j, m in enumerate(CH[chord] + [CH[chord][0] + 12]):
        brs.add(t, brass(mf(m + 12), 2.4, 3000), 0.09 * size, pan=(j - 1.5) * 0.3)


def compose():
    pad, strs, brs, bell, perc, fx, low = (Bus(n) for n in ['pad', 'str', 'brass', 'bell', 'perc', 'fx', 'low'])
    post = Bus('post')
    E, G = tl.EUREKA_AT, tl.T_GOLD
    # ---------- 0-13 MYSTERY: deep atmosphere, low pulses, rising tension
    dr = strings_pad(mf(26), 13.2, 260)
    low.add(0.0, dr * np.linspace(0, 1, len(dr)) ** 0.5, 0.42)
    chords(pad, low, brs, 1.0, 11.0, ['Dm', 'Bb', 'Gm', 'A'], 2.5, 0.045, 1100)
    for k, t in enumerate(np.arange(0.6, 11.0, 1.25)):                         # heartbeat pulses
        perc.add(t, timpani(mf(33), 1.2), 0.10 + 0.02 * k)
        post.add(t, sub_hit(0.9, 46, 30), 0.05 + 0.01 * k)
    for t, m in [(1.4, 62), (2.4, 65), (3.4, 69), (5.0, 67), (6.4, 65), (7.4, 64)]:
        bell.add(t, piano(mf(m)), 0.17)
    fx.add(6.3, whoosh(1.4), 0.05)                                              # the crown into the water
    fx.add(7.6, splash(1.4), 0.07)
    fx.add(8.3, splash(2.0), 0.12)                                              # the overflow
    ostinato(strs, 8.3, 11.1, ['Dm', 'A'], 1.4, 0.06)
    fx.add(10.9, riser(2.15), 0.22)                                             # realization: the swell
    for j, m in enumerate([62, 65, 69, 74]):
        pad.add(11.1, strings_pad(mf(m + 12), 1.95, 3000), 0.07, pan=(j - 1.5) * 0.4)
    post.add(E - 0.85, reverse_swell(0.8), 0.10)                               # ... and a clean gap for the shout
    # ---------- 13.1 EUREKA! -> 14.55 GOLDEN BURST
    fx.add(E + 0.15, splash(1.5), 0.16)                                         # the water thrown skyward
    big_hit(perc, fx, post, brs, G, 'D', 1.5)
    post.add(G, shimmer(3.2), 0.06)
    for j, m in enumerate([74, 78, 81, 86, 90, 93, 98]):
        bell.add(G + 0.1 + 0.11 * j, celesta(mf(m), 2.6), 0.12)
    chords(pad, low, brs, G, tl.T_BRIDGE + 2.4, ['D', 'Bm'], 1.6, 0.08, 3200)
    # ---------- 17-30 THE BRIDGE: complexity -> insight -> momentum -> logo
    cx0, ins = tl.T_BRIDGE + 2.4, tl.INSIGHT
    chords(pad, low, brs, cx0, ins, ['Gm', 'A'], 1.5, 0.06, 1400)
    ostinato(strs, cx0, ins, ['Gm', 'A'], 1.5, 0.07)
    for k in range(4):
        tech_blips(cx0 + 0.3 + k * 0.75, bell, 4, 0.035)
    fx.add(ins - 1.2, riser(1.2), 0.15)
    big_hit(perc, fx, post, brs, ins, 'D', 0.8)                                 # the insight
    fx.add(ins, whoosh(0.9), 0.08)
    chords(pad, low, brs, ins, tl.T_WHO, ['D', 'A', 'Bm', 'G'], 2.0, 0.08, 3200, 0.03)
    ostinato(strs, ins, tl.T_WHO, ['D', 'A', 'Bm', 'G'], 2.0, 0.1)
    drums(perc, ins + 2.0, tl.T_WHO, 0.8)
    fx.add(tl.LOGO_REVEAL - 1.6, riser(1.6), 0.18)
    big_hit(perc, fx, post, brs, tl.LOGO_REVEAL, 'D', 1.1)                      # Eureka logo
    post.add(tl.LOGO_REVEAL, shimmer(2.4), 0.05)
    theme(brs, bell, tl.LOGO_REVEAL + 0.5, THEME, 0.5, 0.07, major=True)
    # ---------- 30-40 WHO WE ARE: warm, proud, still moving
    chords(pad, low, brs, tl.T_WHO, tl.T_WHAT, ['G', 'D', 'A', 'Bm'], 2.5, 0.085, 3000, 0.035)
    ostinato(strs, tl.T_WHO, tl.T_WHAT, ['G', 'D', 'A', 'Bm'], 2.5, 0.09)
    drums(perc, tl.T_WHO, tl.T_WHAT - 0.2, 0.7)
    theme(brs, bell, tl.T_WHO + 1.0, [67, 69, 71, 74, 71, 69, 67, 62], 0.5, 0.06)
    fx.add(tl.T_WHO + 4.6, whoosh(0.8), 0.07)
    # ---------- 40-65 WHAT WE DO: confidence; a purposeful accent per service, harmony moves each time
    big_hit(perc, fx, post, brs, tl.T_WHAT, 'D', 0.8)
    progs = [['D', 'A'], ['Bm', 'G'], ['G', 'A'], ['Em', 'A'], ['D', 'G']]
    for k in range(tl.SV_N):
        a = tl.SV_T0 + k * tl.SV_DUR
        lift = k / (tl.SV_N - 1)
        chords(pad, low, brs, a, a + tl.SV_DUR, progs[k], tl.SV_DUR / 2, 0.085 + 0.015 * lift, 3200 + 800 * lift, 0.03 + 0.02 * lift)
        ostinato(strs, a, a + tl.SV_DUR, progs[k], tl.SV_DUR / 2, 0.10 + 0.03 * lift)
        drums(perc, a, a + tl.SV_DUR, 0.85 + 0.25 * lift)
        fx.add(a - 0.55, whoosh(0.7), 0.08)
        perc.add(a, boom(2.0), 0.28)
        post.add(a, sub_hit(1.4), 0.10)
        theme(brs, bell, a + 0.5, THEME[k % 4: k % 4 + 4], 0.5, 0.05 + 0.02 * lift, major=True)
    # ---------- 65-98 OUR IMPACT: pride; every achievement lands; GAHAR is the big one
    fx.add(tl.T_IMPACT - 1.6, riser(1.6), 0.2)
    big_hit(perc, fx, post, brs, tl.T_IMPACT, 'A', 1.1)
    starts = tl.imp_starts()
    for k, (a, d) in enumerate(zip(starts, tl.IMP_DURS)):
        lift = k / (len(starts) - 1)
        prog = ['D', 'A', 'Bm', 'G'] if k % 2 == 0 else ['G', 'D', 'A', 'A']
        chords(pad, low, brs, a, a + d, prog, d / 2, 0.09 + 0.02 * lift, 3400, 0.04 + 0.03 * lift)
        ostinato(strs, a, a + d, prog, d / 2, 0.11 + 0.03 * lift)
        drums(perc, a, a + d, 0.95 + 0.3 * lift)
        land = a + tl.LAND
        fx.add(land - 1.1, riser(1.1), 0.09)
        if k == 1:                                                               # TEN GAHAR ACHIEVEMENTS
            big_hit(perc, fx, post, brs, land, 'D', 1.45)
            theme(brs, bell, land + 0.3, [74, 78, 81, 86, 81, 78, 81, 86, 90], 0.36, 0.11)
            post.add(land, shimmer(4.0), 0.07)
            for j in range(10):                                                  # one sparkle per institution
                bell.add(a + 0.3 + 0.16 * j, celesta(mf([86, 90, 93, 98][j % 4]), 1.0), 0.06)
        else:
            perc.add(land, boom(2.2), 0.34 + 0.12 * lift)
            post.add(land, sub_hit(1.6), 0.12)
            fx.add(land, crash(2.0), 0.04 + 0.03 * lift)
            for j, m in enumerate(THEME[:3]):
                bell.add(land + 0.1 + 0.12 * j, celesta(mf(m + 24), 1.4), 0.07)
    # ---------- 98-107 PEOPLE: an emotional breath (half-time), strings and piano
    big_hit(perc, fx, post, brs, tl.T_PEOPLE, 'G', 0.6)
    chords(pad, low, brs, tl.T_PEOPLE, tl.T_WALL, ['G', 'D', 'Em', 'A'], 2.25, 0.095, 2600)
    drums(perc, tl.T_PEOPLE, tl.T_WALL - 0.2, 0.6, 'half')
    for k, (dt, m) in enumerate([(0.3, 78), (0.9, 76), (1.5, 74), (2.4, 76), (3.0, 74), (3.6, 71), (4.5, 74),
                                 (5.1, 76), (5.7, 78), (6.6, 81), (7.2, 83), (7.8, 86)]):
        bell.add(tl.T_PEOPLE + dt, piano(mf(m)), 0.2)
    # ---------- 107-124 TRUSTED BY HEALTHCARE LEADERS: an uplifting build to the full network
    fx.add(tl.T_WALL - 1.4, riser(1.4), 0.16)
    big_hit(perc, fx, post, brs, tl.T_WALL, 'D', 0.9)
    chords(pad, low, brs, tl.T_WALL, tl.T_FUTURE, ['D', 'A', 'Bm', 'G'], 2.0, 0.1, 3600, 0.05)
    ostinato(strs, tl.T_WALL + 1.0, tl.T_FUTURE, ['D', 'A', 'Bm', 'G'], 2.0, 0.12)
    drums(perc, tl.T_WALL + 1.0, tl.T_FUTURE - 0.3, 1.15)
    theme(brs, bell, tl.T_WALL + 2.0, THEME, 0.5, 0.08, major=True)
    theme(brs, bell, tl.T_WALL + 8.0, THEME, 0.5, 0.1, major=True, octave=12)
    for k in range(int((tl.T_FUTURE - tl.T_WALL - 2) / 0.6)):                   # logo reveals: light sparkles on the beat
        bell.add(tl.T_WALL + 1.8 + 0.6 * k, celesta(mf([86, 90, 93, 98][k % 4]), 0.9), 0.05)
    # ---------- 124-139 FINALE: full climax on the logo and the line, then a clean resolution
    fx.add(tl.T_FUTURE, riser(tl.FIN_LOGO - tl.T_FUTURE), 0.22)
    ostinato(strs, tl.T_FUTURE, tl.FIN_LOGO, ['A', 'A'], 2.0, 0.14)
    for k in range(10):
        perc.add(tl.T_FUTURE + 1.2 + 0.4 * k, tom(70 + 8 * k, 0.6), 0.14 + 0.025 * k)
    big_hit(perc, fx, post, brs, tl.FIN_LOGO, 'D', 1.4)                         # the Eureka logo
    post.add(tl.FIN_LOGO, shimmer(3.0), 0.06)
    big_hit(perc, fx, post, brs, tl.FIN_LINE, 'D', 1.6)                         # FROM INSIGHT TO IMPACT. — final peak
    theme(brs, bell, tl.FIN_LINE + 0.2, [74, 78, 81, 86], 0.42, 0.12)
    for t, d, c in [(tl.FIN_LOGO, 2.0, 'D'), (tl.FIN_LINE, 2.6, 'G'), (tl.FIN_LINE + 2.6, 5.5, 'D')]:
        for j, m in enumerate(CH[c] + [CH[c][1] + 12, CH[c][2] + 12]):
            pad.add(t, strings_pad(mf(m + 12), d + 1.4, 3000), 0.11, pan=(j - 2) * 0.35)
        for j, m in enumerate(CH[c]):
            brs.add(t, brass(mf(m + 12), d + 0.4, 2000), 0.09, pan=(j - 1) * 0.3)
        low.add(t, strings_pad(mf(CH[c][0] - 12), d + 1.4, 500), 0.34)
    perc.add(tl.FIN_LINE + 2.6, timpani(mf(38), 3.0), 0.3)
    for j, m in enumerate([74, 78, 81, 86, 90]):
        bell.add(tl.FIN_LINE + 2.8 + 0.3 * j, celesta(mf(m), 2.6), 0.08)
    return [pad, strs, brs, bell, perc, fx, low], post


if __name__ == '__main__':
    out = sys.argv[1]
    E, G = tl.EUREKA_AT, tl.T_GOLD
    arc = ([0, 8.3, 11.0, E - 0.25, E - 0.05, G - 0.05, G, tl.T_BRIDGE, tl.T_BRIDGE + 2.4, tl.INSIGHT, tl.T_WHO,
            tl.T_IMPACT, tl.T_PEOPLE - 1, tl.T_PEOPLE + 0.5, tl.T_WALL, tl.T_FUTURE, tl.FIN_LINE, DUR - 4, DUR],
           [-15, -12, -8, -6, -16, -16, 0, -3, -8, -2, -3, -1, 0, -5, -2, -2, 0, -2, -5])
    x = M.mix(*compose(), arc=arc)
    M.write_wav(out, x)
    print('wrote', out)
