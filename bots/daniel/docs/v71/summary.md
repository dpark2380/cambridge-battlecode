# v71: v70 + B178, carriers under threat leave at half health

**Change (`src/bot.cpp`):** `carrier_recall_health` 0.65 → 0.5. A body carrying gems that saw an enemy in the last 30 rounds goes home at 50% health, not 65%.

**Why:** B121 raised it from 0.5 to 0.65 on the old engine, when 24-42% of our deaths carried gems. Since v67 our bags are larger, and since v70 a threatened carrier already banks from 20 gems (B175), so it carries less when it meets an enemy. A sweep against v70 (gain gate, all 128 maps):

| carrier_recall_health | result |
|---|---|
| 0.8 | 180/512 = 35%, gems −152 ± 20, deaths +1.1 |
| 0.5 | **gain PASS** 816/1,536 = 53%, submitted gems +15 ± 12, captured +32 ± 10, deaths +0.5 ± 0.3 |
| 0.4 (vs 0.5) | 250/512 = 49%, gems −4 ± 21 |

Leaving early costs more farming time than the carried gems it saves.
