# v49: v48 + B127, Heart of Ruin leaves at 50% with an enemy in sight

**Change:** one line in `src/bot.cpp` next to Vesper's B99 rule: when an enemy champion is visible, Heart of Ruin's leave threshold becomes at least 0.5 of max health.

**Why:** on v47's panel (`tools/fights.py`), Heart of Ruin became our worst champion in healthy 1v1s, dying in 25% of 277 (opponents' HoR 19%), after the same rule cut Vesper's rate from 34% to 11%.

**Local gates (nonreg):**

| Built on | Opponent | Score | Games | Result |
|---|---|---|---|---|
| v47 (`b127`) | v47 | 49% | 280 | PASS |
| v47 (`b127`) | v12 | 77% | 280 | PASS |
| v47 (`b127`) | Jame v3 | 87% | 280 | PASS |
| v48 (`v49`) | v48 | 50% | 301 | PASS |

**Decision metric:** HoR healthy-1v1 death rate on its panel-v2 run (`fights.py`) against the v48p2 baseline of **19% of 394** (opponents' HoR 18%; on panel v2 our engagement deaths are 14% vs their 15% and every other champion 7-9%, so the v1 figure of 25% was partly the stronger opponents), and `panelcmp.py v48p2 v49p2` deaths and gem margin. Deaths while walking home stay the one asymmetry: 46% of ours vs 30% of theirs. It is a threshold change, the family the process review parks, kept only because it has this target metric.
