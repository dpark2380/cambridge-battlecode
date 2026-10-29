# Daniel bot changelog

One entry per version, newest first: the features added, bug fixes, tuning and tooling that came with it, how it
tested, and how it did on the ladder. The full write-up (hypotheses, rejected experiments, per-map tables) is in
`docs/v<n>/summary.md`. Open issues and planned changes are in `docs/backlog.md`. Update this file in the same
commit as any change to a bot.

Version folder ≠ team submission number: the platform counts every submission the team makes (see "Submitted").

## v18 resubmitted (2026-10-28 04:50Z as team bot version 18; ranked 27-23 until 06:29Z)
- v19 went 16-24 in ranked (#250 1650 → #282 1618) with less gold (4,162 vs 5,376), fewer camp clears (43.7 vs
  50.6) and more deaths (12.4 vs 9.6) than v18, while local gates had it level with v18 (B58). Back to v18, with
  the user's approval. If v18 also struggles at this rating, the drop was the opponents.

## v26 resubmitted (2026-10-28 20:47Z as team bot version 25, auto-revert)
- v28 went 14-21 in ranked (#196 1711 → #217 1688): gold 4,608 vs v26's 5,272, deaths 12.8 vs 11.8, opponents' gold
  5,130 vs v26's 5,646, so not a stronger field. Its panel (31-59 vs 27-63) did not carry over to ranked.

## v29 (from v28; dropped: built on v28, whose kiting was rejected in ranked)
- **B73 on v28:** Vesper treats a fight as even only when ours ≥ 1.3 × theirs (v27's rule on top of the kiting).

## v28 (from v26; submitted 2026-10-28 19:37Z as team bot version 24, overnight auto-submit; v26 closed 55-45; reverted 20:47Z at 14-21)
- **B78b Vesper kites:** with an enemy adjacent and her attack on cooldown, Vesper steps or dashes to a tile in range of
  her target and next to no enemy. Top-10 replays: their Vesper dies in 10% of healthy 1v1s (ours 28%) and is adjacent
  12% of contact rounds (ours 20%). Locally 50% vs v26; 79% vs v12, 91% vs Jame v3.

## v31 (from v27; submitted 2026-10-29 01:54Z as team bot version 27, user-approved; v27 closed 56-49)
- **B80 + B81:** v30's earlier leaving for Ryth/Marcella against pairs, plus the fight check's health-only clause only when
  our damage is ≥ 0.75× theirs (v25-v27: 33% vs Power stackers). Nonreg vs v27 50%, v12 76%, Jame v3 93%.

## v30 (from v27; not submitted)
- **B80 leave earlier against pairs:** Ryth and Marcella leave at 65% when 2+ enemies are within 5 (v27 ranked: 58% of Ryth's
  deaths had 2+ enemies that close, 63% of them on the walk home). Locally neutral (51% vs v27); 78% vs v12, 91% vs Jame v3.

## v27 (from v26; submitted 2026-10-28 22:22Z as team bot version 26, user-approved; v26b closed 22-28; ranked 56-49)
- **B73 Vesper needs a clear edge:** Vesper engages only when ours ≥ 1.3 × theirs. She dies in 38% of healthy ranked
  1v1s (v25) and 39% on v26's panel. Locally neutral (48% vs v26, nonreg borderline PASS).

## v26 (from v25; submitted 2026-10-28 16:15Z as team bot version 23, overnight auto-submit; v25 closed 59-51; ranked 55-45)
- **B68 who closes in:** Vesper does not close in, and no body closes in while outnumbered. From the panel death
  breakdown (Vesper healthy-1v1 deaths 25% → 42% and 3v1 deaths 48% → 74% after B64). Locally neutral (49% vs v25);
  66% vs v22, 90% vs Jame v3.
- **B70 Heart of Ruin health:** HoR buys 65% of its Bruiser shards as health (was 40%; top teams ~64%). Locally neutral
  (51%, nonreg 52%).
- **B71 dash escape:** a body leaving with an enemy close strikes, then retreats with its dash allowed (HoR used it only
  in fights; 85 of 122 ranked HoR deaths came alone, caught on a one-tile retreat). 58% vs v26-without-it, 58% vs v25,
  79% vs v12, 91% vs Jame v3.

## v25 (from v24; submitted 2026-10-28 12:35Z as team bot version 22, user-approved; v22 closed 36-24; ranked 59-51)
- **B54 alone:** a Monolith is struck only with min(team, 3) bodies within 6 of it (no B54b). 01corridors map gate
  68% (41/60) vs v24; nonreg 51%.

## v24 (from v23; not submitted)
- **B64 the gold squad fights:** Vesper, Marcella and Vendetta close in on the weakest enemy like the duo when the
  fight check says we are even or ahead (they only hit what was in range). 61% vs v23 (172/280), 64% vs v22,
  77% vs v12, 91% vs Jame v3, 94% vs hunter-v0.

## v23 (from v22; not submitted)
- **B62 don't walk home under attack:** with an enemy champion close, a leaving body shoots back (ranged, target in
  range) or retreats and strikes, instead of a recall that each hit cancels; the duo leaves at 50% health with an
  enemy in sight (was 75%). Race 61% vs v22 (255/420), gain gate 58% (163/280).

## v22 resubmitted (2026-10-28 10:40Z as team bot version 21, user-approved)
- Back from v18 after the scrim panel (B60): v22 16-44 vs v18 10-50 on the same 60 setups.

## v18 resubmitted again (2026-10-28 10:25Z as team bot version 20, auto-revert; replaced 10:40Z)
- v22 went 50-61 (#243 1656 → #284 1611), 7-21 in its last 28 with gold 4,335 vs 5,012 before, which meets the
  standing revert rule (user, 06:30Z). Its fixed scrim panel (`tools/scrim.py`) went 16-44; v18's panel is queued
  for a like-for-like comparison. Result: v18's panel went 10-50 (gold 4,180, clears 46.3) against v22's 16-44 (4,582,
  53.1). Paired by setup, v22 won 9 setups that v18 lost and v18 won 3 (48 the same), so v22's slump was the field.

## v22 (from v18; submitted 2026-10-28 06:29Z as team bot version 19; withdrawn 10:25Z at 50-61)
- v18 + B56 (monster-free groups at real cluster health). 02treasure-box map gate 65% (39/60) vs v18; nonreg 52%.

## v21 (from v20; not submitted)
- v20 with B54b reverted (gather rule for Monoliths only), plus B56. Nonreg vs v18 50%, vs v19 50%.

## v20 (from v19; not submitted)
- **B56 lone gem clusters at their real health:** a group with nothing that hits back is priced at 120 health per
  cluster, not the 500 effective. On 02treasure_box, 16 lone clusters sit around the altar; v19 cleared 10 groups to
  the opponent's 128 there. 02treasure-box map gate 65% (39/60) vs v19; nonreg 51%.

## v19 (from v18; submitted 2026-10-28 03:22Z as team bot version 17; withdrawn 04:50Z)
- **B54 Monolith siege needs company:** a Monolith is struck only with min(team, 3) bodies within 6 of it. A lone
  body chipping it kept it awake, and it killed our bodies at the camps beside it from behind walls (v18 ranked
  01corridors 0-3, 18-37 camp deaths a game). 01corridors map gate 62% (41/66) vs v18; nonreg vs v18 51% over 70 maps.
- **B54b same for every siege target:** 02harvest lone bodies died at the 2-golem centre group every ~100 rounds
  (v18 ranked 22 camp deaths there). 02harvest map gate 75% (45/60) vs v19-with-B54; nonreg 51%.

## v18 (from v17; submitted 2026-10-27 23:06Z as team bot version 16)
- Started 2026-10-27 13:00Z, from the research note `docs/research/strategy-options-2026-10-27.md` (our economy
  runs at half the top teams' from round 1: gold by r500 1,152 vs 2,427, emblems 4 vs 12).
- **B41 Heart of Ruin dash kit:** damage dashes are kept for fights, aimed at the tile covering the most targets
  around the current target, and counted in `measure_damage` (HoR camp damage 10,980 → 20,464 in one game).
- **B42 shop early:** one 150-gold shop threshold for every role (the duo waited for 300); a bag of ≤10 gems no
  longer blocks the trip when no enemy was seen for 10 rounds.
- **B43 Prospector first:** the first emblem is Prospector of our stat (+25% of our share of cluster rewards).
- **B44 wards:** each turn, a ready ward goes on the bush in reach nearest our target (no ally ward on it).
- **B45 one receiver:** with a reward waiting, an ally already on a spawn tile and no enemy seen, move on.
- **B49 own-altar lock:** right after our bag empties beside an altar, lock it (5 hits to clear).
- Races, each on the previous best: combo1 (B41a+B42a+B43) 57% vs v17 (B41a alone 54%, B43 54%, B42a 51%);
  B44 56% vs combo1; B45 54% and B49 54% (twice) vs B44. Rejected: B41b (HoR off the duo) 56% < B41a's lead,
  B48 bigger bags 52%.
- Gates: gain 200/280 = 71% vs v17; nonreg 210/280 = 75% vs v12, 231/280 = 82% vs Jame v3 (all PASS, data/stack2-gates.txt); gauntlet +346 [+315, +349] vs v17 +240, combo1 +292.

## v17 (from v16; submitted 2026-10-27 13:29Z as team bot version 15; ranked 127-134)
- Started 2026-10-27 10:05Z.
- **Fight fix (B37):** on 00oasis/02crossing top teams trade kills evenly (oasis 13 kills / 13.5 deaths); we
  died without killing (3 / 27) and took 2x their champion damage. When outmatched, bodies walked to spawn and
  ranged ones never shot. Now an outmatched body falls back toward the nearest ally (`retreat_to_allies` 0 → 1),
  and a ranged body with a target in range shoots instead of walking.
- Race vs v16: both 55%, shoot-back only 53%, fall back to ally only 49%.
- Gates: gain 162/280 = 58% vs v16; nonreg 182/280 = 65% vs v12, 216/280 = 77% vs Jame v3 (all PASS, data/b37-gates.txt).

## v16 (from v15; submitted 2026-10-27 07:52Z as team bot version 14; ranked 81-79)
- Started 2026-10-27 07:38Z.
- **Opening fix (B36):** the top-team benchmark showed our first camp clear is the largest gap on almost every map
  (z -2.41; 00elkring r49 vs r12). Bodies soloed camps: each scores its own rate with the value split by bodies
  and joiners valued at 0.45, so splitting always won. `extra_body_value` 0.4538 → 1.0, `max_group_bodies` 2 → 3.
- Races vs v15: cap only (mgb 3/5) 53%/50%; joiners at 1.0 with mgb 3/5 63%/60%.
- Gates: gain 165/280 = 59% vs v15; nonreg 173/280 = 62% vs v12, 218/280 = 78% vs Jame v3 (all PASS, data/b36-gates.txt).

## v15 (from v14; candidate, not submitted)
- Started 2026-10-27 07:20Z.
- **Bug fix (B34):** on 01boss_battle the only walkable tile beside the altar is a Monolith spawn tile, and
  v8 called gems undeliverable there, so carriers held 100-240 gems all game (v14 ranked 1-4, 0 gems in all
  five). Now, when no camp-free altar tile exists, that tile stays the tribute goal and the altar counts as
  walled in, so the B29 breach code kills the Monolith first. Other maps keep the old altar tiles.
- Local 01boss-battle seed 0: 656:0 vs v14 (v14 0:0). Rejected: whole-team-only Monolith strike (0:0).
- Gates: map 01boss-battle 59/60 = 98% vs v14 (PASS); nonreg 138/280 = 49% vs v14, 142/280 = 51% vs v12, 183/280 = 65% vs Jame v3 (all PASS).

## v14 (from v13; submitted 2026-10-26 23:06Z as team bot version 13)
- Started 2026-10-26 15:20Z.
- **Bug fix (B29b):** in ranked 02the_pack (v13, match 611f181c) all three carriers waited inside
  `corridor_gather` from r221 to r2000 and never struck: `breach()` counted allies within 3 tiles of the body
  itself, and the team stood up to 4 apart. It now counts allies standing anywhere in `corridor_gather`.
- **Gates** (`data/b29b-gates.txt`): map 02the-pack 32/60 = 53% vs v13 (FAIL: local carriers usually bunch);
  nonreg 50% vs v13, 51% vs v12, 66% vs Jame v3 (280 games each, PASS). Zero-gem games on 02the-pack: v13 13/44,
  v14 9/44. Remaining 0:0 games: B29c.

## v13 (from v12; submitted 2026-10-26 10:58Z as team bot version 12; ranked 189-176, peak #273 1615)
- Started 2026-10-26 06:50Z.
- **Bug fix (B29):** 02the_pack's only altar sits inside a 48-wolf ring; carriers found no path and stood at the
  ring all game (v12 ranked 0:0, lost on gold; every local game 0:0). At init, when every walk from our spawn to an
  altar crosses a camp, a 0-1 BFS (one kill per camp tile, on local grids: bitboard reads are engine calls) picks
  the corridor to cut (on the_pack, one wolf by a diagonal). A carrier whose altar walk fails waits within 3 tiles
  of it and hits once 2 allies are within 3 (damage wakes the whole ring). Only the_pack sets the flag (all 70
  maps probed).
- Gates: map 02the_pack 51/60 = 85% vs v12 (pass); nonreg all maps 51% vs v12, 57% vs v11, 66% vs Jame v3 (all pass).

## v12 (from v11; submitted 2026-10-26 05:45Z as team bot version 11; ranked 87-68, peak #331 1563)
- Started 2026-10-25 23:15Z for the sprint 3 maps.
- **Feature (B25, accepted):** draft the top-20 core in order, Vesper > Heart of Ruin > Marcella > Vendetta > Ryth,
  map scoring for the rest. Heart of Ruin added to the draft roster (it was never draftable). Marcella and Heart of
  Ruin buy focus shards. Real drafts, 70 maps x 2 sides: 77% vs v11, 79% vs v10, 81% vs v9, 79% vs Jame v3 (v11:
  66%). Without the focus builds: 67% vs v11.
- **Tooling:** `tools/targetmodel.py` (B26), a choice model of which group a champion takes next, fitted to top-team
  and our ranked decisions; `tools/openings.py --export` writes the opening-script table (B24).

## v11 (submitted 2026-10-25 23:14Z, team bot version 10)
- **Tooling:** `draft.cpp` reads `experiment_seed.h` when it exists. `tools/arena.py` writes that header into a
  copy per seed, so random-draft test games run at the real 100k fuel (T1). The same inert hook was ported back
  into v9 and v10 (2026-10-25 18:35Z; nothing changes without the header) so that gates against them also run at
  100k. Without it, a pairing with v10 fell back to the 1M fuel quantum, and the first B19 map gate (52%, failed)
  never saw the freeze it was testing.
- **Bug fix (B19, accepted):** `choose_target` reuses its walking-distance field from our position until we move
  3+ tiles or 10 rounds pass (it cost ~40k fuel a turn on the 100×100 01big_world). big_world vs Jame v3 at 100k:
  fuel-exhausted turns 2,499 → 170 (side A) and 5,972 → 135 (side B); both games go from losses (464:868,
  0:866) to wins (965:843, 1,021:765). The claim/target mismatch was a side effect of turns cut short by fuel.
  Gates at 100k: map mode vs v10 on big-world/ambush/lanes 67% (big-world 17/20); nonreg vs v10 51%, vs v9 60%.
- **Feature (B21, accepted 2026-10-25 20:40Z):** after the Monster and Durability emblems, buy Bruiser shards
  instead of Power (same 40% health split). A Bruiser emblem is 5 of the stat plus 1 of each other, 7 shards'
  worth against Power's 6; the top 20 buy mostly Bruiser (Vesper ~66 Bruiser shards a game vs 11.5 Power).
  Gates at 100k: gain vs v11 135/240 = 56%, gain vs v10 95/160 = 59%; nonreg vs v9 100/160 = 62%, vs Jame v3
  98/160 = 61%. The no-split variant raced 40/80 vs 42/80.
- **Rejected:** a dominant-Monolith value multiplier (B20; x1.5/x2/x3 on rows, corridors, contest, gold-rush:
  22%/11%/9% vs v11; early sieges it cannot finish).
- **Rejected:** lower `max_damage_share` (B17+B18): 1.5 and 2.0 win elkring 57-62% but lose islands ~35% vs v11.
- **Rejected:** build order Treasure > Durability > Power (B11, 51% over 800 games vs v11); late gold-weight decay
  (B15, 50% over 480; a sharp drop after round 500 scores 44%).

## v10 (submitted 2026-10-25 12:54Z, team bot version 9; ranked 143–137, rating 1495 → peak 1542 → 1513)
- **Feature:** also take a fight when behind on health but ahead on fighting power: health × damage, where damage
  is the larger of strength and focus (`fight_enemies`). Variants tried: power only 52% vs v9, power *and* health
  43%, power *or* health 57% (kept).
- **Results:** 57% vs v9 (228/400), 59% vs Jame v3 (v9: 55%), 66% vs v8, 76% vs v7, 89% vs Simon v6, 86% vs
  hunter-v0. Drops packs to 3/10 vs v9 (backlog B7).

## v9 (submitted 2026-10-25 10:16Z, team bot version 8; replaced at 12:54Z)
- **Bug fix:** pathing blocks camps known to be alive even when out of sight. Carriers on 01the_farm oscillated
  beside a wolf camp for 1500 rounds (ranked 1–9) (`move_towards_closest`).
- **Feature:** 40% of Power shards are bought as health (`power_health_share`); 25% and 55% tested worse or equal.
- **Rejected:** two stampede siege tweaks and a Golem siege wait (see v9 summary).
- **Results:** 69% vs v8 (277/400), 55% vs Jame v3 (v8: 39%), 78% vs v7, 93% vs Simon v6, 86% vs hunter-v0.
- **Ranked:** 47–33 (59%) over 80 games; rating 1453 → 1486, rank #461 → #421.

## v8 (week 2 patch port)
- **Port:** camp table for the week 2 patch: the Golem (5,000 health, range 4), camp attack ranges per kind,
  gem and gold clusters planned at an effective 500 health.
- **Features:** Monolith leave rule and siege gate; gold-only play on maps where no altar can be reached
  (01boss_battle).
- **Bug fix:** build tables sized for 13 champion types (Heart of Ruin), so a random missed pick can't index out
  of bounds.
- **Results:** 61% vs v7, 84% vs hunter, 73% vs Simon v6, 43% vs Jame v3.
- **Ranked:** 159–171 (48%) over 330 games.

## v7
- **Bug fixes:** the stall check uses walking distance (218 false give-ups on pilgrimage). Champions respond to
  unseen attackers in bushes.
- **Features:** siege any group too big for two bodies; carriers recall at 50% health while enemies are near.
- **Results:** 59% vs v6; 72% vs Simon v5.
- **Ranked:** 56–44 on the week 2 engine.

## v6
- **Features:** Monolith sieges (damage carries over between trips); gold weight 0.10 → 0.20.
- **Results:** 62% vs hunter (v5: 52%); 61% vs Simon v5.
- **Ranked:** 28–26.

## v5 (team bot version 5)
- Simon's v4 with self-play-tuned constants and the random-draft experiment hook.
- **Results:** 63% vs Simon v4.
- **Ranked:** 18–47.

## Earlier
- v4 (`v5-dp`), v3 (`v4-dp`), v2 (`main-v2`), v1 (`main-v1`): see `docs/README.md`.
