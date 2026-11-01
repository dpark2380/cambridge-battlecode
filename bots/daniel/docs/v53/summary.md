# v53: v52 + B133a, Monster-first build on cluster maps

**Change (`src/bot.cpp`, `build_order`):** when the draft plan's `free_share` is at least 50% (half or more of the map's gems sit in groups that do not hit back), the build becomes Monster (+10% camp damage), Prospector, Treasure, Durability, then Bruiser — Jungle (30% less camp damage taken) is dropped, as clusters deal none. Other maps keep v48's order (Treasure, Prospector, Durability, Jungle, Bruiser). On the panel this is 00galaxy (93% free), 00vault (96%) and adgato_gemcombat2 (100%); 02the_pond (47%) and 02arena (41%) are just under.

**Why (B133, v51p2 panel):** 00vault is a kill-speed race for the central 49-cluster block (343 gems): we capture it 0.7× a game to the opponents' 4.0× (1,143 gems a game), with 26k monster damage done to their 36k; 00galaxy's central cluster group 6.2× vs 15.5×.

**Local gate:** nonreg vs v52 PASS; A − B per game gems −3 ± 30, deaths +0.1 ± 0.7, gold −25 ± 250 (only 3 of 70 maps are affected, so mirror play shows nothing).

**Decision metrics:** `captures.py v53p2` on galaxy/vault/adgato2 (captures of the cluster groups, gems captured) and `panelcmp.py v52p2 v53p2`.
