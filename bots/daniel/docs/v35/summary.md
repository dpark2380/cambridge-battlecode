# v35: v34 + join ally fights + opening pack (B92)

## Strategy
v34 plus two fight changes, each neutral on wins in the first scrim A/B round but each cutting deaths:
- **B87b, join an ally's fight** (`fight_enemies`): a body also takes up an enemy that an ally within `ally_radius`
  is fighting (enemy within `engage_radius` of that ally). Before, the ally counted us in its fight, but we ignored
  enemies outside our own `engage_radius`, so it fought alone.
- **B91a, opening pack** (`choose_target`): before round 60 on 4-5 body maps, a group may take every body and
  joining does not split its value (value / need), so the team clears the first groups together.

## Results
| Test | Result |
|---|---|
| race vs v34 (140) | 57% (80/140) |
| gain gate vs v34 | PASS, 234/420 = 56% |
| nonreg vs v12 | PASS |
| nonreg vs Jame v3 | PASS, 262/280 = 94% |
| nonreg vs v33 | PASS, 162/280 = 58% |
| scrim panel (team bot version 36, 14:06Z) | 28-62 (v34 30-60); paired 8 L→W, 10 W→L, net -2; deaths -0.90/game |

Scrim panels, `tools/fights.py` (death within 24 rounds of contact): v34 28%, b87b 25%, b91a 25%; outnumbered 2v1
v34 49%, b87b 40%, b91a 42%. Opponents: 11-13%.

Local and scrim disagree, as with every candidate since v27. The panel's spread is about ±4 net flips, so it only
detects large effects; the user approved a full ranked run.

## Ranked
Submitted 2026-10-29 14:28Z as team bot version 38. Fallback v34 under the auto-revert rule.

## Weaknesses / next
- Healthy 1v1: our Vesper dies 37-42%, opponents' Vesper 8-13%.
- Ryth and Marcella die walking home 50-70% of their deaths (opponents 20-35%).
