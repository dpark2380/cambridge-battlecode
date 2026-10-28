# v23: v22 + B62 (don't walk home under attack)

## Problem
Research note `docs/research/path-to-60-2026-10-28.md` §2: 46% of our scrim-panel deaths came while walking home
(opponents 19%); for Ryth it was 69%, Heart of Ruin 57%. Two causes:
- `take_turn`'s leave branch recalled whenever no *camp* was near (`threatened()` checks only camps). Next to an
  enemy champion the recall channels in place and every hit cancels it.
- The duo (Heart of Ruin, Ryth) left at `duo_recall_health` 0.75 whenever an enemy was in sight.

## Change
- Leaving with an enemy champion within attack range + 2: a ranged body with a target in range shoots back;
  others retreat and strike if they can.
- `duo_recall_health` 0.7487 → 0.5.

## Results (`data/b61-63-race.txt`, `data/b62b-gates.txt`)
- Race vs v22: **b62b 61% (255/420)**, b62a (no threshold change) 54%, b61 (real champion damage in the fight
  check) 52%, b63 (HoR dash in planning damage) 45%.
- Gain gate vs v22: **58% (163/280), PASS**.
- b62b + b61: 48% vs b62b, dropped.
- Nonreg PASS vs v12 78% (219/280), Jame v3 86% (242/280), hunter-v0 90% (252/280) (`data/v23-gates.txt`).
