# v76: v75 + B204, fight check skipped with no enemy in sight (panel trial)

**Change (`src/bot.cpp`, `fight_enemies`):** return before reading every visible ally's stats when no enemy champion is visible. No decision changes; it only saves fuel (~8k a turn).

**Why:** ranked games since v67 ran out of fuel heavily on big maps (77 of 470 games with 50+ fuel-exhausted turns; 04orchard 250-395 a game, 0-3). In the 04orchard summaries about 185 of our turns stalled in rounds 0-250, the opponent's about 1. A fuel profile found this check costing ~8k fuel a turn with no enemy near. With it skipped, our 04orchard fuel-outs in rounds 0-250 fell 186 → 35 (vs prof-aynir).

**Local evidence is inconclusive** because every local opponent stalls as much as we do, while ranked opponents almost never do: vs pe3 profiles on the panel maps −19 ± 22; on the 44 big maps +6 vs pe3-aynir, −10 vs pe3-meowest (of 176 each). The first v76 (B201: also a 50-round ward back-off after any failed placement) lost to v74 on the pe3 profiles (deaths +0.9) and was never submitted.

**Trial:** a live panel (v76p1) against v75p1 (58-31); back to v75 unless clearly better.
