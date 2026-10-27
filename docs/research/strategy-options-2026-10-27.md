# Strategy options for the next bot (2026-10-27)

Goal from Daniel: a significant strategy change, at least 60% for the next bot. The live bot is `bots/daniel/v16`
(ranked 66-64 at 2026-10-27 ~23:50Z, `python3 tools/ranked.py replays/daniel-v16 --since 2026-10-27T07:52`), and
the dev candidate is `bots/daniel/v17`. The top 20 are rated 2105-2415 (`data/scout/20261027T1257Z.json`), and we
are about 1593.

**Short answer.** Our economy runs at about half the top teams' from round 1, and 28 of v16's 64 losses are
already decided by round 300. Nothing we have tuned so far (constants, build order, fight rules) moved this,
because the gap does not come from constants. It comes from five mechanics the top teams use and we do not:

1. Heart of Ruin's damage dash.
2. Spending gold early.
3. The new Prospector emblem.
4. Wards.
5. Which ally takes a capture's reward.

Each is untested in our line. The candidates below are ranked by expected gain. The gains are **guesses**, based on
the size of the gap each one closes.

## Ranked summary

| Rank | Candidate | Evidence (headline) | Expected effect (guess) | Status of prior tests |
|---|---|---|---|---|
| 1 | **B41 Heart of Ruin kit play**: keep the dash for combat (1.5 x focus area damage + 1-round stun), aim it, count it in our damage estimate, take HoR off the duo role | Per 1000 rounds, our HoR deals 4.7k camp damage to the top 5's 15.1k, and 0.7k champion damage to their 2.8k. It earns 287 gold to their 714. `measure_damage` sees HoR as 30 damage | +4-7 pts vs v17. HoR is in every draft we make | B4 open since day 1, never built |
| 2 | **B42 Spend gold early**: one shop threshold of 150 for every role, a shop trip with a small bag, then Treasure first | Top 5 hold 12 emblems by r500, we hold 4. They have spent 2,130 gold by r500, we have spent 870. First emblem: Vesper r137 vs r323, HoR r291 vs r434. Gold earned by r250 is 1,026 vs 533 | +2-5 pts | Timing never tested. Build order alone was rejected twice (B11 Treasure first, B31 Jungle first: 50-51%) |
| 3 | **B43 Prospector emblem first** (+25% of our share of gem- and gold-cluster rewards) | Engine magnitude 0.25 (probe). 44-54% of the gems we capture come from gem clusters, so +11-13% gems for 150 gold a body. Trzy Kwaterki buy 8.6 Prospector shards a game; it is Marcella's first emblem in 78 of 466 top-5 games | +2-4 pts | Never tested |
| 4 | **B44 Wards**: place one every 10 rounds, on a bush near our path or target | Top 5 place a median of 140 wards a game. 71% of them go on bush tiles, which are 5% of walkable tiles. We place 0. A v7 note in `bot.cpp` records 159 of 496 champion kills on us coming from a bush | +1-3 pts | Never tested |
| 5 | **B45 Capture-reward routing** (unconventional): one ally takes each reward; the others step off at timer 1 and move on with empty bags | Top Vesper earns 1,592 gold per 1000 rounds to our 840, and top Marcella 1,926 to our 1,010. 97% of top captures have one receiver, although 30% have an ally within 3 tiles. B38: joining cut our gold 30% | +1-3 pts | Never tested |
| 6 | **B46 Gem-carrier hunting**: port `bots/simon/hunter-v0` onto v17 | Early in the game a kill is worth 19.8 submitted gems (win model). The engine pays 100 gold a kill (probe), where `GameRules.md` says 50. Top 5 kill 5 a game, we kill 3. hunter-v0 beat daniel/v5 24/34, and v5 scored 45% against it over 170 arena games | +1-3 pts | Tested only on the v5 base |
| 7 | **B47 02guardians banks nothing** (map bug, like B34) | v14+v16: 0 gems banked in 10 of 10 games (3-7, two 0:0 losses on gold). Top 20 bank a median of 363 there | +0.5-1 pt overall | New |
| 8 | **B48 Bigger bags**: tribute_gems 25 → 35, detour rule only within 5 tiles when no enemy has been seen | Median bag 28-30 (top) vs 18 (ours). We make 32 tributes a game for fewer gems; top teams make 21 | +0.5-2 pts | Tuned only in self-play (v3, v7) |
| 9 | **B49 Lock the altar we just used** (unconventional) | Engine: a lock takes 5 hits to break, not 3 (probe), and our own team can still tribute through it. It costs 10 gold and one action | +0.5-1.5 pts | Never tested |
| 10 | **B50 Late-game spawn-tile denial** (unconventional) | Rule: any occupied spawn tile delays the whole group's respawn (`docs/GameRules.md:193`). No top team is seen doing it | 0 to +1 pt, may be negative | Never tested |
| 11 | **B51 Contest enemy captures with `capture_state()`** | The 4.0 API reports `enemy_capturing` with only the group in vision (`sdk/cpp/cambc.h:4719`). Simon v5's sight-based version was neutral | ~0 | Neutral (Simon v5, 48%) |
| 12 | **B52 Draft changes** | Top-20 win rates within ±5 points for every core pick. Heart of Ruin matters (without it: 0.40 / 0.42 in 4 / 5 picks). We win 35% against Tavi, which looks like gold timing (rank 2), not the draft | ~0 | B25 core draft kept (v12) |

