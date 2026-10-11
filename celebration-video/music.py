"""Original procedural orchestral celebration score (royalty-free: composed and
synthesised here, no third-party samples).

120 BPM, 4/4 -> 1 beat = 0.5 s, 1 bar = 2 s. Structure follows timeline.py:
  0-10   elegant intro (strings pad, celesta)
  10-20  build (pulse, soft drums, riser)
  20-64  full celebration in D major, impact on every institution reveal
  64-76  key change to E, denser percussion, riser
  76-77  silence + reverse swell
  77-85  climax ("10" reveal)
  85-90  final resolution
"""
import numpy as np
from scipy import signal

import timeline as T

SR = 48000
DUR = T.DURATION
N = int(SR * DUR)
rng = np.random.default_rng(7)


def mf(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env_adsr(n, a, d, s, r):
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    e = np.full(n, s, dtype=np.float32)
    a = max(1, min(a, n)); e[:a] = np.linspace(0, 1, a)
    dd = max(0, min(d, n - a)); e[a:a + dd] = np.linspace(1, s, dd) if dd else e[a:a + dd]
    r = max(1, min(r, n)); e[n - r:] *= np.linspace(1, 0, r)
    return e


def lowpass(x, fc, order=2):
    fc = min(fc, SR * 0.45)
    sos = signal.butter(order, fc, 'low', fs=SR, output='sos')
    return signal.sosfilt(sos, x, axis=-1).astype(np.float32)


def highpass(x, fc, order=2):
    sos = signal.butter(order, fc, 'high', fs=SR, output='sos')
    return signal.sosfilt(sos, x, axis=-1).astype(np.float32)


def bandpass(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], 'band', fs=SR, output='sos')
    return signal.sosfilt(sos, x, axis=-1).astype(np.float32)


class Bus:
    def __init__(self, name, pan_spread=0.0):
        self.L = np.zeros(N, np.float32)
        self.R = np.zeros(N, np.float32)
        self.name = name

    def add(self, t0, x, gain=1.0, pan=0.0):
        i = int(t0 * SR)
        if i >= N or i + len(x) <= 0:
            return
        if i < 0:
            x = x[-i:]; i = 0
        x = x[:N - i] * gain
        gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        self.L[i:i + len(x)] += x * gl * 1.414
        self.R[i:i + len(x)] += x * gr * 1.414


def supersaw(freq, dur, voices=5, detune=0.012, vib=0.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for v in range(voices):
        d = 1 + detune * (v - (voices - 1) / 2) / max(1, (voices - 1) / 2)
        f = freq * d * (1 + vib * np.sin(2 * np.pi * 5.2 * t + v))
        ph = np.cumsum(f) / SR + rng.random()
        out += (2 * (ph % 1.0) - 1).astype(np.float32)
    return out / voices


# ----------------------------------------------------------------- instruments
def strings_pad(freq, dur, bright=2200):
    x = supersaw(freq, dur + 0.8, voices=7, detune=0.009, vib=0.003)
    x = lowpass(x, bright, 2)
    return x * env_adsr(len(x), 0.6, 0.3, 0.85, 0.9)


def spiccato(freq, dur=0.11, bright=3000):
    x = supersaw(freq, dur + 0.12, voices=3, detune=0.006)
    x = lowpass(x, bright, 2)
    return x * env_adsr(len(x), 0.004, 0.06, 0.45, 0.1)


def brass(freq, dur, bright=1800):
    n = int((dur + 0.4) * SR)
    x = supersaw(freq, dur + 0.4, voices=3, detune=0.004, vib=0.002)
    # filter sweep (brightness opens on attack) – approximate in 3 segments
    a = lowpass(x, bright * 0.45, 2)
    b = lowpass(x, bright, 2)
    w = np.clip(np.arange(n) / (0.12 * SR), 0, 1)
    x = a * (1 - w) + b * w
    return x * env_adsr(n, 0.05, 0.2, 0.8, 0.4)


def celesta(freq, dur=1.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 2 * t) * np.exp(-t * 6)
         + 0.15 * np.sin(2 * np.pi * freq * 4.2 * t) * np.exp(-t * 10))
    return (x * np.exp(-t * 3.2) * np.minimum(1, t / 0.002)).astype(np.float32)


def piano(freq, dur=2.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * freq * k * (1 + 0.0004 * k * k) * t) * np.exp(-t * (1.6 + k * 0.9))
            for k, a in enumerate([1, .5, .28, .16, .08], start=1))
    return (x * np.minimum(1, t / 0.003)).astype(np.float32)


def timpani(freq=55, dur=1.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = freq * (1 + 0.25 * np.exp(-t * 18))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.8)
    x += 0.4 * lowpass(rng.standard_normal(n).astype(np.float32), 900) * np.exp(-t * 25)
    return x.astype(np.float32)


