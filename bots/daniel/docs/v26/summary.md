# v26: v25 + B68 (who closes in) + B70 (Heart of Ruin health)

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