**Combining the top four.** All four target the same gap: half the camp damage and half the gold of the top
teams by r250. They should add up only partly. A guess for 1+2+3+4 together is +8-14 points against v17. That is
the only route to 60% visible in this data. No single fix found here is worth 10 points on its own.

**The 60% target and the ladder.** Rating-matched pairing pulls the ranked record toward 50% (backlog T4). A bot
that is truly stronger shows about 60% ranked only while it climbs. Measure the target with
`gate.py --mode gain` against v17, then with the first ~100 ranked games after submission, not a long-run ranked
average.

## Data used (refreshed for this note)

- Ranked: v16 has 130 games (`replays/daniel-v16`, 66-64), v14 has 240 (`replays/daniel-v14`). Both have full
  summaries. 11 v16 replays were decoded with timelines (downloaded with `cambc matches download`, decoded by
  `node tools/replay/analyze.mjs`, kept outside the repo; 19 of the 30 requested would not download).
- Top teams: `python3 tools/scout.py --top 20 --matches 100 --summaries 40 --replays 30`, run 2026-10-27 12:57Z.
  It gives 3,192 feature rows, 2,162 full summaries and 1,049 decoded replays with gzipped timelines under
  `data/scout/`. "Top 5" means Intercontinental Fish, Mite, Trzy Kwaterki, German Empire Destroyer Destroyers and
  prism best girl (ranks 1-5 at 09:54Z; NEETCoders passed prism best girl by 12:57Z).
- **Engine facts read from the engine.** A throwaway Python probe bot played `cambc run ... --rounds 3` and
  printed `ItemType(i).passive_magnitude()`, `combine_count()`, the stat points, the `cambc.constants` settings,
  and each core champion's `abilities()` payloads. `docs/GameRules.md` is **stale** on several of these values (see
  the next section).
- Every metric below is a median per team-game unless marked otherwise. Our side uses the summary of our own team.
  The scout side uses the scouted top team's side (`side` in `data/scout/features.jsonl`).

## Engine facts that differ from `docs/GameRules.md`

| Fact | `GameRules.md` | Engine 2.0.0 (probe / `sdk/cpp/cambc.h`) |
|---|---|---|
| Kill gold | 50 (`:361`) | `KILL_GOLD=100` |
| Altar-lock hits | 3 (`:235`) | `ALTAR_LOCK_HITS=5` |
| Camp rewards | wolf 22 gems / 90 gold, elk 36/160, gem cluster 24 gems at 500 HP (`:181-185`) | wolf 4 / 40, elk 15 / 90, gem cluster 7 gems, gold cluster 20 gold (`maps/ascii/*.txt` group lines); clusters 120 HP (`cambc.h:237`) |
| Vesper gold bonus | 20% (`:518`) | 33% (`cambc.h:166`) |
| Prism | 0.2 focus per carried gem (`:550`) | 1.5 (`cambc.h:160`) |
| Marcella | stun immunity only (`:644`) | also 2 gold per gem tributed (`cambc.h:169`) |
| Heart of Ruin | not in `GameRules.md` | 1000 HP, 30 strength, 100 focus, melee. Slot 0: self-shield 1.5 x focus for 5 turns. Slot 1: dash, range 2, landing damage **1.5 x focus in radius 1 + 1-round stun**. Passive: up to +50% damage at 0 health (probe; `cambc.h:178`) |
| Ward | "relocate every turn" (`:104`) | `WARD_COOLDOWN=10`, vision radius 6, placement range 2, lifetime unlimited |
| New emblems (sprint 3) | not documented | Tribute: 33% shorter tribute. Capture: team capture capped at 3 turns. **Prospector: +25% of your share of gem/gold-cluster rewards, rounded down.** Hunter: +50 gold a kill. Skirmish: +5% damage to champions. Collectors: +1% damage per emblem family owned. Greed: 25 shards (750 gold) make an emblem worth 35 stat points (all probe values) |

