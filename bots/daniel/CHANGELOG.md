# Daniel bot changelog

One entry per version, newest first: the features added, bug fixes, tuning and tooling that came with it, how it
tested, and how it did on the ladder. The full write-up (hypotheses, rejected experiments, per-map tables) is in
`docs/v<n>/summary.md`. Open issues and planned changes are in `docs/backlog.md`. Update this file in the same
commit as any change to a bot.

Version folder ≠ team submission number: the platform counts every submission the team makes (see "Submitted").

## v11 (in development, from v10)
- **Tooling:** `draft.cpp` reads `experiment_seed.h` when it exists. `tools/arena.py` writes that header into a
  copy per seed, so random-draft test games run at the real 100k fuel (T1). No gameplay change yet.

## v10 (candidate, awaiting approval)
- **Feature:** also take a fight when behind on health but ahead on fighting power: health × damage, where damage
  is the larger of strength and focus (`fight_enemies`). Variants tried: power only 52% vs v9, power *and* health
  43%, power *or* health 57% (kept).
- **Results:** 57% vs v9 (228/400), 59% vs Jame v3 (v9: 55%), 66% vs v8, 76% vs v7, 89% vs Simon v6, 86% vs
  hunter-v0. Drops packs to 3/10 vs v9 (backlog B7).

## v9 (submitted 2026-10-25 ~10:16Z, team bot version 8)
- **Bug fix:** pathing blocks camps known to be alive even when out of sight. Carriers on 01the_farm oscillated
  beside a wolf camp for 1500 rounds (ranked 1–9) (`move_towards_closest`).
- **Feature:** 40% of Power shards are bought as health (`power_health_share`); 25% and 55% tested worse or equal.
- **Rejected:** two stampede siege tweaks and a Golem siege wait (see v9 summary).
- **Results:** 69% vs v8 (277/400), 55% vs Jame v3 (v8: 39%), 78% vs v7, 93% vs Simon v6, 86% vs hunter-v0.
- **Ranked:** 38–27 (58%) over its first 65 games; rating 1453 → 1486, rank #461 → #423.

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