def boom(dur=2.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 32 + 90 * np.exp(-t * 9)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
    return np.tanh(1.6 * x).astype(np.float32)


def kick(dur=0.45):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t * 30)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)).astype(np.float32)


def snare(dur=0.3):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = bandpass(rng.standard_normal(n).astype(np.float32), 900, 7000) * np.exp(-t * 16)
    x += 0.5 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25)
    return x.astype(np.float32)


def tom(freq=95, dur=0.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = freq * (1 + 0.5 * np.exp(-t * 25))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6)
    x += 0.25 * lowpass(rng.standard_normal(n).astype(np.float32), 1500) * np.exp(-t * 30)
    return x.astype(np.float32)


def shaker(dur=0.08):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return (highpass(rng.standard_normal(n).astype(np.float32), 6000) * np.exp(-t * 60)).astype(np.float32)


def crash(dur=3.2):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = highpass(rng.standard_normal(n).astype(np.float32), 3500, 2)
    return (x * np.exp(-t * 1.4) * np.minimum(1, t / 0.003)).astype(np.float32)


def riser(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n).astype(np.float32)
    out = np.zeros(n, np.float32)
    seg = 8
    for k in range(seg):
        a, b = k * n // seg, (k + 1) * n // seg
        fc = 400 * (12 ** (k / seg))
        out[a:b] = bandpass(noise, fc, min(fc * 2.5, 20000))[a:b]
    return out * (t / dur) ** 2


# ------------------------------------------------------------------ harmony
CHORDS = {  # root midi (octave 3), quality
    'D': (50, 'M'), 'A': (45, 'M'), 'Bm': (47, 'm'), 'G': (43, 'M'),
    'E': (52, 'M'), 'B': (47, 'M'), 'C#m': (49, 'm'), 'Esus': (52, 's'),
    'F#m': (54, 'm'),
}


def chord_notes(name):
    r, q = CHORDS[name]
    third = {'M': 4, 'm': 3, 's': 5}[q]
    return r, [r, r + third, r + 7]