## 1. What the top 5 do that we do not, by phase

Sources: `data/scout/features.jsonl`, `data/scout/summaries/*.json.gz` (events: `campClear`, `gemCollection`,
`gemSubmission`, `buyItem`, `itemCombination`, `wardPlacement`, `death`) and `data/scout/replays/*.timeline.csv.gz`.
Our side is `replays/daniel-v14` + `replays/daniel-v16`.

| Phase | Measure | Top 5 | Ours (v14+v16) | Note |
|---|---|---|---|---|
| Draft | Core picks | Vesper, HoR, Marcella, Vendetta (+Ryth) | same (`draft.cpp` `core_order`) | Same picks: the gap is play, not draft |
| r0-250 | First camp clear | r20 | r25 | small gap (B36 closed most of it) |
| | Captures before r250 | 11 | 8 (v16) | |
| | Team gold earned by r250 | **1,026** | **533** (v16), 425 in losses | from `championTimelines` earnedGold |
| | Gems submitted at r250 | 75 | 54.5 | |
| | First purchase (team) | r59 | r103 | |
| | First emblem (team) | r94 | r215 | |
| | Wards placed | from r10, one per champion every ~14 rounds | 0 | |
| r250-1000 | Team gold earned by r500 / r1000 | 2,427 / 5,056 | 1,152 / 2,558 | half, all game |
| | Emblems completed by r500 (team) | **12** | **4** | |
| | Gold spent by r500 | 2,130 | 870 | |
| | Gems submitted at r500 / r1000 | 246 / 712 | 144 / 381 | |
| | Captures before r500; gold and gems in them | 23; 1,800 gold, 310 gems | 16; 880 gold, 183 gems | they take more wolf/elk groups (0.35+0.21 wolves+elks per capture vs our 0.27+0.15) |
| | Share of champion-rounds dead (timelines) | 7% | 16% (7 decoded games, all losses: weak sample) | |
| | Mean gems carried | 13.7 | 5.4 | they hold bigger bags |
| Late | Game length | 985 rounds | 1,462 | they reach 1,000 gems; we run to r2000 in 24 of 130 v16 games |
| All | Deaths / kills per game | 5 / 5 | 9 / 3 | deaths to camps: mean 1.0 vs 3.6 |
| | Tribute bag (median / mean), tributes per game | 28 / 36, 21 | 18 / 21, 32 | |
| | Altar locks bought | 5 (0-8 by team) | 5 | no difference |
| | Captures with one receiver | 97% | 91% | top: 30% of captures have an ally within 3 tiles, but the ally takes no share |
| | Shards per game | Bruiser 114, Jungle 15, Power 15, Treasure 14, Durability 12, Monster 9, Prospector 2.4, Capture 1.9 | Bruiser 134, Monster 19, Durability 17 | we never buy Treasure, Jungle or the new families |
| | First emblem family | Treasure first: Vesper 290/423, HoR 253/429, Marcella 248/439, Vendetta 275/408 | Monster, always | |

### Per-champion output per 1000 rounds (median; top 5 vs v16)

| Champion | Camp damage done | Camp damage taken | Champion damage done | Gold earned | Gems submitted |
|---|---|---|---|---|---|
| Vesper Vale | 24,453 vs 15,197 | 3,997 vs 5,348 | 5,077 vs 3,292 | **1,592 vs 840** | 191 vs 156 |
| **Heart of Ruin** | **15,077 vs 4,702** | 7,224 vs 5,795 | **2,821 vs 714** | 714 vs 287 | 128 vs 71 |
| Marcella | 20,090 vs 15,401 | 5,079 vs 5,276 | 6,543 vs 4,039 | **1,926 vs 1,010** | **258 vs 125** |
| Vendetta | 23,685 vs 16,714 | 5,591 vs 5,449 | 2,595 vs 918 | 1,048 vs 630 | 189 vs 149 |
| Ryth | 18,252 vs 10,334 | 5,270 vs 5,034 | 2,783 vs 1,812 | 421 vs 479 | 54 vs 71 |

Over a whole team, we take the same camp damage per round as the top teams but deal about 60% of their camp damage.
Heart of Ruin is the outlier, at 31%.

## 2. Win and loss by opponent style and by map type

