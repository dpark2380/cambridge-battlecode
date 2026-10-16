# v4: work in progress

Code: `bots/v4` (C++), forked from frozen `bots/v3`. Starts identical to v3; see `bots/docs/v3/summary.md` for the current strategy, tunables and known weaknesses.

## Why: v3 vs the +200 bot (0–5)

Replays in `replays/v3/` (local only), analysis in `replays/v3/analysis/`. We were team A in all five.

| Map | Score | Our deaths / theirs | Kind of loss |
|---|---|---|---|
| packs | 554–1000 (r375) | 2 / 0 | farming race |
| expanse | 540–1022 (r378) | 0 / 0 | farming race |
| monolith | 534–1004 (r432) | 5 / 0 | farming race |
| collision | 36–1016 (r490) | 12 / 1 | lost every fight |
| interlock | 188–1036 (r407) | 12 / 0 | lost every fight |

### 1. They farm solo, we farm in pairs (about half their capture rate)

Capture events taken from the per-round gem and gold deltas in the timelines:

- **packs**: they made ~23 captures, each by a single champion. Their Varg alone took a 2-wolf group (44 gems) every ~45 rounds. We made ~13, nearly all by two champions standing on the same group, which splits the reward. The map is symmetric, so the gap comes from parallelism.
- **expanse**: their Cassi and Issac farm separately, at different groups. Ours stay together and capture 24+24 from one gem group. Our duo also went ~100 rounds (r71–r169) without a capture.
- **The gold squad desyncs.** On expanse, Varg recalls to tribute or shop while Stellar walks on alone to the next target, solo-hits it, drops to 250 HP and recalls. When Varg arrives, Stellar is gone. Stellar captured once all game, despite dealing 9,143 damage to camps. Squad partners show `waited=12..15` in the status lines.
- **Free gems ignored.** On packs, the centre gem+gold clusters (G2/G3: 48 gems, 0 damage) were farmed by them all game; we took one once.

### 2. Retreating gets us killed

Of our 24 deaths on collision and interlock, 20 had an enemy nearby. The ones checked in the timelines follow one pattern:

- We are weaker in the 5-tile health check, so we `retreat()` toward spawn. The chaser keeps hitting us the whole way, and ranged champions can't shoot while walking. Cassi and Issac die together 4 times per game.
- Allies a few tiles away don't count and don't help. Collision r243–251: our Cassi+Issac (~1,230 HP) ran from Issac+Ren (~2,120) and died at (9,5). Our Ryth (1,380) and Stellar (975) stood ~12 tiles away at (21,3) and (20,2). Together we were ~3,600 vs ~2,120.
- Ryth on collision r268–276: chased by Stellar from 718 HP to dead while walking home, never hitting back.

### 3. Builds (secondary)

Their casters use Power focus plus a Bruiser emblem. Over time their HP climbs to 1,375–1,400 on Issac and Ren. They also stack Power strength harder: Varg reached 7 power shards on packs (1,620 gold earned vs our 810), a result of farming faster.

## Plan

1. **Solo farming with claims** (done, below).
2. **Fight as a team**: on hold. Falling back toward allies gives up too much space; revisit separately.
3. Builds: later.

## Changes from v3

| Area | v3 | v4 |
|---|---|---|
| Targets | Gem duo and gold squad each chase one shared target | Every body picks its own target and claims it in shared memory; allies skip claimed groups |
| Sharing a group | Whole squad on every group | Started with the fewest bodies that survive it; others may join (up to `max_group_bodies` = 3) when their share beats their own options. A join the group doesn't need is valued at `extra_body_value` (0.5), since it only splits the claimants' reward |
| Target rate | `gems / (travel + kill + capture)` for one role's resource | `(gems + 0.15 * gold) / bodies` per turn. Turns are counted as `max(travel, respawn) + kill + capture`, plus the walk to an altar, plus channelling the gems. Damage taken is charged pro rata as a trip home (`2 * home distance + 10`) |
| Own damage | Fixed 70 per body | Measured each turn: strength + each camp-targeting spell's damage over its cooldown (Cassi ~47, Tavi ~35, Vendetta 80–200 as it buys shards). Allies are assumed to do 50 |
| Solo limit | `max_damage_share` 1.5 | 3.0: camps neither chase nor heal, and the rate already charges for the trips home |
| Shared memory | Bytes 0–1 squad targets, bytes 2–4 danger marker | One 64-bit word: 6 claims × 6 bits (group + 1) in bits 0–35, then danger x+1 / y / round in bits 36–57. Read and written with one engine call each |
| Banking | Re-decided every turn, Chebyshev distance to the altar | Once a body starts banking it commits until its gems are in. The "altar is close" check uses walking distance |
| Stalls | None | Watchdog: after 25 straight work/fight turns without getting closer to the target or hitting it, skip the target for 60 rounds. It resets after any break (tribute, recall) |

