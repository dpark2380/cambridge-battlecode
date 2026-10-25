# Daniel v9: fixes from 300 ranked v8 games

Code: `bots/daniel/v9` (C++), forked from Daniel v8. **Candidate for submission, awaiting approval** (2026-10-25).

## Verdict: v9 vs v8 and every older model

| Opponent | v8 | v9 | Games |
|---|---|---|---|
| **Daniel v8** (submitted) | — | **277/400 = 69%** (95% CI 65–74%) | 40 maps × 2 sides × 5 drafts |
| Jame v3 (strongest local bot; reproduces ranked losses) | 63/160 = 39% | **88/160 = 55%** | 40 × 2 × 2 |
| Daniel v7 | 94/160 = 59% | **125/160 = 78%** | 40 × 2 × 2 |
| Simon v6 | 129/160 = 81% | **149/160 = 93%** | 40 × 2 × 2 |
| Simon hunter-v0 | 117/160 = 73% | **138/160 = 86%** | 40 × 2 × 2 |

v9 is ahead of v8 against all five opponents. Head to head it wins at least half the games on 38 of 40 maps; the two
below are rows and yellow-brick-road (4/10 each), neither a collapse. 0 crashes in 1,040 games.

**Why it is better.** Two changes, each tied to ranked evidence:
1. *the_farm freeze* (ranked 1–9): carriers never reached the altar behind a camp. Fixed in pathing; the_farm vs v8
   10/10, vs Jame 0/4 → 4/4.
2. *Gold-to-strength conversion* (ranked: losses earn 4.5k gold vs the opponent's 6.9k, and most deaths are to
   camps): v8 put every Power shard into its damage stat, so carriers stayed fragile. v9 buys 40% of Power shards as
   health, like Jame v3 and the ranked opponents in the loss reports we read. This is the big step: 52% → 69% vs v8, 39% → 55% vs Jame.

**Risks.** Starvation stays weak against Jame (0/4 for both). Stampede and the road-of-riches Golem deaths seen in
ranked did not reproduce locally, so they are unaddressed. `power_health_share = 0.4` is a first guess, not tuned.

Per map, games won out of 4 (2 sides × 2 drafts) unless noted:

