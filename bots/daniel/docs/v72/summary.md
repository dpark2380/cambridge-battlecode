# v72: v71 + B180, heal to 95% at spawn

**Change (`src/bot.cpp`):** `spawn_leave_health` 0.7716 → 0.95. A body at spawn waits until it has 95% health before heading back out (0.7716 came from a v5 `tune.py` run).

**Gates:**
- vs v71, gain gate: inconclusive after 3,328 games, 52%; submitted gems +22.5 ± 7.8, gems captured +16.1 ± 6.5, gold +70 ± 44, deaths −0.1 ± 0.2.
- 1.0 vs 0.95: 254/512 = 50%, gems +18 ± 20 (no better).

**Tried on top and dropped (B181, B182):** an engage edge of 1.4x instead of 1.2x passed the gain gate against v71+B180 (54% over 768, deaths −0.5) with flat gems. Stacked as the first v72, it scored only 52% vs v71 over 1,536 with gems +3 ± 11 (B180 alone: +22.5), so it trades gems for deaths, and fight changes have passed locally and lost live before (B152). Threat memory 50 and help wait 30 were neutral.
