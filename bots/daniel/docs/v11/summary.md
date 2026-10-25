# v11 (in development, from v10)

Changes are added one at a time, each gated (`tools/gate.py`) at the real 100k fuel. Backlog ids refer to
`../backlog.md`.

## B21: Bruiser shards instead of Power (accepted 2026-10-25 20:40Z)

**Evidence.** Scout of 750 top-20 games (20:31Z): every main pick buys mostly Bruiser shards (Vesper Bruiser:Strength
46.7 + Bruiser:Health 19.0 a game vs Power 11.5; Marcella 58 Bruiser; Heart of Ruin 32). By the rules
(`docs/GameRules.md:304`) a Bruiser emblem gives 5 of the stat plus 1 of each other stat, 7 shards' worth, where
Power gives 6 of one. We bought Power after the Monster and Durability emblems. This was the untested half of B11.

**Change.** `build_order`'s last entry is the Bruiser shard of our stat; the 40% health split (`power_health_share`)
now buys Bruiser health shards.

| Test | Result |
|---|---|
| race vs v11 (80 games): 40% health split / no split | 42/80 / 40/80 |
| `gate` gain vs v11, all maps | 135/240 = 56%, PASS |
| `gate` gain vs v10, all maps | 95/160 = 59%, PASS (v11 with only B19: 50%) |
| `gate --mode nonreg` vs v9 | 100/160 = 62%, PASS (B19 alone: 60%) |
| `gate --mode nonreg` vs Jame v3 (1M fuel, no seed hook) | 98/160 = 61%, PASS |

**Gauntlet (`tools/gauntlet.py`, 20:47Z, v11 = B19 + B21):** v11 +187 [157, 208], v10 +131 [102, 153], v9 +113,
Jame v3 +37, v8 0, v7 −71, hunter-v0 −153, Simon v6 −213 (Elo scale, 90% intervals). The rough ladder line
(1450 + 0.54 × local, 3 submitted versions) predicts v11 about 30 points above v10.

**New maps (22:54Z):** v11 vs v10 on the 30 maps added to the pool on 2026-10-25: 401/780 = 51% (gain gate fails, no regression).

## B20: dominant Monolith value (rejected 2026-10-25 20:33Z)

**Evidence.** rows 0–6 ranked; the opponent took the 470-gem G6 in 2 losses and we never did. A debug print of
v11's target rates on rows showed G6 rated just under small groups (0.17–0.36 vs 0.21–0.58).

**Change tried.** Multiply a siege group's value by x1.5/x2/x3 when it holds ≥ 50% of the map's gems (rows 80%,
gold-rush 75%, corridors 57%, contest 50%).

**Result.** Map gate vs v11 on those four maps: 22% / 11% / 9% (contest 0/16 in all three). Bodies start the
siege before they can finish it and lose the time in trips home and duo deaths. Parked.

## B19: big_world fuel freeze (accepted 2026-10-25 18:35Z)

**Evidence.** v10 ranked on 01big_world: 4,261 fuel-exhausted turns in one loss. 00ambush 1–5 with 29–60
exhausted turns in every game, lanes 17–31. A fuel probe showed `choose_target` building a full walking-distance
field from our position every turn, about 40k fuel on the 100×100 map. With the move's own field on top, turns
ran past 100k and spilled into the next. Bodies also claimed one group while targeting another; that turned out
to be a side effect of turns cut short.

**Change.** `choose_target` keeps the field (`target_field`) and rebuilds it only after we move 3+ tiles or every
10 rounds. A travel estimate can be off by up to 3 tiles, which is small next to the trip lengths it is compared
against.

**Results (100k fuel, `--release`).**

| Test | Result |
|---|---|
| 01big-world vs Jame v3, side A | fuel-exhausted turns 2,499 → 170; gems 464:868 L → 965:843 W |
| 01big-world vs Jame v3, side B | fuel-exhausted turns 5,972 → 135; gems 0:866 L → 1,021:765 W |
| `gate --mode map` vs v10 (big-world, ambush, lanes) | 40/60 = 67%, PASS (big-world 17/20, lanes 12/20, ambush 11/20) |
| `gate --mode nonreg` vs v10, all maps | 123/240 = 51%, PASS |
| `gate --mode nonreg` vs v9, all maps | 96/160 = 60%, PASS |
| `gate` gain vs v10, all maps | 120/240 = 50%, FAIL (expected: only big maps change) |

