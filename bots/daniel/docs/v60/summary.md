# v60: v59 + B138, cut through camps when no path exists (03fan)

**Change (`src/bot.cpp`, `move_towards_closest`):** if the distance field cannot reach our tile and the goals are free tiles, recompute it with camps as passable. If the next step is a living camp, strike it; otherwise walk the new field. Monoliths and Golems are never struck this way. A cleared group stays open until someone captures it.

**Why:** in ranked v51-v58 we were 1-9 on 03fan, with 0 gems in 7 of those games. A scan of v59 against prof-aynir on every map found 620 `stalled` lines on 03fan and at most 50 anywhere else. Each spawn quarter of 03fan (293 tiles) is sealed by walls and holes, and every exit and the altar are behind wolf or gold camps. `choose_target` measures travel with camps as passable, so the gem groups outside look reachable. `move_towards_closest` treats living camps as walls, so the field from spawn is unreachable (`field=65535`). Every target stalled and was skipped in turn, all game. The profile bots share our movement and freeze the same way.

**Rejected variant:** cutting through for any goal. 02tangle went 3/18 (−348), because bodies cut through the clusters around the Golem to reach it. The cut-through now needs free goals: approaches, the altar, spawn.

**Local results:**
- vs prof-aynir on 03fan: we won 1,008-0 in 466 rounds (v59: 0-0 after 2,000).
- arena vs v59, 8 seeds: 03fan 18/18 (+1,011), 02tangle 9/18 (−10).
- nonreg vs v59: PASS, 177/344 = 51%; gems +16 ± 25, deaths −0.0 ± 0.6.

**Decision metrics:** panel `v60p2` vs `v59p2` must not be worse (03fan is not a panel map). Ranked games on 03fan.

**Result:** Panel v60p2 vs v59p2 (paired, 90): 89/90 identical outcomes, wins 53 → 52, margin −2 ± 6, deaths +0.06 ± 0.05: neutral as expected (03fan is not a panel map); kept. Versions 78 (v61) and 79 (v62) went live during the panel's last games; they play the panel maps the same way.
