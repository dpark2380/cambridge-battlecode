# v6: v4 + capture contesting

Code: `bots/simon/v6` (C++), forked from `bots/simon/v4`. It was built as "v5" and renamed because `bots/daniel/v5` (v4 with self-play-tuned constants) already took that number. The strategy is v4's (`bots/simon/docs/v4/summary.md`), plus one change. It also carries the experiment draft hook from `bots/daniel/v5`, so `tools/arena.py --seeds` works on it.

v6 tested the five recommendations in `bots/simon/docs/research/league_macro.md` one at a time, each against its predecessor, keeping or scrapping each. Only capture contesting survived.

## Changes from v4

| Change | Detail |
|---|---|
| **Contest enemy captures** (`contest_capture`) | An enemy waiting out a capture stands still for 5 rounds on a group it just cleared, usually hurt from the camps. When a body sees one within `contest_range` (10) of itself and is not outnumbered on health around it (ours vs theirs within `engage_radius`), it walks onto the group's tiles and hits the enemy. Stepping on resets their timer, and the reward is ours once they leave or die. It runs after `fight_enemies` and never while banking. It claims the group, so allies don't also walk over |
| `world::group_index_at` | Group index of a spawn tile, for the check above |
| Experiment hook in `draft.cpp` | Copied from `bots/daniel/v5`: with a fuel quantum ≥ 1M the draft picks a random roster. Inert at the real 100k |

## Benchmark method

Engine games are deterministic, so one map and side is one game. 18 games against v4 alone proved too noisy. A strategy-neutral change (flipping `>` to `>=` in target tie-breaks) moved the result from 9/18 to 7/18, and the margin by 510 gems.

Each candidate therefore played 72 games: all 9 maps, both sides, against v4, v4 with that tie-break flip, v3 and v2. It was compared with v4's own score on the same set. Note that every local opponent is our own lineage: same draft, and rarely chases. Ideas aimed at the +200 bot's chasing and hunting can't show their value here. `tools/arena.py --seeds` (random drafts, many distinct games) arrived after these tests.

| Candidate | Wins / 72 | Gem margin | Deaths (ours / theirs) | Kept |
|---|---|---|---|---|
| v4 baseline | 52 | +12,813 | 277 / 319 | |
| 1. Decide fight or flee at sight; fight back when pinned (4 variants) | — | — | always more deaths | no |
| 2. Wards as tripwires; enemy packs set the danger marker | 46 | +10,827 | 239 / 300 | no |
| 3a. Bag cap 70 gems unless an enemy was seen in the last 30 rounds (then 30) | 48 | +11,907 | 288 / 300 | no |
| 3b. Bag cap 15 under threat, 30 otherwise | 47 | +11,819 | 260 / 317 | no |
| **4. Contest enemy captures** | **55** | **+13,977** | 264 / 316 | **yes** |
| 5. Draft Ren on brawl/contested maps (opponent's collision/interlock comps) | 44 | +9,955 | 272 / 283 | no |

Details of the rejected ones, for anyone revisiting them:

- **1 (fight or flee).** Odds as HP × damage within 8 tiles, falling back at sight: 4/18 vs v4, −2,356. Even zero-death games were lost, because fleeing at sight costs farm time. Fighting back only when a melee enemy is within 2 tiles: 8/18, −206. Fighting back only if we can't walk home before the chaser kills us: 10/18 vs v4, +624, but 96 deaths to 79, and 15/18 vs v3 (v4: 16/18). Adding "chased for two turns": 7/18, −44, 96 deaths to 63. Local opponents mostly don't chase (only v4's duo does), so walking away works against them and fighting back just adds deaths. This could still be right against the +200 bot. The code is not in the repo; rebuild it from this description.
- **2 (wards).** Wards see 6 tiles from up to 2 tiles away, and normal sight is 8. So a ward only adds vision where we've left it, or behind walls and bushes. Placing it toward the enemy spawn on arrival and avoiding packs it sees cost farming (monolith as B: 0 deaths, lost).
- **5 (draft).** A bonus big enough to pick Ren on collision and interlock also put Ren into packs, elkring, corners, lanes, monolith and rows (dropping Varg on packs and C&I on elkring). The map signals don't separate collision and interlock from packs.

## Results

`tools/arena.py --seeds 8` (9 maps × 2 sides × (1 real + 8 random drafts) = 162 games):

| Match | Win rate (95% CI) | Notes |
|---|---|---|
| v6 vs `bots/daniel/v5` | **67/162 = 41%** (34–49%) | Corners 2/18 (−599 avg), elkring 15/18 (+148). Daniel's tuned constants beat our contesting |
| `bots/daniel/v5` + capture contesting vs `bots/daniel/v5` | **78/162 = 48%** (41–56%) | Contesting adds nothing measurable on top of the tuned constants |

**Verdict.** Capture contesting is neutral. Its +3 wins in the 72-game test above was within noise (that set's own noise is about ±2 wins per 18 games). The strongest bot we have is `bots/daniel/v5`; submit that rather than v6. v6 is kept as the record of these experiments and as a baseline opponent.

## Known weaknesses

1. All of v4's: fights unchanged, still slower than the +200 bot at farming, monoliths skipped.
2. Capture contesting is untested against the +200 bot, which captures alone and is the case it targets.
3. v6 doesn't have `bots/daniel/v5`'s tuned constants, and loses to it 41%.

## Next steps

1. Submit `bots/daniel/v5` and download its ranked games. They are the only way to test recommendations 1 and 2 (fighting back, wards) against an opponent that really chases and hunts.
2. Benchmark future changes with `tools/arena.py --seeds 8` against `bots/daniel/v5`, not with 18 fixed games: those can't separate a real gain from noise.
3. Start v7 from `bots/daniel/v5`. Farming pace and fights are the open problems; capture contesting can be dropped.

## Tunables (top of `bots/simon/v6/src/bot.cpp`)

v4's set, plus `contest_range` (10).
