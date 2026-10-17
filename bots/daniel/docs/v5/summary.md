# Daniel v5: Simon's v4 with tuned constants (submitted)

Code: `bots/daniel/v5` (C++), forked from `bots/v4` (Simon's solo farming with claims). Strategy is unchanged. v5 adds the
random-draft experiment hook and self-play-tuned constants. Submitted to the platform as team bot version 5
(2026-10-16).
Iterations: [v1](../v1/summary.md) → [v2](../v2/summary.md) → [v3](../v3/summary.md) → [v4](../v4/summary.md) → v5 (this) → [v6](../v6/summary.md).

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

## Ranked results: 65 games (downloaded 2026-10-17, `replays/daniel-v5/`)

**18 wins, 47 losses (28%)**, similar to v3's 6–14 on the ladder. The pool has grown to 17 maps; 8 of them are new and
were never tested locally. As B we went 12–24, as A 6–23. Opponents now mostly draft Varg + Stellar + Cassi & Issac
(61, 55 and 51 of 65 games), plus Tavi, Vendetta or Ren.

| Map | Record | Avg margin | Our / their deaths per game | Note |
|---|---|---|---|---|
| expanse | 4–2 | +141 | 0.0 / 0.3 | farming race we win |
| rushbait-v2 (new) | 2–0 | +615 | 1.0 / 2.5 | |
| collision | 2–1 | +300 | 10.7 / 6.7 | |
| pilgrimage (new) | 2–3 | +100 | 8.8 / 13.6 | |
| rows | 2–5 | −132 | 0.4 / 0.6 | farming race, behind at r200 in 4/7 |
| interlock | 1–5 | −245 | 11.0 / 5.3 | |
| fragment (new) | 2–3 | −266 | 20.0 / 13.2 | brawl |
| elkring | 0–5 | −288 | 4.0 / 2.4 | behind at r200 in 5/5 |
| packs | 0–5 | −390 | 7.4 / 3.2 | (also our one consistent local loss vs v4) |
| swirl (new) | 0–4 | −514 | 27.0 / 9.0 | brawl, 262 carried gems lost per game |
| lanes | 0–4 | −94 | 0.0 / 0.0 | pure farming race, lost |
| monolith | 1–3 | −175 | 5.2 / 4.2 | |
| ambush (new) | 1–2 | −188 | 7.7 / 5.3 | |
| eight (new) | 0–2 | −902 | 22.0 / 7.5 | brawl |
| corners | 1–1 | −113 | 6.0 / 5.0 | |
| stampede (new) | 0–1 | −360 | 23.0 / 23.0 | |
| **contest (new)** | 0–1 | **0–600** | 99 / 4 | **all gems are in 2 Monoliths, which we skip: we can't score at all** (locally v5 vs starter ends 0–0) |

What it says:
1. **Monoliths are now mandatory.** On contest they are the only gem source, and the opponent took one (Varg 400, Issac 200).
   Monoliths also hold most of the gems on monolith and rows.
2. **Losses are now fights more than farming.** Losses average 12.1 deaths (9.2 with an enemy near) and 92 carried gems
   lost; wins average 3.6. The small brawl maps (swirl, eight, fragment, stampede) have 20–27 deaths per game.
3. **Pure farming races are still lost** on lanes, elkring and rows (no deaths, behind on pace). Farming speed is still
   the other gap, as v4's notes said.
4. Opponents build Power stacks plus Durability, Jungle and Bruiser emblems (one of each passive) and spend far more gold
   than us late.

### Tooling notes

- Platform replays now span engine versions 0.0.2 and 0.0.3. `cambc` 2.2.5 (`uv tool upgrade cambc`) brings both, and
  `tools/replay/analyze.mjs` now tries every cached engine until one decodes the replay. Its layouts were calibrated on
  0.0.1; per-champion gem sums still match team totals in all 65 games.
- New platform zips include `team-*.fuel` (per-turn fuel use).
