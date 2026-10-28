# v24: v23 + B64 (the gold squad fights)

## Problem
Research note `docs/research/path-to-60-2026-10-28.md` §4: in `fight_enemies`, Vesper, Marcella and Vendetta (the
gold squad) only hit what is already in range and never step towards an enemy. Our Vendetta dealt about 1.8k champion
damage a game against the opponents' ~10k, and was next to an enemy in 17% of contact rounds (theirs 27%). We lose by
failing to kill: our death rate per contact is the same in wins and losses, theirs falls from 16% to 5%.

## Change
The gold squad closes in on the weakest enemy like the duo does, when the fight check says we are even or ahead.

## Results (`data/b64-race.txt`, `data/b64-gates.txt`)
- Race vs v23: **b64a 66% (92/140)**; b64b (only when an ally is within 2 of the target) 51%.
- Gain gate vs v23: **61% (172/280), PASS**.
- Nonreg PASS: vs v22 64%, v12 77%, Jame v3 91%, hunter-v0 94%.
