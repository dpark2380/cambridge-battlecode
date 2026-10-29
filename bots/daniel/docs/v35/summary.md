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

- 16:02Z: 24-26 over 50 (gold 6.1k in wins, 4.5k in losses); ladder #214, 1700 (14:28Z: about 1690).
- 17:01Z: 38-40 over 78 (last 30: 16-14); our gold 6.6k, opponents' 6.5k → 7.0k; ladder #223, 1691. Ranked
  win rate by opponents' picks is flat at 50-52% for every champion, as rating-matched pairing predicts.

- 18:01Z: **51-54 over 105** (48.6%; last 30: 16-14); our gold 5.7k, opponents' 6.6k; ladder #215, 1697.

**Verdict at ~100 games: neutral.** v34 went 62-53 (54%) over 115, inside the ±9-point interval of either sample, and
the ladder rating is flat (1690 → 1697). No revert trigger (48% at 100+ games; gold above 4,700), so v35 stays live.
Losses are fight snowballs: 20 champion deaths a game vs the opponents' 9, gems level at r250 (59 vs 67) but 138 vs 194
at r500, camp clears 44 vs 67, gold 4.4k vs 8.3k, and the winners buy 50% more shards (Bruiser + Power).

Gauntlet (`data/gauntlet-v35.txt`): v35 +384 [+340, +392] (v8 = 0), predicted ladder 1605; the local pool is far
below it, so the gauntlet no longer separates candidates.

## Weaknesses / next
- Healthy 1v1: our Vesper dies 37-42%, opponents' Vesper 8-13%.
- Ryth and Marcella die walking home 50-70% of their deaths (opponents 20-35%).
