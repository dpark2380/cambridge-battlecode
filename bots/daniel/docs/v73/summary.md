# v73: v72 + B183, gold weight 0.3

**Change (`src/bot.cpp`):** `gold_weight` 0.2 → 0.3. A camp group's value is gems + gold_weight × gold per body per turn, so gold groups rank higher.

**Why:** 0.2 dates from v6. On engine 3.0.0 gold per clear fell 13% and the panel opponents outearn us (B154: their gold +923 a game, Power shards 75 → 96). The sweep against v72 (gain gate, all 128 maps):

| gold_weight | games | win | submitted gems | deaths | gold |
|---|---|---|---|---|---|
| 0.12 | 512 | 43% | −55 ± 21 | +2.1 | −1,304 |
| 0.25 | 1,024 | 51% | +33 ± 14 | −1.6 ± 0.3 | +605 |
| **0.3** | 1,024 | 51% | **+44 ± 14** | **−2.2 ± 0.3** | **+900** |
| 0.4 (vs 0.3) | 512 | 46% | −34 ± 19 | −1.4 | +549 |

More gold buys shards sooner, and stronger bodies die less. In the mirror the win rate stays flat (the gain gate fails on pair score), so the panel decides: the panel opponents are where the gold gap was measured.

**Gates:** nonreg vs v71 (v72 + B183 together): PASS 274/512 = 54%; submitted gems +49.6 ± 20.0, deaths −2.4 ± 0.4, gold +986 ± 150, gems captured +22.6 ± 17.6.
