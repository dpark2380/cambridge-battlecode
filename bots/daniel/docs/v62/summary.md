# v62: v61 + B140, work a lone monster ringed by its own clusters from outside the ring

**Change (`src/bot.cpp`, `work_group`):** B137's fallback (walk to the group's approaches, strike any member in reach) now also applies to a monster target when the group's damage is at most one elk's (60). Groups with more damage keep v51's give-up.

**Why:** we are 1-11 in ranked on both 00gem_fields (captures 30 vs 57 a game) and 01concentrated_wealth (39 vs 54) since v50. Their richest groups are a single elk inside a ring of clusters, 71 gems each: 00gem-fields G4/G5 beside each spawn (1 elk, 8 clusters) and 01concentrated-wealth G0 in the centre (1 elk, 20 clusters, 330 gold). The elk has no path, so the target stalled and the group was skipped. 03the-front's 2-elk rings lost when worked this way in B137 testing, so they are excluded.

**Local results:**
- arena vs v61, 6 seeds: 00gem-fields 12/14 (+229), 01concentrated-wealth 11/14 (+220), 03the-front 7/14 (+0).
- nonreg vs v61: PASS, 172/344 = 50%.
- profgate vs v61: margin +0.6 ± 0.6, so the panel maps are essentially unchanged.

**Decision metrics:** rides v60's panel, being near-identical on panel maps. Judge it on ranked games on 00gem_fields and 01concentrated_wealth.
