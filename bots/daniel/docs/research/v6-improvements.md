# What would most improve Daniel v6 in ranked play (54 ranked games, 28–26)

Sources: the 54 ranked v6 games in `replays/daniel-v6/` (`analysis/games.json`, `*.stats.json`, `*.timeline.csv`, our
`team-*.stdout` / `team-*.fuel` inside each zip), the 65 v5 games in `replays/daniel-v5/` for comparison, the map dumps
in `maps/ascii/`, the rules in `docs/GameRules.md`, and the code in `bots/daniel/v6/src/`. Short replay ids (`b78596fd`)
are the first 8 hex digits of `match-<id>.zip`. All code references are to `bots/daniel/v6/src/`.

How the death numbers below were computed: a death is a round where a champion's `alive` goes 1 → 0 in the timeline.
The killer is the enemy whose `kills` count goes up in that round. "Near" means an enemy alive within Chebyshev 5 at
round r−1. "hp5" is the victim's health five rounds earlier. "Still" means the victim didn't move in its last 3 rounds.
"Killer in bush" means the killer's tile at r−1 is `"` in the map dump and the victim's tile isn't. Kills by the
opponent's champions are 496 of our 539 deaths. The other 43 have no champion killer (camps).

## TL;DR: ranked changes

| # | Change | Expected impact | Effort | Evidence |
|---|---|---|---|---|
| 1 | **Siege any group too big for `max_group_bodies`, not just monoliths** | High on stampede (0–3, 0 gems scored in all 3 games). Medium on eight / pilgrimage / swirl, where 49% / 31% / 22% of gems sit in such groups | ~30 lines | §1 |
| 2 | **React to unseen attackers** (health drops with no visible enemy → retreat and mark danger), and **retry a blocked step** | 32% of the deaths where an enemy champion got the kill (159/496) had that killer in a bush while our victim was outside it. On stampede it was 55 of 90 deaths | ~15 lines | §2 |
| 3 | **Stall check on walking distance, not Chebyshev** | 240 of 560 "stalled" give-ups were false. 218 of them were on pilgrimage (3–4, 348 stalls in 7 games) | ~10 lines | §5 |
| 4 | **A hurt carrier recalls before banking under threat** (recall keeps gems) | 45 of 79 deaths with gems (1,419 of 2,717 gems handed to the killer) came after the carrier was already below 50% health 5 rounds earlier | ~3 lines | §2 |
| 5 | **First emblem Jungle instead of Monster** (same 5 shards, only the passive changes) | Unverified estimate: about 180 vs 70 body-turns per game (Jungle vs Monster), based on our measured camp damage taken and dealt | 1 line | §3 |
| 6 | Gold squad stops farming while a ranged enemy pokes it from out of reach | Their casters get ~3 kills/game each, ours 0.4–1.8. 68 "still" deaths had only ranged enemies near. Uncertain: Simon's fight-or-flee variants lost locally | medium | §2, §3 |
| 7 | Draft profile: don't count siege-only groups as farmable splash/elk value | Low until #1 lands. Draft data can't separate picks from maps | ~5 lines | §4 |

Not problems: fuel (max 94,041 in a turn, p99 48k), side (A 12–12, B 16–14), runtime errors (no `cast failed` /
`lock failed` lines in any stdout). See §5.

Suggested order: 3 and 2 first (small, unambiguous bugs), then 1, then 4/5 as tunable experiments.

---

## 1. Groups that need ≥3 bodies

**Why v6 never takes them.** `max_group_bodies = 2` (`bot.cpp:54`) caps helpers at 1 (`bot.cpp:617`), so `needed()`
returns 0 for any group two bodies can't survive (`bot.cpp:620-624`). Such groups are skipped (`bot.cpp:682-683`)
unless they hold a monolith (`bot.cpp:651-675`, siege branch). The survival test uses fixed per-helper figures
(`body_damage = 50`, `body_health = 900`, `bot.cpp:37`) and `max_damage_share = 4.0351` (`bot.cpp:43`).

