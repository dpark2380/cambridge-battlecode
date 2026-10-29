# v32: v27 + B83 (clusters priced at 250, not 500)

## Evidence
v25-v31 ranked (460 games, 50%): 00gem_fields 1-10, 00elkring 1-6. On 00gem_fields:
- Top teams open on G4/G5 (1 elk + 8 clusters, 71 gems + 90 gold) at r25-31. We take lone 7-gem clusters first and
  G4 at r126-143 (`tools/openings.py`).
- We earn 700-1,900 gold a game; they earn 2,300-5,600.

`world.cpp` priced each cluster at 500 health (real 120) in groups with a monster, so G4 looked like 6,400 health.

## Change
`cluster_effective_health` 500 → 250.

## Results (`data/b83-race.txt`, `data/b83-gates.txt`, `data/b83-gain.txt`)
- Race vs v27: 58% (81/140); at 120 health, 55%. Gain gate vs v27: 50% (211/420), FAIL, so neutral locally.
- Map gate on gem-fields + elkring: 45% (local opponent v27 shares the mispricing).
- Nonreg PASS vs v12 80%, Jame v3 92%.
- Mechanism check, 00gem_fields vs v12:
  - gems at r250: 213 vs v27's 138;
  - gold earned at r500: 762 vs 461.
