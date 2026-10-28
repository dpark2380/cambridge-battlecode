# v19: v18 + B54/B54b (sieges need company)

## Problem
v18 ranked (85 games, 51-34) lost 01corridors 0-3 with 18-37 deaths to camps a game; top teams die 6 times
there (benchmark deaths z -5.9). Deaths are our largest cross-map gap (z -0.66 over 49 maps).

Debug prints (`bots/_var/b54dbg`, local vs v12): our bodies took 180 a turn with no camp in vision. One body
chipped the Monolith at (25,19) alone (19,628 → 17,960 health over 120 rounds), which kept it awake. It
hit our bodies at the elk and wolf camps in the next corridors from behind walls, so `threatened()` never
saw it.

## Change
In `work_group`, a Monolith siege target is struck only with `min(team_bodies, monolith_gather = 3)`
bodies within 6 of it. Otherwise a body waits, and gives up after `max_wait_turns`, as for an unsurvivable group.

## Results
- Gain vs v18: 51% (144/280), FAIL. It is a one-map fix.
- Map gate on the 22 Monolith maps: pair score 0.523, FAIL (against the 0.65 it tests for).
- Nonreg vs v18 on all 70 maps: PASS, 51%.
- Map gate on 01corridors: **62% (41/66), PASS**.
- Local corridors vs v12: side-A deaths 32 → 16.

Gates: `data/b54-gates.txt`.

## B54b: every siege target
02harvest: Vesper and Heart of Ruin walked alone to the centre group G20 (6 gem clusters, 2 golems), hit a golem
for ~45 a turn while taking 240, and died every ~100 rounds (local and ranked). Sieged groups skip the
survivable check, so the gather rule now covers every siege target. Gain 51% FAIL; 02harvest map gate
**75% (45/60) PASS**; nonreg 51% PASS (`data/b54b-gates.txt`).

## Next
Deaths on 02harvest, 02guardians, 00eight, 02fields and adgato_gemcombat2.