| Map | vs v8 (/10) | Jame v8→v9 | v7 v8→v9 | Simon v6 v8→v9 | hunter-v0 v8→v9 |
|---|---|---|---|---|---|
| 00ambush | 6/10 | 0/4 → 1/4 | 3/4 → 3/4 | 4/4 → 4/4 | 2/4 → 3/4 |
| 00collision | 8/10 | 1/4 → 2/4 | 1/4 → 3/4 | 2/4 → 4/4 | 4/4 → 4/4 |
| 00contest | 9/10 | 0/4 → 0/4 | 2/4 → 2/4 | 2/4 → 4/4 | 4/4 → 3/4 |
| 00corners | 7/10 | 1/4 → 2/4 | 2/4 → 3/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 00eight | 7/10 | 0/4 → 1/4 | 2/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 00elkring | 7/10 | 1/4 → 2/4 | 3/4 → 3/4 | 4/4 → 4/4 | 3/4 → 4/4 |
| 00expanse | 9/10 | 4/4 → 4/4 | 2/4 → 4/4 | 4/4 → 4/4 | 2/4 → 4/4 |
| 00fragment | 8/10 | 0/4 → 0/4 | 2/4 → 4/4 | 2/4 → 3/4 | 3/4 → 3/4 |
| 00gem-fields | 6/10 | 4/4 → 4/4 | 1/4 → 2/4 | 3/4 → 4/4 | 4/4 → 4/4 |
| 00gemfight | 6/10 | 1/4 → 3/4 | 2/4 → 3/4 | 3/4 → 4/4 | 4/4 → 4/4 |
| 00great-wall | 7/10 | 2/4 → 2/4 | 4/4 → 4/4 | 4/4 → 4/4 | 3/4 → 4/4 |
| 00interlock | 9/10 | 3/4 → 4/4 | 2/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 00lanes | 8/10 | 4/4 → 4/4 | 3/4 → 3/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 00lost-world | 6/10 | 4/4 → 4/4 | 4/4 → 3/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 00monolith | 8/10 | 2/4 → 3/4 | 1/4 → 3/4 | 4/4 → 4/4 | 3/4 → 4/4 |
| 00packs | 9/10 | 1/4 → 3/4 | 4/4 → 4/4 | 3/4 → 4/4 | 1/4 → 4/4 |
| 00pilgrimage | 8/10 | 1/4 → 0/4 | 2/4 → 4/4 | 2/4 → 3/4 | 2/4 → 3/4 |
| 00quadrants | 6/10 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 00reverse-spiral | 6/10 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 00road-of-riches | 7/10 | 0/4 → 0/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 00rows | 4/10 | 4/4 → 3/4 | 1/4 → 2/4 | 1/4 → 3/4 | 0/4 → 3/4 |
| 00rushbait-v2 | 5/10 | 1/4 → 3/4 | 1/4 → 0/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 00split | 5/10 | 1/4 → 2/4 | 2/4 → 4/4 | 4/4 → 4/4 | 3/4 → 3/4 |
| 00stampede | 9/10 | 0/4 → 1/4 | 2/4 → 3/4 | 4/4 → 4/4 | 3/4 → 3/4 |
| 00swirl | 8/10 | 4/4 → 4/4 | 2/4 → 2/4 | 2/4 → 4/4 | 2/4 → 3/4 |
| 01big-world | 6/10 | 2/4 → 2/4 | 1/4 → 1/4 | 2/4 → 2/4 | 3/4 → 2/4 |
| 01boss-battle | 6/10 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 01broken-curve | 5/10 | 0/4 → 0/4 | 2/4 → 2/4 | 3/4 → 4/4 | 3/4 → 4/4 |
| 01concentrated-wealth | 6/10 | 2/4 → 2/4 | 2/4 → 3/4 | 3/4 → 2/4 | 2/4 → 2/4 |
| 01corridors | 5/10 | 0/4 → 0/4 | 3/4 → 4/4 | 4/4 → 4/4 | 2/4 → 3/4 |
| 01elk-arena | 9/10 | 1/4 → 4/4 | 3/4 → 4/4 | 0/4 → 4/4 | 0/4 → 2/4 |
| 01fracture | 8/10 | 0/4 → 1/4 | 3/4 → 3/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 01gold-rush | 8/10 | 0/4 → 4/4 | 2/4 → 4/4 | 3/4 → 4/4 | 1/4 → 4/4 |
| 01hooks | 5/10 | 0/4 → 1/4 | 2/4 → 3/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 01islands | 6/10 | 4/4 → 4/4 | 2/4 → 4/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 01shortcut | 9/10 | 0/4 → 0/4 | 3/4 → 2/4 | 4/4 → 4/4 | 4/4 → 4/4 |
| 01starfish | 7/10 | 0/4 → 1/4 | 2/4 → 4/4 | 3/4 → 4/4 | 2/4 → 4/4 |
| 01starvation | 5/10 | 0/4 → 0/4 | 3/4 → 4/4 | 0/4 → 1/4 | 0/4 → 0/4 |
| 01the-farm | 10/10 | 0/4 → 4/4 | 1/4 → 4/4 | 3/4 → 4/4 | 3/4 → 4/4 |
| 01yellow-brick-road | 4/10 | 3/4 → 1/4 | 1/4 → 0/4 | 4/4 → 3/4 | 2/4 → 1/4 |


## Ranked starting point (v8, newest 300 ranked games, 2026-10-25)

`replays/daniel-v8/report.txt` (`tools/ranked.py --limit 300 --replays losses`). **144–156 (48%)**. Wins and losses
differ in gold again: 7.7k vs 4.5k earned in our wins, 4.5k vs 6.9k in our losses.

