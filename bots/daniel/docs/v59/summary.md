# v59: v51 + B137, walk to a cluster group's approaches when the chosen cluster has no path

**Change (`src/bot.cpp`, `work_group`):** when `move_towards_closest` cannot reach the chosen camp's own tile and that camp is a gem or gold cluster, walk to the tiles beside the group (its approaches) and strike whichever live member of the group is in reach. Monster targets keep v51's behaviour: no step, and after `stall_turns` the group is skipped.

**Why (v51p2 panel):** 00vault was 0-6, with gems at r500 of 190 against 700. In match 6c423894, meowest cleared the 49-cluster block G0 (343 gems) at r47 and captured it 3 times by r374. Our four bodies stood still at (22,22)-(23,25) from r4. A debug build (`dbg r5 at 22,22 tgt 14,18 moved=0`, every turn) showed why. From r4 every body targeted clusters (15,18)/(14,18), which it could see through the holes at (15,19)/(16,19). The camp tile's neighbours are clusters, walls and holes, so the distance field had no path. After 14 turns `watch_progress` skipped the group for `give_up_rounds`, and the bodies farmed the 4-gem gold groups instead.

**Rejected variant:** the fallback for monster targets too. 03the-front went 5-6 of 18 against v51 (margin −115 to −131): its elks sit inside a ring of gem clusters (`gkg`), and walking up to them was worse than v51's give-up.

**Local results:**
- vs prof-meowest on 00vault: gems captured 391 → 1,053; the opponent's fell from 1,097 to 16.
- vs v51, 00vault + 03the-front, 8 seeds: vault 11/18 (+120), front 8/18 (−15).
- profgate vs v51 (6 profiles × 15 panel maps × 2 sides, paired): margin **+81 ± 32**, deaths **−0.6 ± 0.3**, gold +19 ± 99, captured +28 ± 16.
- nonreg vs v51: PASS, 173/344 = 50%; gems −7 ± 25, deaths +0.2 ± 0.6.

02the-pond is unchanged: its island clusters need teleports (B132).

**Decision metrics:** panel `v59p2` vs `v51p2` (`panelcmp.py`): gem margin, gems captured, and 00vault in particular.