The draft roles (`gem_duo` / `gold_squad`) now steer only fighting (the duo chases and recalls earlier when enemies are near) and the shop-trip threshold.

## Results

Farming pace: rounds to 1000 against `starter-cpp`, every map, both sides (18 games):

| Bot | Sum of rounds | |
|---|---|---|
| v3 | 10,811 | |
| v4, first cut (claims only) | 8,507 | −21% |
| v4, final | 8,391 | −22%; interlock went from 732 to 448 once the stall bugs were fixed |

Head to head vs `bots/v3`: **16–2** (lost packs and rows as B). The first cut went 11–7.

We still farm slower than the +200 bot. Against v3 it reached 1000 at r375 (packs), r378 (expanse) and r432 (monolith). v4 against v3 does r446/r540, r486/r452 and r490/r567 (as A/B). Their 4-body packs team made ~23 captures by r375; ours makes ~26 by r456.

Fuel: at least 45k of 100k left on every turn on expanse, lanes and corners (r1–400).

## Errors encountered → fixes

| Symptom | Cause | Fix |
|---|---|---|
| `analyze.mjs` failed on macOS: "no cambc assets" | It only searched `%LOCALAPPDATA%` | Also searches `~/Library/Caches/cambc` and `$XDG_CACHE_HOME/cambc` |
| First v4 cut lost rows to v3 on both sides | Five bodies, three groups per side, and no joining: casters waited on 3-wolf groups, and a lone melee body tanked all three wolves | Joining claimed groups (up to 3 bodies) |
| Casters waited for help on 2-wolf groups, or sat in a bush for 25 rounds on a cluster group | Damage assumed to be 70 per body; Cassi does ~47 | Measure own damage each turn; raise the solo limit to 3.0 |
| Interlock vs starter: Issac and Stellar held 22 gems for 400 rounds | `should_tribute` used Chebyshev distance to an altar behind a wall: tribute and work alternated every turn | Commit to banking; walking distance for the altar check |
| Interlock: Cassi walked toward its target, met an idle enemy, fell back, and repeated that for 200 rounds | Fight retreat and target approach alternated | Stall watchdog |
| Watchdog skipped targets on rows during the walk back from spawn | The best distance from before a recall carried over | Reset the watchdog after any break in work/fight turns |

## Known weaknesses

1. **Fights are unchanged from v3**, and solo bodies are more exposed. Collision and interlock (12 deaths each vs the +200 bot) will still be lost on fights.
2. Still ~15–25% slower than the +200 bot at farming (see Results).
3. Bodies walk deep into the enemy half for groups (rows: enemy-side 3-wolf groups at y=44).
4. Cassi never spends gold (packs vs starter: 280 earned, 0 spent; the +200 bot's Cassi has no items either). Cause not checked.
5. Monoliths are still skipped.

## Next steps

1. Submit and get replays against the +200 bot; compare captures per body per 100 rounds.
2. Find the rest of the farming gap: idle time between captures, tribute trips, the order wolves are killed in.
3. Fights (plan item 2), in a form that doesn't give up space.
4. Carried over from v3: contest the centre on maps with central free gems.

## Tunables (top of `bots/v4/src/bot.cpp`)

v3's set, plus `claim_bits`, `body_damage` (allies, 50), `max_damage_share` (3.0), `stall_turns` (25), `gold_weight` (0.15), `recall_turns` (10), `max_group_bodies` (3), `extra_body_value` (0.5), `help_wait_turns` (25). `mining_weight` is gone.
