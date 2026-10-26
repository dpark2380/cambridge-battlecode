# Daniel bot changelog

One entry per version, newest first: the features added, bug fixes, tuning and tooling that came with it, how it
tested, and how it did on the ladder. The full write-up (hypotheses, rejected experiments, per-map tables) is in
`docs/v<n>/summary.md`. Open issues and planned changes are in `docs/backlog.md`. Update this file in the same
commit as any change to a bot.

Version folder ≠ team submission number: the platform counts every submission the team makes (see "Submitted").

## v14 (from v13; submitted 2026-10-26 23:06Z as team bot version 13)
- Started 2026-10-26 15:20Z.
- **Bug fix (B29b):** in ranked 02the_pack (v13, match 611f181c) all three carriers waited inside
  `corridor_gather` from r221 to r2000 and never struck: `breach()` counted allies within 3 tiles of the body
  itself, and the team stood up to 4 apart. It now counts allies standing anywhere in `corridor_gather`.
- **Gates** (`data/b29b-gates.txt`): map 02the-pack 32/60 = 53% vs v13 (FAIL: local carriers usually bunch);
  nonreg 50% vs v13, 51% vs v12, 66% vs Jame v3 (280 games each, PASS). Zero-gem games on 02the-pack: v13 13/44,
  v14 9/44. Remaining 0:0 games: B29c.

## v13 (from v12; submitted 2026-10-26 10:58Z as team bot version 12; ranked 189-176, peak #273 1615)
- Started 2026-10-26 06:50Z.
- **Bug fix (B29):** 02the_pack's only altar sits inside a 48-wolf ring; carriers found no path and stood at the
  ring all game (v12 ranked 0:0, lost on gold; every local game 0:0). At init, when every walk from our spawn to an
  altar crosses a camp, a 0-1 BFS (one kill per camp tile, on local grids: bitboard reads are engine calls) picks
  the corridor to cut (on the_pack, one wolf by a diagonal). A carrier whose altar walk fails waits within 3 tiles
  of it and hits once 2 allies are within 3 (damage wakes the whole ring). Only the_pack sets the flag (all 70
  maps probed).
- Gates: map 02the_pack 51/60 = 85% vs v12 (pass); nonreg all maps 51% vs v12, 57% vs v11, 66% vs Jame v3 (all pass).

## v12 (from v11; submitted 2026-10-26 05:45Z as team bot version 11; ranked 87-68, peak #331 1563)
- Started 2026-10-25 23:15Z for the sprint 3 maps.
- **Feature (B25, accepted):** draft the top-20 core in order, Vesper > Heart of Ruin > Marcella > Vendetta > Ryth,
  map scoring for the rest. Heart of Ruin added to the draft roster (it was never draftable). Marcella and Heart of
  Ruin buy focus shards. Real drafts, 70 maps x 2 sides: 77% vs v11, 79% vs v10, 81% vs v9, 79% vs Jame v3 (v11:
  66%). Without the focus builds: 67% vs v11.
- **Tooling:** `tools/targetmodel.py` (B26), a choice model of which group a champion takes next, fitted to top-team
  and our ranked decisions; `tools/openings.py --export` writes the opening-script table (B24).

## v11 (submitted 2026-10-25 23:14Z, team bot version 10)
- **Tooling:** `draft.cpp` reads `experiment_seed.h` when it exists. `tools/arena.py` writes that header into a
  copy per seed, so random-draft test games run at the real 100k fuel (T1). The same inert hook was ported back
  into v9 and v10 (2026-10-25 18:35Z; nothing changes without the header) so that gates against them also run at
  100k. Without it, a pairing with v10 fell back to the 1M fuel quantum, and the first B19 map gate (52%, failed)
  never saw the freeze it was testing.
- **Bug fix (B19, accepted):** `choose_target` reuses its walking-distance field from our position until we move
  3+ tiles or 10 rounds pass (it cost ~40k fuel a turn on the 100×100 01big_world). big_world vs Jame v3 at 100k:
  fuel-exhausted turns 2,499 → 170 (side A) and 5,972 → 135 (side B); both games go from losses (464:868,
  0:866) to wins (965:843, 1,021:765). The claim/target mismatch was a side effect of turns cut short by fuel.
  Gates at 100k: map mode vs v10 on big-world/ambush/lanes 67% (big-world 17/20); nonreg vs v10 51%, vs v9 60%.
