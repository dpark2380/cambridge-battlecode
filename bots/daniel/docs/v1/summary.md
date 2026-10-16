# Daniel v1: first heuristic bot

Code: `bots/daniel/main-v1` (C++). Written from the starter, independent of the team's `v<N>` line.
Iterations: v1 (this) → [v2](../v2/summary.md) → [v3](../v3/summary.md) → [v4](../v4/summary.md) → [v5](../v5/summary.md).

## Strategy

Every champion, every turn: shop at spawn → recall when hurt (after first stepping out of camp reach) → heal or
shield → hit an enemy champion if favourable → tribute when carrying enough gems or near an altar → farm.

- **Camp choice** (`choose_group`): the best reward per turn across all camp groups. Rate = `(gems + W_GOLD × gold) /
  helpers / (travel + respawn wait + kill time + recall cost + capture)`, where helpers = 1 + allies that claimed the
  group. Damage beyond what we can absorb costs recall round trips rather than ruling a group out.
- **Claims**: one shared-memory byte per champion slot holds its target group, so allies spread out or pile onto
  dangerous groups together.
- **Capture**: stand on a spawn tile only while the reward is waiting, never while the group respawns (an occupied
  tile delays the respawn).
- **Movement**: a static distance field per camp group plus one to the nearest altar; step to the best free
  neighbour, dash when far, and fall back to the SDK's `move_towards` when allies block the route.
- **Combat**: spells, then basic attack, then attack reset for a second hit.
- **Shop**: Jungle emblem, then Monster, then Power shards; every Nth shard is health.
- **Draft**: fixed priority list (Varg, Vendetta, Ryth, Vesper, Ren, …).

## Results

| Opponent | Result |
|---|---|
| `starter-cpp` | 16/18 (89%); lanes and rows were the weak maps |

## Errors encountered → fixes

| Symptom | Cause | Fix |
|---|---|---|
| ~1,200 "crashes" per game, champions frozen | **Fuel.** Each turn cost 80–130k of the 100k budget: `vision::camps()` alone costs ~35k, and per-group `spawn_tiles() & visible_tiles()` checks another ~27k | Cache static group data once; `camp_tiles()` + `camp_at()` only near us; test a few known tiles for visibility |
| `engine error 32: Destination is unreachable` | Dash targets taken from `valid_tiles()`, which doesn't check the path | Dash only to tiles in `reachable_tiles(origin, 2)` |
| Champion stood on a respawning camp forever | Standing on a spawn tile freezes the respawn timer | Capture only while the reward is available; step off respawning groups |
| Whole team idle on rows (0 gems) | Hard survivability filter rejected every 3-wolf pack | Turn excess damage into a time penalty (recall trips) instead |
| Champions died mid-recall | Damage cancels recall | Walk out of camp/enemy reach first, then recall |
| Ranged champions stuck behind allies in corridors | Static field's best step was blocked | Direct "approach the camp" step to the nearest free neighbour |

## Weaknesses

1. Big maps (lanes 90×30, expanse 80×80): too little fuel left to build distance fields, so champions stall.
2. Fixed recall threshold: champions with gems still die to camps.
3. Hand-written draft.

## Tunables

`src/params.h`: `RECALL_HP`, `RECALL_HP_GEMS`, `TRIBUTE_GEMS`, `TRIBUTE_NEAR`, `W_GOLD`, `CAMP_SAFETY`, `RECALL_TRIP`,
`TRAVEL_W`, `FIGHT_RATIO`, `STAT_HEALTH_EVERY`.
