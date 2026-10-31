# Daniel v42: v41 + B113b (value gold more before round 500)

Code: `bots/daniel/v42` = `bots/daniel/v41` plus `early_gold_weight = 0.5` for rounds < 500 in `choose_target`
(gold_weight stays 0.2 after). Two lines.

## Evidence (backlog B113)

130 ranked games of v38/v41 since 2026-10-31 04:35Z, timelines at round 500. In losses we trail on gold 1,211 vs 2,256 and
die 7 times to their 3; in wins we lead 1,773 vs 1,298. Losses are decided early, and gold buys the emblems that win fights.

## Tests

| Test | Result |
|---|---|
| Race vs v41 (140 each) | 0.5: 83/140 = 59%; 0.35: 74/140 = 53% |
| Gain gate vs v41 | **PASS 233/420 = 55%** |
| Nonreg vs v12 / Jame v3 | PASS 81% / 90% |

Ranked trial from 2026-10-31 ~09:25Z as team bot version 53 (follow-newest). User target: rank ≤180 (≈1750) by the
sprint 3 deadline; we were #245, 1676.
