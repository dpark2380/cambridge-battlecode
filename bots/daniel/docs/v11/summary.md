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

## Next

B17+B18 (`max_damage_share` race 1.0/1.5/2.0/4.04), from 20:30Z at the earliest (one change every 2 hours).
