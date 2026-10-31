# Daniel v40: v38 + B112a (lone Vesper/Heart of Ruin fall back)

Code: `bots/daniel/v40` = `bots/daniel/v38` plus B112a at the top of `fight_enemies` (`bot.cpp`).

## Evidence (backlog B112)

19 v38 ranked loss replays decoded with timelines (2026-10-31). Vesper died 88 times: 68% with no ally within 4 tiles,
43% outnumbered by 2+, and only 11% below half health 10 rounds earlier. Heart of Ruin died 80 times: 55% alone, 34%
outnumbered, 11% hurt beforehand. They are burst from healthy while alone. In v38's losses, deaths to champions at
r300-1000 are 7.8 a game vs 3.2 in wins.

## Change

A Vesper or Heart of Ruin with no ally within 4 that sees 2+ enemies within 6 marks danger and falls back toward the
nearest ally (within 12) or home before the fight, still striking if a target is in reach.

## Tests

| Gate | Result |
|---|---|
| Nonreg vs v38 | PASS 285/560 = 51% |
| vs hunter-v0 (420 games) | 91% (v38 93%) |
| Nonreg vs v12 / Jame v3 | PASS 82% / 93% |

Locally neutral, as expected: no local bot hunts lone bodies. Ranked trial from 2026-10-31 02:30Z as team bot version 50,
against v38's 83-62 over 145 (21:15Z-02:10Z). Sprint 3 rule: the bot live at the deadline is the best proven one.
