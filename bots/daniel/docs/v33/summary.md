# v33: v32 + B84 (gold-only clusters at 250)

v32 (B83: clusters in monster groups at 250, not 500) plus B84. Monster-free groups with gems keep B56's real 120 per
cluster; 0-gem gold-only groups are priced at 250.

Evidence (`docs/research/worst-maps-2026-10-29.md`): B56 made 0-gem gold groups the best target, because they pay no
damage cost, altar trip or split. On corners/rows/gold_rush/boss/fracture/collision we went 69-47 (59%) before B56 and
16-41 (28%) after. In our first 300 rounds 50-100% of clears were gold-only (top teams 14-26%), and we still had less
gold by r300.

Locally (`data/b84-race.txt`): race vs v27 53%; map gate on the 6 maps vs v27 49%. At 500 per cluster the map gate was
40%, because v27 farms gold groups and wins the late fights in self-play. Ranked is the judge.
- Nonreg PASS: vs v27 50% (212/420), v12 80%, Jame v3 92% (`data/v33-gates.txt`).

## Submitted 2026-10-29 04:16Z (team bot version 29, user-approved). Scrim panel (90 games)
30-60 vs v27's 32-58; paired: v33 won 11 setups v27 lost, v27 won 13. Level, as expected: the panel's maps barely
overlap the target maps (only 00collision). Ranked results on the worst maps decide.
- Ranked, 30 games (16-14): gems r500 217 vs their 182 (ahead), but `tools/fights.py` shows deaths per contact 21% (v27 17%)
  and Vesper healthy-1v1 33% (v27 26%). The pricing change may send bodies into bigger groups where enemies catch them;
  recheck at ~60.
- Ranked final (07:49Z, 105 games): **54-51**. 46-34 at 80 games (#207, 1702 at 06:56Z), then 11-19 over the last 30 against stronger opponents (their gold 5.4k → 6.0k, their deaths 13.0 → 8.2; ours 12.3 → 13.6). The auto-revert trigger fired on the last 30 (37%) but looked like a field shift; the user chose to submit v34 instead of reverting to v27.
