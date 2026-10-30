# v36: v34 + B100 (stop running out of fuel on many-group maps)

## Problem
Ranked v34/v35: a champion ran out of fuel in ~30% of games, 100-490 times a game on many-group maps (02tangle
272-491, 01islands 42-270, 01big_world 106-179, 00lanes 55-249, 01boss_battle 118-306, 02harvest 55-193). A body out
of fuel stops mid-turn and resumes next round, a turn late. Ranked games with 80+ such turns: 15-23 (39%), others
263-244 (52%).

Profiled with a copy that sums `fuel_remaining()` deltas per section (`bots/_var/fuelprof`, 02tangle, 33 groups):
`move_towards_closest` cost ~45k of the 100k turn, ~33k of it in one loop, `blocked |= g.tiles & unseen` for every
living group. Each bitboard temporary is an engine call and an allocation, ~1k fuel per group. The distance field
itself was ~6k. Over half of all turns used 60k+.

## Change
`move_towards_closest` keeps the union of living groups' tiles and rebuilds it only when the set of living groups
changes (`living_key`, `living_camps` in `bot.h`). Decisions are identical whenever v34 had the fuel.

## Results (`data/b100-gates.txt`, `data/v36-gates.txt`)
| Test | Result |
|---|---|
| Fuel-exhausted turns, one local game vs v33 | 02tangle 402 → 98, 01islands 32 → 2, 00lanes 65 → 10 |
| Gain gate vs v34 on 02tangle, 01islands, 01big-world, 00lanes, 01boss-battle, 02harvest, 00ambush | **PASS, 91/154 = 59%** (02tangle 16/22, 01islands 14/22) |
| Nonreg vs v34, all maps | PASS, 140/280 = 50% |
| Nonreg vs v12 | PASS, 222/280 = 79% |
| Nonreg vs Jame v3 | PASS, 259/280 = 92% |

## Remaining fuel (02tangle, after the fix)
Turns average ~34k. Peaks: `target_field` recompute (~38k every 10 rounds), `go_tribute`'s two walk fields
(~38k), the camp union rebuild (~16k when a group changes), `place_ward` ~6k every turn, `terrain_blocked()`
rebuilt on every call (static: could be cached).

## Ranked
Submitted 2026-10-30 00:36Z as team bot version 40 (user: "yes submit"), replacing v34 at 86-79 over 165 since its 19:01Z resubmission. Fallback v34 under the auto-revert rule. Scrim panel queued 00:37Z (includes 01islands and 00lanes).