- **Feature (B21, accepted 2026-10-25 20:40Z):** after the Monster and Durability emblems, buy Bruiser shards
  instead of Power (same 40% health split). A Bruiser emblem is 5 of the stat plus 1 of each other, 7 shards'
  worth against Power's 6; the top 20 buy mostly Bruiser (Vesper ~66 Bruiser shards a game vs 11.5 Power).
  Gates at 100k: gain vs v11 135/240 = 56%, gain vs v10 95/160 = 59%; nonreg vs v9 100/160 = 62%, vs Jame v3
  98/160 = 61%. The no-split variant raced 40/80 vs 42/80.
- **Rejected:** a dominant-Monolith value multiplier (B20; x1.5/x2/x3 on rows, corridors, contest, gold-rush:
  22%/11%/9% vs v11; early sieges it cannot finish).
- **Rejected:** lower `max_damage_share` (B17+B18): 1.5 and 2.0 win elkring 57-62% but lose islands ~35% vs v11.
- **Rejected:** build order Treasure > Durability > Power (B11, 51% over 800 games vs v11); late gold-weight decay
  (B15, 50% over 480; a sharp drop after round 500 scores 44%).

## v10 (submitted 2026-10-25 12:54Z, team bot version 9; ranked 143–137, rating 1495 → peak 1542 → 1513)
- **Feature:** also take a fight when behind on health but ahead on fighting power: health × damage, where damage
  is the larger of strength and focus (`fight_enemies`). Variants tried: power only 52% vs v9, power *and* health
  43%, power *or* health 57% (kept).
- **Results:** 57% vs v9 (228/400), 59% vs Jame v3 (v9: 55%), 66% vs v8, 76% vs v7, 89% vs Simon v6, 86% vs
  hunter-v0. Drops packs to 3/10 vs v9 (backlog B7).

## v9 (submitted 2026-10-25 10:16Z, team bot version 8; replaced at 12:54Z)
- **Bug fix:** pathing blocks camps known to be alive even when out of sight. Carriers on 01the_farm oscillated
  beside a wolf camp for 1500 rounds (ranked 1–9) (`move_towards_closest`).
- **Feature:** 40% of Power shards are bought as health (`power_health_share`); 25% and 55% tested worse or equal.
- **Rejected:** two stampede siege tweaks and a Golem siege wait (see v9 summary).
- **Results:** 69% vs v8 (277/400), 55% vs Jame v3 (v8: 39%), 78% vs v7, 93% vs Simon v6, 86% vs hunter-v0.
- **Ranked:** 47–33 (59%) over 80 games; rating 1453 → 1486, rank #461 → #421.

## v8 (week 2 patch port)
- **Port:** camp table for the week 2 patch: the Golem (5,000 health, range 4), camp attack ranges per kind,
  gem and gold clusters planned at an effective 500 health.
- **Features:** Monolith leave rule and siege gate; gold-only play on maps where no altar can be reached
  (01boss_battle).
- **Bug fix:** build tables sized for 13 champion types (Heart of Ruin), so a random missed pick can't index out
  of bounds.
- **Results:** 61% vs v7, 84% vs hunter, 73% vs Simon v6, 43% vs Jame v3.
- **Ranked:** 159–171 (48%) over 330 games.

## v7
- **Bug fixes:** the stall check uses walking distance (218 false give-ups on pilgrimage). Champions respond to
  unseen attackers in bushes.
- **Features:** siege any group too big for two bodies; carriers recall at 50% health while enemies are near.
- **Results:** 59% vs v6; 72% vs Simon v5.
- **Ranked:** 56–44 on the week 2 engine.

## v6
- **Features:** Monolith sieges (damage carries over between trips); gold weight 0.10 → 0.20.
- **Results:** 62% vs hunter (v5: 52%); 61% vs Simon v5.
- **Ranked:** 28–26.

## v5 (team bot version 5)
- Simon's v4 with self-play-tuned constants and the random-draft experiment hook.
- **Results:** 63% vs Simon v4.
- **Ranked:** 18–47.

## Earlier
- v4 (`v5-dp`), v3 (`v4-dp`), v2 (`main-v2`), v1 (`main-v1`): see `docs/README.md`.
