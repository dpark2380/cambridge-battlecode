# Daniel v5: Simon's v4 with tuned constants (submitted)

Code: `bots/daniel/v5` (C++), forked from `bots/v4` (Simon's solo farming with claims). Strategy is unchanged. v5 adds the
random-draft experiment hook and self-play-tuned constants. Submitted to the platform as team bot version 5
(2026-10-16).
Iterations: [v1](../v1/summary.md) → [v2](../v2/summary.md) → [v3](../v3/summary.md) → [v4](../v4/summary.md) → v5 (this).

## Changes from v4

| Change | Detail |
|---|---|
| Experiment hook in `draft.cpp` | With a fuel quantum ≥ 1M (`tools/arena.py` `seed_fuel`), the draft decodes a seed and picks a random roster, still writing a plan. Inert at the real 100k. Enables `tools/tune.py` and `arena.py --seeds` on this bot. |
| Tuned constants (`tools/tune.py`, 20 iterations, 2 accepted) | `max_group_bodies` 3→**2**, `danger_radius` 6→**2**, `stall_turns` 25→14, `max_damage_share` 3.0→4.0, `help_wait_turns` 25→50, `gold_weight` 0.15→0.10, `recall_turns` 10→11, `extra_body_value` 0.5→0.45, `recall_health` 0.35→0.29, `duo_recall_health` 0.5→0.75, `spawn_leave_health` 0.9→0.77, `tribute_gems` 30→25, `tribute_detour` 8→10, `engage_radius` 5→4 |

Reading the changes: fewer bodies per group (more parallel farming), a much smaller no-go zone after a lost skirmish
(v3's analysis found the danger marker made us cede the centre), giving up on stalled targets sooner, banking smaller
loads more often, and taking more camp damage solo before calling a group too costly.

## Results

| Opponent | Result |
|---|---|
| v4 code with the hook (random drafts, `--seeds 8`) | **102/162 = 63%** (95% CI 55–70%) |
| `bots/v4`, real drafts | **11/18** (+1,162 total gem margin; corners 2/2 +868, rows 2/2 +143, interlock +258; packs 0/2 −152) |
| Farming pace vs `starter-cpp` (sum of rounds to 1000, 18 games) | 8,438 vs v4's 8,391: unchanged |

The gain comes from games against a real opponent (contested camps, centre, fights), not raw farming speed.

A second tuning round (15 iterations, smaller steps, 3 accepted) did **not** confirm: 80/162 (49%) against these values
and 8/18 against v4. Its accepted steps were noise, so it was discarded. The constants look close to a local optimum.

## Per-map result vs `bots/v4` (real drafts)

corners 2/2 +868 · interlock 1/2 +258 · rows 2/2 +143 · elkring 2/2 +27 · expanse 1/2 +23 · lanes 1/2 +12 ·
collision 1/2 −6 · monolith 1/2 −11 · **packs 0/2 −152** (consistent: `max_group_bodies` = 2 may hurt there).

## Next steps

1. **Submit v5** and download its ranked games to `replays/v5/`. The real test is the +200 bot.
2. Farming pace is now the limit (v4 notes: still ~15–25% slower than the +200 bot). Tuning didn't move it, so it needs
   structural changes: idle time between captures, tribute routing, wolf kill order.
3. Fights (v4 weakness 1) are untested locally, because local games rarely produce real fights.
