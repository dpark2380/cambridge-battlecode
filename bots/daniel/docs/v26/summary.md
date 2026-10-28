# v26: v25 + B68 (who closes in) + B70 (Heart of Ruin health) + B71 (dash escape)

## Evidence
`tools/fights.py` on the scrim panels (same 60 setups), v22 → v25:
- Enemy deaths per contact rose from 7% to 12%; ours rose from 24% to 28%.
- Outnumbered 2v1 deaths rose from 34% to 47%, 3v1 from 48% to 74%.
- Healthy-1v1 deaths: Vesper rose from 25% to **42%**; Vendetta fell from 20% to 11%, Ryth from 27% to 19%.

B64's closing in works for Vendetta and Ryth, but it feeds Vesper and outnumbered bodies.

## Change
In `fight_enemies`, after a missed strike:
- Vesper does not close in.
- No body closes in while outnumbered (enemies within 4 > allies within 4, counting us).

## Results (`data/b68-race.txt`, `data/b68-gates.txt`)
- Race vs v25: 49% (b68a Vesper only 49%, b68b outnumbered only 48%).
- Nonreg PASS: vs v25 49% (276/560), v22 66%, Jame v3 90%.

It is neutral locally because our own bots do not punish these fights. The evidence comes from real opponents, so judge v26
on its scrim panel against v25's 14-46: fewer outnumbered and Vesper deaths, with kills kept near 8.8.

## B70: Heart of Ruin builds health like the top teams
Scout 2026-10-28 13:42Z (top 20 teams, 2,000 games): top Heart of Ruins buy ~64% of their Bruiser shards as health; ours
bought 40% (`power_health_share`). Ranked v25: our HoR dies in 30% of healthy 1v1s, theirs in 19%. v26 gives HoR a
0.65 health share. Race vs v26-without-it: 51% (0.80: 51%); nonreg 52% (`data/b70-race.txt`, `data/b70-gates.txt`).
- Final v26 nonreg PASS (`data/v26-gates.txt`): vs v25 50% (208/420), v22 66%, v12 80%, Jame v3 91%.

## B71: Heart of Ruin escapes with its dash
Ranked v25 timelines (`replays/daniel-v25/timelines`), 122 HoR deaths:
- 85 had no ally within 3 eight rounds before, and 109 were above 50% health then.
- Typically HoR stood adjacent to an enemy and lost 80-150 a round to 0, because the enemy followed its one-tile retreat.

`move_towards_closest` kept damage dashes for fights. Now, when leaving with an enemy close, a body strikes, then
retreats with any dash allowed. Race vs v26-without-it: 59% (82/140). Gain gate **58% (163/280) PASS**. Nonreg vs v25
58%, v12 79%, Jame v3 91% (`data/b71-race.txt`, `data/b71-gates.txt`).

**v26 as a whole is 58% vs v25, the live bot.**
- Gauntlet (old 8-bot pool): v26 +373 vs v25 +365 (saturated pool).
- Gauntlet with v18/v22/v25 in the pool (`data/gauntlet-v18-v26.txt`): v26 +399, v25 +375, v18 +297, v22 +293; v26 vs v25 162/280 (58%).
