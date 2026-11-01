# v46: v45 + B121, carriers leave earlier

**Change:** `carrier_recall_health` 0.5 → 0.65 in `src/bot.cpp`, so a body carrying gems heads home at 65% health instead of 50%.

**Why:** the B112 death context showed 24-42% of deaths happen while carrying gems, and the killer takes them. The caution stack (v41 → v43 → v44) cut panel deaths from 19.0 to 15.8 a game.

**Local gates (nonreg):**

| Opponent | Score | Games | Result |
|---|---|---|---|
| v45 | 52% | 420 | PASS |
| v12 | 80% | 280 | PASS |
| Jame v3 | 90% | 280 | PASS |

**Status:** ready. It goes live after v45's A/B against v44 is decided.
