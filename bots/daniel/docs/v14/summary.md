# v14 summary (from v13)

## Change: B29b, the_pack gather check

**Evidence.** v13's first ranked 02the_pack game (match 611f181c, side B) ended 0:0. Decoded with the T10 fix:
from r221 to r2000 Vesper (26,24), Heart of Ruin (26,25) and Marcella (22,27) stood still at full health, all
inside `corridor_gather`. `breach()` struck only once 2 allies were within 3 tiles of the body itself; Marcella
was 4 away, so no body ever saw two allies and nobody struck.

**Change.** `gathered` counts visible allies standing in `corridor_gather` (one line in `breach()`).

## Results (`data/b29b-gates.txt`)

| Test | Games | Result |
|---|---|---|
| map 02the-pack vs v13 | 60 | 32/60 = 53%, FAIL (map gate wants 65%) |
| nonreg vs v13 | 280 | 50%, PASS |
| nonreg vs v12 | 280 | 51%, PASS |
| nonreg vs Jame v3 | 280 | 66%, PASS |

Zero-gem games on 02the-pack (10 draft seeds, both sides, vs v12 and Jame v3, ranked fuel): v13 13/44, v14 9/44.
The map gate cannot show the ranked deadlock because local carriers usually bunch, so the win rate barely moves.

## Weaknesses

- **B29c:** in 3 of 10 seeds as side A, all three bodies strike at r94-113 and die to the woken ring, then two
  carriers wait at the corridor forever while the third stays by gold group 19 (23,13). Not yet diagnosed.
- the_pack is about 1 in 70 ranked games, so the expected ladder effect is small.
