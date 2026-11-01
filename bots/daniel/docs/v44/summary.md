# Daniel v44: v43 + B112a (stack the caution changes)

Code: `bots/daniel/v44` = `bots/daniel/v43` (fight only at ≥1.2x power) plus B112a from v40: a lone Vesper or Heart of
Ruin (no ally within 4) that sees 2+ enemies within 6 falls back toward the nearest ally or home before the fight.

## Evidence

- v43 ranked 23-12 over 35 in its first stint (v41 ~50% at the same rating, 3-12 right after the revert).
- B112a alone (v40): scrim panel 27-63 vs 24-66, deaths -3.1/game; ranked level with v38.

## Tests

| Gate | Result |
|---|---|
| Nonreg vs v43 | PASS 481/980 = 49% |
| Nonreg vs v12 / Jame v3 | PASS 81% / 92% |

Next: scrim A/B against v43's panel (24-66, deaths 17.7) and a ranked comparison with v43 at the same rating.