**Survey of all 17 maps** (`maps/ascii/*.txt` camp-group lines). I applied v6's own `survivable()` and `exposure`
formulas (`bot.cpp:184-188`, `world.cpp:54-61`) at base stats (50 damage, 900 health per body). In brackets: the
bodies still needed by a geared body (120 damage, 1,300 health) with base-stat helpers:

| Map | Groups needing ≥3 bodies (non-monolith) | Share of map gems |
|---|---|---|
| stampede | G10 6 elk + 6 gem clusters, 360 gems, at (57,24): needs 5 (3) | **100%** |
| eight | G4/G5 3 elk + gem + gold, 132 gems each, at (14,26)/(26,26): need 3 (2) | 49% |
| pilgrimage | G12 4 elk + 4 gold, 144 gems, at (24,58): needs 3 (2) | 31% |
| swirl | G16/G17 4 elk + 2 gems, 192 gems each, at (12,2)/(32,27): need 3 (2) | 22% |
| the other 13 | none | 0% (contest, monolith and rows have monolith gems instead: 100% / 63% / 53%) |

Stampede is the extreme case. Its draft log reads `gems=360 ... elk=1.00 splash=1.00` (`67b81b5d` team-a.stdout), and
our bodies spent the game on gold clusters, including the enemy's home row (`b78596fd` team-b.stdout: Vendetta
`target=6 (42,1)` at r200/r300, `target=0 (24,1)` at r700-r900).

**How opponents took it (stampede).**
- `d77ac689` (they: Stellar, Tavi, Prism, C&I, Ren). All five sat on the group from r100 to r140 at base health
  (700-900) and banked 360 by r250, again by r430 and again by ~r470. They had 0 deaths. A whole-team rush works at
  base stats.