- **Styles** (`python3 tools/styles.py replays/daniel-v14 replays/daniel-v16 --k 5`, 370 games): 38% against
  Willow/Marcella/Home-shard drafts (16 games), 45% against Power-shard Vesper drafts (119), 52% against
  Treasure+Jungle Tavi drafts (52), 52% against Bruiser core drafts (82), and 54% against Stellar/Ren/Varg drafts
  (101). The spread is modest. No style explains the 50%.
- **Opponent picks (v14+v16):** we win 33/93 = **35%** against teams with Tavi and 55% against the rest. Tavi teams
  out-earn us (median gold 5,022 vs 4,470 against non-Tavi teams). Tavi shops in the field, which is the same
  spend-early effect as candidate 2. We win 56% against Cassi & Issac.
- **Team size:** 3 picks 46/68 = **68%**, 4 picks 38/91 = **42%**, 5 picks 101/211 = **48%**. With 4-5 bodies the
  economy gap compounds the most.
- **Map area** (from the `maps/ascii` headers): 54% on maps up to 1,600 tiles, 44% on larger ones.
- **Worst maps (v14+v16):** 01starvation 0-6 (B40 in test), 00stampede 0-4, 02the_pond 0-4, 00oasis 1-9,
  00rows 1-6, 00pilgrimage 1-5, 00galaxy 1-5, 01elk_arena 1-5, 00eight 1-5, 02crossing 2-7,
  adgato_gemcombat2 2-7, 02guardians 3-7 (B47).
- **Loss signatures (v16, `tools/ranked.py`):** 16 race, 16 tiebreak, 9 spiral, 5 camp_trap, 4 fuel, 1 frozen.
  The 16 "tiebreak" losses are slow games, not real tiebreaks: only 2 of v16's 24 round-2000 games ended level on
  gems. The other 14 trail by 50-900 gems. The two exact 0:0 losses are both 02guardians, lost on gold.

## 3. What decides games (win model)

`python3 tools/winmodel.py --ours replays/daniel-v16` trains on 3,532 games with per-round timelines. Held-out
accuracy is 73.7% in r100-500, 84.2% in r600-1000 and 88.4% after.

- Value in submitted gems in **r100-500**: 1 gold = **0.32**, 1 kill = **19.8**, 1 death = -2.2, 1 carried gem
  = 0.54. In r600-1000: gold 0.09, kill 12.8.
- Collapse round of v16's 64 losses (our win probability below 0.3 for good): **28 by r300**, 17 in r400-700,
  12 after r700, and 7 never below 0.3.

So the early economy decides most losses. Gold at r250 (533 vs 1,026) is worth about 160 gems at that phase's
price.

## 4. Draft: is the fixed core still right?

Over 2,757 top-20 games in `data/scout/features.jsonl`, the win rate with and without each pick, by team size:

- **Heart of Ruin:** 4 picks 0.55 with / 0.40 without (n 479 / 130), 5 picks 0.53 / 0.42 (1,482 / 185). The
  only large effect, so keep it.
- Vesper, Marcella and Vendetta are within ±6 points either way. Ryth is 0.47 with / 0.56 without in 4 picks
  (n 259 / 350); our 4-pick core already leaves Ryth out.
- Prism, 4 picks: 0.64 (n 88), but 0.34 at 3 picks (n 47) and 0.47 at 5. Mixed, and Prism needs a
  gem-holding play pattern (1.5 focus per carried gem; top Prisms submit a median of 0 gems).
- Cassi & Issac, 5 picks: 0.62 (n 164). Intercontinental Fish (74% wins) draft them, so this is probably the team
  more than the pick.
- **Counter-picks:** top-20 teams win 0.51-0.55 whatever the number of core picks in the opponent's draft
  (2 to 5). There is no counter-pick effect to exploit. Our record against opponents with 3 / 4 core picks is
  0.44 / 0.47, and 0.55 against 5: the mirror is no worse for us.

Verdict: keep the core. The HoR result says HoR's **play** is worth the most (candidate 1).

## 5. Candidates in detail

### B41 Heart of Ruin kit play (rank 1)

**Hypothesis.** Our HoR wastes its main damage source. Its dash (slot 1) lands for 1.5 x focus in radius 1 with
a 1-round stun (probe: `AbilityDash(range=2.0, radius=1.0, modifier=1.5, duration=1)`, damage 150 at base focus).
In v17:

- `move_towards_closest` spends the dash on travel whenever the path is still longer than 2 (`bot.cpp:494-507`).
- `cast_offense` never casts a dash (`bot.cpp:541-571`).
- `measure_damage` counts only `is_damage`/`is_aoe_damage` spells (`bot.cpp:191-206`), so HoR plans as a
  30-damage body (status lines in our ranked stdout: `heart_of_ruin ... dmg=30`).
