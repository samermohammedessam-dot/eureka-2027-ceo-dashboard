"""THE MOMENT v2 — one shared timeline for picture (moment_v2.py) and score (score_v2.py).

No narration: the only voice is the single synchronized "EUREKA!".
  0-17     DISCOVERY      mystery -> realization -> "EUREKA!" -> golden burst
  17-30    THE BRIDGE     golden ripples -> a leader facing complexity -> insight -> geometry -> blueprint -> hospital -> logo
  30-40    WHO WE ARE
  40-65    WHAT WE DO     five services, two actor panels each
  65-98    OUR IMPACT     eight counters; the ten GAHAR achievements get the longest, biggest moment
  98-107   PEOPLE
  107-124  TRUSTED BY HEALTHCARE LEADERS   logo panels from the approved upload, then the full network
  124-139  FINALE         light through the institutions -> Eureka logo -> FROM INSIGHT TO IMPACT
"""
DUR = 139.0
EUREKA_AT = 13.10                  # the voiced insert starts here (its own lip-synced audio)
EUREKA_CUT = 1.45                  # only the first, strongest shout
T_GOLD = EUREKA_AT + EUREKA_CUT    # golden light bursts from the water
T_BRIDGE, T_WHO, T_WHAT, T_IMPACT, T_PEOPLE, T_WALL, T_FUTURE = 17.0, 30.0, 40.0, 65.0, 98.0, 107.0, 124.0

INSIGHT = T_BRIDGE + 5.4           # the leader's moment of insight (match to Archimedes)
LOGO_REVEAL = T_BRIDGE + 9.6

SV_T0, SV_DUR, SV_N = T_WHAT + 1.5, 4.7, 5
IMP_T0 = T_IMPACT + 2.0
IMP_DURS = [3.6, 6.2, 3.6, 3.4, 3.4, 3.6, 3.6, 3.6]   # 10 GAHAR achievements: the long one
LAND = 1.65                        # inside a counter: the moment the number lands

WALL_HEAD = 1.6                    # heading before the first logo panel
WALL_PANEL = 4.2                   # each panel of five large logos
FIN_LOGO = T_FUTURE + 5.2          # Eureka logo lands
FIN_LINE = T_FUTURE + 7.2          # "FROM INSIGHT TO IMPACT." — the final musical peak


def imp_starts():
    out, t = [], IMP_T0
    for d in IMP_DURS:
        out.append(t)
        t += d
    return out
