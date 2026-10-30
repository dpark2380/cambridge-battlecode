# Daniel v38: v34 + B109 (02guardians gate)

Code: `bots/daniel/v38` = `bots/daniel/v34` plus backlog B109 (three lines in `breach`, `bot.cpp`). Built after v37 was
auto-reverted (10-20 over 30 ranked games); v37's B99c is not included.

## Change

02guardians: two Monoliths (20,000 health, 200 damage) seal the only altar. We scored 0 gems in 9 of 12 ranked games
since v27, carrying 1,000+ gems until the opponent broke in. In `breach`, a carrier with 100+ gems and more than 60%
health now strikes the gate alone (Monoliths never heal; it recalls as usual when hurt). Before, it struck only with
two allies gathered.

## Tests (vs v34)

| Gate | Result |
|---|---|
| Map (02guardians, 01boss-battle) | PASS, 50/80 = 62% |
| Nonreg, all maps | PASS, 141/280 = 50% |

The same change on v37 passed 40/60 = 67% (map) and 140/280 = 50% (nonreg). Expected ranked effect: about +1 point
overall, from the 2-3% of games on 02guardians. Elsewhere it plays exactly like v34.
