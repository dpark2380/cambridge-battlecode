# Daniel v43: v41 + B118 (fight only with a clear edge)

Code: `bots/daniel/v43` = `bots/daniel/v41` with `even = ours >= 1.2 * theirs` in `fight_enemies` for every champion
(Vesper keeps 1.3x; the old "or more health" tiebreak is removed).

## Evidence

- B117: close ranked games are level at round 250 and split on a net 3-4 deaths (336 close games).
- T11: the aggressive sparring bot (fights at 0.8x) lost 41% to v41, so caution looks better than aggression.

## Tests

| Gate | Result |
|---|---|
| Race vs v41 (140) | 72/140 = 51% (1.4x variant 47%) |
| Nonreg vs v41 | PASS 875/1820 = 48% (borderline) |
| Nonreg vs v12 / Jame v3 | PASS 81% / 92% |

Locally neutral, as expected for a fight change (local bots cannot test fights, T11). The test is a scrim A/B against a
fresh v41 panel (label `v41-1101`, 2026-11-01) and a ranked trial against v41 at the same rating.