| Map | v8 ranked | Note |
|---|---|---|
| 01the_farm | 1–9 | We finish with 0–25 gems and almost no deaths: frozen (fixed, change 1) |
| 00gem_fields | 1–8 | Race lost by ~200 gems before round 800 |
| 00road_of_riches | 2–9 | 23–37 deaths per loss |
| 00fragment | 2–9 | Games go to round 2000 at 400–600 gems |
| 00stampede | 1–7 | We score 0–160: never capture the only gem camp (6 elks, 160 gems) |
| 01starvation | 1–7 | 32–55 deaths |
| 00elkring | 1–6 | Race lost (opponent reaches 1000 by round ~850) |

`bots/jame/v3` reproduces most of these locally (v8 vs Jame v3 on farm, gem-fields, road-of-riches, fragment,
stampede and starvation: 7/36), so it is the local stand-in for ranked opponents.

## Changes from v8

### 1. Block living camps out of sight when pathing (kept)

**Hypothesis.** On the_farm, both altars sit behind wolf camp G16 at (24,19), the only gap in a wall. Local repro
(v8 vs Jame v3): from round ~500 to 2000 all four of our champions carry 100 gems between them and shuffle at
(18–21, 13–18), 6–7 tiles from the altar, never tributing. `move_towards_closest` blocked only *visible* camp
tiles. Next to G16 it sees the wolves and turns towards the long detour; one step back the wolves leave vision,
the short path through the camp reopens and it turns round again.

**Change.** `move_towards_closest` also blocks the spawn tiles of every cached group that is not known to be
respawning or holding its reward (`world` knowledge), restricted to tiles out of vision (visible ones are exact).

**Results.**

| Opponent | Map(s) | v8 | v9 |
|---|---|---|---|
| v8 | all 40 maps × 2 sides × 5 drafts (400) | — | **208/400 = 52%** (95% CI 47–57%); the_farm **10/10** (+801 gems), every other map 4–8/10 |
| Jame v3 | the_farm (6) | 0/6 (−76) | **6/6 (+674)** |
| Jame v3 | farm, gem-fields, road-of-riches, fragment, stampede, starvation (36) | 7/36 | 15/36 |

### 3. Split Power shards between our stat and health (kept)

**Hypothesis.** Ranked wins and losses differ mostly in gold (4.5k vs 6.9k in losses) and most of our deaths are to
camps. Jame v3, which beats v8 61%, builds Power shards as a mix of its stat and health; v8 put all Power shards into
its stat (strength or focus), so late-game champions hit hard but die to camps and carriers drop their gems.

**Change.** `shop()`: once the Monster and Durability emblems are done, buy Power shards one at a time, choosing health
while health is under `power_health_share` (0.4) of Power shards owned. Health builds (Ryth) are unchanged.

**Results.** vs v8 **277/400 = 69%** (with change 1; change 1 alone: 52%). vs Jame v3 88/160 = 55% (v8: 39%).

### Rejected

| Change | Target | Result |
|---|---|---|
| No `help_wait_turns` penalty for mob sieges (nobody claimed the stampede elk siege first) | 00stampede | vs Jame v3 on 5 maps: stampede 0/6 (−825, was −571); reverted |
| `siege_value` 2.0 / 3.0 (with the above) | 00stampede | vs Jame v3: 7/30 and 4/30 (v8: ~6/30), stampede 1/6 and 0/6; reverted |
| Mob sieges wait out of range until every claimant has arrived (or `max_wait_turns`) | 00road_of_riches: 145/185 ranked loss deaths at the Golem corners | vs v8: **204/400 = 51%**, starvation 8/10 but pilgrimage 1/10, great-wall 3/10, eight 3/10. The Golem chain never reproduced locally (v8 vs Jame v3, Simon v6, hunter-v0, v7, starter: 1–8 deaths, none at the corners), and v9 died more on road-of-riches in all four local matchups. Reverted |

Ranked weaknesses that do not reproduce locally (stampede, road-of-riches Golem deaths) need games against real
ladder opponents (`cambc match-groups create`, shared website quota) to test.
