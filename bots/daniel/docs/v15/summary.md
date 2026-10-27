# v15 (from v14): deliver gems on 01boss_battle (B34)

## Evidence
- v14 ranked 01boss_battle 1-4, 0 gems banked in all five; v13 2-3 with 3 games tagged frozen.
- Losses 0:1013 to 0:1527: opponents bank nothing until ~r900, then kill the Monolith (G16, 2 tiles, 20,000 HP
  each) and tribute from its spawn tile (24,20), the only walkable tile beside the altar (25,20).
- Local v14 vs v13: 0:0 at r2000, carriers holding 100-240 gems. Cause: v8 removed camp spawn tiles from the
  altar tiles, so `gems_deliverable = false` and gems were valued at 0.

## Change
`init`: remove camp tiles from the altar tiles only if a camp-free one exists. Otherwise keep them; the altar
then counts as walled in and B29's breach gathers beside the Monolith and strikes it.

## Results
- Local seed 0: v15 656:0 vs v14. Monolith first down ~r1500; 24 deaths, 22 to camps (piecemeal strikes).
- Rejected: strike a Monolith corridor only with the whole team, cutting both tiles: 0:0, never gathered.
- Gates (data/b34-gates.txt): map 01boss-battle 59/60 = 98% vs v14 (PASS); nonreg 138/280 = 49% vs v14, 142/280 = 51% vs v12, 183/280 = 65% vs Jame v3 (all PASS).

## Weaknesses / next
- B34b: the kill is slow and costly. Opponents reach 1013 by r900.
