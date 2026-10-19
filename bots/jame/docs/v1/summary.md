# Jame v1: independent mechanics baseline

Created 2026-10-17. Source: [bots/jame/v1](../../v1/).

## Intent and provenance

Implement a small, understandable, runnable baseline before choosing a competitive strategy. Written against `sdk/cpp/cambc.h` and the game rules, using the official template's turn-loop contract and the shared CMake build. No teammate implementation, draft ranking, tuned constant set, experimental hook, or world model is used.

Attacking an enemy is not universally the best decision. Separate mechanical correctness (legal targets, channel handling, movement constraints) from the deliberately simple policy choices below.

## Features

1. Deterministically pick the first unused champion in SDK enum order. No map scoring, counter-picking, or randomness.
2. Preserve recall, tribute, and teleport channels; skip dead or disabled champions.
3. Basic-attack the first visible living enemy already in range. Never pursue enemies.
4. Below 25% health, commit to recovery until healed at spawn. Recall outside visible basic-attack coverage; otherwise take a shortest step toward spawn. The safety check does not predict moves, spells, or hidden enemies.
5. Bank any carried gems at a reachable altar. The engine handles attacks on opposing altar locks during tribute attempts.
6. With no bag, basic-attack a camp in range, stay on a cleared region for capture, or take a shortest path toward a camp/capture tile. Walking and attacking are combined only when the SDK reports both legal.
7. Skip visibly respawning groups. Use known static camp locations to explore, without querying hidden lifecycle state.
8. Cache physical camp handles and spawn masks once; use native SDK bitboards and distance fields. Retry bounded hidden-occupant movement failures without pretending a move succeeded.
9. Catch/log errors per turn and always yield. Periodic action/fuel logs and a turn-overrun diagnostic make runtime problems observable.

## Explicit policy defaults

- Enemy attacks take priority over recovery, banking, and farming. No fight-strength calculation.
- Recall threshold: `recovery_fraction = 0.25f` in `src/bot.cpp`, untuned.
- Deposit every positive bag; no batching threshold or trip economics.
- Farm by nearest reachable goal, not gem rate, camp danger, map ownership, or team assignment.
- Attack target ties follow SDK iteration order. No damage prediction or champion-specific kill order.

These are reproducible defaults, not assertions that the behavior is always optimal.

## Deliberately omitted

Abilities, shopping/builds, wards, consumable purchases, enemy chasing, combat search, shared-memory coordination, roles, team-vision reconstruction, map-specific plans, opponent models, draft training, and parameter tuning. Gold is retained. Cassi and Issac have no special linked-risk management. These omissions keep the initial implementation distinct and small.

## Validation

Built with `.venv/bin/cambc build bots/jame/v1`. Runner: CLI 2.1.3, engine 0.0.1 / packed 65536. The available CLI warns that an update exists; no SDK, toolchain, or engine upgrade was performed as part of this baseline.

Played against `bots/starter-cpp` on **all 17 locally available maps, both sides: 34 completed full games** at default fuel. There were **zero Jame bot faults, zero logged action exceptions, and zero detected turn overruns**. The lowest reported running minimum was **27,422 fuel remaining** before periodic diagnostic printing. This is a local diagnostic, not a worst-case guarantee for unseen games.

| Map | Jame as A: score / opponent | Jame as B: score / opponent |
| --- | --- | --- |
| ambush | 1,006 / 663 | 1,000 / 716 |
| collision | 1,012 / 198 | 1,012 / 572 |
| contest | 0 / 0 | 0 / 0 |
| corners | 1,008 / 44 | 1,022 / 146 |
| eight | 1,020 / 672 | 1,028 / 788 |
| elkring | 702 / 1,026 | 1,008 / 612 |
| expanse | 1,016 / 670 | 1,012 / 640 |
| fragment | 1,020 / 780 | 1,028 / 554 |
| interlock | 1,016 / 718 | 1,016 / 296 |
| lanes | 1,020 / 792 | 1,020 / 336 |
| monolith | 1,016 / 688 | 1,004 / 308 |
| packs | 1,014 / 986 | 1,008 / 500 |
| pilgrimage | 136 / 0 | 136 / 0 |
| rows | 1,056 / 858 | 1,012 / 792 |
| rushbait-v2 | 1,012 / 308 | 1,012 / 594 |
| stampede | 0 / 0 | 0 / 0 |
| swirl | 880 / 496 | 1,006 / 72 |

Jame won 32/34 by the engine's outcome, including zero-gem tiebreak games. This is only a smoke-test baseline against starter, not a competitive win-rate estimate. `contest` and `stampede` produce no gems for either side; Jame still attacks camps, captures gold, and moves, but the nearest-goal rule does not prioritize scoring resources. `pilgrimage` only banks 136 by the round limit. These are explicit policy limitations retained for v1, not reasons to tune this version into a larger strategy.

The Swirl games exercised banking and capture: as A, 880–496 at the 2,000-round limit; as B, 1,006–72 at round 1,349. Logged actions also exercised basic enemy/camp attacks, melee movement plus attacks, spawn healing, recall/recovery, dead/disabled handling, and channel preservation. Hidden-occupant retries and altar-lock handling are implemented but were not isolated in a targeted scenario.

Local artifacts (gitignored): `replays/jame/v1/<map>-a|b/` contains each replay and final statistics; `replays/jame/v1/smoke-matrix.json` holds the 34-game results and diagnostic checks. Source and this summary form the version record; future meaningful strategy work should start in v2.

## Known limitations and next steps

- Nearby enemies can monopolize basic attacks even when retreating or banking would be better.
- Farmers can duplicate effort or crowd one capture; no claims are communicated.
- A nearest-goal policy can choose dangerous monsters, including monoliths, or repeatedly switch objectives.
- No equipment or spells means poor scaling and intentionally incomplete use of champion kits.
- Gold-only camps can monopolize the nearest-goal policy on some maps; v1 does not optimize scoring income.
- Recovery is conservative around idle camps but cannot guarantee safe recall against an active opponent.
- Replays and engine/version details must accompany performance claims. Future strategy changes belong in v2.
