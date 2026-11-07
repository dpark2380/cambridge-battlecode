# v78: v77 + B204, fight check skipped with no enemy in sight

**Change (`src/bot.cpp`, `fight_enemies`):** return before reading every visible ally's stats when no enemy champion is visible. No decision changes; it saves ~8k fuel a turn (the same change as v76, now on v77).

**Why now:** ranked games by version (7 Nov):

| version | games | won | mean fuel-out turns | games with 20+ fuel-outs (won) |
|---|---|---|---|---|
| v75 | 85 | 43 | 21.9 | 17 (9) |
| v76 (this fix on v75) | 35 | 20 | 12.1 | 5 (2) |
| v77 | 60 | 25 | 36.7 | 20 (7) |

On the 04* maps since v75 (27-39) the 'fuel' loss signature recurs on 04gap, 04wilds, 04comb, 04gem_rush, 04mountain_pass, 04butterfly, 04waves, 04two_kingdoms, 04terraces. Local opponents stall as much as we do, so local gates cannot show the gain (v76: pe3 −19 ± 22, big maps net −4/352); v76's panel (55 vs 58, 9 of 89 flipped) was within noise; in ranked it halved fuel-outs.

**Gate:** nonreg vs v77 PASS 260/512 = 51%, gems +6 ± 20.