- `67b81b5d` (they: Varg, Ryth, Tavi, Willow, Vesper). One body at a time, each walking away hurt: Ryth 2,480 → 758
  hp over r620-650, Tavi r690-700, Vesper 1,764 → 966 over r780-800, then a capture (B's score 0 → 360 by r800). Later
  captures came at ~r990 and ~r1190. No single trip could deal 17,400 health against 360 damage per turn. Progress
  must carry over: dead members stay dead until the group is captured (`docs/GameRules.md:193`, "respawns together
  after rewards are claimed"). Whether *damaged* elks keep their damage is unverified, but v6 measured it for monoliths
  (`world.h:31-32`).

**Proposed generalisation (exact places).**
1. Add a predicate `sieged(g) = g.monolith || needed(g) == 0` inside `choose_target`. It is dynamic, so a 3-elk group
   becomes a normal two-body target once our own damage has grown. Use it in place of `g.monolith` in `cap`
   (`bot.cpp:633`), in the keep-current test (`bot.cpp:637-638`), in the skip test and branch (`bot.cpp:651-653`), and
   in `work_group`'s wait-for-help guard (`bot.cpp:738`, `!(group.monolith && siege)`). `work_group` can't see
   `needed`, so store the flag on `group_info` when choosing.
2. `world.cpp:104`: track `remaining` for every group with `mobs`, not only `monolith`. It costs one `camp.health()`
   per member, only when the whole group is in sight.
3. The siege time model (`bot.cpp:661-667`) charges `kill * g.damage / bodies`. For elk groups that overstates the
   damage taken, since it falls as elks die. Scaling `g.exposure` by `remaining / health` is closer, and conservative
   enough to start with.
4. **Safety, required.** Monsters hit "the nearest champion every turn" (`GameRules.md:189`) at range 3
   (`GameRules.md:206`). Six elk deal 360 per turn (GameRules table, `GameRules.md:179`). A melee body adjacent to the
   group needs ~3 steps to get out of range, so leaving at `recall_health = 0.288` (`bot.cpp:60`, 259 health on a
   900-health body) dies, and camp kills destroy carried gems (`GameRules.md:361`). On a sieged group, leave when
   `health < (steps_out + 1) * group damage`.

**Test.** `python3 tools/arena.py bots/daniel/v7 bots/daniel/v6 --maps stampede eight pilgrimage swirl --seeds 8`. Then
run the full gate (`--seeds 8`, all maps) to confirm the other 13 maps are unchanged (they have no qualifying groups,
so they should be). Check the stdout for captures of stampede G10 (`target=10`).

## 2. Why we die on eight, stampede and swirl

| Map (v6 record) | Our deaths/game | Main pattern |
|---|---|---|
| eight (0–3) | 33.3 | 32/100 deaths within 8 tiles of our spawn. Hottest 4×4 cell is (0-3, 8-11), the north exit of our walled spawn (walls x=3-4, y=9-21). 642 carried gems lost in 3 games. The map's **only altar is at (20,15)**, between hole rows 13 and 17: 10 of 17 deaths with gems were within 5 of it, e.g. `8c9e4251` r1002 Vesper with 132 gems at (18,15) |
| stampede (0–3) | 30.0 | 41/90 "still", 62/90 with no ally within 5, killers Tavi 40, Stellar 19, Prism 13. **55/90 killed from a bush** |
| swirl (1–2) | 23.7 | 60/71 deaths in the centre block x 20-27, y 12-19, around G10/G11 (elk + 3 gold) which lies between both spawns. v5 died there too (73 of its 108 swirl deaths in the same cells), so this is not caused by v6's gold weight |

**Across all 54 games** (539 of our deaths, 291 of theirs):
- 68% of our deaths were to ranged killers: Stellar 124, Tavi 104, Prism 42, Vesper 38, Cassi 24. 49% (264) had no
  ally within 5. Deaths in 1v1 (one enemy near, no ally): 94 ours vs 66 theirs.
- In losses, 126 of 385 deaths (33%) were in our own third of the map, against 39/154 in wins. Only 20 of all our
  deaths were in the enemy's third. Opponents come to us. We don't overextend.
- 27% of our deaths (146) came from ≥90% health within 5 rounds (burst), against 16% (47) of theirs.
- **Hidden killers.** 159 of 496 champion kills on us had the killer in a bush and our victim outside it (theirs: 50
  of 255). By map, losses: stampede 55, swirl 14, eight 12, fragment 12, rows 7, rushbait-v2 6.
  - Worked example, `b78596fd` r494-499. Our Vendetta walks to (12,13). Their Tavi sits at (14,11), a bush tile
    (stampede row 11, x 14-16, is `"""`). Vendetta takes 310, then 180 and 90 per turn, for 4 turns **without
    moving**, and dies at r499.
  - Bushes hide units from outside (`GameRules.md:340`). `threatened()` (`bot.cpp:190-196`), `enemy_seen`
    (`bot.cpp:821`) and `fight_enemies` (`bot.cpp:487-498`) only use visible champions, so the bot neither retreats
    nor fights back. Out of reach of camps it starts a recall (`bot.cpp:824-828`), which damage cancels.
  - **Unverified mechanism for standing still:** its path north ran through that bush. A step into a hidden unit
    returns `false` (`GameRules.md:163`), and `move_towards_closest` gives up instead of retrying another tile
    (`bot.cpp:355-356`).
- **Gems handed over:** 79 deaths with gems (2,717 gems). 66 had an enemy near, and 45 of them (1,419 gems) came
  after the carrier was already below 50% health 5 rounds earlier. Ways it happens: `tribute_detour` sends any
  carrier within 10 tiles to the altar (`bot.cpp:541-542`), and gold-squad bodies only leave at 28.8% health
  (`bot.cpp:60`, `823-824`). Recall keeps carried gems (`GameRules.md:373-377`).

**Fixes.**
- (#2) Keep `last_health` in `Bot`. If health fell this turn and `threatened()` is false, treat it as an enemy sighting:
  set `last_enemy_round`, use `duo_recall_health` for every body, `mark_danger` at our own position, and `retreat()`
  rather than `recall()`. In `move_towards_closest`, when `move_absolute` returns false, retry the next-best tile
  (`bot.cpp:352-359`).
- (#4) At `bot.cpp:823`, use the higher threshold for any body carrying gems after a recent sighting (`last_enemy_round`
  within `threat_memory`), not only the duo. Start at 0.5 and tune with `tools/tune.py`.
- (#6) In `fight_enemies`, the gold squad returns `hit` when it can't reach (`bot.cpp:521-523`). A melee body with more
  health than a ranged poker therefore keeps farming in its range. 68 deaths were "still" with only ranged enemies
  near (enemy at distance 3 in 38 of them, 4 in 12). Option: if no visible enemy is within our attack range and one
  is within its own range (3/4), count as outmatched and step out. Simon's fight-or-flee variants lost locally against
  non-chasing opponents (`bots/simon/docs/v6/summary.md`, "Details of the rejected ones"). Test only against
  `bots/daniel/hunter`.

**Test.** `python3 tools/arena.py bots/daniel/v7 bots/daniel/hunter --seeds 8` (hunter chases, which matches ranked),
plus `--maps stampede eight swirl fragment` for the bush-heavy maps. Watch deaths/game in the per-map output, not
only wins. Local bots don't sit in bushes, so #2 may read as neutral locally even if it helps in ranked.

## 3. Combat power: builds, gold, who kills

**Champion damage and kills per appearance** (`*.stats.json`, all 54 games):

| Champion | Theirs: kills/game, champion damage/game | Ours |
|---|---|---|
| Tavi | 3.0, 5,447 (n=26) | 0.4, 1,184 (n=10) |
| Stellar | 2.9, 5,746 (n=34) | 1.8, 3,169 (n=54) |
| Prism | 2.8, 6,188 (n=11) | — |
| Vesper | 3.0, 3,706 (n=9) | 0.8, 2,650 (n=24) |
| Varg | 0.7, 2,513 | 0.3, 1,003 |
| Vendetta | 1.1, 1,668 | 0.1, 535 |

The same champion deals 2-4.6× more champion damage for them (Tavi, Stellar, Varg). The gap is behaviour, not draft.
Our gold squad never chases (`bot.cpp:521-523`) and our engage radius is 4 (`bot.cpp:64`).

**Gold spent per champion by round** (timeline `earnedGold − gold`): us 30 / 129 / 237 / 487 at r100 / 200 / 300 /
500, them 57 / 158 / 258 / 496. Earned: us 76 / 186 / 295 / 545, them 87 / 194 / 298 / 545. They spend about one
shard earlier through r300 and the gap closes by r500. Small. Our shop trip waits for 150 / 300 gold
(`bot.cpp:597`).

**Emblem passives** (share of champions that finished one):

| | Monster | Power | Durability | Jungle | Bruiser | Treasure | Home |
|---|---|---|---|---|---|---|---|
| Us | 95% | 79% | 89% | 0% | 0% | 0% | 0% |
| Them | 52% | 70% | 41% | 54% | 20% | 10% | 8% |

**Value of each passive for us** (per game per team: camp damage taken 14,978, champion damage taken 14,945, camp
damage dealt 74,849). Families from `GameRules.md:298-303`:
- Jungle (−30% camp damage) saves ~4.5k health. At v6's own cost model (each health bar of damage costs a trip home,
  `bot.cpp:694`, about 2 × home_distance + 11 turns) that is ~4-5 trips, roughly 180 body-turns.
- Durability (−10% all damage) saves ~3.0k (≈120 body-turns), half of it in fights.
- Monster (+10% camp damage) cuts about 9% off ~150 team-turns of hitting camps, ≈70 body-turns.
- Home saves 2 turns per recall.
- These are estimates (unverified). Each emblem gives the same 5 shards of stats (`GameRules.md:298-302`, "Counts as 5 shards of the chosen stat"), so swapping the
  family changes only the passive.

**Change (#5).** In `build_order` (`bot.cpp:130-139`), make the first emblem `jungle_shard_of_<stat>` instead of
`monster_shard_of_<stat>`. Optionally make it Jungle → Durability → Monster → Power by adding one entry to the array.
Farming-race losses are a real share of our losses: `090957f7` rows 990-1056 and `8688a68d` rows 990-1056 (0 deaths
each), and `7f76683d` lanes 924-1000. In `090957f7` every enemy champion had Monster + Durability + Jungle + Home and
their Stellar dealt 55,136 camp damage to our Stellar's 21,314.
Test: `python3 tools/arena.py bots/daniel/v7 bots/daniel/v6 --seeds 8` and against `bots/daniel/hunter`.

## 4. Draft

Our draft is deterministic per map. All 3 eight games and all 3 stampede games used the same roster (Varg, Stellar,
Vesper, C&I, Vendetta), so pick win rates are confounded with map win rates. Our picks, wins/games: Ryth 19/28,
Stellar 28/54, C&I 27/51, Varg 11/33, Vesper 10/24, Vendetta 9/22, Tavi 6/10, Willow 8/14. Ryth was drafted on the
good maps (collision, corners, interlock, monolith, rushbait-v2) and Varg on the bad ones. No pick-level conclusion
survives that.

Their picks, their wins/games against us: Prism 8/11, Marcella 7/8, C&I 12/22, Ryth 19/39, Varg 18/39, Stellar
17/34, Tavi 12/26. On our losing maps they drafted: eight C&I ×3, Stellar ×2, Ryth ×2, Ren ×2; stampede Tavi ×3,
Prism ×2, Stellar ×2, Ryth ×2. Ranged stunners (Tavi, Prism, Stellar) are the common thread, and they are also the
top killers (§3). Since our own Tavi gets 0.4 kills/game, drafting them alone would not copy that.

**One concrete draft bug.** `map_profile.cpp:95-100` counts every non-monolith camp as farmable splash/AoE value, and
`map_profile.cpp:91-92` puts elk groups into `elk_gems`. On stampede the only gems are the one group v6 can't take, yet
it produced `splash=1.00 aoe=1.00 elk=1.00 gold_bonus=2.39` and made Varg the top opening score (1.80, `67b81b5d`
team-a.stdout). Treat groups that need more than `max_group_bodies` at base stats as `boss_gems` there, so they feed
the boss signal (Ryth, stuns, `draft.cpp:101-124`) instead. Do this after #1, since what to draft depends on whether we
siege. Test: `python3 tools/arena.py bots/daniel/v7 bots/daniel/v6 --maps stampede eight pilgrimage swirl` without
`--seeds`, because random drafts bypass the draft.

## 5. Cheap fixes and non-issues

- **Stall metric (#3).** `watch_progress` measures progress as Chebyshev distance to the anchor (`bot.cpp:879`) and
  gives up after 14 turns without improvement (`bot.cpp:47`, `891-895`), skipping the group for 60 rounds.
  - Stdout has 560 `stalled` lines: pilgrimage 348 (7 games), ambush 88, eight 25, swirl 19, stampede 17.
  - I re-measured each with a BFS on the map dump. In 240 of them, 218 on pilgrimage, the walking distance exceeds the
    Chebyshev distance by ≥10.
  - Example: team A on pilgrimage stalls on G11 at (46,44) from (0,17), (0,21) and (0,38) (`8d4fd823`, `c4850c69`,
    `cab6ad90`). Walking down the x=0 lane keeps the Chebyshev distance at 46 until the bottom row.
  - Fix: on target change compute a `distance_field` to the target's tiles once, kept as a member like `altar_walk`
    (`bot.cpp:282`), and compare `field.get(pos)`. The fuel cost of one field on 50×65 is unverified, but well under
    the observed headroom.
  - Test: `python3 tools/arena.py bots/daniel/v7 bots/daniel/v6 --maps pilgrimage ambush --seeds 8`, and count
    `stalled` lines.
- **Fuel.** I decoded `team-*.fuel` as u64 records from byte 13 (layout inferred: four budget pairs, then 1M-budget
  draft turns, then per-turn use). Over 231,144 game turns the max is 94,041, p99 48,148, and 24 turns are above 80k.
  Fuel is not a problem.
- **Side.** v6 is A 12–12, B 16–14 (v5: A 6–23, B 12–24). No asymmetry.
- **Errors.** No `cast failed`, `lock failed` or exception lines in any of the 54 stdouts.
- **Close losses are pace losses.** 9 of 26 losses were by ≤250 gems, mostly with ≤2 deaths (rows ×2, lanes,
  pilgrimage, ambush, corners). #3 and #5 target those, and #1-#2 the blowouts (eight, stampede, swirl, fragment: 23-38
  deaths each).
