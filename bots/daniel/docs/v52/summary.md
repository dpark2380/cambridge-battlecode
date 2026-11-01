# v52: v51 + B131, gold weight 0.5

**Change:** `gold_weight` 0.2 → 0.5 in `src/bot.cpp` (the gold term in a camp group's value for target choice, all game; B113b/B125 had tried 0.5 before round 500 only).

**Why (v51p2 panel, scratch `mirror.py`: our captures of each group on our half vs the opponents' captures of its mirror):** the opponents re-farm the small wolf + gold groups on their half about 10 times a game and we take ours 0-2 times: 00collision G1/G3 0.0×/0.3× vs 10×/12×, 00galaxy G4 0 vs 10.7×, 00interlock G5/G11 2.3×/1.8× vs 9.5×/11×, 01big_world G18 0 vs 8.3×. Each is ~600 gold a game; with `gold_weight` 0.2 a 4-gem/60-gold group is worth 16 against 19 for an 11-gem wolf, so they never rank. Gold is the loop behind the fight gap (review §2.3: equal damage per shard, 23% fewer shards), and B126's Treasure emblem showed gold moves on the panel (+582 ± 165).

**Local gate:** nonreg vs v51 (see `data/b131-gate.txt`).

**Decision metrics:** `panelcmp.py v51p2 v52p2` gold, gold/clear, captures, gem margin, deaths; `mirror.py v52p2` captures of the wolf + gold groups above.
