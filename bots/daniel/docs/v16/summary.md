# v16 (from v15): bodies join camps (B36)

## Evidence
- tools/benchmark.py, v14's 240 ranked games vs scouted top-20 rows: first clear is the largest gap (z -2.41 over
  68 maps), then gems at r1000 (-1.18) and deaths (-1.08).
- tools/openings.py 00elkring: top teams clear the nearest elk camp at r10-13 and chain one every ~15 rounds
  (median clears #1/#3/#5 r12/42/103); ours r49/58/161.
- Local v15 vs v14 on 00elkring: four bodies on four elk camps, solo or in pairs, down to 25% health over 30+ rounds.

## Change
choose_target values a body joining a claimed group at its full share (extra_body_value 0.4538 → 1.0), and up to
three bodies take a non-siege group (max_group_bodies 2 → 3).

## Results
- Race vs v15 (140 games each): mgb3 53%, mgb5 50% (cap alone does not bind); join3 63%, join5 60%.
- Gates: gain 165/280 = 59% vs v15; nonreg 173/280 = 62% vs v12, 218/280 = 78% vs Jame v3 (all PASS, data/b36-gates.txt).

## Weaknesses / next
- Not tuned: 1.0 and 3 are the first values tried; tune.py over extra_body_value, max_group_bodies, help_wait_turns.
- Check the ranked first-clear gap closes (benchmark.py on v16's games).
