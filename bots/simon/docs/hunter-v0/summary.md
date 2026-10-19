# hunter-v0: daniel/v5 that hunts gem carriers

Code: `bots/simon/hunter-v0` (C++), forked from `bots/daniel/v5`. It was built as a test opponent that plays like the +200 bot that beat daniel/v5 1–4 (`bots/simon/docs/v6/summary.md`): it fights at worse odds, chases carriers and converges as a team. It turned out stronger than daniel/v5 and about even with simon/v6, so it is now a line of its own. Draft and farming are daniel/v5's, unchanged, including the experiment draft hook.

## Changes from daniel/v5

| Change | Detail |
|---|---|
| **Fight at worse odds** (`fight_enemies`) | Engage when allies' health nearby is at least `hunt_ratio` (0.8) of the enemies'. daniel/v5 needs parity. Every body chases its target, not just the duo. |
| **Chase gem carriers** | Enemies carrying gems count within `hunt_radius` (8) tiles, other enemies within `engage_radius` (4). The richest carrier is the target, then the most hurt enemy. Visible enemies' `gem_count()` is readable. |
| **Prey marker** | Chasing a carrier writes its position into the danger-marker bits of shared memory. Empty-handed bodies within `prey_reach` (12) tiles of a marker under `prey_rounds` (10) rounds old walk to it. `near_danger` always returns false, so no group is avoided. Outmatched bodies fall back without marking. |

The first version chased every enemy within 8 tiles at 0.6 odds and converged from 20 tiles away. It lost 27/34 to daniel/v5 because it stopped farming. Restricting long chases to carriers fixed that.

## Results

| Match | Result |
|---|---|
| hunter-v0 vs `bots/daniel/v5`, 34 real-draft games | 24/34. daniel/v5 dies 631 times (365 in self-play) to the hunter's 405 |
| `bots/daniel/v5` vs hunter-v0, arena | 45% (170) |
| `bots/simon/v6` vs hunter-v0, arena | 48% (306) |

## v1 attempts (none kept)

v1 starts from hunter-v0 and is benchmarked first against it, then against v6 and daniel/v5. Nothing beat v0, so there is no hunter-v1 folder yet.

| Attempt | vs hunter-v0 | Notes |
|---|---|---|
| v0 + v6's farming fixes (camp detours, heal while waiting, team objectives) | 43% (306) | 48% vs v6, 53% vs daniel/v5. Alone each is neutral: 48%, 51%, 48% (170) |
| `tools/tune.py` on `hunt_ratio`, `hunt_radius`, `prey_rounds`, `prey_reach`, `engage_radius`, `recall_health` (15 iterations × 3 candidates × 68 games) | | Nothing accepted: the best reached 55.9% against the 56% bar |
| Best tuner candidate (`hunt_ratio` 0.573, `hunt_radius` 6, `prey_rounds` 11, `prey_reach` 10, `recall_health` 0.241) | 51% (306) | Noise |
| `recall_health` 0.24, `prey_reach` 10 (what most near-misses agreed on) | 50% (306) | Noise |

## Known weaknesses

1. All of daniel/v5's farming weaknesses: slow early pace, big gem groups and monoliths skipped, gold banked rather than spent.
2. It chases only what it sees: no wards, no waiting at the altars enemy carriers use.
3. It has never played the real +200 bot.

## Next steps (candidate v1 changes, each benchmarked against v0)

1. **Gold and shards.** The +200 bot out-earned us 2–4× and bought up to 32 shards on one champion: value gold higher, shop earlier and more often.
2. **The +200 bot's roster:** varg, stellar, cassi_and_issac, tavi (buys shards anywhere), ren. Only the 34 real-draft games of an arena run show draft changes.
3. **Wait at altars.** Idle bodies wait beside the altar enemy carriers use.

## Tunables (top of `bots/simon/hunter-v0/src/bot.cpp`)

daniel/v5's set, plus `hunt_ratio` 0.8, `hunt_radius` 8, `prey_rounds` 10, `prey_reach` 12.
