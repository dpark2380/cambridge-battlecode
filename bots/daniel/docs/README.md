# Daniel's iterations

| Iteration | Bot folder | Summary | Key result |
|---|---|---|---|
| [v1](v1/summary.md) | `main-v1` | First independent heuristic bot: reward-per-turn camp choice with claims, retreat-before-recall | 16/18 vs starter |
| [v2](v2/summary.md) | `main-v2` (`main-cpp` = working copy) | Fuel fix for big maps, danger-aware recall, learned draft table, tuned constants | 70% vs v1; 3/18 vs team v3, so retired |
| [v3](v3/summary.md) | `v4-dp` | Team v3 + gem-aware gold squad + tuned constants | 55% over 288 vs v3 code |
| [v4](v4/summary.md) | `v5-dp` | Daniel v3 + simple solo farming | 13/18 vs Daniel v3; 9/18 vs Simon's v4 |
| [v5](v5/summary.md) | `v5` | Simon's v4 + self-play-tuned constants. Submitted (team bot version 5); ranked 18–47 | 102/162 (63%) and 11/18 vs Simon's v4 |
| [v6](v6/summary.md) | `v6` | v5 + Monolith sieges + gold weight 0.20 (gold wins fights) | 62% vs hunter (v5: 52%); 61% vs Simon's v5 |
| [v7](v7/summary.md) | `v7` | v6 + fixes from the ranked research: walking-distance stall check, unseen-attacker response, sieges for any too-big group, carriers recall at 50% | 59% vs v6; 72% vs Simon's v5 |
| [v8](v8/summary.md) | `v8` | v7 ported to the week 2 patch: Golem/range camp table, Monolith leave rule and siege gate, gold-only play when no altar can be reached | 61% vs v7; 84% vs hunter |
| [v9](v9/summary.md) | `v9` | v8 + pathing blocks living camps out of sight (the_farm freeze) + 40% of Power shards as health. Submitted 10:16Z (team bot version 8); ranked 47–33 | 69% vs v8; 55% vs Jame v3 (v8: 39%) |
| [v29](v29/summary.md) | `v29` | v28 + B73: Vesper fights only with a clear edge. Not submitted | 48% vs v28 (neutral locally), 76% vs v12, 91% vs Jame v3 |
| [v28](v28/summary.md) | `v28` | v26 + B78b: Vesper kites (steps away while her attack recharges). **Submitted 2026-10-28 19:37Z as team bot version 24, the live bot** | 50% vs v26 (neutral locally), 58% vs v25, 79% vs v12, 91% vs Jame v3 |
| [v27](v27/summary.md) | `v27` | v26 + B73: Vesper fights only with a clear edge. Not submitted | 48% vs v26 (neutral locally), 56% vs v25, 76% vs v12, 91% vs Jame v3 |
| [v26](v26/summary.md) | `v26` | v25 + B68: Vesper and outnumbered bodies don't close in; B70: HoR buys 65% health shards; B71: a leaving body dashes away. Team bot version 23 (16:15Z), ranked 55-45 | **58% vs v25**, 79% vs v12, 91% vs Jame v3 |
| [v25](v25/summary.md) | `v25` | v24 + B54 (Monolith struck only with 3 bodies; no B54b). Team bot version 22 (12:35Z), ranked 59-51 | 01corridors 68% vs v24, nonreg 51%; 65% vs v22, 78% vs v12, 91% vs Jame v3 |
| [v24](v24/summary.md) | `v24` | v23 + B64: the gold squad closes in on enemies too. Not submitted | 61% vs v23, 64% vs v22, 77% vs v12, 91% vs Jame v3 |
| [v23](v23/summary.md) | `v23` | v22 + B62: a hurt body near an enemy fights back instead of recalling; the duo leaves at 50% health. Not submitted | 58% vs v22 (gain gate); 78% vs v12, 86% vs Jame v3, 90% vs hunter-v0 |
| [v22](v22/summary.md) | `v22` | v18 + B56 only (no siege rule). Team bot version 19 (06:29Z, 50-61); resubmitted 2026-10-28 10:40Z as team bot version 21 (36-24) (scrim panel 16-44 vs v18 10-50) | 02treasure-box 65% vs v18, nonreg 52% |
| v21 | `v21` | v20 with B54b reverted (Monolith-only gather rule + B56). Not submitted | 50% vs v18, 50% vs v19 |
| [v20](v20/summary.md) | `v20` | v19 + B56: monster-free groups at real cluster health (02treasure_box). Not submitted | 02treasure-box 65% vs v19, nonreg 51%; 80% vs v12, 85% vs Jame v3 |
| [v19](v19/summary.md) | `v19` | v18 + B54/B54b: strike a siege target (Monolith, golem groups) only with 3 bodies there. Team bot version 17 (03:22Z), withdrawn at 04:50Z after 16-24 | 01corridors 62% vs v18, 02harvest 75%; 52% vs v18, 77% vs v12, 85% vs Jame v3 |
| [v18](v18/summary.md) | `v18` | v17 + research strategy stack: HoR dash in fights, shop early, Prospector first, wards, one capture receiver, own-altar lock. Team bot version 16 (23:06Z); resubmitted 04:50Z as team bot version 18 (27-23); resubmitted 10:25Z as team bot version 20 (replaced 10:40Z) | 71% vs v17, 75% vs v12, 82% vs Jame v3; gauntlet +346 |
| [v17](v17/summary.md) | `v17` | v16 + B37: outmatched bodies fall back to allies; ranged bodies shoot back instead of running. Team bot version 15, ranked 127-134 | 58% vs v16, 65% vs v12, 77% vs Jame v3 |
| [v16](v16/summary.md) | `v16` | v15 + B36: bodies join a claimed camp (joiner value 1.0, up to 3 per camp). Team bot version 14, ranked 81-79 | 59% vs v15, 62% vs v12, 78% vs Jame v3 |
| [v15](v15/summary.md) | `v15` | v14 + B34: on 01boss_battle, tribute from the Monolith tile instead of calling gems undeliverable. Candidate | boss-battle 98% vs v14; nonreg 49% v14, 51% v12, 65% Jame v3 |
| [v14](v14/summary.md) | `v14` | v13 + B29b: the_pack strike waits for allies in the gather zone, not near itself. **Submitted 2026-10-26 23:06Z as team bot version 13** | the_pack 53% vs v13; nonreg 50% vs v13, 51% vs v12, 66% vs Jame v3 |
| [v13](v13/summary.md) | `v13` | v12 + B29 the_pack corridor: carriers cut through the wolf ring around the only altar. Team bot version 12, ranked 189-176 | the_pack 85% vs v12; nonreg 51% vs v12, 57% vs v11, 66% vs Jame v3 |
| [v12](v12/summary.md) | `v12` | v11 + B25 top-20 core draft (Heart of Ruin draftable; Marcella/HoR buy focus). **Submitted 2026-10-26 05:45Z as team bot version 11** | real drafts: 77% vs v11 (old maps 70%, new 87%), 79% vs v10, 81% vs v9, 79% vs Jame v3; seeded 64% vs v11; on SDK 4.0: 68% vs v11, 69% vs Jame v3 |
| [v11](v11/summary.md) | `v11` | v10 + B19 big-map fuel fix (cached target field) + B21 Bruiser shards instead of Power. **Submitted 2026-10-25 23:14Z (team bot version 10)** | 59% vs v10, 56% vs v11-B19, 62% vs v9, 61% vs Jame v3; B19 map gate 67% vs v10 (big-world 17/20) |
| [v10](v10/summary.md) | `v10` | v9 + also fight when ahead on fighting power (health × damage). Submitted 2026-10-25 12:54Z (team bot version 9) | 57% vs v9; 59% vs Jame v3 (v9: 55%) |
| — | `hunter` | Test opponent: v5 made aggressive (chases, engages at 8 tiles) | sparring partner for fight-related changes |

All bots accept bare names in the tools (`python3 tools/arena.py v5 v4`). Iterations v2–v8 have the random-draft
experiment hook (`--seeds`, `tools/tune.py`).

Ranked data: `python3 tools/ranked.py replays/<version>` downloads and summarises our ranked games.

Research notes: [`research/v6-improvements.md`](research/v6-improvements.md) (what the 54 ranked v6 games say to fix next).

Overnight report with the v11 recommendation: [overnight-2026-10-26.md](overnight-2026-10-26.md).
