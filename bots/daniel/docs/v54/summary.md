# v54: v53 + B130b, a death at the target marks it a battleground

**Change (`src/bot.cpp`, before the leave check):** when a body is back at spawn with full health after a death (no alive turn for 20+ rounds, or 0 health on its last turn), and its last alive position was within 8 of its target group's anchor with an enemy champion seen within `threat_memory` (30 rounds) before the death, that group gets `skip_until = round + 150` for this body (`battleground_rounds`). The group is still visible to the other bodies.

**Why (B130, v48p2/v50p2 panels):** on 00eight our bodies spend 650-1,200 rounds a game within 5 of the 2-elk group beside our spawn, 12 of our deaths a game are champion kills there, and we capture it 0.2× a game (the opponents take their mirror 8.8-10×); after each death the body walked straight back. B130a (start such groups only with an ally near) was neutral with negative deltas.

**Local gate:** nonreg vs v53 PASS; A − B per game deaths −0.8 ± 0.7, gems +8 ± 24, gold +188 ± 208, gems captured +18 ± 20.

**Decision metrics:** `panelcmp.py v53p2 v54p2` deaths and gem margin; deaths near the 00eight/00interlock/00collision elk groups.
