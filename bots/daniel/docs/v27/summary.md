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
- Gauntlet (`data/gauntlet-v27.txt`): v26 +396, v27 +390, v25 +369; v27 vs v26 137/280, vs v25 157/280.

## Overnight decision (17:40Z): not auto-submitted
v26's own ranked breakdown (35 games, `replays/daniel-v26/timelines`) cut Vesper's healthy-1v1 deaths to 26% (v25 38%) and
deaths per contact to 17% (v25 21%). That leaves too little evidence for a change that is neutral locally, so v26 keeps
its sample and v27 goes to the user in the morning.
- Gauntlet with b78 (`data/gauntlet-b78.txt`): v26 +394, v27 +387, b78 +385, v25 +361 (newest three within noise).
