"""Shared timeline (seconds). 120 BPM: beat = 0.5 s, bar = 2 s.
Both music.py and render.py import this so cuts land on the beat."""
DURATION = 90.0
FPS = 30
W, H = 1920, 1080
BEAT = 0.5

S1 = (0.0, 10.0)    # The Spark of Excellence
S2 = (10.0, 20.0)   # The People Behind the Success
S3 = (20.0, 64.0)   # Celebrating Our Partners (20-24 title, then 10 x 4 s)
S4 = (64.0, 77.0)   # The Celebration Builds (76-77 = silence before the climax)
S5 = (77.0, 85.0)   # The Grand Reveal
S6 = (85.0, 90.0)   # The Grand Finale

PARTNERS_TITLE = (20.0, 24.0)
SLOT = 4.0
N_INSTITUTIONS = 10
INSTITUTION_STARTS = [24.0 + i * SLOT for i in range(N_INSTITUTIONS)]
