# v17 (from v16): hit back when outmatched (B37)

## Evidence
- v14/v16 ranked 00oasis 0-8 and 02crossing 0-7, mostly mirror drafts (v13 won the same mirrors, oasis 5-1).
- Scouted top-40 games on those maps (12 oasis, 21 crossing): top teams trade evenly (oasis median kills 13,
  deaths 13.5; crossing 6/6). We: oasis 3 kills / 27 deaths, crossing 2.5 / 19.5, and 2x their champion damage taken.
- v16 match 41f5a255 (oasis): 74 deaths, 70 with an enemy near, between our spawn and the centre.
- fight_enemies: when outmatched, retreat() to spawn; a ranged body spends its move walking and cannot shoot.

## Change
- `retreat_to_allies` 0 → 1: an outmatched body falls back toward the nearest visible ally within 12 tiles.
- An outmatched ranged body (attack range > 1) with the weakest enemy in range strikes instead of walking.

## Results
- Race vs v16 (140 games each): both 55%, shoot back only 53%, fall back to ally only 49%.
- Gates: gain 162/280 = 58% vs v16; nonreg 182/280 = 65% vs v12, 216/280 = 77% vs Jame v3 (all PASS, data/b37-gates.txt).

## Weaknesses / next
- Local opponents are our own bots and do not hunt like the ranked teams; check ranked oasis/crossing kills/deaths.
