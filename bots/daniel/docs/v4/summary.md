# Daniel v4: solo farming

Code: `bots/daniel/v5-dp` (C++), forked from Daniel v3 (`bots/daniel/v4-dp`). Draft and gem duo unchanged; the gold squad stops moving as one pack.
Iterations: [v1](../v1/summary.md) → [v2](../v2/summary.md) → [v3](../v3/summary.md) → v4 (this) → [v5](../v5/summary.md).

## Why

The 20 ranked v3 games in `replays/v3/` (analysis in `bots/docs/v3/summary.md`) were 6–14. Most losses were economy, not
fights. Opponents farm wolf packs **solo, one champion per lane** (rows: three champions each banking 66 gems every
~60 rounds), while v3's gold squad always shared one target. Capture rewards are split among the allies present, so
a pack only kills faster; it doesn't earn more. `plan.split_farm` was computed in the draft but never used.

## Changes from Daniel v3

| Change | Detail |
|---|---|
| **Own claim per gold-squad member** | Member k (by `champion_type` order among gold-squad roles) writes its target to `gold_member_slots[k]` = shared-memory byte 1, 5, 6 or 7. Released while dead or recalling. |
| **Solo targeting** | Each member scores groups by reward per turn with `bodies = 1 + squad-mates already claiming it`. The reward is divided by bodies, and kill time uses our damage plus `body_damage` per helper. If no group is takeable, it falls back to v3's whole-squad estimate, so elk/large groups still get done. |
| **Real-stat survivability** | Solo checks (`solo_survivable`) use our own camp damage (strength, attack resets, damage spells / 8, ×1.5 for Varg's splash, × camp multiplier) and max health, allowing `solo_damage_share` (2.0) × health: camps do not chase, so an expensive group costs a recall, not a death. Used both when choosing and when engaging (`work_group`). |
| `solo_farm` switch | `0` restores v3/v4 squad behaviour for A/B tests. |

The first attempt kept v3's generic `survivable()` (70 damage, 900 health). Solo champions then judged every wolf pack
unsafe and mined gold clusters instead (0 gems for the whole gold squad on rows, −726 margin). Using real stats in
both places fixed it.

## Results

| Opponent | Result |
|---|---|
| Daniel v3 (`v4-dp`), real drafts | **13/18 (72%)**: rows 2/2 +270, corners 2/2 +657, collision 2/2 +622, elkring 2/2 +180; no map below −23 average |
| `bots/v3`, real drafts | **14/18 (78%)** |
| Daniel v3, random drafts (`--seeds 6`) | 68/126 (54%). Smaller gain: random rosters often lack a solo-capable gold squad |

No faults. `tools/tune.py` (12 iterations over `solo_damage_share`, `squad_gold_weight`, `mining_weight`, `tribute_gems`,
`recall_health`, `body_damage`) found nothing better than the defaults.

## Weaknesses / next steps

1. **Still cedes the centre** on corners/interlock/packs (v3 finding 3). Next: contest central gem clusters next to an
   altar when the health check allows. Testing it needs a centre-camping opponent bot.
2. Solo champions don't help each other when an enemy turns up; the danger marker is the only coordination.
3. Damage estimate is rough (spell damage averaged over cooldown, flat ×1.5 splash).
4. Untested on the ladder: submit v5 and download its replays into `replays/v5/`.

## Tunables

Daniel v3's set plus `solo_farm`, `solo_damage_share` (top of `bots/daniel/v5/src/bot.cpp`).

## Compared with Simon's `bots/v4` (2026-10-16)

Simon's v4 implements the same idea more thoroughly: claims for every body, joining up to 3, banking commitment and a
stall watchdog. Real-draft arena, every map and both sides:

| Matchup | Result |
|---|---|
| v4 vs v3 | 16/18 |
| v5-dp vs v4 | 9/18, total margin −1,169 gems: wins rows 2/2, packs 2/2, elkring 2/2; loses collision 0/2 (−657), lanes 0/2 (−514), monolith 0/2 |

Farming pace (sum of rounds to reach 1000 vs `starter-cpp`, 18 games): v3 10,811; **v4 8,391**; v5-dp 8,580. v5-dp is faster
on rows (530 vs 595), elkring (509 vs 542), packs (459 vs 477) and expanse (440 vs 451), and slower on collision
(663 vs 515) and lanes (445 vs 381).

**Verdict:** build on Simon's v4. Ideas worth testing there: a lower solo limit or no joining on rows/elkring, the tuned
recall/tribute constants from v4-dp, and the experiment draft hook so `tools/tune.py` gets random-draft samples.