**Errors hit.** The first map and nonreg gates were invalid. v10, v9 and Jame v3 had no seed hook, so the tools
fell back to the 1M fuel quantum and the freeze never showed (map gate 52%). The hook was ported back into v9 and
v10, where it does nothing without the header, and the gates were rerun. Gates against Jame v3 still run at 1M
fuel.

## B17+B18: max_damage_share (rejected 2026-10-25 18:46Z)

**Hypothesis.** `max_damage_share = 4.04` (tuned before the week 2 patch) lets a body start an elk group it cannot
finish (elkring first clear r67 vs Jame's r11), and leaves islands re-clearing a 0-gem group.

| Test | 1.0 | 1.5 | 2.0 | 3.0 |
|---|---|---|---|---|
| `race.py` vs v11, all maps | 35/80 | 119/240 | 39/80 | 120/240 |
| elkring vs Jame v3: first clears | r27, r28, r70 | r27, r28, r70 | r27, r32, r54 | – |
| islands vs Jame v3: first gem group G38 | r84 | r84 | r223 | – |
| `gate --mode map` vs v11 (elkring, islands) | – | 47% FAIL (17/30, 11/30) | 49% FAIL (21/34, 12/34) | – |

v11 itself: elkring first clears r67, r67, r80; islands G38 at r193. The constant helps elkring and hurts islands,
so it stays at 4.04. A targeted rule (don't open an elk group alone unless we can finish it) is the follow-up.

**Tool fix.** `gate.py --mode map` on two maps defaulted to 12 seeds (26 pairs), under the 30-pair minimum, so it
could never decide. The default now scales with the map count.

## B11: build order (rejected 2026-10-25 18:53Z)

Top teams finish Treasure, then Jungle, then Bruiser emblems; v11 builds Monster > Durability > Power.
`race.py` vs v11 (80 games each): Treasure > Durability > Power 45/80, Treasure > Jungle > Power 41/80, Jungle >
Treasure > Power 40/80. Gain gate of the winner vs v11: 405/800 = 51%, FAIL. Bruiser was not tried: its emblem
needs one shard of every other stat, which `shop()` does not buy.

## B15: gold weight decay (rejected 2026-10-25 18:58Z)

The win model values 1 gold at 0.22 gems before round 500 and 0.05 after; v11 uses a fixed `gold_weight = 0.20`.
Race vs v11: 0.20 then linear to 0.05 by r1000 42/80, 0.10 after r500 36/80, 0.06 after r500 35/80. Gain gate of the
linear variant: 240/480 = 50%, FAIL. The win model predicts submitted gems, but ranked games are often decided by
the lifetime-gold tiebreak (21 of v10's 71 losses), so late gold keeps its value.

## B14: duo health in fights (neutral, not applied, 2026-10-25 19:15Z)

**Evidence.** v10 ranked (150 games): 25.9 deaths per loss vs 14.0 per win; camp deaths flat (8.6 vs 7.6), champion
kills the gap (17.3 vs 6.4). Cassi and Issac die 4.0 times each per loss (1.4 per win). They share one life, so
that is 4 duo deaths a game, the most of any unit. `fight_enemies` adds both bodies' health, but the pair dies with
its weaker body.

| Variant | race vs v11 | vs Jame v3 (400 games) |
|---|---|---|
| v11 (sum both bodies) | – | 65% |
| pool = weaker body (min) | 41/80 | 65% |
| pool = 2 × weaker body | 38/80 | – |
| min + recall on the weaker body's health | 41/80 | 61% |

Neither local opponent hunts the duo. An exploiter (`bots/_var/duo-hunter`, v11 that hits a duo body first) gains
nothing either: v11 vs it 201/400 = 50%, min vs it 206/400 = 52%. So ranked duo deaths come from something other
than target choice.

**Replay look.** In 81 v10 loss reports, at 315 duo deaths Cassi and Issac were a median 10 tiles apart (64% 8+
tiles apart, 14% within 2): each body picks its own group, and Cassi (700 health) farms alone. A follower body
that takes its partner's claimed group (`bots/_var/b14-follow-*`) keeps them together (median distance 16-21 →
1-7.5 tiles vs Jame v3), but scores 40/80 and 38/80 in the race vs v11 and 63% vs Jame v3 (v11 65%). Parked: only
ranked play or scrims can show whether ranked opponents punish the split.

## Next

B14 (camp deaths) and B12 (draft meta) need diagnosis from the ranked losses before any variant is built.
