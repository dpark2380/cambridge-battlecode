# Worst maps, 2026-10-29: why v25-v31 lose on rows, vault, boss_battle, the_farm, yellow_brick_road, corners, road_of_riches, fracture and gold_rush

Data: ranked v25, v26, v26b, v27, v28, v31, deduplicated by match id (v28 and v26b share games). Top teams:
`data/scout` (rank 1-20). Local reproductions: five `cambc run` games, with replays and stdout in the session scratchpad.
Variant sources are in the scratchpad too (`b84`, `b85`, `b86`). Nothing under `bots/daniel/` was changed.
00gem_fields and 00elkring are left out (B83).

## TL;DR

| Rank | Fix | Maps | Mechanism | Evidence | Expected |
|---|---|---|---|---|---|
| 1 | **B84: gold-only groups with no fighters go back to 500 planning health per cluster** (keep B56's 120 for gem clusters) | 00corners, 00rows, 01gold_rush, 01boss_battle, 01fracture, plus 00collision, 02the_pack, 00lanes, 02tangle, 00expanse, 00swirl, 00monolith, 01big_world | B56 (v22) made 0-gem gold groups the best rate on the map; bodies farm them for the first 300-600 rounds and bank half the gems, and not even more gold | Pre-B56 → post-B56 on the 6 named maps: **69-47 (59%) → 16-41 (28%)**; first-300-round clears that are gold-only: ours 50-100% vs top 14-26% | +1.5-2.5 pts overall (13 maps, 16% of games, now 45%) |
| 2 | **B85: give up a capture that stays contested** (and later: go fight the contester) | 01yellow_brick_road (+ 00the_line) | An enemy on a far tile of a 30-tile gold row contests the capture for good. The watchdog counts "on a ready tile" as progress, so bodies sit there for hundreds of rounds | Reproduced: v27 vs v12, 272:1012, all 5 bodies on G0/G1 tiles from r20 to r300+, `ready=1` | +0.5-1 pt |
| 3 | **B86: at 01boss_battle's Monolith altar, bank only a siege-sized bag with siege health** | 01boss_battle | `tribute_detour` sends carriers holding 9-19 gems to the breach beside the 2-Monolith altar. They wait there for allies, then strike and die | 21-31% of our body-rounds are spent within 4 of (24,20) with a median of 19 gems, and 10-21% dead. Gold 6.1k vs top 17.3k | +0.3-0.5 pt |

Shared root cause: **target pricing in `world.cpp`, in both directions.** B83 makes clusters in mixed groups too
expensive (500 against a real 120); B56 makes gold-only groups too cheap compared with everything else. Both push bodies
off the monster+cluster groups that top teams open with. B83 is already being tested and fixes the mixed-group side
(gem_fields, elkring, and partly the_farm). B84 fixes the gold-only side. They stack, so race them together as well
as apart.

Not fixable by targeting: **00vault** (the brawl at the 343-gem vault, like B30 gemfight) and **00road_of_riches**
(no local reproduction; v27 beat v12 1012:530 there). The notes for both are below.

## 1. What happens in our losses (per map)

Medians, our games (v25-v31) vs top-20 rows on the same map.

| Map | Us | r250 gems us/top | r500 us/top | gold us/top | clears us/top | first clear us/top | deaths us/top | Gold-only share of clears ≤ r300, us/top |
|---|---|---|---|---|---|---|---|---|
| 00rows | 1-5 | 18 / 62 | 96 / 219 | 10.8k / 9.0k | 62 / 46 | 41 / 29 | 2 / 1 | **0.68 / 0.18** |
| 00vault | 1-4 | 24 / 343 | 409 / 406 | 2.9k / 1.3k | 19 / 11 | 3 / 4 | 8 / 5 | 0.57 / 0.50 |
| 01boss_battle | 1-5 | 0 / 0 | 0 / 0 | **7.2k / 17.3k** | 43 / 56 | 34 / 28 | **22 / 8** | **0.70 / 0.19** |
| 01the_farm | 1-4 | 85 / 70 | 215 / 260 | 5.3k / 6.7k | 37 / 34 | 30 / 38 | 9 / 2 | 0.00 / 0.00 (fighterless gem pairs 0.50 / 0.00) |
| 01yellow_brick_road | 1-4 | 16 / 72 | 100 / 221 | **4.7k / 10.6k** | 23 / 46 | **110 / 34** | 6 / 5 | 0.00 / 0.14 |
| 00corners | 2-7 | 23 / 78 | 111 / 241 | 10.5k / 8.5k | 94 / 60 | 20 / 17 | 6 / 6 | **0.87 / 0.26** |
| 00road_of_riches | 2-5 | 163 / 83 | 294 / 335 | 2.7k / 2.9k | 63 / 60 | 9 / 18 | 5 / 5 | 0.39 / 0.35 |
| 01fracture | 2-6 | 37 / 38 | 182 / 179 | 6.5k / 7.5k | 52 / 52 | 41 / 37 | **1 / 4** | **0.50 / 0.19** |
| 01gold_rush | 2-6 | **0 / 22** | 24 / 66 | 8.2k / 6.0k | 80 / 68 | 26 / 17 | **18 / 6** | **1.00 / 0.69** |

Rows, corners, fracture and the_farm are **races**: we die no more than top teams and lose on gems. Boss_battle and
gold_rush add deaths. Yellow_brick_road is a **freeze**.

## 2. Root cause A: B56 made gold-only groups the best target (fix B84)

### The change
`world.cpp:80`, since v22 (B56, a 02treasure_box fix):

```cpp
if (fighters.empty())
    info.health = 120.0f * static_cast<float>(group.camps().size());
```

Every group with nothing that hits back is now priced at its real cluster health. Gem-cluster groups were the target
(treasure_box's 16 lone gem clusters). But the change also covers every **0-gem gold-only** group. Such a group pays
no damage-trip term and no altar trip (`gems > 0 ? altar_distance : 0`), and its value is not split by a second body,
so its per-turn rate beats every monster group near it.

Worked example, ranked 00rows 6b0915f7-288f-4634-a5fc-a948c04e26c4 (v27, lost 603:1017). At round 1 Vesper (dmg 45)
compares two targets:
- G0 (3 wolves + 3 gold, 12 gems / 180 gold), joining Marcella: kill 5,550/95 = 58 turns, plus 0.85 of a heal trip
  (31 turns). That is about 121 turns for (12 + 36)/2 = 24 value, a rate of **0.20**.
- G7 (4 gold, 80 gold, at (48,16)): 45 travel + 480/45 + 5 = 61 turns for 16 value, a rate of **0.26**.

With B84, G7 costs 2,000/45 = 44 turns and its rate falls to 16/94 = **0.17**, below G0's.

In the replay, Vesper sits on G7 at (47,15) from r41 to r121, and HoR on G8 at (0,31) from r61 to r141 and again at
r261-321. HoR ends with 0 gems and 9,000 monster damage over 1,268 rounds. Meanwhile Marcella and Vendetta duo the
wolf groups and walk home hurt. HoR is the low-damage body in 5 of our 6 rows games.

### Openings (`tools/openings.py`, decoded clear events)
- **00rows**: top teams open G0 → G2 → G4 at r29 / r60 / r85, all wolf groups with clusters. We open G0 at r41, then
  G7 and G8 (gold-only) at r46 / r69. G2 comes at r224 in the one game where it shows up in our first six clears.
- **00corners**: in all 9 games our first six clears are gold-only: G2 → G3 → G20 → G21 → G8/G9 between r20 and r79.
  Several of these sit on the enemy half: G3, G21, G9. Top teams mix G7 (wolf+gold), G19 (elk+gem), G17 and the
  central G2/G3.
- **01gold_rush**: all 8 of our first-300-round clear sets are 100% gold-only, and we bank 0 gems by r250 in every
  loss. Top teams take the 11-gem wolf groups G9-G14 early: 31% of their clears.
- **01boss_battle**: we open G25 (2 gold) → G12 (3 gold) → G21 at r34-40, and 70% of our clears by r300 are
  gold-only. Top teams take the elk+gold groups G8/G17/G23/G29, and earn 2,370 gold by r300 to our 830.
- **01fracture**: our share of fighterless clears is 0.2-0.7 in every window up to r1000. Opponents' is 0.0-0.1. At
  r600-1000 they collect 151-393 gems from clears, we 186-237.

**Gold-only farming does not even buy gold.** Gold from clears by r300, ours vs top: rows 1,010 vs 1,500, corners
1,260 vs 1,395, boss 830 vs 2,370, fracture 890 vs 1,185, gold_rush 690 vs 870, collision 520 vs 1,280.

### Before and after B56 (v22 = v18 + B56 only)

Our ranked record on the six named maps:

| Map | v12-v19 (pre) | v22-v31 (post) | gems r250, pre → post (ours vs theirs) |
|---|---|---|---|
| 00corners | 15-3 | 3-8 | 74 vs 57 → 23 vs 78 |
| 00rows | 9-13 | 2-6 | 31 vs 58 → 18 vs 65 |
| 01gold_rush | 9-4 | 3-8 | 44 vs 33 → 0 vs 24 |
| 01boss_battle | 9-11 | 2-5 | gold 11.7k vs 10.9k → 6.1k vs 14.5k |
| 01fracture | 12-10 | 3-8 | — |
| 00collision | 15-6 | 3-6 | 55 vs 33 → 18 vs 19 |
| **total** | **69-47 (59%)** | **16-41 (28%)** | |

Our record over all maps barely moved: 51.6% pre, 50.9% post.

Gold-only share of our own first-300-round clears, pre → post: rows 0.45 → 0.68, corners 0.61 → 0.87, gold_rush
0.55 → 1.00, boss 0.47 → 0.70, fracture 0.11 → 0.50, collision 0.54 → 0.91, the_pack 0.44 → 0.85, lanes 0.30 →
0.72. Our gems by r300 fell on every one of these maps (corners 136 → 44, collision 98 → 18, lanes 141 → 71,
gold_rush 50 → 0).

The 13 maps where our gold-only share exceeds the top teams' by 0.25 or more: v17 63% (others 45%), v18/v19 56%
(others 54%), v22 47% (others 51%), v25-v31 **45%** (others 53%). Across all maps, the gold-only excess correlates
−0.46 with the r300 gem gap, and that gap correlates +0.39 with win rate. The world.cpp comment already records the
same effect from v8: planning with real cluster health lost 1/8 on gold-rush vs v7.

### The change to test (B84)

`world.cpp` (works on v27 and on top of B83, whatever `cluster_effective_health` becomes):

```cpp
// Planning health of a gold cluster in a group with nothing that hits back (B84; v8-v21 behaviour).
constexpr float gold_only_cluster_health = 500.0f;
...
        // v20 (B56): real health for fighterless *gem* groups (02treasure-box). B84: gold-only groups at 120 took 50-100%
        // of our first-300-round clears on 00corners/00rows/01gold-rush/01boss-battle (top teams 14-26%).
        if (fighters.empty())
            info.health = (info.gems > 0 ? 120.0f : gold_only_cluster_health) * static_cast<float>(group.camps().size());
```

Variants `b84-500` and `b84-250` (gold_only_cluster_health 500 / 250). Also race `b83-120 + b84-500`.

```
python3 tools/race.py bots/daniel/v27 bots/_var/b84-500 bots/_var/b84-250 bots/_var/b83b84
python3 tools/gate.py bots/_var/b84-500 bots/daniel/v27 --mode map --maps 00corners 00rows 01gold-rush 01boss-battle 01fracture 00collision
python3 tools/gate.py bots/_var/b84-500 bots/daniel/v27 --mode nonreg
```

**Caution, from one local game.** b84 vs v27 on 00corners (b84 as A) lost 653:1014. b84 opened as top teams do:
G2 → G18 → G26 → G27, 177 gems from clears by r300 against v27's 44. But v27 farmed every gold patch, ended with
12.7k gold to b84's 5.6k, and won the fights 20 kills to 11. Against itself, gold-first is strong because the mirror
fights over the centre. In ranked we already out-gold top teams on corners (10.5k vs 8.5k) and still lose the race
with 6 deaths a game. So a self-play gate may under-rate B84: confirm with the scrim panel or a ranked A/B. On nonreg,
watch the maps where gold-only groups are the whole opening for top teams too: 00stampede, 00contest, 01elk_arena,
00pilgrimage, 01hooks, 00ambush, 00quarry, 00ribs.

## 3. Root cause B: contested captures freeze bodies (fix B85), 01yellow_brick_road

G0 and G1 on 01yellow-brick-road are rows of 30 gold clusters (600 gold, fighterless) at y=12 and y=17, from x=5 to
x=34. They wall both spawns in, so both teams use them. Any enemy on any of the 30 tiles contests the capture.

**Local reproduction**: v27 vs v12, v27 as A, lost **272:1012**.
- r20-r300: Vesper, HoR and Vendetta stand on G0 tiles (15,17), (12,17) and (16,17). Marcella and Ryth stand on G1
  tiles (13,12) and (12,12).
- v12's Vendetta stands on (22,17) and its Vesper on (21,12): other tiles of the same groups.
- Every status line from r100 to r300 reads `target=0/1 ready=1`, gems 0, gold 0. Our bank is still 0 at r750.
- From r500 to r1500, Vesper and HoR sit at (5,12) and (6,12) on G1 with `ready=1`, while v12's bodies sit at (33,12)
  and (34,12). Final earned gold: Vesper 266, HoR 200.

Ranked: in ff56d62d-429b-4f6c-b060-4574d76f0df1 (v31, lost 562:1018, first clear r336), Vesper earned 266 gold and HoR
200, with 984 and 2,436 monster damage. The same freeze shows in 77f136c8 (a win, 157:75 at round 2000, 1,140 gold).

Why it never ends:
- `work_group` keeps a body on a ready tile.
- `watch_progress` treats `group->reward_ready && group->tiles.is_set(pos)` as progress (bot.cpp:1246).
- The B45 one-receiver skip needs no enemy in sight.
- `fight_enemies` only engages enemies within `engage_radius` 4, and the contester stands 6-17 tiles away.

The change (B85), in `work_group`'s reward-ready branch. Tested in the scratchpad (`b85/src/bot.cpp`); it builds:

```cpp
constexpr int max_contested_turns = 10;  // B85
...
        if (!group.tiles.is_set(pos)) {
            move_towards_closest(group.tiles);
            return;
        }
        // B85: an enemy on another tile of the group (01yellow-brick-road's 30-tile gold rows) contests the capture
        // for good and the watchdog counts standing on a ready tile as progress: give up after a while.
        bool contested = false;
        try {
            const auto state = group.group.capture_state().state;
            contested = state == cambc::map::camp_group_capture_type::contested
                || state == cambc::map::camp_group_capture_type::enemy_capturing;
        } catch (const cambc::error&) {
        }
        contested_turns = contested ? contested_turns + 1 : 0;   // new Bot member, int contested_turns = 0
        if (contested_turns > max_contested_turns) {
            contested_turns = 0;
            group.skip_until = round + give_up_rounds;
            current_target = claim = -1;
        }
        return;
```

Local results on the same setup:

| Variant | Score vs v12 | Gold, ours / v12's |
|---|---|---|
| v27 | 272:1012 | 6.8k / 10.0k |
| B85 alone | 293:1010 | 2.2k / 16.4k |
| B84 + B85 | 602:1001 | 5.9k / 18.5k |

Without us sitting on the rows, v12 takes them and earns 16-18k gold. So giving up only goes halfway: the rows are
worth having, and top teams earn 10.6k gold on this map. A follow-up (B85b) would walk along the group's tiles to the
nearest visible enemy on them and fight it, and give up only when no contester can be seen. Gate:
`python3 tools/gate.py bots/_var/b85 bots/daniel/v27 --mode map --maps 01yellow-brick-road 00the-line`, plus nonreg.
Only 00the-line also has a group spanning 8 or more tiles; it has one of 22.

## 4. Root cause C: 01boss_battle's breach eats the bodies (fix B86)

Since B34 (v15), the only altar tile (24,20) is a Monolith spawn tile, `altar_walled` is true, and `corridor` = {(24,20)}.
`should_tribute` sets `banking = true` when `altar_walk ≤ tribute_detour` (10). That holds next to the central groups
G8 and G17 at (28,12) and (28,16), so carriers holding 9-19 gems walk to the breach. They wait in `corridor_gather`
for 2 allies, then strike G16 (2 × 20,000 HP, 2 × 200 damage).

Timelines:

| Match | Result | Body-rounds within 4 of (24,20) | Median gems carried there | Body-rounds dead |
|---|---|---|---|---|
| a213784c-464a-4733-8dbe-74a9caa45fae | L 0:2253 | 21% | 19 | 21% |
| 5c2effe4-4504-4c4f-91ce-939bfaea26f6 | L 0:0, tiebreak | 31% | 19 | 10% |
| e79cd8bd-ef29-48db-911e-fb8c54728f09 | L 60:1000 | 25% | 19 | 14% |
| ce3aea51 | W 952:111 | 30% | 15 | 12% |

In a213784c, Vendetta stands at (23,19) holding 9 gems from r81 to r201, and Marcella at (21,17) holding 10. Then
Vendetta, Ryth and Marcella die at the breach at r230, r232 and r234, and three more bodies die there at r442-445 and
r577-579 ("camp?"). Our gold is 6.1k vs top teams' 17.3k. They farm, carry 234-985 gem bags, and kill the Monolith
late: their gems by r1000 are 64.

The change (B86):

```cpp
// bot.h
int corridor_group = -1;   // B86: the Monolith group the breach must cut (01boss-battle), else -1
// init(), after the corridor is built (bot.cpp ~374)
for (int i = 0; i < static_cast<int>(camps.groups().size()); ++i)
    if (camps.groups()[i].monolith && !(camps.groups()[i].tiles & corridor).is_empty())
        corridor_group = i;
// should_tribute(), after `if (gems == 0 || !gems_deliverable) return false;`
constexpr int walled_tribute_gems = 100;
// B86: carriers banked 9-19 gem bags through tribute_detour beside the Monolith altar and waited at the breach
// (21-31% of body-rounds, 10-21% dead; gold 6k vs top 17k). Until it is dead, bank only a siege-sized bag with siege health.
if (const auto* g = camps.group(corridor_group); g && !g->reward_ready && !g->known_respawning(round)
    && (gems < walled_tribute_gems || own.health < (1 + monolith_hit_turns) * g->damage))
    return banking = false;
// shop_trip(): let carriers recall to shop on that map (they now hold bags for a long time)
const unsigned bag_limit = corridor_group >= 0 ? 1000u : (calm ? 10u : 0u);   // was (calm ? 10u : 0u)
```

`g->damage` for G16 is 400, so a body banks only once it has 1,600 health, which our bodies reach around r400-600.
It changes nothing on 02the_pack, whose corridor is wolves. Risk: bigger bags lost on death go to the killers. Gate:
`python3 tools/gate.py bots/_var/b86 bots/daniel/v27 --mode map --maps 01boss-battle`, plus a crash check. No other
map has a Monolith corridor.

## 5. Other maps

- **01gold_rush**: B84 is the main lever, since 100% of our early clears are gold-only. Also, the centre gold groups
  G1-G8 sit within range 5 of G0's Monolith at (15,15). Our bodies die there at r32-51 in all four timelines:
  b2afce4a, 1d956ac6, 6b36914e and 32ff2282 (HoR at (16,16), (15,16), (14,14), (11,16)). Marcella loses 200 health a
  round at (12,13) in b2afce4a: the Monolith is awake. Not diagnosed who wakes it (our HoR's dash aims at "the most
  camp tiles" in its radius, which includes the Monolith, but B63 says the dash cannot target camps). Worth one
  debug run.
- **01the_farm**: our first-300-round clears are 50% lone 2-gem groups G26/G27, which keep B56. Top teams take 0%.
  22% of our clears are on the enemy half (G27 at (48,19)); top teams take none there. Our median tribute bag is 25
  gems against their 56. B83 helps, because mixed groups like G10 (elk + 2 gems) and G0 get cheaper. A candidate
  fix (not tested): charge extra travel time in `choose_target` for groups nearer the enemy spawn. Over all maps our
  enemy-half share is +0.08 above top teams', with rows +0.29, gold_rush +0.23, the_farm +0.22, fracture +0.18.
- **00vault**: this is a fight. G0 (49 gem clusters, 343 gems) is priced the same as top teams price it, and we reach
  it as early. In 33c225a8-9992-4b34-8cfb-267ba70496a7 all four of our bodies enter at r16 and die between r31 and r46
  to the mirror team, with 13 deaths to their 1. In 506877ee-2829-4ad5-8903-a40778dae59e we banked 389 by r150 and
  then lost every fight after r200 (8 deaths to 5; their Prism tributed 630). This belongs with B30 (gemfight), not
  with targeting.
- **00road_of_riches**: not reproduced (local v27 beat v12 1012:530). The map is a spiral: the altar is a **120-tile**
  walk from spawn, and G28 sits 4 tiles from spawn as the crow flies but 138 tiles away on foot. We lead at r250
  (163 vs 83) and stall from r400. In cf7121b8-18bb-4abb-8f46-340ccbf635d6 our bank stays at 198 from r400 to r750
  while the opponent goes from 211 to 946, clearing G0, G4 and G8 near the altar. Our bodies roam the outer ring
  holding 7-29 gem bags for hundreds of rounds; HoR holds 21 gems from r201 to past r761. Locally HoR earned 0 gold
  in 1,300 rounds, targeting G32 (2 gold, `ready=1`) a spiral away. B84 removes some of those 20-40 gold singleton
  targets. The rest is a bag-size and roaming question with no clear fix yet.

## 6. Order of work

1. **B84** (with B83): race, map gate on the six maps, nonreg on all maps, then the scrim panel. It covers 5 of
   the 9 maps here plus 8 more, about 16% of ranked games, at 45% now. Getting those back to the other maps' 53%
   would be worth +1.3 pts; getting them back to their pre-B56 59% would be worth +2.3.
2. **B85**: map gate on yellow_brick_road and the_line, plus nonreg. Small diff and low risk. Follow with B85b
   (fight the contester).
3. **B86**: map gate on boss_battle.

Log B84-B86 in `bots/daniel/docs/backlog.md` before testing (cadence rule). This note does not edit the backlog.

## Openings vs the top teams (scout 2026-10-29 12:25Z, `tools/openings.py <map> --ours replays/daniel-v26..v34`)

Median round of clears #1/#3/#5, top teams vs us:

| Map | Top | Us |
|---|---|---|
| 00vault | 6 / 95 / 214 | 3 / 61 / 102 |
| 01islands | 5 / 66 / 122 | 2 / 71 / 130 |
| 00expanse | 26 / 49 / 66 | 29 / 50 / 64 |

Our opening clears are as fast as theirs, or faster. On these maps the losses come after round 100, in fights and in holding objectives, not in the opening. This fits B91a: the opening pack was neutral on wins.
