# v6: daniel/v5 + farming and fight fixes from the +200 losses

Code: `bots/simon/v6` (C++), forked from `bots/daniel/v5` (Simon's v4 with self-play-tuned constants and the experiment draft hook). Strategy and shared-memory layout are v4's (`bots/simon/docs/v4/summary.md`); v6 adds four changes. Each came from `bots/daniel/v5`'s 1–4 loss to a +200 elo bot. Each was tested on its own against its predecessor, then kept or scrapped.

## Why daniel/v5 lost (5 ranked games against the +200 bot)

`node tools/replay/analyze.mjs` on `replays/v5-daniel/` (gitignored). The opponent drafted varg, stellar, cassi_and_issac, tavi and ren every game.

| Map | Result | What decided it |
|---|---|---|
| rushbait-v2 | won 1000–110 | |
| packs | lost 400–1044 | Pace. Their varg and vendetta cycled the wolves beside their spawn every ~45 rounds from r24; our first gems came at r67. Our varg went to a centre camp, lost it to their duo at r61, stood 40 rounds at 68% health waiting for it to respawn, then died. It spent 10 gold all game. |
| elkring | lost 90–1026 | Carried gems. Their first capture was r19, ours r59. We lost 288 gems in 8 deaths, they died 0 times. Carriers walked the map edges inside the range of awake elk (camps hit the nearest champion in range 3). One stellar walked the same route to the same altar three times with 36 gems and died on the third. |
| corners | lost 46–1030 | Fights. 20 deaths to 2, at the four centre gem camps; our bodies arrived one at a time. |
| stampede | lost 0–360 | One group holds all 360 gems (six elk). `max_group_bodies = 2` meant it never looked survivable, so we never tried it. Their varg bought shards and took it alone at r1701. They killed us 87 times (6 deaths) and earned 18.9k gold to our 7.5k. |

In every loss they earned 1.8–4.4× our gold and spent it on shards (up to 32 on one champion).

## Changes from daniel/v5

| Change | Detail |
|---|---|
| **Detour around awake camps** (`camp_hazard`, in `move_towards_closest`) | While carrying gems or below `hazard_health` (50%), tiles within `camp_range` (3) of a visible monster that is hurt and isn't our goal count as walls. Camps wake only when hit and never heal, so a hurt camp is or soon will be fighting. If no path is left, walk through anyway. |
| **Heal while a target respawns** (`work_group`) | A body waiting beside a respawning group that is hurt (below `spawn_leave_health`) and safe recalls home. It only does so if the respawn is further away than the recall, the walk back and `heal_turns` (5). |
| **Team objectives** (`group_info::big`, `max_bodies_for` in `choose_target`) | A group worth at least `big_group_share` (40%) of the map's gems per cycle may take every body (`max_bodies`), not `max_group_bodies` (2), and monoliths among them are no longer skipped. That covers stampede's six elk, contest's two monoliths and rows' centre monolith group. The threshold leaves out pilgrimage (31%) and the monolith map (31%). |
| **Rally to an outnumbered ally** (`danger_marker`, in `take_turn`) | When a body is outmatched it already writes the danger marker. Now healthy (≥ `rally_health`, 60%), empty-handed bodies within `rally_reach` (10) tiles of a marker under `rally_rounds` (5) rounds old walk to it. This replaces leaving the ally to die. |

## Benchmark method

- **Win rate:** `python3 tools/arena.py <A> <B> --seeds 4|8` over all 17 maps × 2 sides × (1 real + 4 or 8 random drafts) = 170 or 306 games. The 95% interval is about ±7% at 170 games and ±5.5% at 306.
- **Deaths:** the 34 real-draft games (every map, both sides) replayed with `cambc run -o`, then `analyze.mjs` per side, summing our deaths, deaths to camps and gems carried at death. These numbers are deterministic, so the same bot always gives the same totals.
- **Opponents:** daniel/v5 for steps 1–4. Step 5 used `bots/simon/hunter-v0` (`bots/simon/docs/hunter-v0/summary.md`). daniel/v5 neither hunts carriers nor groups up, so self-play can't reward fight or carrier changes.

## Results

Steps 1–4 against `bots/daniel/v5`. daniel/v5 against itself gives 17/34 wins, 365 deaths, 89 to camps, 2042 gems lost.

| Step | Arena | Wins / 34 | Deaths | To camps | Gems lost | Kept |
|---|---|---|---|---|---|---|
| 1a. Detour around awake camps always | 44% (170) | 14 | 352 | 79 | 2013 | no: detours cost more than hits |
| **1b. Only while carrying gems or below 50%** | 50% (170), 49% (306) | 17 | 361 | 87 | **1364** | **yes** |
| 2. Bank any gems within 30 rounds of seeing an enemy + avoid an altar we turned back from (120 rounds) | 42% (170) | 14 | 346 | 76 | 1667 | no |
| 2a. Altar avoidance only | | 13 | 353 | 85 | 1783 | no: the other altar is often much further |
| 2b. Bank under threat only | | 15 | 341 | 78 | 1522 | no: small bags mean more trips |
| 2c. Outmatched carrier within 3 tiles of an altar tributes instead of retreating | 47% (170) | 18 | 348 | 75 | 1479 | no |
| 3a. Contested groups (enemy within 2 tiles of our distance) at 60% value | 41% (170) | 15 | 296 | 69 | 1988 | no: hands the centre to the opponent |
| **3b. Heal while a target respawns** | 55% (170), **52% (306)** | **20** | 340 | 84 | **1097** | **yes** |
| 4a. Team objectives at 30% share | 52% (170) | 19 | 296 | 71 | 1143 | no: pilgrimage 6/10 → 4/10 |
| **4b. Team objectives at 40% share** | **51% (306)** | 20 | 284 | 67 | **1033** | **yes**: stampede margin +20 → +130, contest 0 → +111 |

Step 5 against `bots/simon/hunter-v0` (the "Hunter deaths" column counts the opponent's deaths). daniel/v5 scores 45% (170) against it.

| Step | Arena vs hunter | Wins / 34 | Deaths | Gems lost | Hunter deaths | Kept |
|---|---|---|---|---|---|---|
| 4b (start) | 42% (306) | 12 | 546 | 4464 | 352 | |
| 5a. Bigger danger zone (radius 6, 30 rounds) | 37% (170) | 6 | 608 | 5086 | 322 | no: avoiding cedes ground |
| 5b. Carriers and hurt bodies path around enemies (4 tiles) | 42% (170) | 16 | 553 | 3911 | 362 | no |
| **5c. Rally to an outnumbered ally** | **48% (306)** | 14 | 570 | **3243** | **463** | **yes** |
| 5c + 5b | 47% (306) | 16 | 527 | 3893 | 525 | no |

**Final v6:** 52% (306) against `bots/daniel/v5`, 48% (306) against `bots/simon/hunter-v0`. Each kept step is small and within noise on win rate alone. Steps were kept when they didn't regress and their targeted metric improved.

## Known weaknesses

1. Gold and shards. The +200 bot out-earned us 2–4× in every loss and v6 doesn't address it.
2. Pace on safe maps (packs, elkring) is unchanged: bodies still pick contested centre camps and arrive one at a time.
3. Team objectives are slow: stampede's elk group usually falls after r1500, once shards make it survivable. Contest wins went 11/18 → 10/18 despite the gem margin, possibly because the enemy finishes a monolith we wore down.
4. The hunter is still slightly ahead of v6 (52%).

## Next steps

1. Submit v6 or hunter-v0 and download the ranked games. Neither has been tested against the real +200 bot.
2. Gold and shopping: value gold more, shop earlier and more often.
3. Further work is going into the hunter line (`bots/simon/docs/hunter-v0/summary.md`), which edges out v6.

## Tunables (top of `bots/simon/v6/src/bot.cpp`)

daniel/v5's set, plus:
- `camp_range` 3, `hazard_health` 0.5
- `heal_turns` 5
- `big_group_share` 0.4
- `rally_reach` 10, `rally_rounds` 5, `rally_health` 0.6
