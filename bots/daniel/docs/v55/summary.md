# v55: v54 + B133b, four bodies on cluster-only groups

**Change (`src/bot.cpp`, `choose_target`):** a group with nothing that hits back may take `max_group_bodies` + 1 = 4 bodies instead of 3; monster groups keep 3.

**Why (B133, v51p2 panel):** 00vault's 49-cluster block (24.5k HP, 343 gems) is a kill-speed race: we capture it 0.7× a game to the opponents' 4.0×, our monster damage done 26k to their 36k, and with the 3-body cap the fourth body idled on 4-gem wolf groups.

**Local gate:** nonreg vs v54 PASS; A − B per game gems +9 ± 28, deaths +0.0 ± 0.7, gold −26 ± 248, gems captured +11 ± 25 (few maps affected).

**Decision metrics:** `captures.py v55p2` on 00vault/00galaxy/adgato2 + `panelcmp.py v54p2 v55p2`.
