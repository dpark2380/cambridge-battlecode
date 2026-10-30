# Daniel v39: v38 + B111 (Willow on six maps)

Code: `bots/daniel/v39` = `bots/daniel/v38` plus backlog B111 in `draft.cpp` (`willow_maps`, `project_team`).
Only the draft changes, and only on six maps; everywhere else v39 plays exactly as v38.

## Evidence

Top-60 scout (2026-10-30 14:40Z, 5,950 games): teams that draft Willow win far more often on six maps (z ≥ 2):

| Map | With Willow | Without |
|---|---|---|
| 00dunes | 79% (19) | 37% (52) |
| 00eight | 68% (34) | 35% (43) |
| 00vault | 71% (21) | 43% (58) |
| 00monolith | 72% (18) | 46% (74) |
| 00crater | 66% (32) | 43% (58) |
| 02crossing | 65% (34) | 43% (54) |

Across all maps Willow is neutral (52% vs 50%), and the per-map effect spreads both ways (01fracture z −3.8), so part of
it is chance or team selection; only the z ≥ 2 maps are used. Our ranked record on these six since 28 Oct: 35-44 (44%)
vs 472-464 (50%) elsewhere.

## Change

On those maps (keyed by width, height and total gems, unique over the 70 maps) Willow replaces the last core pick:
Vesper, Heart of Ruin, Marcella, Vendetta, Willow (Ryth out); on 4-pick 00vault, Willow replaces Vendetta.

## Tests

| Gate | Result |
|---|---|
| Map vs v38 (the six) | FAIL 31/60 = 52%: locally neutral; no local bot punishes a team without a healer |
| vs hunter-v0 on the six (60 games) | 93% (v38 95%) |
| Nonreg vs v38, all maps | PASS 141/280 = 50% |
| Nonreg vs v12 | PASS 226/280 = 81% |
| Nonreg vs Jame v3 | PASS 257/280 = 92% |

Submitted under the overnight scout-evidence clause (locally neutral, fixes a weakness measured against real opponents).
The real test is ranked and scrims on those maps.
