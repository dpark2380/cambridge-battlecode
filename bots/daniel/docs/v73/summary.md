# v73: v72 + B183 gold weight 0.3 + B184 four bodies per group

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

**Also (B184):** `max_group_bodies` 3 → 4: up to four bodies work one group. vs v73-with-3: gain PASS 414/768 = 54%, submitted gems +35 ± 16, captured +28 ± 13, deaths −0.8 ± 0.4. Folded in before submission. (Duo recall 0.65 was worse: 46%.)

**Golem maps (B189):** groupgap flagged seven maps where opponents take Golem + gem groups 2-4 a game and we 0.5-1.3. Against prof-aynir on them (2 seeds): v71 27/42 = 64%, v73 36/42 = 86%; four bodies make a Golem group a normal target. On seven elk + gem maps also flagged: v71 21/42 = 50%, v73 30/42 = 71%.

**Live (version 90, live 16:32:05Z 6 Nov).** Panel v73p1 56-34: vs v71p1 (90 paired) wins 56 → 56, gem margin +20 ± 59, our gold +570 ± 207 (z 2.8), our deaths −1.1 ± 0.7, their deaths +1.6 ± 0.6 (z 2.6). Neutral on wins, better on gold and deaths: kept. Ranked 29-31 while live (16:32-18:32Z). Replaced by v74.
