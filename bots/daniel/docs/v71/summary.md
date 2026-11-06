# v71: v70 + B178/B179, bodies leave earlier: carriers under threat at 50%, everyone at 40%

**Change (`src/bot.cpp`):** `carrier_recall_health` 0.65 → 0.5. A body carrying gems that saw an enemy in the last 30 rounds goes home at 50% health, not 65%.

**Why:** B121 raised it from 0.5 to 0.65 on the old engine, when 24-42% of our deaths carried gems. Since v67 our bags are larger, and since v70 a threatened carrier already banks from 20 gems (B175), so it carries less when it meets an enemy. A sweep against v70 (gain gate, all 128 maps):

| carrier_recall_health | result |
|---|---|
| 0.8 | 180/512 = 35%, gems −152 ± 20, deaths +1.1 |
| 0.5 | **gain PASS** 816/1,536 = 53%, submitted gems +15 ± 12, captured +32 ± 10, deaths +0.5 ± 0.3 |
| 0.4 (vs 0.5) | 250/512 = 49%, gems −4 ± 21 |

Leaving early costs more farming time than the carried gems it saves.

**Also (B179):** `recall_health` 0.288 → 0.4, the health at which any body goes home (v23 set 0.288). Against v71-with-B178-only: 3,328 games, 53% (gain gate inconclusive, LLR +2.05), **deaths −1.5 ± 0.2**, submitted gems +28 ± 8, gold +138 ± 54. 0.5 vs 0.4: 234/512 = 46%, gems −16 ± 20. Folded in before submission.

**Final v71 vs v70** (gain gate, all 128 maps): inconclusive after 3,328 games, 53% (LLR +1.90); submitted gems +28.6 ± 8.1, gems captured +55.4 ± 7.2, gold +264 ± 54, deaths −0.9 ± 0.2.