- `survivable()` then needs helpers for most groups, so HoR waits, gets skipped, or tanks.
- The draft gives HoR the duo role (highest `fight_score`, `draft.cpp` `make_plan`). That sets a 300-gold shop
  threshold and a 75% recall line whenever an enemy is in sight (`duo_recall_health`, `bot.cpp:1023`). HoR's
  passive does the opposite: damage rises as health falls.

We also buy Bruiser:Focus for HoR (`build_stat`, `bot.cpp:135-141`), copied from the top teams, but nothing we
cast uses focus except the shield.

**Evidence.** Top-5 HoR per 1000 rounds: 15,077 camp damage, 2,821 champion damage, 714 gold, 128 gems. Ours:
4,702, 714, 287, 71. In 7 decoded v16 games our HoR is dead 18% of rounds before r1000; top HoRs are dead 8%
(300 sampled games). Teams without HoR lose 10-15 points (draft section).

**Expected effect.** If our HoR reaches half the top HoR's damage, team camp damage rises ~8-10% and HoR's stuns
join fights. **+4-7 points vs v17 (guess).**

**Implementation (`bots/daniel/v17/src/bot.cpp`):**

1. Add a helper, `dash_damage(const ability&)`: the modifier from `ability.info()` (`ability_dash`), times
   `me.focus()`. `ability.damage_amount()` already includes the HoR passive.
2. `measure_damage()`: for a dash with a modifier above 0, add `damage_amount() / max_cooldown x 1.5`. The 1.5 is
   the expected hits per landing (tunable).
3. `move_towards_closest()`: skip travel dashes whose modifier is above 0, unless no target is within 12 tiles.
   Vesper's and Vendetta's dashes (modifier 0) keep their travel use.
4. `cast_offense()`: for a ready damage dash, score each tile `t` in `ability.valid_tiles() & ~blocked_tiles()`.
   The score is the count of live visible camp members (`vision::camp_tiles()`, members of awake or targeted
   groups) or enemy champions within Chebyshev `radius` of `t`. An enemy carrying gems counts double. Cast at the
   best tile if its score is at least 1 (enemies) or 2 (camps), or at least 1 when the target group has a single
   member. Cast before the basic attack. Damage wakes camps, so never dash into a sleeping group that is not the
   current target.
5. `make_plan()` (`draft.cpp`): do not give HoR the `gem_duo` role. Exclude it from the `fight_score` sort, or
   give the duo threshold only to non-HoR picks. In `take_turn`, use `recall_health` (0.29) for HoR. Its passive
   rewards fighting low.
6. Keep `cast_support`'s shield, and add: also shield when a camp or enemy is awake within 3 tiles and HoR has
   taken damage this turn.

**Test.** `gate.py bots/daniel/b41 bots/daniel/v17 --mode gain` (every draft has HoR), then `--mode nonreg`
against v12 and Jame v3. Smoke-check 00elkring and 01islands: the first five clears should come sooner, as the
B17/B18 maps were tempo-bound. Check in stdout that `dmg=` for HoR is around 50, not 30.

### B42 Spend gold early: shop timing, then Treasure first (rank 2)

**Hypothesis.** Our gold sits unspent. Shop trips need 150 gold for the gold squad and **300 for the duo**, and
none happen while a body carries any gem (`shop_trip`, `bot.cpp:763-776`). So the first emblem comes at r215
(team), against r94 for the top 5. The economy then compounds: top teams finish 12 emblems by r500 to our 4.
Treasure first is what every top-5 core champion does: 59-69% of their first emblems.

**Evidence.**

- Team gold earned by r250: 1,026 vs 533. Spent by r500: 2,130 vs 870.
- First buy / first emblem per champion: Vesper r96/r137 vs r184/r323, Marcella r100/r180 vs r162/r302, HoR
  r147/r291 vs r234/r434.
- Win model: early gold is worth 0.32 gems.
- We win 35% against Tavi teams, which spend in the field.
- **Against:** B11 (Treasure first, 3.0.5, Power shards: gate 51%) and B31 (Jungle first, gate 50%) rejected
  build-order changes in self-play. The timing half is untested.

**Expected effect.** +2-5 points (guess). The timing part is the larger, more certain half.

**Implementation.**

- (a) `shop_trip()`: one threshold for all roles, the cost of the shards still missing from the current emblem
  (150 at first). Allow the trip with `gem_count() <= 10` when the walk to the nearest altar is longer than the
  walk home, and never while an enemy has been in sight in the last 10 rounds.
