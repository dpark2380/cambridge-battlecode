# v63: v62 + B143, lone Golems ringed by clusters are worked from outside the ring

**Change (`src/bot.cpp`, `work_group`):** B140's fallback (walk to the group's approaches and strike any member in reach) also covers a Golem target when its group deals at most one Golem's damage (120).

**Why:** we are 3-17 on 02cuts in ranked, with 39.5 captures a game against 64.5. Its G16/G17 are one Golem inside 6 clusters (78 gems). The Golem has no path, so the group was skipped. The same shape appears on 00crater, 00dunes, 00quadrants, 00road-of-riches, 00split, 03riverbed and 03twisty.

**Local results:**
- arena vs v62, 3 seeds on the 8 maps: 38/64 = 59%, with a positive margin on 7 of them.
- gain gate on the 8 maps: PASS, 46/80 = 57%; gems +34 ± 42.
- nonreg on all maps: PASS, 186/344 = 54%; gems +37 ± 27, deaths −0.3 ± 0.6, gems captured +35 ± 23.

**Decision metrics:** ranked games on the 8 maps. The panel maps have no lone-Golem rings.
