# v27: v26 + B73 (Vesper needs a clear edge)

## Evidence
- Ranked v25, 75 games (`tools/fights.py`): Vesper dies in 38% of healthy 1v1s (HoR 26%, Marcella 10%). Only 17% of her
  deaths come on the walk home, so she dies fighting.
- Scrim panels: Vesper's healthy-1v1 deaths were 51% for v25 and still 39% for v26, our worst body by far.

The fight check rates her at max(strength, focus) = 100, about twice her real ~45. B61's general real-damage fix lost
locally twice, so this is narrower.

## Change
`fight_enemies`: Vesper treats a fight as even only when ours ≥ 1.3 × theirs (health × damage), and drops the
health-only clause.

## Results
- Race vs v26: 48% (67/140), neutral locally.
- Nonreg vs v26: 48% (543/1120), PASS (borderline).
- Nonreg PASS vs v12 76%, Jame v3 91%, v25 56% (`data/v27-gates.txt`).