- (b) Also shop when passing within 3 tiles of our spawn (walk in instead of recalling).
- (c) Variant: `build_order()` becomes Treasure (main stat) > Jungle > Bruiser, then Durability for melee. Race
  (a) alone, then (a)+(c) vs (a).

**Test.** `race.py bots/daniel/v17 b42a b42ac b42a-monster`, then gate the winner (gain vs v17). Read
`gold@500` and `emblems by r500` from the local summaries to check that the mechanism fires.

### B43 Prospector emblem first (rank 3)

**Hypothesis.** Prospector adds 25% to the capturer's share of gem- and gold-cluster rewards, rounded down per
capture (probe magnitude 0.25; tooltip text in the visualiser bundle). It also gives the same 5 stat shards as
Monster. Gem clusters give 44% (top 5) to 54% (ours) of captured gems. Clusters have 120 HP and do not attack, so
nothing else in the game raises gems per turn this directly.

**Evidence.**

- Group values in `maps/ascii` (gem cluster 7 gems, gold cluster 20 gold).
- Our capture mix from `campClear` events joined to the `maps/ascii` group lines: 54% of captured gems and 36% of
  gold come from clusters.
- Top use: Trzy Kwaterki 8.6 Prospector shards a game, GEDD 5.3. Prospector is the first emblem in 78 of 466
  top-5 Marcella games, 38 Vendetta, 25 Vesper.
- Rounding: one 7-gem cluster gives 8 (+14%), not 8.75.

**Expected effect.** About +10% gems for each body with the emblem on cluster maps. **+2-4 points (guess).**
It loses value on elk/Monolith maps: the draft profile has the cluster share, so gate per map type.

**Implementation.** `build_order()`: the first family becomes `item_family::prospector` of the champion's stat
(`get_item_enum(item_family::prospector, stat)`, `cambc.h:1787`). Do this either for everyone, or only when
`plan.features` says the map's gem-cluster share is at least 30% (add the share to `map_profile`). Durability
moves to second, then Bruiser.

**Test.** Race Prospector-first vs Monster-first (v17) vs Treasure-first (B42c), then gate on all maps. Expect
the gain on 00gemfight, 00gem_fields and the adgato_gemcombat* maps.

### B44 Wards (rank 4)

**Hypothesis.** Wards do three things for us:

- **Bushes:** ambushers hide in bushes, and a ward's vision radius is 6.
- **Camp knowledge:** `world::observe` learns respawn timers only in vision. B26 found that we wait at respawning
  groups and re-clear them.
- **Cost:** one call every 10 rounds.

**Evidence.**

- Top 5: a median of 140 wards a game (Mite 208, Fish 150, GEDD 55). 71% go on bush tiles, against a 5% median
  bush share of walkable tiles over the 70 maps. 65% go within 4 tiles of a camp spawn, 23% within 4 of an altar.
  A champion places one every 14 rounds (median gap).
- We place 0 (`grep place_ward bots/daniel/v17/src` finds nothing).
- The v7 note at `bot.cpp:1009` says 159 of 496 champion kills on us came from a bush.

**Expected effect.** Fewer ambush deaths and better target timing. **+1-3 points (guess).**

**Implementation.** In `take_turn`, after acting, if `me.ward_cooldown() == 0`, compute
`tiles = me.ward_placement_tiles() & cambc::map::bushes()`. Prefer the tile nearest our current target's anchor
or the next altar on our route. When no bush is in range, use the placement tile nearest the target anchor, if the
anchor is more than 6 tiles away. Call `me.place_ward(tile)` and retry once on `false`. Vision is per champion, so
place only where this champion is heading.

**Test.** Gain gate vs v17. Then count bush deaths on ranked: deaths whose killer is unseen. The `hidden_round`
logic already detects these. Add a counter to the r100 status line.

### B45 Capture-reward routing (rank 5, unconventional)

**Hypothesis.** Rewards split among the allies present at completion (`GameRules.md:193`). So the team chooses
who receives each capture:

- **Vesper** gets 33% extra gold, 43% with Treasure.
- **Marcella** turns every tributed gem into 2 gold.
- A **Prospector** holder gets +25% of the cluster part.

Every other body steps off one round before completion. It then walks to its next target with an empty bag and
needs no altar trip. Picking the receiver:

- Wolf (4 gems / 40 gold): Vesper adds 13 gold, Marcella 8.
- Elk (15 / 90): Vesper 30, Marcella 30.
- Gem cluster: Marcella 14 gold, or Prospector +1-2 gems.

**Evidence.**

- Top Vesper earns 1,592 gold per 1000 rounds to ours 840. Top Marcella earns 1,926 gold to ours 1,010 and
  submits 258 gems to ours 125.