def bar_chord(t):
    """Chord sounding at time t."""
    if t < 10:
        return ['D', 'Bm', 'G', 'A', 'A'][int(t // 2)]
    if t < 20:
        return ['D', 'Bm', 'G', 'A', 'A'][int((t - 10) // 2)]
    if t < 64:
        return ['D', 'A', 'Bm', 'G'][int((t - 20) // 2) % 4]
    if t < 76:
        return ['E', 'B', 'C#m', 'A'][int((t - 64) // 2) % 4]
    if t < 77:
        return None
    if t < 85:
        return ['E', 'C#m', 'A', 'B'][int((t - 77) // 2)]
    return 'E'


def compose():
    pad, strings, brs, bell, perc, fx, low = (Bus(n) for n in
                                              ['pad', 'str', 'brass', 'bell', 'perc', 'fx', 'low'])

    # ---- sustained pad + bass, per bar
    sections = [(0, 10, 0.20, 1400), (10, 20, 0.24, 2000), (20, 64, 0.22, 2600),
                (64, 76, 0.24, 3000), (77, 85, 0.30, 3600)]
    for s0, s1, g, br in sections:
        t = s0
        while t < s1 - 1e-6:
            ch = bar_chord(t + 0.01)
            r, notes = chord_notes(ch)
            for k, m in enumerate(notes + [notes[1] + 12, notes[2] + 12]):
                pad.add(t, strings_pad(mf(m + 12), 2.0, br), g * 0.33, pan=(k - 2) * 0.3)
            low.add(t, strings_pad(mf(r - 12), 2.0, 600), g * 0.9)
            t += 2

    # ---- celesta arpeggio in intro & build (8ths)
    for s0, s1, g in [(1.0, 20, 0.16), (20, 64, 0.08)]:
        t = s0
        while t < s1 - 1e-6:
            ch = bar_chord(t + 0.01)
            _, notes = chord_notes(ch)
            seq = [notes[0] + 24, notes[1] + 24, notes[2] + 24, notes[0] + 36]
            i = int(round(t / 0.25))
            m = seq[i % 4] if i % 8 < 4 else seq[3 - i % 4]
            bell.add(t, celesta(mf(m)), g * (0.6 + 0.4 * min(1, t / 8)), pan=0.4 * np.sin(i))
            t += 0.25

    # ---- intro piano motif
    for t, m in [(2.0, 66), (2.5, 69), (3.0, 74), (4.0, 73), (6.0, 71), (6.5, 74), (7.0, 78), (8.0, 76)]:
        bell.add(t, piano(mf(m)), 0.32)

    # ---- string pulse (8ths) 10-20, spiccato 16ths after 20
    for s0, s1, step, g in [(10, 20, 0.25, 0.20), (20, 64, 0.125, 0.16), (64, 76, 0.125, 0.19)]:
        t = s0
        while t < s1 - 1e-6:
            ch = bar_chord(t + 0.01)
            r, notes = chord_notes(ch)
            i = int(round((t - s0) / step))
            m = [r, r + 12, notes[2], r + 12][i % 4]
            acc = 1.0 if i % 4 == 0 else 0.7
            strings.add(t, spiccato(mf(m)), g * acc, pan=-0.35)
            strings.add(t, spiccato(mf(m + 12), bright=3600), g * 0.5 * acc, pan=0.35)
            t += step

    # ---- drums
    for b in np.arange(10, 20, 1.0):  # soft kick on 1 & 3
        perc.add(b, kick(), 0.35)
    for b in np.arange(18, 20, 0.125):  # snare roll crescendo into 20
        perc.add(b, snare(), 0.08 + 0.25 * (b - 18) / 2)
    fx.add(16, riser(4.0), 0.22)
    for s0, s1, dense in [(20, 64, False), (64, 76, True)]:
        b = s0
        while b < s1 - 1e-6:
            beat = int(round((b - s0) / 0.5)) % 4
            perc.add(b, kick(), 0.55)
            if beat in (1, 3):
                perc.add(b, snare(), 0.30)
            perc.add(b + 0.25, shaker(), 0.10)
            if dense:
                perc.add(b + 0.125, shaker(), 0.06); perc.add(b + 0.375, shaker(), 0.06)
                perc.add(b, tom(80 if beat % 2 else 110), 0.30)
            b += 0.5
    # tom fills at end of each 2-bar institution slot
    for s in np.arange(22, 64, 4.0):
        for k, dt in enumerate([1.5, 1.625, 1.75, 1.875]):
            perc.add(s + dt, tom(140 - k * 18), 0.32)
    # snare roll + riser into the silence
    for b in np.arange(72, 76, 0.0625):
        perc.add(b, snare(), 0.05 + 0.3 * ((b - 72) / 4) ** 2)
    fx.add(70, riser(6.0), 0.35)

    # ---- impacts: section downbeats + every institution reveal
    impacts = [20.0] + list(T.INSTITUTION_STARTS) + [64.0]
    for t in impacts:
        perc.add(t, boom(), 0.55)
        fx.add(t, crash(), 0.16)
        perc.add(t, timpani(mf(38)), 0.4)

    # ---- brass: stabs on institution reveals + chords
    for s0, s1, g in [(20, 64, 0.16), (64, 76, 0.2)]:
        t = s0
        while t < s1 - 1e-6:
            r, notes = chord_notes(bar_chord(t + 0.01))
            for m in notes:
                brs.add(t, brass(mf(m + 12), 1.4), g * 0.6)
            brs.add(t + 1.5, brass(mf(notes[1] + 12), 0.4), g * 0.4)
            t += 2

    # ---- heroic melody (horn/strings), in eighths per 4-bar phrase
    phrase_D = [(0, 66, 2), (2, 69, 2), (4, 74, 3), (7, 73, 1),
                (8, 76, 2), (10, 73, 2), (12, 69, 4),
                (16, 71, 2), (18, 74, 2), (20, 78, 3), (23, 76, 1),
                (24, 74, 2), (26, 71, 2), (28, 69, 4)]
    for p0 in np.arange(28, 64, 8.0):
        for e, m, L in phrase_D:
            brs.add(p0 + e * 0.25, brass(mf(m), L * 0.25 * 0.95, 2600), 0.20, pan=0.15)
            strings.add(p0 + e * 0.25, strings_pad(mf(m + 12), L * 0.25, 3200) * 0.6, 0.20, pan=-0.15)
    for p0 in [64.0, 72.0]:
        for e, m, L in phrase_D:
            if p0 + e * 0.25 >= 76:
                continue
            brs.add(p0 + e * 0.25, brass(mf(m + 2), L * 0.25 * 0.95, 3000), 0.24, pan=0.15)
            strings.add(p0 + e * 0.25, strings_pad(mf(m + 14), L * 0.25, 3600) * 0.6, 0.24)

    # ---- the silence: reverse swell into 77
    rc = crash(1.0)[::-1].copy()
    post = Bus('post')  # added after the silence duck
    post.add(76.0, rc * np.linspace(0, 1, len(rc)) ** 2, 0.5)
    post.add(76.0, riser(1.0), 0.25)

    # ---- CLIMAX 77-85
    perc.add(77, boom(4.0), 0.85)
    fx.add(77, crash(4.0), 0.30)
    for b in np.arange(77, 85, 0.5):
        perc.add(b, kick(), 0.6)
        perc.add(b, timpani(mf(40) if int((b - 77) * 2) % 2 == 0 else mf(47), 0.8), 0.32)
        if int(round((b - 77) / 0.5)) % 2 == 1:
            perc.add(b, snare(), 0.32)
        perc.add(b + 0.25, shaker(), 0.12)
    for t in [79.0, 81.0, 83.0]:
        fx.add(t, crash(), 0.14)
    t = 77.0
    while t < 85:
        r, notes = chord_notes(bar_chord(t + 0.01))
        for m in notes + [notes[0] + 12]:
            brs.add(t, brass(mf(m + 12), 1.9, 2600), 0.20)
        t += 2
    climax_mel = [(0, 76, 4), (4, 80, 2), (6, 83, 2), (8, 85, 4), (12, 83, 2), (14, 80, 2),
                  (16, 81, 4), (20, 85, 2), (22, 88, 2), (24, 87, 6), (30, 86, 2)]
    for e, m, L in climax_mel:
        brs.add(77 + e * 0.25, brass(mf(m - 12), L * 0.25 * 0.95, 3200), 0.24)
        strings.add(77 + e * 0.25, strings_pad(mf(m), L * 0.25, 4200) * 0.6, 0.22)
    for b in np.arange(84, 85, 0.0625):  # timpani roll into the finale
        perc.add(b, timpani(mf(40), 0.4), 0.10 + 0.25 * (b - 84))

    # ---- FINALE 85-90: big E major chord, ring-out
    perc.add(85, boom(4.5), 0.75)
    fx.add(85, crash(5.0), 0.30)
    for m in [40, 52, 56, 59, 64, 68, 71, 76]:
        pad.add(85, strings_pad(mf(m), 4.2, 3200), 0.12)
        brs.add(85, brass(mf(m), 3.2, 2400), 0.10)
    for k, m in enumerate([76, 80, 83, 88, 92]):
        bell.add(85.5 + k * 0.25, celesta(mf(m), 3.0), 0.18)
    return [pad, strings, brs, bell, perc, fx, low], post


def reverb_ir(seconds, decay, lp):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    irs = []
    for _ in range(2):
        x = rng.standard_normal(n).astype(np.float32) * np.exp(-t * decay)
        irs.append(lowpass(x, lp))
    irs = np.stack(irs)
    return irs / np.sqrt((irs ** 2).sum(axis=1, keepdims=True))


def mix(buses, post):
    sends = {'pad': 0.55, 'str': 0.35, 'brass': 0.45, 'bell': 0.55, 'perc': 0.18, 'fx': 0.3, 'low': 0.1}
    gains = {'pad': 1.0, 'str': 1.0, 'brass': 1.1, 'bell': 0.9, 'perc': 1.0, 'fx': 0.9, 'low': 0.8}
    dry = np.zeros((2, N), np.float32)
    wet_in = np.zeros((2, N), np.float32)
    for b in buses:
        st = np.stack([b.L, b.R]) * gains[b.name]
        dry += st
        wet_in += st * sends[b.name]
    ir = reverb_ir(2.8, 2.2, 5000)
    wet = np.stack([signal.fftconvolve(wet_in[c], ir[c])[:N] for c in range(2)])
    out = dry + 0.55 * wet
    out = highpass(out, 28, 2)
    # bus compression (slow RMS follower) + soft clip
    rms = np.sqrt(lowpass((out ** 2).mean(axis=0), 3, 1).clip(1e-9))
    target = np.percentile(rms, 95)
    gr = np.minimum(1.0, (target / rms) ** 0.2)
    out = out * gr
    out /= np.abs(out).max()
    # dynamic arc: elegant intro -> celebration -> climax, plus the dramatic silence
    t = np.arange(N) / SR
    keys_t = [0, 9.5, 10, 19.5, 20, 63.5, 64, 75.9, 76.05, 76.95, 77.0, 85, 90]
    keys_db = [-11, -9, -7.5, -5, -2.5, -2.5, -1.5, -0.5, -26, -26, 0, 0, 0]
    out *= 10 ** (np.interp(t, keys_t, keys_db) / 20)
    out += np.stack([post.L, post.R]) * 0.5
    out = np.tanh(out * 1.6) / np.tanh(1.6)
    # final fade
    fade = np.clip((90 - t) / 1.8, 0, 1) ** 1.5
    out *= fade
    out *= 0.89 / np.abs(out).max()
    return out


def write_wav(path, x):
    import wave
    pcm = (np.clip(x.T, -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == '__main__':
    import sys, os
    out = sys.argv[1] if len(sys.argv) > 1 else 'build/score.wav'
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    write_wav(out, mix(*compose()))
    print('wrote', out)
