# Daniel v45: v44 + B120 (lone fall-back for every champion)

Code: `bots/daniel/v45` = `bots/daniel/v44` with the lone fall-back (no ally within 4, 2+ enemies within 6 → fall back
toward an ally or home before the fight) applied to every champion, not only Vesper and Heart of Ruin.

## Evidence

Caution stack on the fresh panel (2026-11-01): v41 24-66 (deaths 19.0) → v43 24-66 (17.7) → v44 28-62 (15.8). Vendetta and
Marcella also die alone 61-65% of the time (B112, 19 loss replays).

## Tests

| Gate | Result |
|---|---|
| Nonreg vs v44 | PASS 145/280 = 52% |
| Nonreg vs v12 / Jame v3 | PASS 81% / 89% |

Next: scrim A/B vs v44's panel (28-62, deaths 15.8) and a ranked comparison with v44 at the same rating.
