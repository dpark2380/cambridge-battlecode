# v25: v24 + B54 (Monolith only)

v24 plus v19's Monolith rule: a Monolith is struck only with min(team, 3) bodies within 6 of it. It does not
include B54b, the gather rule for every siege target, which regressed in ranked (v19 16-24, B58). A lone body
chipping a Monolith wakes it, and it hits our bodies at the camps beside it from behind walls (01corridors).

## Results (`data/b54v24-gates.txt`)
- Map gate on 01corridors vs v24: **68% (41/60), PASS** (on v18: 62%).
- Nonreg vs v24: 51% (144/280), PASS.

It changes target logic like B54b did, so judge it on ranked camp deaths in the Monolith's reach and on the panel's
corridors games (0-12 for v18 and v22).
