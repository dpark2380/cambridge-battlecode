# v20: v19 + B56 (lone gem clusters at their real health)

## Problem
v19 ranked 02treasure_box: we cleared 10 groups to the opponent's 128 and lost 68-1031, signature "frozen".
Locally v12 beat v19 there 1024-372, so the problem predates v19.

The map has 16 single 7-gem clusters (no monsters) around the altar. `choose_target` priced each one at
`cluster_effective_health` 500 (real 120) plus a full altar trip, so our bodies took the outer monster camps.

## Change
In `world.cpp`, a group with no members that hit back has health 120 × its clusters. Groups that include
monsters keep the 500 effective health per cluster: v8 found the real value over-valued mixed groups on gold-rush.

## Results (`data/b56-race.txt`, `data/b56-gates.txt`)
- Race vs v19: b56a 54%. b56b (also no altar trip for bags under 25) 46%, dropped.
- Gain vs v19: 50% (279/560), FAIL. It is a one-map fix.
- Map gate on 02treasure-box: **65% (39/60), PASS**.
- Nonreg vs v19: 51%, PASS.
- Local treasure-box vs v12: 1020-514 (v19 lost 372-1024).
- Nonreg vs v12 80% (224/280), Jame v3 85% (237/280), PASS (`data/v20-gates.txt`).
