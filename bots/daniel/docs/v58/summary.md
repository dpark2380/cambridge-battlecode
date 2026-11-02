# v58: v51 + B136, walk home around enemies

**Change (`src/bot.cpp`, `retreat()`; `src/bot.h`):** when a body walks home, tiles within 2 of any visible enemy champion count as walls for that path (a new `avoid` bitboard that `move_towards_closest` adds to its blocked tiles, empty except during `retreat()`). If that leaves no path, the body takes the direct route as before.

**Why (B136):** on panel v2, 46% of our deaths happen walking home against the opponents' 30% (`tools/fights.py`), and B93 found those victims mostly healthy travellers 20+ tiles from home. The leave thresholds were tuned repeatedly with neutral results (B93, B122, B123); the route never changed: `retreat()` took the shortest path to spawn, straight past visible enemies. v51's worst ranked map on 2 Nov, 00swirl (0-4), had 39-61 deaths a game to champions.

**Local gate:** nonreg vs v51 PASS 174/344 = 51% (86 maps, including the 16 new ones); A − B per game deaths +0.3 ± 0.6, gems +2 ± 25, gold −43 ± 198 (mirror games rarely put a retreating body past an enemy).

**Decision metrics:** `panelcmp.py v51p2 v58p2` deaths and gem margin; the walking-home share of deaths in `fights.py` (vs 46%); then ≥100 ranked games before anything is stacked on it.
