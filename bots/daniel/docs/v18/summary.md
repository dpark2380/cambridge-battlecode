# v18 (from v17): the research strategy stack

## Evidence
`docs/research/strategy-options-2026-10-27.md`: we draft the top teams' core but our economy runs at half
theirs from round 1 (gold by r500 1,152 vs 2,427, gems at r500 144 vs 246, emblems 4 vs 12); 28 of v16's 64
losses were decided by r300. The gap is in mechanics we did not use: Heart of Ruin's damage dash, early
shopping, the Prospector emblem, wards, single-receiver captures, altar locks.

## Changes (all in src/bot.cpp, tagged v18 (B4x))
- B41 HoR dash kept for fights, aimed, counted in measure_damage.
- B42 shop at 150 gold for every role; a ≤10-gem bag does not block the trip when calm.
- B43 Prospector first emblem.
- B44 ward on the bush nearest the target whenever ready.
- B45 leave a waiting reward to an ally already capturing when calm.
- B49 lock the altar right after our own tribute.

## Results
- Races (140-420 games each, on the previous best): combo1 57% vs v17; B44 56% vs combo1; B45 54%, B49 54% vs B44.
- Gates: gain 200/280 = 71% vs v17; nonreg 210/280 = 75% vs v12, 231/280 = 82% vs Jame v3 (all PASS, data/stack2-gates.txt); gauntlet +346 [+315, +349] vs v17 +240, combo1 +292.
- The gauntlet maps to the ladder as ~1445 + 0.6 x local: +106 over v17 is roughly the +110 estimated for a 60%
  expected score against peers at our rating.

## Weaknesses / next
- Self-play overstates ladder gains (v16: 59% vs v15 locally, ~50% ranked). Judge it on its first ~100 ranked games.
- Untested from the note: B46 carrier hunting, B42c Treasure first, B50 spawn-tile denial, B47 guardians.
