# Daniel v10: take fights we win on fighting power

Code: `bots/daniel/v10` (C++), forked from Daniel v9 (submitted 2026-10-25 ~10:16Z as team bot version 8).
**Submitted 2026-10-25 12:54Z as team bot version 9** (approved by Daniel).

## Verdict

| Opponent | v9 | v10 |
|---|---|---|
| **Daniel v9** (submitted) | — | **228/400 = 57% (95% CI 52%-62%)** over 40 maps × 2 sides × 5 drafts |
| Jame v3 | 88/160 = 55% (95% CI 47%-63%) | **94/160 = 59% (95% CI 51%-66%)** |
| Daniel v8 | 103/160 = 64% (95% CI 57%-71%) | **106/160 = 66% (95% CI 59%-73%)** |
| Daniel v7 | 125/160 = 78% (95% CI 71%-84%) | **121/160 = 76% (95% CI 68%-82%)** |
| Simon v6 | 149/160 = 93% (95% CI 88%-96%) | **142/160 = 89% (95% CI 83%-93%)** |
| hunter-v0 | 138/160 = 86% (95% CI 80%-91%) | **138/160 = 86% (95% CI 80%-91%)** |

(All but the v9 row: 40 maps × 2 sides × 2 drafts = 160 games.) 0 crashes in 1,200 games.

v10 is ahead of v9 head to head (57%, 95% CI 52–62%) and against Jame v3 (+4 points) and v8 (+2). It is level with
v9 against hunter-v0 and slightly behind against Simon v6 (−4) and v7 (−2), both within noise (CIs overlap). Per map vs
v9, the clearest gains are hooks, shortcut, starfish and starvation (8/10). The one clear loss is packs (3/10);
gem-fields, quadrants, reverse-spiral, rows, corridors and gold-rush are 4/10.

**Why it is better.** v9's first 35 ranked games (22–13) lose to fights it misjudges. On 00eight it lost 0–943 with
131 deaths. On 00contest it lost 0–0 with 84 deaths, 66 of them next to an enemy. `fight_enemies` compared total
health only, so damage was ignored: a healthy team with weak hits looked as strong as one that kills twice as fast.
v10 also fights when it is behind on health but ahead on fighting power, defined as health × damage (damage = the
larger of strength and focus, both visible on enemies).

| Fight rule | vs v9 | vs Jame v3 |
|---|---|---|
| v9: health ≥ enemy health | — | 55% |
| fighting power only | 207/400 = 52% | 98/160 = 61% |
| both (more cautious) | 103/240 = 43% | 88/160 = 55% |
| **either (v10)** | **228/400 = 57%** | **94/160 = 59%** |

The cautious variant lost to v9. The gain comes from taking fights that v9 refused, not from avoiding bad ones.

**Risks.** This is a smaller step than v9's (+7 points vs +19). Jame-like losses on stampede, road-of-riches,
corridors, broken-curve and shortcut are unchanged (0/4 for both). The ranked eight/contest losses were to much
stronger opponents (11–23 Power shards against our 0–2), and no local bot reproduces that gap. So the ranked effect
on those maps is a hypothesis.

## Per map

Games won: vs v9 out of 10; the rest out of 4, shown as v9 → v10.

