# Overnight report, 2026-10-26 (written 2026-10-25 23:00Z = 10:00 AEDT)

**Recommendation: submit `bots/daniel/v11`, and approve T9 (scrims against top-20 teams).**
v11 is v10 plus two gated changes: the big-map fuel fix (B19) and Bruiser shards instead of Power (B21).
It beats v10 59% on the old 40 maps and 51% on the 30 maps added yesterday. It rates +56 Elo above v10 in the
local gauntlet. It also fixes a bug that makes v10 lose every game on 01big_world.

## 1. v10 on the ladder (submitted 2026-10-25 12:54Z, team bot version 9)

| | |
|---|---|
| Ranked record (to 22:36Z) | **143–137** (51%), 280 games |
| Rating | 1495 at submission → peak **1542** (#355, 20:27Z) → **1513** (#389, 22:38Z) |
| v9's window | 47–33, 1479 → 1486 |
| v8 | 1453 |

Rating trend from the hourly snapshots (`docs/ladder_history.csv`):

| Time (Z) | Rank | Rating |
|---|---|---|
| 10:16 v9 submitted | #430 | 1479 |
| 12:54 v10 submitted | #410 | 1495 |
| 14:46 | #434 | 1473 |
| 18:23 | #373 | 1524 |
| 20:27 | #355 | 1542 |
| 21:29 | #375 | 1523 |
| 22:38 | #389 | 1513 |

The pool grew from 40 to 70 maps during the evening. v10 is 6–10 on the new maps it has met so far (anvil 0–3,
crater 0–2), which accounts for part of the drop since the 20:27Z peak.

**Where v10 loses** (`tools/ranked.py` loss-signature table, 280 games):

| Map | W–L | What happens |
|---|---|---|
| 01big_world | **0–6** | All 6 losses frozen by fuel exhaustion (we bank 0–12 gems). **Fixed in v11 (B19).** |
| 00ambush | 2–5 | Fuel signature in all 5 losses. v11 passed its map gate here too. |
| 00packs | 0–7 | B7, open. |
| 00rows | 0–6 | The opponent takes the 470-gem Monolith (B20, the tried fix was rejected). |
| 01starvation | 0–5 | No gems for 1,000 rounds (B22, diagnosed, not fixed). |
| 00anvil (new) | 0–3 | Not yet studied. |

## 2. What was built and tried overnight

Every change was logged in `backlog.md` before testing. All gates ran at the real 100k fuel with `--release`.

| Item | Change | Result | Outcome |
|---|---|---|---|
| **B19** | Cache `choose_target`'s distance field (rebuild after 3+ tiles moved or every 10 rounds) | big_world vs Jame v3: fuel-exhausted turns 2,499 → 170 and 5,972 → 135, both games turn from losses into wins. Map gate vs v10 (big-world, ambush, lanes) 40/60 = **67%**; nonreg vs v10 51%, vs v9 60% | **in v11** |
| **B21** | Bruiser shards instead of Power after the Monster and Durability emblems (the top 20 buy mostly Bruiser; a Bruiser emblem is 7 shards' worth, Power 6) | Gain vs v11 (B19 only) 135/240 = **56%**; gain vs v10 95/160 = **59%**; nonreg vs v9 100/160 = 62%, vs Jame v3 98/160 = 61% | **in v11** |
| B17+B18 | `max_damage_share` 1.0/1.5/2.0/3.0 (elk groups opened alone) | Race 44–50%; helps elkring (57–62%), hurts islands (~35%) | rejected |
| B11 | Treasure-first build orders | Race 50–56%; gain gate of the best 405/800 = 51% | rejected |
| B15 | Gold weight falling over the game | Race 44–52%; gain gate 240/480 = 50% | rejected |
| B14 | Duo deaths: health pool counts the duo as its weaker body | Race 38–41/80; vs Jame v3 65% either way | neutral, not applied |
| B14 | Duo-hunter exploiter bot (Phase 3) | Focusing our duo gains an opponent nothing locally (50%) | tool only |
| B14 | The second duo body follows its partner's target | Works (duo distance 16–21 → 1–7.5 tiles) but neutral: race 38–40/80, vs Jame 63%; starvation map gate 52% | **parked: needs T9** |
| B20 | Value a Monolith group ≥ 50% of the map's gems at ×1.5/×2/×3 | Map gate on rows/corridors/contest/gold-rush: 22% / 11% / 9% (bodies start sieges they cannot finish) | rejected |
| B22 | starvation diagnosis | Bodies reach the one 88-gem elk group one at a time and wear down; v11 loses to Jame v3 there locally too | open |
| B23 | 30 new maps pulled and dumped (`maps/ascii/`) | v11 vs v10 on the new maps: 401/780 = **51%** (gain gate fails, no regression; per map 11–16/26) | checked |

Tooling fixes: `ladder.py` refetches when the ladder moves while we page; `gate.py --max-seeds` scales with the
number of maps (a 2-map gate could never decide); the seed hook was ported back into v9 and v10, so gates against
them run at 100k fuel. Gates against Jame v3 still run at the 1M fuel fallback.

## 3. v11 compared with v10, v9 and older models

Local gauntlet (`tools/gauntlet.py`, Bradley–Terry on an Elo scale, v8 = 0, 90% intervals; 20:47Z):

| Bot | Local rating | Ladder (actual or predicted) |
|---|---|---|
| **v11** (B19 + B21) | **+187** [157, 208] | ~1551 predicted |
| v10 (live) | +131 [102, 153] | 1495–1542 actual |
| v9 | +113 [86, 135] | 1479–1486 actual |
| Jame v3 | +37 [7, 63] | |
| v8 | 0 | 1453 actual |
| v7 | −71 | |
| Simon hunter-v0 | −153 | |
| Simon v6 | −213 | |

Head to head (gates at 100k fuel):

| v11 vs | Result |
|---|---|
| v10, old 40 maps | 95/160 = 59% |
| v10, 30 new maps | 401/780 = 51% |
| v9 | 100/160 = 62% |
| Jame v3 | 98/160 = 61% |
| Simon v6 / hunter-v0 (gauntlet) | 147/160 / 141/160 |

The ladder prediction (1450 + 0.54 × local, from three submitted versions) is rough. Local gains have reached the
ladder at about a third to a half of their size so far.

## 4. Recommendation

1. **Submit v11.** Reasons, strongest first:
   - It fixes a bug that loses every game on 01big_world (0–6 ranked, frozen by fuel) and every loss on ambush
     (2–5, fuel signature in all 5).
   - Bruiser shards pass a gain gate against v10 (59%) and match what all top-20 teams buy.
   - No regression anywhere: 51% on the new maps, 61–62% against v9 and Jame v3.

   The risk is low. Both changes are small (a cached field and three shop item swaps), and the gates ran at ranked
   fuel. After submitting, run
   `python3 tools/ladder.py submitted bots/daniel/v11 --time <ISO> --platform-version 10 --note "Daniel v11: big-map fuel fix + Bruiser shards"`.

2. **Approve T9 (match-groups scrims against top-20 teams).** Three findings can only be tested against real
   opponents:
   - The duo-follow fix (B14). Ranked duo deaths are our largest gap: 4 per loss vs 1.4 per win, the bodies a
     median 10 tiles apart. No local bot punishes a split duo.
   - starvation (B22).
   - The new maps.

   T9 spends shared quota and plays only the submitted bot, so it is most useful right after the v11 submission.

## 5. Next (during the day, same rules: one change per 2 hours, gated)

- B22/B17: a "gather before opening an elk group" rule, map-gated on starvation and elkring.
- B7: packs (0–7).
- The new maps: anvil and crater losses once v11 has ranked games on them.
- B12: draft towards the top-20 core (Vesper 90%, Heart of Ruin 84%, Marcella 82%).
