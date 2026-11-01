# v51: v50 + B129, camp-damage-aware leave at every monster group

**Change (`src/bot.cpp`, the leave check):** the siege-style leave threshold now applies to every monster group within 5 of the body, with the real escape cost: `leave when health < (exit + 1) × group damage × remaining share / bodies at the group`, where `exit` = elk range (4) + 1 − own attack range (4 steps for a melee body, 2 for range 3). Before, a non-siege monster group had no camp-aware leave at all (a body stayed to `recall_health` 28.8% = 345 HP while two elks dealt 120 a turn and it needed 4 steps to leave their range), and the siege branch used a flat 3 escape turns.

**Why (v48p2 panel):** deaths to camps 1.87 a game vs the opponents' 1.32: 01starfish 15.0 a game (theirs 8.7), 00eight 5.3 (1.5), 01islands 3.3. On 00eight our bodies spend 650-1,200 rounds a game within 5 of the 2-elk group G0, die there 15.5 times a game (3.2 to the elks) and capture it 0.3×; camp kills also destroy the gems carried.

**Local gate:** nonreg vs v50 PASS 146/280 = 52%; A − B per game: deaths −0.0 ± 0.7, gems −4 ± 29, gold −90 ± 237 (mirror play cannot show a camp-death change this small).

**Decision metrics:** camp deaths per game on `v51p2` vs `v50p2`/`v48p2` (features rows `deaths_by.camp`; starfish and eight in particular), captures of the elk groups (`captures.py`), and `panelcmp.py` deaths and gem margin.