| Map | v10 vs v9 | Jame v3 | v8 | v7 | Simon v6 | hunter-v0 |
|---|---|---|---|---|---|---|
| 00ambush | 6/10 | 1/4 → 3/4 | 2/4 → 3/4 | 3/4 → 4/4 | 4/4 → 4/4 | 3/4 → 4/4 |
| 00collision | 5/10 | 2/4 → 3/4 | 2/4 → 4/4 | 3/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 00contest | 7/10 | 0/4 → 0/4 | 4/4 → 4/4 | 2/4 → 4/4 | 4/4 → 4/4 | 3/4 → 3/4 |
| 00corners | 7/10 | 2/4 → 2/4 | 2/4 → 4/4 | 3/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 00eight | 6/10 | 1/4 → 0/4 | 4/4 → 2/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 00elkring | 6/10 | 2/4 → 4/4 | 4/4 → 4/4 | 3/4 → 2/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 00expanse | 6/10 | 4/4 → 4/4 | 4/4 → 3/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 00fragment | 7/10 | 0/4 → 2/4 | 3/4 → 4/4 | 4/4 → 4/4 | 3/4 → 4/4 | 3/4 → 3/4 |
| 00gem-fields | 4/10 | 4/4 → 4/4 | 2/4 → 1/4 | 2/4 → 2/4 | 4/4 → 4/4 | 4/4 → 3/4 |
| 00gemfight | 6/10 | 3/4 → 3/4 | 2/4 → 3/4 | 3/4 → 2/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 00great-wall | 5/10 | 2/4 → 4/4 | 2/4 → 2/4 | 4/4 → 3/4 | 4/4 → 3/4 | 4/4 → 3/4 |
| 00interlock | 6/10 | 4/4 → 4/4 | 3/4 → 3/4 | 4/4 → 3/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 00lanes | 5/10 | 4/4 → 4/4 | 3/4 → 1/4 | 3/4 → 3/4 | 4/4 → 4/4 | 4/4 → 3/4 |
| 00lost-world | 5/10 | 4/4 → 4/4 | 3/4 → 1/4 | 3/4 → 4/4 | 4/4 → 3/4 | 4/4 → 3/4 |
| 00monolith | 7/10 | 3/4 → 3/4 | 2/4 → 3/4 | 3/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 00packs | 3/10 | 3/4 → 3/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 00pilgrimage | 5/10 | 0/4 → 1/4 | 3/4 → 1/4 | 4/4 → 3/4 | 3/4 → 2/4 | 3/4 → 3/4 |
| 00quadrants | 4/10 | 4/4 → 3/4 | 2/4 → 2/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 00reverse-spiral | 4/10 | 4/4 → 3/4 | 2/4 → 2/4 | 4/4 → 3/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 00road-of-riches | 6/10 | 0/4 → 0/4 | 2/4 → 2/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 00rows | 4/10 | 3/4 → 3/4 | 1/4 → 2/4 | 2/4 → 2/4 | 3/4 → 3/4 | 3/4 → 3/4 |
| 00rushbait-v2 | 6/10 | 3/4 → 3/4 | 2/4 → 2/4 | 0/4 → 0/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 00split | 5/10 | 2/4 → 2/4 | 2/4 → 2/4 | 4/4 → 4/4 | 4/4 → 3/4 | 3/4 → 4/4 |
| 00stampede | 6/10 | 1/4 → 0/4 | 3/4 → 2/4 | 3/4 → 2/4 | 4/4 → 4/4 | 3/4 → 3/4 |
| 00swirl | 5/10 | 4/4 → 4/4 | 3/4 → 3/4 | 2/4 → 2/4 | 4/4 → 4/4 | 3/4 → 4/4 |
| 01big-world | 5/10 | 2/4 → 2/4 | 2/4 → 2/4 | 1/4 → 1/4 | 2/4 → 1/4 | 2/4 → 2/4 |
| 01boss-battle | 5/10 | 4/4 → 4/4 | 3/4 → 3/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 01broken-curve | 6/10 | 0/4 → 0/4 | 2/4 → 2/4 | 2/4 → 3/4 | 4/4 → 3/4 | 4/4 → 3/4 |
| 01concentrated-wealth | 6/10 | 2/4 → 4/4 | 2/4 → 3/4 | 3/4 → 2/4 | 2/4 → 2/4 | 2/4 → 2/4 |
| 01corridors | 4/10 | 0/4 → 0/4 | 2/4 → 2/4 | 4/4 → 4/4 | 4/4 → 4/4 | 3/4 → 3/4 |
| 01elk-arena | 7/10 | 4/4 → 3/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 2/4 → 3/4 |
| 01fracture | 6/10 | 1/4 → 2/4 | 4/4 → 3/4 | 3/4 → 2/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 01gold-rush | 4/10 | 4/4 → 3/4 | 3/4 → 4/4 | 4/4 → 3/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 01hooks | 8/10 | 1/4 → 0/4 | 2/4 → 3/4 | 3/4 → 3/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 01islands | 6/10 | 4/4 → 4/4 | 1/4 → 2/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 01shortcut | 8/10 | 0/4 → 0/4 | 4/4 → 4/4 | 2/4 → 3/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 01starfish | 8/10 | 1/4 → 0/4 | 2/4 → 2/4 | 4/4 → 2/4 | 4/4 → 3/4 | 4/4 → 4/4 |
| 01starvation | 8/10 | 0/4 → 0/4 | 1/4 → 3/4 | 4/4 → 3/4 | 1/4 → 0/4 | 0/4 → 0/4 |
| 01the-farm | 6/10 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 01yellow-brick-road | 5/10 | 1/4 → 2/4 | 1/4 → 1/4 | 0/4 → 0/4 | 3/4 → 3/4 | 1/4 → 2/4 |

## Ranked starting point (v9, first 35 ranked games)

22–13 (63%; v8 was 48% over 330). Rating 1453 → 1479, rank #461 → #430 an hour after submission. Losses:
eight 0–943, contest 0–0, corridors 0–2, pilgrimage, starvation, broken-curve, elkring, rushbait.
`replays/daniel-v9/`.
