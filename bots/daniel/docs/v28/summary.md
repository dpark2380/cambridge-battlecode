# v28: v26 + B78b (Vesper kites)

## Evidence (`docs/research/fight-benchmark-2026-10-28.md`)
60 top-10 replays on 20 maps vs v26's 65 ranked games (`tools/fights.py`):
- Overall trade is close: deaths per contact 15% vs 16%.
- Vesper is the gap. Her healthy-1v1 deaths are **10% vs 28%**, and she is adjacent to an enemy in 12% of contact
  rounds vs 20%. Top teams keep her at range; she is ranged, with a 2-tile travel dash.

## Change
In `fight_enemies`: when a ranged Vesper has an enemy adjacent and her attack is on cooldown, she steps or dashes to a
tile within range of her target and next to no enemy. When the attack is ready she shoots as before. A ranged body
cannot walk and shoot in one turn, so this is kiting.

## Results (`data/b78b-race.txt`, `data/b78b-gates.txt`)
- Race vs v26: 50% (70/140). B78 without the cooldown condition scored 46%, losing shots.
- Nonreg PASS: vs v26 50%, v12 79%, Jame v3 91%.

It is neutral locally because our bots do not punish adjacent trading. Judge it on the panel (v26: 27-63) and on
Vesper's adjacency and healthy-1v1 deaths in its ranked replays.
