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
- Mechanism check vs Jame v3 (10 maps × 2 sides, `tools/fights.py`): Vesper adjacent 13% vs v26 14%, healthy-1v1 deaths 5% vs 9%. Jame does not chase her, so this is weak evidence; the panel is the test.
- Gauntlet (`data/gauntlet-v28.txt`): v28 +394, v26 +394, v27 +388, v25 +364.
- Nonreg vs v25 58% (162/280) PASS (`data/v28-gates.txt`).

## Scrim panel (19:38Z, 90 games, `data/scrims/v28`)
**31-59 vs v26's 27-63** on the same setups. Paired: v28 won 7 setups that v26 lost, v26 won 3. Gold 5,783 vs 5,531,
deaths 17.0 vs 17.7. Vesper on the panel (`tools/fights.py`): healthy-1v1 deaths 34% vs 39%, adjacent 26% vs 28%.
The direction is right, but she is still far from top teams' 12% adjacency.

## Ranked and revert (20:47Z)
14-21 over 35 ranked games: gold 4,608 (v26 5,272), deaths 12.8 (11.8), opponents' gold 5,130 (v26's 5,646). That met
the trigger (≤ ~44% at 35 games) with no stronger field, so v26 was resubmitted. The panel's +4 (31 vs 27) did not
hold in ranked.
