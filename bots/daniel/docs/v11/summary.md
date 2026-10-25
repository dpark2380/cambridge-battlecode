# v11 (in development, from v10)

Changes are added one at a time, each gated (`tools/gate.py`) at the real 100k fuel. Backlog ids refer to
`../backlog.md`.

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

## Next

B14 (camp deaths) and B12 (draft meta) need diagnosis from the ranked losses before any variant is built.