- 97% of top captures have one receiver, although 30% have an ally within 3 tiles. Ours: 91% single, 46% with an
  ally within 3.
- B38: B36's joining cut our gold 30% per game, because every joiner takes a share.

**Expected effect.** +1-3 points (guess). It also removes the B38 cost of joining.

**Implementation.**

1. In `work_group()`'s `reward_ready` branch, read `camps.group(index)`'s engine group's `capture_state()` (one
   call, only while on its tiles).
2. If the state is `ally_capturing`, the timer is 1 or less, and a visible ally of higher receiver priority stands
   on `group.tiles`, step onto a `beside` tile and drop the claim. Leaving does not reset the capture while one
   ally stays.
3. Priority: if the group's gems are at least gold / 4 and Marcella is there, she receives; else Vesper; else the
   lowest current bag (spreads risk). Prospector holders win groups with gem clusters.

**Test.** Gain gate vs v17. Check `earnedGold` per champion in local summaries: Vesper and Marcella should rise.

### B46 Gem-carrier hunting (rank 6)

**Hypothesis.** A kill early in the game is worth ~20 gems. It pays 100 gold (`KILL_GOLD`, probe), the carried
gems, and a 60-round respawn. We kill 3 a game to the top 5's 5. Visible enemies' `gem_count()` is readable
(`bots/simon/docs/hunter-v0/summary.md`).

**Evidence.**

- Win model, r100-500: kill = 19.8 gems.
- hunter-v0 (daniel/v5 + carrier chasing + shared-memory prey marker) beat daniel/v5 24/34 in real drafts. v5
  scored 45% against it over 170 arena games, and Simon v6 48% over 306.
- **Against:** local fight-rule changes are usually neutral (B3, B14, B28, B39).

**Expected effect.** +1-3 points (guess). It should interact well with B41: HoR's stunning dash on a carrier.

**Implementation.** Port hunter-v0's three changes into `fight_enemies()`:

- Engage at 0.8 health odds when the target carries 20+ gems.
- Look out to `hunt_radius` 8 for carriers.
- Write a prey marker in the danger bits of shared memory (`mark_danger` layout, `bot.cpp:31-35`). Use a new
  1-bit flag, so that prey and danger are told apart.

Restrict long chases to carriers, as hunter-v0 found. Unrestricted chasing lost 27/34.

**Test.** Gain gate vs v17, and vs `bots/simon/hunter-v0` as a hostile opponent.

### B47 02guardians banks nothing (rank 7)

**Evidence.** In v14+v16 we bank 0 gems in all 10 games (3-7). Two v16 losses are 0:0 on the gold tiebreak
(2,478 vs 2,870 and 1,729 vs 3,332), and the opponent banked 306-1,135 in four others. Top-20 teams bank a median
of 363 there and win 11 of 21.

**Hypothesis (guess).** The same pattern as B34 (01boss_battle): `gems_deliverable` turns off, or the altar is
walled by a Monolith or Golem.

**Next.** Play one local game with the init debug print (as for B34), then fix it.

**Expected effect.** 02guardians is ~1.4% of games. +0.5-1 point overall.

**Test.** `gate.py --mode map --maps 02guardians` + nonreg.

### B48 Bigger bags (rank 8)

**Evidence.** Bags median 28-30 and mean 36 (top 5) vs 18 / 21 (ours), with 21 vs 32 tributes a game. v17
banks at 25 gems, or anything within 10 walking tiles of an altar, or anything when no target is worth taking
(`should_tribute`, `bot.cpp:671-689`). Past tuning was self-play only (v3: 30 → 36; v7 re-tune: 19).

**Expected effect.** +0.5-2 points (guess). Fewer walks to the altar. The cost is bigger losses when we die,
since death gives the gems to the killer.

**Implementation.**

- `tribute_gems` 35.
- `tribute_detour` 5 when no enemy has been seen within `threat_memory`, and 10 otherwise.
- Keep `threat_tribute_gems`.

**Test.** Race 30/35/40 vs v17, then gate.

### B49 Lock the altar we just used (rank 9, unconventional)

**Hypothesis.** Our lock blocks only enemy tributes (`GameRules.md:237`). Breaking it takes **5** basic attacks
(probe). Today we place a lock only when an enemy is already at the altar (`place_lock`, `bot.cpp:425-444`).
Placing it as we leave an altar costs one action and 10 gold. It also puts a 5-turn delay on every enemy carrier
that arrives while ours is not there.

**Evidence.** Rules and constants only. No top team is seen doing it (their lock purchases, 0-8 a game, match
ours). Treat it as an experiment.

