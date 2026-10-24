"""THE MOMENT — original 135 s orchestral score (synthesised from music.py instruments: royalty-free).

Cues follow moment_film.py:
  0-8.3     mystery: low strings, a lone piano motif in B minor (Archimedes studies the crown)
  8.3-13.1  the overflow, a held breath, a rising swell into the realization
  13.1      "EUREKA!" — the first full-orchestra hit, resolving to D major
  13.1-17   golden light: celesta shimmer
  17-30     purpose: a pulse is born; the Eureka logo lands at ~26.6
  30-50     who we are: warm piano and strings under the narration
  50-75     what we do: momentum, an accent on every service
  75-105    our impact: building drums and brass, an award hit on every achievement
  105-125   people & partnerships: emotional strings, sparkles on the partner logos
  125-135   the future: crescendo, the finale hit and a warm resolution
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import music as M  # noqa: E402

DUR = 135.0
M.N = int(M.SR * DUR)
from music import (Bus, boom, brass, celesta, crash, kick, mf, piano, riser, shaker, snare,  # noqa: E402
                   spiccato, strings_pad, timpani, tom)

B = 0.6
EUREKA, PURPOSE, LOGO, WHO, WHAT, IMPACT, PEOPLE, PARTNERS, FUTURE = 13.1, 17.0, 26.6, 30.0, 50.0, 75.0, 105.0, 117.0, 125.0
SERV_T0, SERV_DUR = WHAT + 1.8, (IMPACT - WHAT - 1.8) / 7
IMP_T0 = IMPACT + 2.2
IMP_DUR = (PEOPLE - IMP_T0) / 8
FINALE = FUTURE + 4.2
CH = {'D': [50, 54, 57], 'A': [45, 49, 52], 'Bm': [47, 50, 54], 'G': [43, 47, 50], 'F#m': [42, 45, 49], 'Em': [40, 43, 47]}
MOTIF = [71, 74, 78, 76]   # B4 D5 F#5 E5 — the "discovery" motif


def chord_at(t):
    if t < EUREKA:
        return ['Bm', 'G', 'Em', 'F#m'][int(t / 3.3) % 4]
    if t < WHO:
        return ['D', 'A', 'Bm', 'G'][int((t - EUREKA) / 2.4) % 4]
    if t < WHAT:
        return ['G', 'D', 'A', 'Bm'][int((t - WHO) / 2.5) % 4]
    if t < IMPACT:
        return ['D', 'Bm', 'G', 'A'][int((t - SERV_T0) / SERV_DUR) % 4] if t >= SERV_T0 else 'A'
    if t < PEOPLE:
        return ['D', 'A', 'Bm', 'G'][int((t - IMP_T0) / IMP_DUR) % 4] if t >= IMP_T0 else 'A'
    if t < FUTURE:
        return ['Bm', 'G', 'D', 'A'][int((t - PEOPLE) / 3.0) % 4]
    return 'A' if t < FINALE else ('G' if FINALE + 2.4 <= t < FINALE + 3.6 else 'D')


def spans(t0, t1, step):
    t = t0
    while t < t1 - 0.05:
        yield t, min(step, t1 - t), chord_at(t + 0.01)
        t += step


def pads(pad, low, t0, t1, step, gain, bright, octave_up=True):
    for t, d, c in spans(t0, t1, step):
        notes = CH[c] + ([CH[c][1] + 12] if octave_up else [])
        for j, m in enumerate(notes):
            pad.add(t, strings_pad(mf(m + 12), d + 0.4, bright), gain, pan=(j - 1.5) * 0.4)
        low.add(t, strings_pad(mf(CH[c][0] - 12), d + 0.4, 480), gain * 3.2)


def pulse(strs, perc, t0, t1, lift, kick_on=True, snare_on=False, step=B / 2):
    t = t0
    j = 0
    while t < t1 - 0.05:
        c = chord_at(t)
        strs.add(t, spiccato(mf(CH[c][0] + 12 + (12 if j % 2 else 0))), 0.08 + 0.06 * lift, pan=0.3 if j % 2 else -0.3)
        if kick_on and j % 2 == 0:
            perc.add(t, kick(), 0.18 + 0.12 * lift)
        if snare_on and j % 4 == 2:
            perc.add(t, snare(), 0.09 + 0.08 * lift)
        if lift > 0.3:
            perc.add(t, shaker(), 0.03 + 0.02 * lift, pan=0.4)
        t += step
        j += 1


def hit(perc, fx, brs, t, big=1.0, chord='D'):
    perc.add(t, boom(3.2), 0.45 * big)
    perc.add(t, timpani(mf(38), 1.8), 0.32 * big)
    fx.add(t, crash(3.0), 0.07 * big)
    for j, m in enumerate(CH[chord] + [CH[chord][0] + 12]):
        brs.add(t, brass(mf(m + 12), 2.2, 2600), 0.07 * big, pan=(j - 1.5) * 0.3)


def compose():
    pad, strs, brs, bell, perc, fx, low = (Bus(n) for n in ['pad', 'str', 'brass', 'bell', 'perc', 'fx', 'low'])
    post = Bus('post')
    # 0-13.1 mystery and the held breath
    drone = strings_pad(mf(35), 13.5, 300)
    low.add(0.0, drone * np.linspace(0, 1, len(drone)) ** 0.6, 0.36)
    pads(pad, low, 1.5, EUREKA, 3.3, 0.05, 1300, octave_up=False)
    for k, (t, m) in enumerate([(1.2, 71), (2.0, 74), (2.8, 78), (3.9, 76), (5.4, 71), (6.2, 74), (7.0, 79), (8.3, 78)]):
        bell.add(t, piano(mf(m)), 0.22)
    perc.add(8.3, timpani(mf(35), 1.6), 0.22)                 # the overflow
    fx.add(8.3, riser(2.6), 0.08)
    for t in np.arange(8.3, 11.0, B / 2):                     # a nervous pulse while the water spills
        strs.add(t, spiccato(mf(47 + (12 if int(t / (B / 2)) % 2 else 0))), 0.06, pan=-0.2)
    fx.add(11.1, riser(2.0), 0.2)                              # the realization: the swell
    for j, m in enumerate([59, 62, 66, 71]):
        pad.add(11.1, strings_pad(mf(m + 12), 2.1, 2600), 0.06, pan=(j - 1.5) * 0.4)
    # 13.1 EUREKA!
    hit(perc, fx, brs, EUREKA, 1.25, 'D')
    for j, m in enumerate([74, 78, 81, 86, 90, 93, 98]):
        bell.add(EUREKA + 0.15 + 0.11 * j, celesta(mf(m), 2.6), 0.12)
    pads(pad, low, EUREKA, PURPOSE, 2.4, 0.08, 2600)
    for j, m in enumerate([86, 90, 93, 98, 102]):            # golden light from the water
        bell.add(15.7 + 0.18 * j, celesta(mf(m), 2.2), 0.10)
    # 17-30 purpose
    pads(pad, low, PURPOSE, WHO, 2.4, 0.075, 2000)
    pulse(strs, perc, PURPOSE + 2.4, WHO - 0.2, 0.2, kick_on=False)
    fx.add(LOGO - 1.6, riser(1.6), 0.15)
    hit(perc, fx, brs, LOGO, 0.9, 'D')
    for j, m in enumerate(MOTIF):
        bell.add(LOGO + 0.2 + 0.25 * j, celesta(mf(m + 12), 2.0), 0.11)
    # 30-50 who we are: warm and human
    pads(pad, low, WHO, WHAT, 2.5, 0.07, 2200)
    for k in range(8):
        t = WHO + 0.4 + 2.5 * k
        c = chord_at(t)
        for j, m in enumerate([CH[c][0] + 12, CH[c][1] + 12, CH[c][2] + 12, CH[c][1] + 24]):
            bell.add(t + 0.3 * j, piano(mf(m)), 0.16)
    pulse(strs, perc, WHO + 10.0, WHAT, 0.3, kick_on=True)
    # 50-75 what we do: momentum with an accent per service
    perc.add(WHAT, boom(2.4), 0.35)
    fx.add(WHAT, crash(2.0), 0.05)
    pads(pad, low, WHAT, IMPACT, SERV_DUR, 0.075, 2600)
    pulse(strs, perc, SERV_T0, IMPACT - 0.3, 0.55, kick_on=True, snare_on=True)
    for k in range(7):
        t = SERV_T0 + k * SERV_DUR
        perc.add(t, timpani(mf(38), 1.2), 0.22)
        fx.add(t - 0.5, riser(0.5), 0.07)
        bell.add(t + 0.1, celesta(mf(MOTIF[k % 4] + 12), 1.4), 0.08)
    # 75-105 our impact: an award hit on every achievement, building
    fx.add(IMPACT - 1.5, riser(1.5), 0.18)
    hit(perc, fx, brs, IMPACT, 1.0, 'A')
    pads(pad, low, IMPACT, PEOPLE, IMP_DUR, 0.085, 3000)
    pulse(strs, perc, IMP_T0, PEOPLE - 0.3, 0.8, kick_on=True, snare_on=True)
    for k in range(8):
        land = IMP_T0 + k * IMP_DUR + 1.65
        lift = k / 7
        perc.add(land, boom(2.2), 0.3 + 0.15 * lift)
        perc.add(land, timpani(mf(38), 1.4), 0.25)
        fx.add(land, crash(2.2), 0.04 + 0.03 * lift)
        fx.add(land - 1.2, riser(1.2), 0.08)
        for j, m in enumerate(MOTIF):
            bell.add(land + 0.1 + 0.12 * j, celesta(mf(m + 12), 1.6), 0.09)
        if k >= 3:
            c = chord_at(land)
            for j, m in enumerate(CH[c]):
                brs.add(land, brass(mf(m + 12), IMP_DUR - 1.7), 0.05 + 0.04 * lift, pan=(j - 1) * 0.3)
    # 105-125 people and partnerships: emotional
    perc.add(PEOPLE, boom(3.0), 0.3)
    pads(pad, low, PEOPLE, FUTURE, 3.0, 0.085, 2400)
    for k, (dt, m) in enumerate([(0.4, 78), (1.0, 76), (1.6, 74), (2.2, 76), (3.4, 74), (4.0, 73), (4.6, 71), (5.2, 74),
                                 (6.4, 74), (7.0, 76), (7.6, 78), (8.2, 81), (9.4, 81), (10.0, 83), (10.6, 85), (11.2, 86)]):
        bell.add(PEOPLE + dt, piano(mf(m)), 0.22)
    pulse(strs, perc, PEOPLE + 6.0, PARTNERS, 0.35, kick_on=True)
    for j in range(10):
        bell.add(PARTNERS + 0.75 + 0.18 * j, celesta(mf([86, 90, 93, 98, 93, 90, 86, 90, 93, 98][j]), 1.4), 0.08)
    # 125-135 the future: crescendo, finale, resolution
    fx.add(FUTURE, riser(4.2), 0.2)
    pulse(strs, perc, FUTURE, FINALE, 1.0, kick_on=True, snare_on=True, step=B / 4)
    for k in range(7):
        perc.add(FUTURE + 1.4 + 0.4 * k, tom(90 + 12 * k), 0.12 + 0.03 * k)
    hit(perc, fx, brs, FINALE, 1.3, 'D')
    for j, m in enumerate([74, 78, 81, 86, 90, 93, 98]):
        bell.add(FINALE + 0.1 + 0.12 * j, celesta(mf(m), 3.0), 0.12)
    for t, d in [(FINALE, 2.4), (FINALE + 2.4, 1.2), (FINALE + 3.6, 2.4)]:
        c = chord_at(t + 0.01)
        for j, m in enumerate(CH[c] + [CH[c][1] + 12, CH[c][2] + 12]):
            pad.add(t, strings_pad(mf(m + 12), d + 1.2, 2600), 0.1, pan=(j - 2) * 0.35)
        for j, m in enumerate(CH[c]):
            brs.add(t, brass(mf(m + 12), d + 0.4, 1800), 0.08, pan=(j - 1) * 0.3)
        low.add(t, strings_pad(mf(CH[c][0] - 12), d + 1.2, 500), 0.3)
    perc.add(FINALE + 2.0, timpani(mf(38), 2.0), 0.25)          # "FROM INSIGHT TO IMPACT."
    for j, m in enumerate(MOTIF):
        bell.add(FINALE + 2.1 + 0.28 * j, celesta(mf(m + 12), 2.4), 0.1)
    return [pad, strs, brs, bell, perc, fx, low], post


if __name__ == '__main__':
    out = sys.argv[1]
    arc = ([0, 8.3, 11.0, EUREKA - 0.05, EUREKA, PURPOSE, WHO, WHAT, IMPACT, PEOPLE - 1, PEOPLE, FUTURE, FINALE, DUR - 2, DUR],
           [-13, -11, -9, -6, 0, -4, -6, -4, -2, -1, -4, -3, 0, -2, -6])
    x = M.mix(*compose(), arc=arc)
    M.write_wav(out, x)
    print('wrote', out)
