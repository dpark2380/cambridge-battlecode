# v52: v51 + B131b, gold weight 0.5 before round 500

**Change:** the gold term in a camp group's value for target choice is weighted 0.5 before round 500 and 0.2 after (`early_gold_weight`, `early_rounds` in `src/bot.cpp`; the B113b/B125 rule, now on v51). The all-game 0.5 variant (`b131`) failed its gate: gold +1,691 ± 172 and deaths −2.8 ± 0.6 a game, but gems captured −72 ± 17 — bodies farm safe gold instead of gems.

**Why (v51p2 panel, scratch `mirror.py`: our captures of each group on our half vs the opponents' captures of its mirror):** the opponents re-farm the small wolf + gold groups on their half about 10 times a game and we take ours 0-2 times: 00collision G1/G3 0.0×/0.3× vs 10×/12×, 00galaxy G4 0 vs 10.7×, 00interlock G5/G11 2.3×/1.8× vs 9.5×/11×, 01big_world G18 0 vs 8.3×. Each is ~600 gold a game; with `gold_weight` 0.2 a 4-gem/60-gold group is worth 16 against 19 for an 11-gem wolf, so they never rank. Gold is the loop behind the fight gap (review §2.3: equal damage per shard, 23% fewer shards), and B126's Treasure emblem showed gold moves on the panel (+582 ± 165).

**Local gate:** nonreg vs v51 PASS 150/280 = 54%; A − B per game: gold +687 ± 238, deaths −1.4 ± 0.7, gems +26 ± 29, gems captured +14 ± 26 (`data/b131b-gate.txt`).

**Decision metrics:** `panelcmp.py v51p2 v52p2` gold, gold/clear, captures, gem margin, deaths; `mirror.py v52p2` captures of the wolf + gold groups above.
