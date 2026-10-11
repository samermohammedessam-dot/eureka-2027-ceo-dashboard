"""Timeline for 'Lighting the City of Excellence' (seconds).
Beat = 0.55 s (~109 BPM); every torch arrival lands on a bar line of the music."""
DURATION = 90.0
BEAT = 0.55
BAR = 4 * BEAT                     # 2.2 s

S1 = (0.0, 10.0)                   # The Beginning
S2 = (10.0, 18.0)                  # The Spark
IGNITE = 10.3
SLOT0, SLOT, ARRIVE = 18.0, 4.4, 1.1   # Ten Milestones: travel 1.1 s, then 3.3 s showcase
N = 10
SLOT_STARTS = [SLOT0 + i * SLOT for i in range(N)]
ARRIVALS = [s + ARRIVE for s in SLOT_STARTS]          # 19.1, 23.5, ... 58.7
S4 = (62.4, 75.2)                  # The City Comes Alive
MUSIC_S4 = 63.1                    # key change bar
DROP = 75.2                        # music drops, energy flows to the centre
HIT = 77.4                         # the giant 10
FINALE = 85.1                      # final thank you
