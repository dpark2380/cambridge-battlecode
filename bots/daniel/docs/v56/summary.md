# v56: v55 + B134 (v52 + B133b + B134; B130b dropped), Vesper receives gold captures

**Change (`src/bot.cpp`, the `reward_ready` block of `work_group`):** when a group's reward is waiting, no enemy was seen for `threat_memory` rounds, the group carries gold, and a Vesper ally is within 3 of its spawn tiles, a non-Vesper body steps beside the tiles (off them if it was on them) and skips the group for 10 rounds so Vesper takes the capture alone.

**Why (review H9):** Vesper gains 20% more gold (40% with her Treasure emblem); top teams' Vesper earns 2.7k gold a game to our 1.9k. B90 (the same idea on v34) raced 48% in self-play and was parked; the panel can measure gold and per-champion `earnedGold` directly.

**Local gate (as `b134` on v54):** nonreg PASS 50% (280); A − B per game gold +115 ± 232, gems +3 ± 28, deaths 0.0 ± 0.7.

**Decision metrics:** `panelcmp.py v55p2 v56p2` gold, gold/clear, margin; Vesper's `earnedGold` share from the summaries.
