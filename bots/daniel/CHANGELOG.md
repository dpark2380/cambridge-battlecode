# Daniel bot changelog

One entry per version, newest first: the features added, bug fixes, tuning and tooling that came with it, how it
tested, and how it did on the ladder. The full write-up (hypotheses, rejected experiments, per-map tables) is in
`docs/v<n>/summary.md`. Open issues and planned changes are in `docs/backlog.md`. Update this file in the same
commit as any change to a bot.

Version folder ≠ team submission number: the platform counts every submission the team makes (see "Submitted").

## v76 (2026-11-07, not submitted)

- v75 + B201: fuel fixes with no decision change. Wards wait 50 rounds after a failed placement (out of charges, every turn threw at ~7k fuel); fight_enemies returns before reading allies when no enemy is visible (~8k a turn). (B203, a ward back-off with no bush in reach, was removed before submission: 72% vs 77% on big maps.)
- From ranked: 04orchard ran out of fuel ~185 times in rounds 0-250 (opponent ~1), 0 gems by r300-r500.
- Gates: vs prof-aynir on 44 big maps 77% (v75 73%, same setups); nonreg vs v75 PASS. A slower target-field refresh (full B201) cancelled the gain and was dropped.

## v75 (2026-11-07)

- v74 + B198: a body carrying 150+ unspent gold weights gold at 0.3× in target value. From v74's ranked breakdown: 04* maps 30-43, with 04orchard/04wheel banking nothing until r300-r500 while farming gold.
- Gates: arena on 42 04* maps 55% vs v74; gain vs v74 PASS 54% (512), gems +23 ± 21.
- Submitted 02:51Z 7 Nov as team bot version 92.
- Rejected: B199 lone-Monolith value ×1.5 (39% on lone-Monolith maps).

## v74 (2026-11-06)

- v73 + B193: eight constants tuned together by `tools/tune.py` (max_damage_share 4.04 → 4.90, help_wait_turns 50 → 40, gold_weight 0.30 → 0.233, recall 0.40 → 0.42, carrier recall 0.50 → 0.52, spawn leave 0.95 → 0.94, extra_body_value 1.0 → 1.12, threat bag 20 → 19).
- Gate: gain vs v73 PASS 59% (512), gems +64 ± 20, captured +69 ± 17, deaths −0.9.
- Submitted 18:27Z 6 Nov as team bot version 91 (live 18:32Z). Panel v74p1 57-33, the best on engine 3 (v73p1 56-34, v71p1 56-34). Later tune rounds on v74 (B194-B196) found no further step. Ranked 80-70 over its first 150 games (53%); ladder 1746 #217 at 23:36Z.
- Rejected on v73 before it: B184c 5 bodies, B185 extra body value alone, B186 siege value, B187 detour 6 / stall 20, B188 Vesper recheck, B190 siege bodies / Monolith gather, B191 bag 30/42, B192 Cassi & Issac.

## v73 (2026-11-06)

- v72 + B183 + B184: max_group_bodies 3 → 4 (gain PASS 54% vs 3, gems +35 ± 16). B183: gold_weight 0.2 → 0.3 (target value = gems + weight × gold). vs v72: gems +44 ± 14, deaths −2.2 ± 0.3, gold +900 at a flat 51% mirror win rate; 0.25 similar, 0.4 and 0.12 worse.
- Gates: nonreg vs v71 PASS 54% (512), gems +50 ± 20, deaths −2.4 ± 0.4, gold +986. v72 was never submitted on its own.
- Submitted 2026-11-06T16:29:20Z as team bot version 90 (live 16:32Z). Panel v73p1 56-34 (= v71p1), gold +570 (z 2.8), deaths −1.1, their deaths +1.6 (z 2.6): kept.

## v72 (2026-11-06)

- v71 + B180: bodies heal to 95% at spawn before heading out (was 0.7716 from a v5 tune). vs v71: 52% over 3,328, gems +22.5 ± 7.8, captured +16 ± 7.
- Tried and dropped: B181 engage edge 1.4 (stacked, gems +3 ± 11 vs v71), B182 threat memory 50 / help wait 30.

## v71 (2026-11-06)