**Expected effect.** +0.5-1.5 points (guess). It is larger on maps with one or two altars (the_pack, starfish,
boss_battle).

**Implementation.** In `take_turn`, after a tribute completes, place the held lock on that altar if it has no
lock. Restrict it to maps with at most 2 altars, or to altars nearer the enemy spawn than ours. `shop()` already
rebuys a lock at spawn.

**Test.** `gate.py --mode map --maps 02the_pack,01starfish,00gemfight` + nonreg.

### B50 Late-game spawn-tile denial (rank 10, unconventional)

**Hypothesis.** An occupied spawn tile stops a whole group from respawning (`GameRules.md:193`). The enemy then
cannot farm it, and neither can we.

- **Use case:** after r1200, when we lead on submitted gems, one body with nothing better to do (target rate
  below a floor, or a full bag waiting on a contested altar) parks on a spawn tile of the enemy's best
  near-spawn group.
- **Cost:** one body's farming.

**Evidence.** Rule only. Not seen in top play.

**Expected effect.** 0 to +1 point, and it could be negative. Low priority.

**Implementation.** In `choose_target`, when it returns -1 late with a lead, move to the spawn tile of the
largest group nearest the enemy spawn.

**Test.** Map gate on 2-3 maps with rich enemy-side groups.

### B51 Contest captures with `capture_state()` (rank 11)

**What is new.** The API now reports `enemy_capturing` for a group in vision, even when the capturing champion is
hidden (`cambc.h:4719`). Simon v5 contested on sight and found it neutral (48% on daniel/v5,
`bots/simon/docs/v5/summary.md:43-46`). Retest only after B41/B44 make fights and vision stronger.

### B52 Draft changes (rank 12)

Not recommended now (section 4). If tried: put Prism in 4-pick drafts only (0.64, n 88) with a gem-holding play
(carry to ~60 gems for +90 focus before banking). It is low priority until our HoR plays its kit.

### Ideas considered and dropped

- **Fuel-heavy planning on the first turn (2x) or in the draft (100x).** B33 found fuel exhaustion is 1-2% of
  turns and not decisive. The B19 cache removed the big-map freezes. No data shows a decision limited by fuel.
- **Team B tiebreak and gold-tiebreak play in general.** Only 2 of 24 v16 round-2000 games were level on gems,
  both 02guardians (B47 covers them).
- **New emblem families other than Prospector:**
  - Capture (3-turn capture) saves ~2 turns per capture, about 90 body-turns a game.
  - Tribute (33% shorter) saves ~30 turns a game.
  - Hunter is +50 gold a kill, at ~3-5 kills a game.
  - Skirmish and Collectors are +5% and ~+5% damage.
  - Greed needs 750 gold for 10 extra stat points over 25 shards.

  All are small next to B43. Capture could pair with B45, as one receiver captures faster.

## 6. Testing notes

- Local opponents (v12, Jame v3, our own lineage) do not reproduce the ranked failure modes. Backlog B14, B28 and
  B30 all needed ranked evidence. Gate each candidate against v17 **and** Jame v3. Watch the mechanism counters
  (HoR `dmg=`, gold@500, emblems by r500, wards placed) in local summaries, so that a neutral result is known to
  be "fired, no effect", not "never fired".
- Log each candidate as a backlog row (B41-B52) before testing it, as the cadence requires.
- Suggested order: B41 → B42(a) → B43 → B44, each gated on top of the last. The first two are the largest
  economy gaps and are independent of each other.

## Appendix: how the numbers were made

The scripts were throwaway Python run with stdlib only, kept outside the repo.

- **Phase table:** per team-game medians over `features.jsonl`. Our rows are deduplicated by match; scout rows by
  (match, team).
- **Event metrics:**
  - Tributes from `gemSubmission`.
  - Captures from `gemCollection` with context `campGroup`, receivers counted per (round, group).
  - Purchases from `buyItem` and `itemCombination`.
  - Wards from `wardPlacement`.
  - Map tiles and groups from `maps/ascii/<map>.txt`.
- **Gold curve:** the team sum of `championTimelines` `earnedGold` at rounds 250/500/1000.
- **Allies near a capture:** decoded timelines at the capture round (Chebyshev distance).
- **Engine facts:** a Python probe bot printing `cambc.ItemType(i)` metadata, `cambc.constants._SETTINGS`, and
  `cambc.me().abilities()` payloads for a Heart of Ruin, Vesper, Marcella, Vendetta, Ryth draft on 00rows
  (`cambc run <probe> bots/starter-python --map 00rows --rounds 3`).
