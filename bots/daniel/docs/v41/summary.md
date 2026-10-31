# Daniel v41: v38 + B100 (fuel cache), retried

Code: `bots/daniel/v41` = `bots/daniel/v38` plus B100 (`move_towards_closest` caches the union of living camp groups'
tiles, rebuilt only when the set of living groups changes). Same decisions whenever fuel sufficed.

## Evidence

- v38 ranked since 2026-10-31 04:35Z: 5 of 41 losses carry the fuel signature (fuel-exhausted turns), next to 11 races
  and 7 spirals.
- B100 first shipped as v36 (v34 + B100): fuel-exhausted turns 02tangle 402 → 98, 01islands 32 → 2, 00lanes 65 → 10; gain
  gate vs v34 on 7 fuel-heavy maps PASS 59%. Its ranked revert (11-19 over 30) was a 30-game window; on 31 Oct v38 and
  v40 both went 22-28 over 50 at the same rating, so such windows are noise near our equilibrium.

## Tests vs v38

| Gate | Result |
|---|---|
| Gain on 00lanes, 01big-world, 01boss-battle, 01islands, 02harvest, 02tangle, 02guardians | 137/252 = 54%, inconclusive (LLR +1.17) |
| Nonreg, all maps | PASS 138/280 = 49% |
| Nonreg vs v12 / Jame v3 | PASS 79% / 92% |

Ranked trial from 2026-10-31 ~07:15Z as team bot version 52 (follow-newest mode). Sprint 3 rule: the bot live at the
deadline is the best proven one; v38 (83-62 over 145, 1651 → 1745) remains the benchmark.