- Submitted 15:04Z 6 Nov as team bot version 89 (live 15:12Z). Panel v71p1 56-34 (v70p1 52-38, v69p1 53-37). Ranked 20-15 while live.
- v70 + B178: carriers under threat leave at 50% health (B121's 65% → 50%). Gain PASS vs v70, 53% over 1,536, captured +32 ± 10; 0.8 was 35%, 0.4 no better than 0.5.
- B179: every body goes home at 40% health, not 28.8% (v23). 53% over 3,328, deaths −1.5 ± 0.2, gems +28 ± 8; 0.5 was worse.
- Rejected on v70: B176 Ryth health soak (51%), B177 tribute detour 15 (48%).

## v70 (2026-11-06)

- v69 + B170: five-pick drafts take Vendetta for Vesper (Marcella, Heart of Ruin, Vendetta, Ryth, Varg); no draft takes Vesper now. B171c: four-pick drafts take Varg for Vendetta (60% on four-pick maps, nonreg 52%). B175: carriers bank from 20 gems for 30 rounds after seeing an enemy (52% over 3,328, gems +22 ± 8).
- Submitted 13:31Z 6 Nov as team bot version 88 (live 13:42Z). Panel v70p1 52-38, neutral vs v69p1 (53-37). Final v70 vs v69 nonreg 54% (512), gems +48 ± 20.
- Gates vs v69: arena on five-pick maps 57% (324); nonreg PASS 54% (512); gain PASS 54% (768), gems +30 ± 15, deaths −0.7. Rejected on the way: B169 bag 28, B170b (Vendetta for Marcella, 39%).

## v69 (2026-11-06)

- v68 + B167: four-pick drafts take Vendetta for Vesper; five-pick drafts take Varg for Vendetta. B168: Varg buys Vendetta's order (Prospector, Durability, Jungle, then Bruiser) instead of Treasure first (arena 55% on five-pick maps, nonreg 53%).
- Submitted 12:00Z 6 Nov as team bot version 87 (live 12:12Z). Panel v69p1 53-37: vs v68p1 wins 48 → 53, margin +115 ± 59.
- Gates vs v68: nonreg PASS 53% (512); gain inconclusive at 53% over 3,328 games, submitted gems +48 ± 7, captured +57 ± 7, deaths −0.5 ± 0.2; profgate +11 ± 32. Rosters rejected on the way: B165a-c (3 picks), B166a/b (Willow, Prism).

## v68 (2026-11-06)

- v67 + B164: three-pick drafts take Heart of Ruin, Ryth, Marcella (Aynir) instead of Vesper, Heart of Ruin, Vendetta. Found with `groupgap.py` (04compass, 04standing_stones) and arena against the profile bots.
- Gates vs v67: arena on the 21 three-pick maps 62% (126 games); profgate +40 ± 23; nonreg PASS 52% (512), gems +30 ± 19.
- Team bot version 86, live 11:12Z 6 Nov; panel v68p1 48-42, neutral vs v67p1 (+19 ± 26). Replaced by v69 (version 87) 12:00Z.
- Rejected on the way (backlog): B157 Aynir soak settings, B159 Jungle first for all, B160/B162 Cassi & Issac (our play dies 8-11 more a game), B161 forced pairs (−323), B163 top-10 build grafts. New tools: `tools/fights.py`, `profiles.py extract --scout`.

## v67 (2026-11-06)

- v66 + B156: meowest's shop order (no Treasure; Jungle/Prospector/Durability, then Bruiser with no health), a 36-gem bag, and its 3- and 4-body drafts, from `src/profile.h` (generated by `tools/profiles.py build --prefix/--only`, new options).
- Profgate vs v66: margin +65 ± 41, deaths −1.3 ± 0.5; build + bag alone +31 ± 33, deaths −1.6 ± 0.4. Rejected on the way: B155 Power soak (−23 ± 12).
- Gates: nonreg vs v66 PASS 53% (512), deaths −1.7 ± 0.4, gems captured +28.5 ± 16.
- Submitted 2026-11-06 10:02Z as team bot version 85 (live 10:12Z). Panel v67p1 vs v64p3: 44 vs 41 wins over 84 paired, deaths −2.1 (z −2.4), margin +45 ± 59: better, kept.

## v66 (2026-11-06)

- v64 + B153: a gem-less group's gold counts up to 150 in the target value. On the new 04lines, 31-cluster gold walls (620 gold, 0 gems) rated 124 against 11-19 for gem groups; both teams farmed gold all game (11-0 at r2000).
- Platform: engine 3.0.0 since 2026-11-04 23:00Z (cambc/SDK 5.0.0, 42 new 04* maps); local tools upgraded 6 Nov 07:30Z. v65's panel (engine 3.0.0) vs v64p2 (2.0.0) is not a fair comparison; v64 re-uploaded 07:23Z as version 83 and re-paneled as v64p3.
- Gates vs v64 (engine 3.0.0): 04lines 8/8 (+872), 04orchard 7/8 (+322); nonreg PASS 50% (512); profgate +4 ± 4.

## v65 (2026-11-06)

- v64 + B152: Heart of Ruin engages only with a 1.5x power edge. Ranked per 1000 rounds, our HoR deals 6.0k champion / 8.6k camp damage against the opponents' HoR 4.3k / 12.7k, and dies 2.5 vs 1.6.
- Rejected on the way (profgate vs v64): B150 bigger bags (−17, −56), B151 HoR strength build (−134).
- Gates: nonreg vs v64 PASS 50%; profgate −8 ± 23 (blind to fight changes).
- Submitted 2026-11-06T06:20Z as team bot version 82 (live 06:32Z). Fair test on engine 3.0.0 (v65p2 vs v64p3, paired 90): wins 44 → 39, margin −50 ± 33, gems −42 ± 22 (z −2.0), deaths −0.3 ± 0.5; the first comparison against v64p2 (engine 2.0.0) was invalid. **Rejected**; v64 re-uploaded 07:23Z (version 83). v64 itself fell from 51 wins (v64p2, engine 2.0.0) to 44 (v64p3, engine 3.0.0). User 06:10Z: "Try carrier safety, and more trials" (carrier losses turned out not to be a gap: 14.7 gems a game vs the opponents' 27).

## Ranked check, v62-v64 (2026-11-04T10:20Z)

- Ranked 03:01-10:20Z 4 Nov (145 games): v62 20-15, v63 16-19, v64 33-47; overall 65-80, rating 1713 → 1659. On maps none of v62-v64's changes touch the line falls the same way (v62 16-13, v63 13-15, v64 28-35), so the drop is the field (the morning pool, B135), not the changes; changed maps under v64: Golem rings (B143) 1-5, islands (B145) 3-4, early fixes (B137-B140) 1-3; 03fan 1-1 (won 1011:164), 00gem_fields 1-0, 00dunes 2-0, 00crater 2-1, 03riverbed 0-3. Held; not reverted (too few games per changed map).

## v64 (2026-11-04)

- v63 + B145: Teleport Crystals. Groups of 20+ gems whose approaches our spawn cannot reach on foot, with 5+ shore tiles within range 3, are priced as walk-to-shore + 4; bodies buy a crystal on such maps, teleport onto an approach and recall home after the capture.
- Gates vs v63: gain on the 4 island maps PASS 67% (72; quadrants 14/18, big-world 15/18); nonreg PASS 51% (516).
- Submitted 2026-11-04T06:40Z as team bot version 81 (live 07:20Z). Panel v64p2 vs v60p2 (paired, 80 of 90 synced): wins 46 → 51, margin +72 ± 48, gems +45 ± 23, gems r500 +13 ± 5, captures +1.8 ± 0.8, deaths −0.4 ± 0.5: neutral by §1.6 (margin z 1.5) with the early game and captures up; kept (team bot version 81, live 07:20Z).

## v63 (2026-11-04)

- v62 + B143: the ring fallback also for a lone Golem ringed by clusters (02cuts G16/G17: 1 Golem in 6 clusters, 78 gems; ranked 3-17; same shape on 7 more maps).
- Gates vs v62: gain on the 8 maps PASS 57% (80); nonreg PASS 54% (344), gems +37 ± 27.
- Submitted 2026-11-04T03:57Z as team bot version 80.

## v62 (2026-11-04)

- v61 + B140: B137's approach fallback also for a monster target when the group deals at most one elk's damage: the 71-gem groups of 00gem-fields (1 elk in 8 clusters beside each spawn) and 01concentrated-wealth (1 elk in 20 clusters) were skipped as unreachable (ranked 1-11 on each).
- arena vs v61: gem-fields 12/14 (+229), concentrated-wealth 11/14 (+220), the-front 7/14; nonreg PASS 50%; profgate +0.6 (panel maps unchanged).
- Whole stack vs v51 (gain gate, mirror, 516 games): 51%, gems +2 ± 22. The fixes touch ~5 of 86 maps and mirror games cannot show bugs both sides share, so this is not a verdict. Version 79 live 03:01Z (v61 = version 78 never went live).

## v61 (2026-11-04)

- v60 + B139: the target rate's gold weight drops to 0.01 when the map's gold is worth 10x all its gems (only 03one-gem: one 7-gem cluster, 1,600 gold; ranked 0-5, our gems 1 vs 129 because a 60-gold group always outrated the cluster).
- arena vs v60: 03one-gem 10/10 (+215), other maps identical. Uploaded while v60's panel ran (same play on panel maps).

## v60 (2026-11-04)

- v59 + B138: in `move_towards_closest`, when no path reaches free goals (approaches, altar, spawn), path through the camps and strike the first one in the way (never a Monolith or Golem). On 03fan each spawn quarter is sealed by camps: ranked 1-9, 0 gems in 7 games; the bodies stood at spawn all game.
- Gates: vs v59 03fan 18/18 (+1,011), 02tangle 9/18; nonreg PASS 51% (344).
- Submitted 2026-11-04T02:39Z as team bot version 77. Panel v60p2 vs v59p2 (paired, 90): 89/90 identical outcomes, wins 53 → 52, margin −2 ± 6, deaths +0.06 ± 0.05: neutral as expected (03fan is not a panel map); kept. Versions 78 (v61) and 79 (v62) went live during the panel's last games; they play the panel maps the same way. The first version without the free-goal condition lost 02tangle 3/18 (cut through clusters to the Golem).

## v59 (2026-11-04)

- v51 + B137: in `work_group`, when the chosen cluster's tile has no path (00vault: clusters seen through the holes, walled in by their own group), walk to the group's approaches and strike any member in reach instead of standing still until `stall_turns` gives the group up. Monster targets are unchanged (the same fallback for them lost 03the-front 5/18).
- Gates: profgate vs v51 margin +81 ± 32, deaths −0.6 ± 0.3; nonreg vs v51 PASS 50% (344); vs prof-meowest on 00vault, gems captured 391 → 1,053.
- Submitted 2026-11-04T01:27Z as team bot version 76. **Panel v59p2 vs v51p2 (paired, 90):** wins 46 → 53, margin **+68 ± 35** (z 1.9), gems captured +37 ± 21, gems/capture +1.9 ± 1.0, gems r500 +20 ± 12, opponents' gold −246 ± 104, champion damage done −2.4k ± 1.2k; 00vault 0-6 → 3-3 (gems captured 305 → 772, r500 190 → 509). Neutral by §1.6 (z < 2) with every economy metric up and the early game not worse: **kept** (team bot version 76).
- Intl qualifier snapshot (3 Nov 23:59Z) entered v51 = team bot version 75; seeded at #227, 1711 (01:07Z 4 Nov). Trials resumed on the user's "Yes resume" (01:10Z).

## v51 re-uploaded (2026-11-02T12:54Z as team bot version 75, revert of v58)

- v58's panel (`v58p2` vs `v51p2`, paired): wins 46 → 40, gem margin −95 ± 53 (z −1.8), gold −456 ± 262, opponents' gold +481 ± 257, deaths +0.8 ± 0.8, kills −1.3 ± 0.8; walking-home share of deaths 48% → 45% (opponents 29-33%). Neutral by the rule but every metric leans negative and the target barely moved: **B136 rejected**. A detour around enemies costs farming time and leaves the gold to them; the walking-home deaths are not caused by the route. Ranked 11-9 over 20.

## v58 (2026-11-02)

- v51 + B136: `retreat()` walks home around visible enemies (tiles within 2 of an enemy are walls for that path; falls back to the direct route). 46% of our panel deaths happen walking home, the opponents' 30%.
- Gate: nonreg vs v51 PASS 51% (344 games on 86 maps, including the 16 new `03*`/halloween maps pulled 11:30Z); deaths +0.3 ± 0.6.
- Submitted 2026-11-02T11:41Z as team bot version 74 (user: "improve rating", 11:20Z). Ladder #229 1696 at 11:40Z; v51 76-68 over 145 since 05:21Z.

## Trials of 2026-11-01 23:35Z – 2026-11-02 07:15Z (summary)

User: "Do new trials" (23:35Z), "keep going" (00:05Z). **Live at the end: v51 = team bot version 73** (re-uploaded 05:10Z).

| Version | Change | Paired panel vs base | Ranked | Outcome |
|---|---|---|---|---|
| v52 (66) | B131b gold weight 0.5 before r500 | vs v51p2: wins 46 → 51, gold +555 ± 332, margin +70 ± 64, **gems r500 −47 ± 10** | line 61-79 over 155 | kept on the panel, **reverted 05:10Z on ranked** |
| v53 (67) | B133a Monster-first build on cluster maps | vs v52p2: gems captured −28 ± 13, vault 477 → 225 | 11-9 / 20 | rejected |
| v54 (69) | B130b skip a group 150 rounds after dying there | vs v52p2: **margin −113 ± 45** | 4-16 / 20 | rejected |
| v55 (71) | B133b four bodies on cluster-only groups | vs v52p2: 87/90 identical, margin +8 ± 16 | 6-14 / 20 | neutral |
| v56 (72) / v57 | B134 Vesper receives gold captures | not panelled; on v51 the gate deltas were negative | — | parked |
| — | B131 gold 0.5 all game; B131c window 300 | local: gems captured −72 ± 17; gold −282 ± 121 | — | rejected locally |
| — | B132 teleport to island groups | built; the pond needs teleport + two dashes | — | parked |

Ladder: #192 1745 (23:31Z) → high #189 1750 (02:26Z) → #264 1660 (05:42Z) → #251 1671 (07:13Z). v51 since its re-upload:
26-28 over 55. B135: from ~02:30Z every version lost on gems to a pool of ordinary ~50% teams (11 of 17 opponents new
to us, teams we used to beat now beating us), so part of the slide is the field at this hour, not the bots; scouting
them found nothing new to copy. Lessons (process review addendum): a panel-neutral change with a large early-game swing
needs ≥100 ranked games before anything is stacked on it; skipping or redistributing work around contested groups
(B130b, B133b) hands them to the opponent.

## v51 re-uploaded (2026-11-02T05:10Z as team bot version 73; the v52 line reverted)

- Ranked since the v52 switch (23:52Z, rating 1745): **61-79 over 155 (39%)** across v52/v53/v54/v55/v56 windows, against v51's 79-71 (53%) over its 150; ladder 1750 (02:26Z) → 1673 (05:04Z). The v52 panel (+5 wins, gold +555, margin +70 ± 64, **gems r500 −47 ± 10**) did not generalise: the ranked field punishes the slower first 500 rounds. B131b rejected in ranked; v53 (B133a) and v54 (B130b) were already rejected on the panel; v55/v56 (B133b, B134) are rebased on v51 for a fresh gate. Lesson for the process review: a panel-neutral change with a large early-game metric swing needs a ranked check at ≥100 games before stacking on it.

## v56 (2026-11-02)

- v55 + B134 (review H9): when a group's reward is waiting, no enemy was seen for 30 rounds, the group carries gold and a Vesper ally is within 3 of its tiles, a non-Vesper body steps beside the tiles and skips the group 10 rounds so Vesper (+20% gold, +40% with Treasure) takes it.
- Gate: nonreg vs v55 PASS 52% (280); A − B per game gold +250 ± 243, gems +16 ± 30, deaths −0.1 ± 0.7.
- Submitted 2026-11-02T05:04Z as team bot version 72. After its verdict, live trials pause for ~2 h on the best bot.

## v55 (2026-11-02)

- v52 + B133b: a group with nothing that hits back may take 4 bodies instead of 3 (B133: 00vault's 49-cluster block is a kill-speed race; the 4th body idled on 4-gem wolf groups).
- Gate: nonreg vs v52 PASS 49% (280); deltas ~0 (few maps affected).
- Submitted 2026-11-02T03:50Z as team bot version 71. Ladder #225 1700 at 03:50Z (v53/v54's trials cost ~50 rating; v52 was live again from 03:34Z).
- 05:03Z: panel `v55p2` vs `v52p2`, paired: 87/90 identical, margin +8 ± 16, deaths 0.0 ± 0.1, gold −107 ± 78; galaxy 824 → 862 gems captured (3-3 → 4-2), vault 477 → 411 (their 931 → 1,215), adgato2 948 → 958. Neutral, kept as the base (it is v52 on 12 of 15 maps). Ranked 6-14 over 20; ladder #241 1679 at 04:49Z.

## v52 re-uploaded (2026-11-02T03:34Z as team bot version 70, revert of v54)

- v54's panel (`v54p2` vs `v52p2`, paired): **gem margin −113 ± 45 (z −2.5)**, gems −63 ± 25, gems captured −49 ± 22, gold −370 ± 240, deaths +0.0 ± 0.7, wins 51 → 42 (net −9). Ranked 4-16 over 20, rating 1750 → 1716. **WORSE: B130b rejected** — a body that skips its target for 150 rounds after a death hands the group to the opponents more often than it avoids a second death. v55/v56 rebuilt on v52 without it.

## v54 (2026-11-02)

- v52 + B130b: a body back at spawn with full health after a death, whose last alive position was within 8 of its target group with an enemy seen within 30 rounds before, skips that group for 150 rounds (this body only). B130: on 00eight our bodies walked straight back to the contested 2-elk group where 12 of our deaths a game happen.
- Gate: nonreg vs v52 PASS 50% (420); A − B per game deaths −0.6 ± 0.7, gold +152 ± 210, gems +2 ± 23.
- Submitted 2026-11-02T02:22Z as team bot version 69.

## v52 re-uploaded (2026-11-02T02:04Z as team bot version 68, revert of v53)

- v53's panel (`v53p2` vs `v52p2`, paired; 86/90 games identical, only the three cluster maps changed): gems captured −28 ± 13 (z −2.1), gem margin −26 ± 24, wins 51 → 49; on its target maps 00vault 477 → 225 gems captured a game (1-5 from 2-4), adgato_gemcombat2 948 → 774, 00galaxy 824 → 834. The Monster-first build (no Jungle, Treasure third) loses the kill-speed race it was meant to win. **B133a rejected**; v53 ranked 11-9 over 20. v54/v55 rebuilt on v52 without it.

## v53 (2026-11-02)

- v52 + B133a: on maps whose draft plan has `free_share` ≥ 50% (half the gems in groups that do not hit back: 00vault 96%, 00galaxy 93%, adgato_gemcombat2 100% on the panel) the build is Monster, Prospector, Treasure, Durability, then Bruiser (no Jungle). B133: 00vault's 343-gem block is a kill-speed race we lose (0.7× vs 4.0× captures, 26k vs 36k monster damage).
- Gate: nonreg vs v52 PASS (3 of 70 maps affected; deltas ~0).
- Submitted 2026-11-02T00:54Z as team bot version 67.

## v52 (2026-11-01)

- v51 + B131b: camp groups' gold is weighted 0.5 before round 500 (0.2 after, as before). From the v51p2 panel: the opponents re-farm the wolf + gold groups on their own half ~10× a game, we take ours 0-2× (00collision, 00galaxy, 00interlock, 01big_world), ~600 gold a game per group.
- Gates: nonreg vs v51 PASS 54% (280), A − B per game gold +687 ± 238, deaths −1.4 ± 0.7, gems +26 ± 29. The all-game 0.5 variant failed (45%: gold +1,691 but gems captured −72).
- Submitted 2026-11-01T23:48Z as team bot version 66 (user: "Do new trials", 23:35Z). Ladder #192 1745 at 23:31Z.
- 00:53Z 2 Nov: panel `v52p2` vs `v51p2`, paired: wins 46 → 51, gem margin +70 ± 64, gold +555 ± 332, captures +2.5 ± 1.5, deaths −0.2 ± 0.9, gems r500 −47 ± 10 (the gold detour before r500); vault 0-6 → 2-4, galaxy 1-5 → 3-3. Neutral by the rule, not worse: **kept as the base**. Ranked 11-9 over 20.

## Night of 2026-11-01 (summary, written 21:30Z; ranked and ladder figures as of 23:25Z)

**Live in the morning: v51 = team bot version 65** (v48 + B127 + B128a + B129; live since 18:21Z). It is the first candidate
judged *better* than its base by the new rule: paired panel vs v50, deaths −0.94 ± 0.43 (z −2.2), gem margin +20 ± 32,
gems at r500 +6.8 ± 3.4, champion damage taken −1.7k ± 1.2k, wins 41 → 46; a confirmation panel replayed it 90/90.
Fallback: v50 = version 64 (`bots/daniel/v50`).

**Process (docs/research/process-review-2026-11-01.md, adopted 14:00-14:35Z):** every instrument we had was blind to
1-3 point effects, half the scrim panel could not move (0-405 vs the #1 team, 15-17% maps), and all 23 ranked verdicts
since v19 were below power. Now in use: `tools/panelcmp.py` (paired Δ ± SE per opponent/map/side for margin, deaths, gold,
captures, gems captured, gems/capture, bags, first emblem, damage), `tools/captures.py` (per-map capture lists ours vs
theirs), economy fields in `tools/features.py`, A − B per-game deltas in `gate.py`, panel v2 (`scrim.py`: six ~50%
opponents, four dead maps swapped for 50-56% ones; runs labelled `vNNp2`), ranked-like seeded rosters in `random_team`
(v49 on), and the §1.6 rule: better / worse / neutral on paired metrics, never on W-L flips inside ±9 or ranked windows
under 200 games, revert only on rating −100. Found on the way: the panel is fully deterministic within the hour
(v49p2 = v48p2 and v51p2b = v51p2 game for game), so a candidate's panel is an exact measurement on its 90 setups.

| Version | Change | Paired panel vs base | Ranked (window) | Verdict |
|---|---|---|---|---|
| v48 (62, 13:32Z) | B126b Treasure/Prospector/Durability/Jungle emblems before Bruiser | panel v1 vs v47: gold +582 ± 165, gold/clear +7 ± 3, kills +1.1 ± 0.5, margin 0 ± 50, deaths +0.7 ± 0.8 | 14-25 over 40 | neutral, kept (gold pays) |
| v49 (63, 16:03Z) | B127 HoR leaves at 50% with an enemy in sight | v49p2 = v48p2 game for game (90/90) | 8-12 over 20 | no-op |
| v50 (64, 17:12Z) | B128a camp exposure priced one monster at a time | vs v49p2: margin +12 ± 41, deaths +0.1 ± 0.7, gems/capture +1.07 ± 0.39, gems r500 +12 ± 4, captures −4.9 ± 1.2, gold −304 ± 204 | 13-7 over 20 | neutral, kept |
| v51 (65, 18:21Z) | B129 camp-damage-aware leave at every monster group | vs v50p2: **deaths −0.94 ± 0.43, margin +20 ± 32**, gems r500 +6.8 ± 3.4, camp deaths 1.83 → 1.54/game, wins 41 → 46 | 79-71 over 150 (23:25Z) | **BETTER**, kept |

Panel v2 baseline (`v48p2`): 44-46, every opponent between 6-9 and 9-6, as designed. Ladder: #213 1713 (13:24Z) → #228
1691 (15:27Z) → #195 1739 (19:24Z) → #206 1726 (21:24Z) → #210 1720 (22:25Z) → **#192 1745 (23:25Z)**.

**Found but not fixed (next):**
- B130: 00eight's 37-gem elk group beside our spawn is a battleground, not a pricing problem: our bodies spend 650-1,200
  rounds a game within 5 of it, 12 of our deaths a game are champion kills there, we capture it 0.2× (they take their
  mirror 8.8-10×). B130a (start 2-body groups only with an ally within 6) was neutral locally with negative deltas, parked.
- The economy gap is now measured, not guessed: equal captures, 746 vs 866 gems captured a game on panel v2; the
  remaining big gaps are 00vault's 343-gem cluster (0.7× vs 4.0×), 02the_pond and 00galaxy gem-only clusters, 01big_world
  and 01islands elk groups (`tools/captures.py v51p2`).
- Deaths walking home: 46% of ours vs 30% of theirs (fights.py, panel v2); the threshold family is parked (B93/B122/B123).
- Review items not done: #8 handicapped-candidate local test, #9 profile bots from panel opponents' summaries.

## v51 (2026-11-01)

- v50 + B129: the siege-style leave threshold applies at every monster group with the real escape cost, `(exit + 1) × group damage × remaining share / bodies at the group`, exit = elk range 4 + 1 − own attack range. Before, a non-siege monster group had no camp-aware leave (a body stayed to 28.8% under 120+ damage a turn with 4 tiles to walk).
- Gate: nonreg vs v50 PASS 52% (280).
- 19:23Z: panel `v51p2` vs `v50p2`, paired: **deaths −0.94 ± 0.43 (z −2.2), gem margin +20 ± 32, gems r500 +6.8 ± 3.4**, champion damage taken −1.7k ± 1.2k, wins 41 → 46, camp deaths 1.83 → 1.54 a game. **BETTER** by the process-review rule, the first of the night; kept as the base. Ranked 12-8 over 20; ladder #198 1733 at 19:08Z. Confirmation panel `v51p2b` (19:24-20:10Z) replayed `v51p2` game for game: 90/90 identical outcomes and metrics, so the verdict stands and the panel is fully deterministic within the hour (the 75/90 of v41 a day apart was opponent drift, not sampling noise). Ranked 26-25 over 55 at 20:12Z; ladder #206 1727.
- Submitted 2026-11-01T18:15Z as team bot version 65. v50's panel (`v50p2` vs `v49p2`, paired): wins 44 → 41 (net −3), gem margin +12 ± 41, deaths +0.1 ± 0.7, gems/capture +1.07 ± 0.39, gems r500 +12 ± 4, captures −4.9 ± 1.2, gold −304 ± 204, camp deaths 1.83/game (eight 32 → 20 per 6 games): neutral, kept as the base. Our 00eight elk group is still taken 0.2× a game (theirs 8.8×). v50 ranked 13-7 over 20; ladder #211 1716 at 17:59Z.

## v50 (2026-11-01)

- v49 + B128a: a camp group's `exposure` sums each monster's health × its own damage instead of × the whole group's damage, so 22-59-gem elk groups are no longer priced below 8-11-gem wolf pairs (H1 of the process review: 00eight's 37-gem elk group taken 0.3× a game by us vs 10× by the opponents; 547 gems captured a game vs 892 with equal capture counts).
- Gates: nonreg vs v49 PASS 49% (980); race vs v47 47%.
- Submitted 2026-11-01T17:06Z as team bot version 64. v49's panel (`v49p2`) replayed v48p2 game for game: 90/90 identical outcomes, every paired delta 0 — B127 is a no-op (HoR with an enemy in sight is already at the duo/carrier threshold), v49 kept as the base. v49 ranked 8-12 over 20; ladder #225 1694 at 16:51Z.

## v49 (2026-11-01)

- v48 + B127: Heart of Ruin leaves at 50% health with an enemy in sight (the B99 Vesper rule), after HoR became our worst healthy-1v1 death rate on v47's panel (25% vs opponents' 19%). Also ranked-like seeded rosters in `random_team` (no-op in real drafts).
- Gates (nonreg): v48 50% (301); as `b127` on v47: v47 49%, v12 77%, Jame v3 87%.
- Submitted 2026-11-01T15:42Z as team bot version 63. v48's panel-v2 baseline (`v48p2`, the new ~50% panel): 44-46, deaths 11.1, gold 7,208, gems captured 734 vs 860. v48 ranked 14-25 over 40 (below the 200-game bar; rating 1719 → 1691, not near the −100 revert line).

## v48 (2026-11-01)

- v47 + B126b: each body finishes Treasure (own stat), Prospector, Durability (health) and Jungle (own stat) emblems, then Bruiser forever (was Prospector, Durability, Bruiser).
- Gates (nonreg): v47 52%, v12 73%, Jame v3 90%; race vs v47 49% (self-play hides an economy edge).
- Submitted 13:25Z as team bot version 62. v47's trial: panel 29-61 (= v46) with deaths 12.1 (v46 13.9), ranked 19-11 over 30, ladder #226 1687 → #213 1713: kept as the base.
- 14:20Z: panel v1 paired vs v47 (`tools/panelcmp.py`, new): wins 29 → 30, gold +582 ± 165, kills +1.1 ± 0.5, deaths +0.7 ± 0.8, gem margin 0 ± 50. Not worse, gold up: **kept as the base**. Process review (`docs/research/process-review-2026-11-01.md`) adopted: paired panel metrics decide, not W-L or short ranked windows; panel v2 (near-50% opponents and maps) queued on v48 14:21Z as the new baseline.

## v47 (2026-11-01)

- v46 + B124 = B99c from v37: plain dashes kept for escapes while an enemy was seen lately; Vesper leaves at 50% with an enemy in sight; a leaving Vesper runs unless her target is below 25%.
- Gates (nonreg): v46 51%, v12 77%, Jame v3 88%.
- Submitted 12:10Z as team bot version 61 (first upload attempt returned an invalid response). v46's panel was 29-61 with 13.9 deaths (v44 28-62, 15.8): kept as the base. Ladder #230, 1688 at 12:10Z.

## v46 (2026-11-01)

- v45 + B121: `carrier_recall_health` 0.5 → 0.65, so a body carrying gems leaves at 65% health.
- Gates (nonreg): v45 52%, v12 80%, Jame v3 90%.
- Submitted 11:35Z as team bot version 60 for an A/B vs v44 (panel 28-62). v45's panel was 26-64 (deaths 14.7), not clearly better than v44's.

## v45 (2026-11-01 11:04Z uploaded as team bot version 59, scrim A/B + ranked trial vs v44)
- v44 + B120: the lone fall-back for every champion. Nonreg PASS vs v44 52%, v12 81%, Jame v3 89%. See `docs/v45`.
- Baseline: v44 20-20 over 40 since 09:32Z, panel 28-62 (deaths 15.8); ladder #237 1678.

## v44 (2026-11-01 09:29Z uploaded as team bot version 58, scrim A/B + ranked trial vs v43)
- v43 + B112a: a lone Vesper/Heart of Ruin that sees 2+ enemies within 6 falls back before the fight.
- Nonreg PASS vs v43 49%, v12 81%, Jame v3 92%. See `docs/v44`.
- Baseline: v43 38-27 over its two stints (stint 2 15-15), panel 24-66 (deaths 17.7); ladder #242 1676.
- Live by 09:32Z. Panel (10:20Z): **28-62** (v43 24-66, v41 24-66); deaths 15.8 vs 17.7 vs 19.0, gold 5,255. Ranked 11-4 at
  10:03Z, ladder #220 1701. Kept for a full ranked trial (fallback v43).

## v43 (2026-11-01 06:27Z uploaded as team bot version 55, scrim A/B + ranked trial)
- v41 + B118: every champion fights only with ≥1.2x power (Vesper 1.3x; the health tiebreak is gone).
- Race vs v41 51%; nonreg PASS vs v41 48% (borderline), v12 81%, Jame v3 92%. See `docs/v43`.
- Baseline: fresh v41 panel `v41-1101` (06:26Z) 24-66, deaths 19.0/game; v41 ranked 263-262 over 525, ladder #251 1663.
- Live by 06:32Z. Panel (07:15Z): 24-66 = v41-1101's 24-66; deaths 17.7 vs 19.0, gold 5,148 vs 4,988. Not clearly
  better (rule: net ≥ +5), so revert to v41; two re-uploads at 07:20Z failed (platform 'invalid response'). Ranked 10-5 at 07:04Z.
- v41 re-uploaded at 07:36Z as team bot version 56 (third attempt).
- v41 then went 3-12; v43 re-uploaded 08:14Z as team bot version 57 for a full ranked trial (user-approved).

## v41 re-uploaded (2026-10-31 10:40Z as team bot version 54, revert of v42)
- Live by 10:56Z: 8-7 over 15 by 11:31Z, ladder #239 1686. On the 7 fuel-heavy maps v41 is 4-3 vs v38 8-14.
- **100 games (14:14Z): 54-46 (54%)**, rating 1660 → 1707 (#222). Proven; the sprint 3 deadline bot.
- 18:00Z freeze: 110-95 over 205, ladder #199 1730. Stays live to the deadline.
- Deadline check (23:49Z): 198-177 over 375, ladder #182 1749 (sprint best).
- v42 went 11-19 over 30 (37%) vs v41's 22-28 (44%) at the same rating (~1660-1676). Its gold rose (losses 6.4k vs ~4.2k)
  but deaths in losses stayed at 16: more gold did not buy wins. B113b rejected in ranked.

## v42 (2026-10-31 09:20Z uploaded as team bot version 53, ranked trial)
- v41 + B113b: gold counts 0.5 (not 0.2) in target choice before round 500. Losses trail 1.2k vs 2.3k gold by r500.
- Race vs v41 59%; **gain gate vs v41 PASS 55% (233/420)**; nonreg PASS vs v12 81%, Jame v3 90%. See `docs/v42`.
- v41 ended 22-28 over 50 (07:27-09:20Z), rating ~1676.

## v41 (2026-10-31 07:10Z uploaded as team bot version 52, ranked trial)
- v38 + B100 (fuel cache, first tried as v36). 5 of v38's 41 losses since 04:35Z are fuel stalls.
- Gain on 7 fuel-heavy maps vs v38 54% (inconclusive, leaning positive); nonreg PASS vs v38 49%, v12 79%, Jame v3 92%.
  See `docs/v41`.
- Live by 07:27Z. Scrim panel (08:30Z): 25-65 (v38 24-66); 01islands 2-4 (v38 1-5). Ranked 6-9 over the first 15.
- 35 games (08:32Z): 14-21 (40%) at rating 1672-1694, v38 at the same rating 33-47 (41%). Fuel-exhausted turns per ranked
  game 6.3 vs v38's 17.5-18.5; games with 50+ such turns 2/35 vs 20/225. Mechanism confirmed; results level.

## v38 re-uploaded (2026-10-31 04:18Z as team bot version 51, revert of v40)
- Live by 04:35Z. After 50 games (06:12Z) v38 itself was 22-28 at rating ~1723, the same as v40's 22-28: the revert made no
  measurable difference. Near our equilibrium rating (~1725-1745) every bot wins about half; compare by rating over 100+ games.
- v40 went 22-28 over 50 (44%, under the ~45% limit at 50). Opponents' gold was higher (6,315 vs 5,456), but v38's own last
  50 games at the same rating (1700-1745, 00:30-02:00Z) went 32-18 against 5,313: the gold rise is our deaths feeding kill
  gold, not a stronger field. Ranked deaths per game: Vesper 3.44 (v38 4.01), Heart of Ruin 3.80 (3.90); the panel's
  death cut did not carry over. B112a rejected in ranked; B112b (same rule for all champions) dropped with it.

## v40 (2026-10-31 02:05Z uploaded as team bot version 50; live by 02:29Z, ranked trial)
- v38 + B112a: a lone Vesper/Heart of Ruin (no ally within 4) that sees 2+ enemies within 6 falls back toward the nearest
  ally or home before the fight. Evidence: 19 loss replays, their deaths come alone and from healthy (B112).
- Nonreg PASS vs v38 51%, v12 82%, Jame v3 93%; hunter-v0 91% (v38 93%). See `docs/v40`.
- Baseline to beat: v38 83-62 over 145 (21:15Z-02:10Z), ladder #187 1745 at 02:30Z.
- Scrim panel (03:20Z): 27-63 (v38/v39 24-66); deaths 15.2 vs 18.3 a game, kills 8.4 vs 7.9, gold 5,414 vs 5,098; 89 of 90
  games diverged. Ranked 10-10 over the first 20.
- 35 games (03:36Z): 15-20 (43%, trigger). Kept as a field shift: panel better, opponents' gold 5,456 (v38 window) → 6,695.
  Ranked deaths 13.5 a game vs v38's 12.7, so the panel's death cut is not showing yet.

## v38 re-activated (2026-10-30 20:55Z, `cambc submissions activate 47`, auto-revert of v39)
- v39 went 63-67 over 130; the last 30 were 7-23 (limit 43%), on the six Willow maps 2-9. Opponents' gold rose only
  5,852 → 6,266 and v39's panel was no better than v38's, so the rule reverted it. B111 (Willow draft) rejected in ranked.
- Live again by 21:15Z: 41-34 over 75 games by 23:50Z. Ladder #223, 1701.

## v39 (2026-10-30 16:14Z as team bot version 49, overnight auto-submit)
- v38 + B111: Willow replaces the last core pick on 00dunes, 00eight, 00vault, 00monolith, 00crater, 02crossing (top-60
  teams drafting Willow win 65-79% there vs 35-46% without; our record there 44%). Draft only; elsewhere identical to v38.
- Map gate vs v38 52% (neutral); nonreg PASS vs v38 50%, v12 81%, Jame v3 92%. See `docs/v39`.
- v38 at 60 ranked games: 38-22 (63%); ladder #214, 1706 (14:43Z).
- v38 at 100 games: 55-45; the last 30 went 9-21 (trigger), but opponents' gold rose 4,743 → 6,443 a game as we
  climbed to #212 (field shift), and v34 plays identically off 02guardians, so no revert. v39 submitted under the
  overnight scout-evidence clause; fallback v38 (version 47).
- Live by 16:32Z. Scrim panel (17:21Z): 24-66, same as v38's 24-66; 53 of 90 games identical. Willow maps: 00eight 2-4
  (v38 1-5), 00vault 0-6 (v38 3-3; on 4-pick vault Willow replaces Vendetta). Ranked 7-8 over the first 15.
- Ranked: 17-13 at 30, 31-29 at 60, 57-53 at 110 (20:20Z); on the six Willow maps 2-7. Ladder #213 1715 at 19:15Z, #219
  1702 at 20:21Z.

## v38 (2026-10-30 ~12:22Z, submitted by the user as team bot version 47)
- 12:40-12:42Z a second session resubmitted v34 by mistake (version 48, cancelled); v47 re-pinned live. Count v38's
  ranked sample from 12:42Z. The team is now in pinned mode: a new submit goes live only after `cambc submissions activate <n>`.
- v34 + B109: on 02guardians a carrier with 100+ gems and >60% health strikes the Monolith gate alone.
- Map gate vs v34 (02guardians, 01boss-battle) PASS 50/80 = 62%; nonreg vs v34 PASS 141/280 = 50%. See `docs/v38`.
- Nonreg PASS vs v12 227/280 = 81%, vs Jame v3 257/280 = 92%. Gauntlet +408 [+360, +412] (predicted ladder 1655; actual
  1651 at 13:00Z).
- Ranked: 19-11 over the first 30 games (13:41Z), 63%; gold 8.1k in wins, 4.0k in losses. v37's 20 ranked losses: 8 races, 4 fuel, 3 tiebreak, 2 spirals; no map cluster pointing at B99c.

## v34 resubmitted (2026-10-30 12:12Z as team bot version 46, auto-revert)
- v37 went 10-20 over 30 ranked games (33%, limit 43%). Its panel beat v34's, but opponents' gold fell (5,320 a game vs
  5,500-6,100 in v34's last three samples), so the rule reverted it. Next, on the user's approval: B109 ported onto v34
  (`bots/_var/b109v34`) once its map and nonreg gates pass.

## v37 (2026-10-30 11:14Z as team bot version 45, user-approved)
- v34 + B99c: while an enemy was seen in the last `threat_memory` rounds, plain movement dashes are kept for escapes;
  Vesper leaves at 50% health with an enemy in sight; a leaving Vesper runs unless her target is below 25% health.
- Scrim A/B (team bot version 43): panel 32-58 (v34 30-60), net +2 vs v34 and +6 vs v36, deaths 14.2 a game vs 17.7;
  ranked 16-9 while live. Local race 53%, gain gate 51%. Nonreg PASS vs v12 80%, Jame v3 89%.

## v34 resubmitted (2026-10-30 10:08Z as team bot version 44, end of the scrim A/B round)
- b95v34 (Jungle, team bot version 42) panel 23-67, net -7: rejected. b99c (team bot version 43) → v37. b97 skipped.

## v34 resubmitted (2026-10-30 01:32Z as team bot version 41, auto-revert)
- v36 went 11-19 over 30 ranked games (37%, limit 43%); its panel was 26-64 vs v34's 30-60, so the rule reverted it.
  On most maps v36 plays exactly as v34, so much of the 11-19 is the field (opponents' gold 5.5k → 6.1k); the 4
  panel flips in fuel games all went W→L.

## v36 (2026-10-30 00:36Z as team bot version 40, user-approved)
- v34 + B100: `move_towards_closest` caches the union of living camp groups' tiles instead of ORing every group's
  tiles on every move (~1k fuel per group: 33k of a 45k move on 02tangle). Same decisions whenever fuel sufficed.
- Fuel-exhausted turns, local vs v33: 02tangle 402 → 98, 01islands 32 → 2, 00lanes 65 → 10.
- Gain gate vs v34 on seven fuel-heavy maps PASS (91/154 = 59%); nonreg vs v34 all maps PASS (140/280 = 50%).

## v34 resubmitted (2026-10-29 19:01Z as team bot version 39, auto-revert)
- v35 went 64-71 over 135 ranked games (last 30: 13-17), at the 48% limit; its panel was no better than v34's and
  opponents' gold fell, so the rule reverted it.

## v35 (2026-10-29 14:28Z as team bot version 38)
- v34 + B87b + B91a (backlog B92). B87b: a body also takes up a fight an ally within `ally_radius` is in, not only
  enemies within its own `engage_radius`. B91a: before round 60 on 4-5 body maps, a camp group takes all bodies and
  joining does not split its value, so the team clears the first groups together.
- Local: race vs v34 57% (80/140); gain gate vs v34 PASS (234/420 = 56%); nonreg PASS vs v12 and Jame v3 (94%).
- Scrim A/B (team bot version 36, 14:06Z): panel 28-62 vs v34's 30-60, paired net -2 (noise ±4), deaths -0.9/game.
  Submitted for a full ranked run on the user's approval; fallback v34.

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

## v34 (from v33; submitted 2026-10-29 07:49Z as team bot version 30)
- **B86 01boss_battle bags:** until the Monolith corridor to the only altar is open, carriers bank only 100+ gems (they
  died at the breach with 9-19). Map gate 97% (58/60) vs v33; nonreg 51%.

## v33 (from v32; submitted 2026-10-29 04:16Z as team bot version 29, user-approved; v27b closed 7-13)
- **B84 gold-only groups at 250:** B56 had priced 0-gem gold groups at 120 per cluster too, making them the best target;
  the six maps they dominate fell from 59% to 28% after B56. Gem groups keep 120. Locally neutral (53% race, 49% map gate).

## v32 (from v27; not submitted)
- **B83 clusters at 250:** gem and gold clusters in groups with a monster were priced at 500 health (real 120), so the
  71-gem elk+8-cluster groups on 00gem_fields looked too slow (top teams open them at r25-31, we at r126-143; 1-10 there).
  Locally neutral (50% vs v27); 80% vs v12, 92% vs Jame v3; gems at r250 213 vs 138 on gem-fields.

## v27 resubmitted (2026-10-29 03:37Z as team bot version 28, auto-revert)
- v31 went 24-26, 12-18 over its last 30 (≤43% trigger), and its panel was 28-62 vs v27's 32-58, which confirms it.

## v31 (from v27; submitted 2026-10-29 01:54Z as team bot version 27, user-approved; v27 closed 56-49; reverted 03:37Z at 24-26)
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
