# v3: v2 + altar locks, safer fights, passive-collecting build

Code: `bots/v3` (C++), forked from frozen `bots/v2`. The draft and squad roles are unchanged. Changes target the losses in `bots/docs/v2/summary.md` (0/5 vs a +200 elo bot).

## Changes from v2

| Problem in v2 | v3 change |
|---|---|
| Skipped locked altars; the team stalled for 300 rounds once both were locked | `go_tribute` breaks enemy locks: basic-attack the lock from attack range (3 hits). It prefers a free altar unless that is more than `lock_detour` (6) path tiles further |
| Never used locks | Buy one altar lock (10g) on every shop. `place_lock` drops it on an altar within 2 tiles when an enemy stands next to it, which cancels their tribute |
| Duo fed kills at contested gem spots | Fights are weighed by **total visible health** within 5 tiles, ours vs theirs: fight at parity or better, or finish an enemy below 30%. Otherwise mark danger, fall back, and take any legal shot |
| Walked back into the same fights | **Danger marker** in shared memory (bytes 2–4: x+1, y, round mod 256), set where we were the weaker side. Both squads skip targets within 6 tiles of it for 20 rounds |
| Duo too fragile in fights | Duo recalls at 50% HP while an enemy is in sight (35% otherwise) |
| Stacked one emblem family (passives don't stack) | Build: Monster emblem of our stat, then Durability emblem of health, then Power shards, as the +200 bot does |
| `engine error 44: Champion cannot act` while stunned | Return early when unable to move, attack or cast |

## Results

| Opponent | Result | Notes |
|---|---|---|
| `starter-cpp` | 18/18 | 1 death across all 18 games (v2: ~20) |
| `bots/v2` | 12–6 | As B 8–1, as A 4–5. Each pairing is one deterministic game |
| v3 mirror, elkring | finishes in 706 rounds | Team B placed 4 locks; team A broke them and still won: no stall |

## Errors encountered → fixes

| Symptom | Cause | Fix |
|---|---|---|
| First v3 draft lost 10 of 18 to v2, mostly with zero kills (tempo) | "Fight only when strictly ahead by head count" made every 1v1 a retreat; the danger marker (set on any 2 enemies, radius 8) blocked normal farming; the 50% duo recall applied against camps too | Health-weighted fight check; danger only when weaker, radius 6 for 20 rounds; 50% recall only with enemies in sight |
| Elkring v3-vs-v2 ran to round 2000 (v3 stuck at 720 gems) | 4-vs-5 standoff next to the altar: v3 retreated every turn though it had ~4,500 HP vs ~3,100 | Same health-weighted check |
| v2 baseline failed to build after the `main`→`v2` rename | Stale CMake cache in `bots/v2/.cambc` pointed at the old path | Deleted the build folder. After renaming a bot folder, delete its `.cambc/` |

## Known weaknesses

1. **Untested against the +200 bot**, which is the real target.
2. **Side asymmetry vs v2** (4–5 as A, 8–1 as B). Corners A lost 454–1000: v2's duo took the free centre gems (528) while ours avoided it, and our 4-body squad spent ~100 rounds gathering for one elk group.
3. The gold squad trickles in and waits (`max_wait_turns`) for big groups.
4. Monoliths are still skipped; the untested mechanics from v2 still apply.

## Next steps

1. Run v3 against the +200 bot; put replays in `replays/v3/` and run `node tools/replay/analyze.mjs --out replays/v3/analysis replays/v3`.
2. Contest the centre on maps with central free gems (corners, interlock, lanes) when the health check allows, rather than ceding it.
3. Squad cohesion: gather at a rally point before engaging big groups, instead of trickling in.

## Tunables (top of `bots/v3/src/bot.cpp`)

v2's set, plus `danger_radius`, `danger_rounds`, `duo_recall_health`, `lock_detour`, `lock_place_range`; the build order is in `build_order()`.
