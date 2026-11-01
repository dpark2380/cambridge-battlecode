# v47: v46 + B124 (B99c Vesper escapes, from v37)

**Changes in `src/bot.cpp`:**
- Plain movement dashes are kept for escapes while an enemy was seen within `threat_memory` rounds (`save_dash`).
- Vesper leaves at 50% health with an enemy in sight.
- A leaving Vesper runs instead of shooting back, unless her target is below 25% health.

**Why:** in v45's scrim panel (fights.py), our healthy Vesper dies in 34% of 1v1s. The opponents' Vesper dies in 8%, and none of our other champions comes close. B99c as v37 posted the best panel on record: 32-58 with 14.2 deaths a game, against v34's 30-60 with 17.7. It also went 16-9 in ranked during its A/B. It was reverted after 10-20 over its next 30 ranked games, but windows that short proved to be noise near our equilibrium rating.

**Local gates (nonreg):**

| Opponent | Score | Games | Result |
|---|---|---|---|
| v46 | 51% | 560 | PASS |
| v12 | 77% | 280 | PASS |
| Jame v3 | 88% | 280 | PASS |
