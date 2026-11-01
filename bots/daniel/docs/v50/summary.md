# v50: v49 + B128a, camp-group exposure priced one monster at a time

**Change:** in `src/world.cpp`, a group's `exposure` is the sum of each fighter's `health × own damage` instead of `health × the whole group's remaining damage`. `choose_target` turns exposure into the health a body pays to clear the group (and `survivable()` into how many bodies it needs), so the change re-ranks multi-monster groups against small ones without touching anything else.

**Why (H1 of the process review, `tools/captures.py v47`):** on the v1 panel we make as many captures as the opponents (48 vs 53 a game) for 547 gems vs their 892. Per map they re-farm the big groups and we re-farm the small ones: on 00eight our 37-gem elk group 0× a game vs their mirror 8.2×, our 11-gem wolf 10.3×; 00ribs 43-gem groups 3× vs 7×; 00vault's 343-gem cluster 0.5× vs 3.0×. A debug print of `choose_target` on 00eight charged the 2-elk group 2,009 HP for a 1,200-HP body (2 bodies needed, +50 `help_wait_turns`, 75 turns of trips home): rate 0.183 vs 0.192 for the 8-gem wolf pair beside it. The rules say damage wakes the whole group (GameRules l.207), so the new figure is deliberately optimistic; a local v47 mirror on 00eight took the elk groups 7-9× a side with 57-77k monster damage and 1-5 camp deaths, so the damage is survivable.

**Also in v49/v50:** `random_team` draws seeded rosters by the top-30 teams' draft rates (process review #5), a no-op in real drafts.

**Local tests:**

| Test | Result |
|---|---|
| race vs v47 (140 each, as `b128a`/`b128b`) | 47% / 45% (b128b = + help_wait 20) |
| nonreg `b128a` vs v47 | PASS 49% (560) |
| nonreg v50 vs v49 | PASS 49% (980) |

**Decision metrics:** `tools/captures.py v50p2` per-group captures of the 22-59-gem groups vs `v49p2`; `panelcmp.py v49p2 v50p2` gems captured, gem margin, deaths (camp deaths in particular).
