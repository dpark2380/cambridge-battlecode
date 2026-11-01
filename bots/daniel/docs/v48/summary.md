# v48: v47 + B126b, collect emblem passives early

**Change:** `build_order` in `src/bot.cpp` is now a list. Each body finishes one emblem of each family below, in this order, then buys Bruiser of its stat for the rest of the game:

| Order | Family | Stat | Passive |
|---|---|---|---|
| 1 | Treasure | own | 20% more gold |
| 2 | Prospector | own | +25% of our share of cluster rewards |
| 3 | Durability | health | 10% less incoming damage |
| 4 | Jungle | own | 30% less damage from camps |

The old order was Prospector, Durability, then Bruiser forever.

**Why:** on v46's panel we clear as many camps as opponents (49 vs 52), but earn 5.2k gold against their 6.9k and take 41.7k champion damage against 34.7k. Kill gold explains only about 150 of the gold gap. Opponents collect several passives early: one panel opponent's Vesper finished six emblems by r200 and ended with 8.6k gold, 13 kills and 0 deaths.

**Local tests (on v47):**

| Test | Variant | Result |
|---|---|---|
| Race, 140 each | b126b: Treasure, Prospector, Durability, Jungle | 49% |
| Race, 140 each | b126a: Prospector, Treasure, Durability | 46% |
| Race, 140 each | b126c: Prospector, Treasure, Jungle, Durability, Monster | 45% |
| nonreg gate | vs v47 | PASS 52% |
| nonreg gate | vs v12 | PASS 73% |
| nonreg gate | vs Jame v3 | PASS 90% |

Self-play can't show an economy edge, because both sides farm the same camps. The real test is the scrim panel: gold, damage taken and deaths against v47.
