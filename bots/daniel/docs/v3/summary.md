# Daniel v3: Simon's v3 + gem-aware gold squad, tuned constants

Code: `bots/daniel/v4-dp` (C++), forked from the team's `bots/v3` after v2 lost to it 3/18. (The folder was first called
`bots/v4`, then renamed when Simon pushed his own v4.) Strategy, roles and draft are unchanged; this iteration is about
measurement plus two small, tested improvements.
Iterations: [v1](../v1/summary.md) → [v2](../v2/summary.md) → v3 (this) → [v4](../v4/summary.md) → [v5](../v5/summary.md).

## Changes from v3

| Change | Why |
|---|---|
| **Gold squad scores targets by `gems + 0.25 * gold`** (`squad_gold_weight`), not gold alone. Groups with no gold are no longer skipped. | v2/v3 notes: the gold squad is our main gem source, yet it chose targets by gold. Gems decide games; gold only buys stats. |
| **Constants tuned** by `tools/tune.py` (self-play evolution against the incumbent): `recall_health` 0.35→0.30, `duo_recall_health` 0.5→0.67, `spawn_leave_health` 0.9→0.96, `tribute_gems` 30→36, `tribute_detour` 8→9, `engage_radius` 5→4, `max_damage_share` 1.5→1.42, `mining_weight` 0.5→0.41, `max_wait_turns` 20→21, `give_up_rounds` 60→74, `danger_radius` 6→9, `danger_rounds` 20→24, `lock_detour` 6→4. | One accepted step in 15 iterations. Treat individual values as noisy; the gate below is what counts. |
| **Experiment hook** in `draft.cpp`: with a fuel quantum ≥ 1M (`tools/arena.py` `seed_fuel`), the draft decodes a seed and picks a random roster (still writing a plan). Real matches run at 100k, so this is inert in competition. | The engine is deterministic: one map and side give one game. Random drafts give hundreds of distinct games for tuning and comparisons. |

## Results

| Opponent | Result | Notes |
|---|---|---|
| v3 code with the hook (no other changes) (random drafts both sides) | **159/288 = 55%** (95% CI 49–61%) | gem scoring alone: 158/288; tuned constants alone: 72/126 |
| `bots/v3`, real drafts | 11/18 (61%) | deterministic: one game per map and side |
| `bots/daniel/main-v2` (the older heuristic bot from `tools/`) | v3 already beats it 15/18 | |

The gain is small but consistent across three independent samples. No faults in any run.

## Weaknesses (unchanged from v3)

Monoliths are still skipped, squads trickle into big groups, and the bot is still untested against the +200 bot.
See `bots/docs/v3/summary.md`.

## Next steps

1. **Side asymmetry**: in mirror games Team B wins 60–77% (`docs/research/drafting.md`). Find out why; turn order
   on contested camps or captures is the first suspect.
2. **Re-learn draft values for this bot**: `python3 tools/draft_lab.py collect --bot v4` / `fit --no-write`.
   Compare with the hand-set `base` and `map_bonus` in `draft.cpp`. Earlier data (old bot) showed rosters explain
   only 2–7% of gem margin, so expect small gains.
3. **Tune more**: longer runs (`--iterations 40 --seeds 3`) and the shop thresholds in `shop_trip` (150 / 300),
   which are not yet top-level constants.

## Tunables

v3's set plus `squad_gold_weight`. Tune with:
`python3 tools/tune.py --bot v4 --params recall_health,tribute_gems,... --iterations 15`.
