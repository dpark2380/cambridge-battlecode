# v64: v63 + B145, Teleport Crystals onto island groups

**Change (`src/bot.cpp`, `bot.h`):**
- **Island detection (`init`):** an island is a group worth 20+ gems (no Monolith) none of whose approaches our spawn reaches on foot (camps count as passable; walls, holes, altars and the enemy spawn do not). It also needs at least 5 shore tiles (mainland tiles within a crystal's range 3 of an approach). Its home distance becomes the recall (11) and its altar distance the recall plus the spawn's walk to an altar.
- **Shopping (`shop`):** on such maps every body buys a Teleport Crystal (10 gold, one held).
- **Pricing (`choose_target`):** an island target with a crystal in hand costs the walk to its shore + 4 (the 3-turn channel).
- **Getting on (`work_group`):** walk to the shore and teleport onto an approach.
- **Getting off (`take_turn`):** a body that teleported recalls home once it should bank, or when nothing reachable is left.

**Why:** we never used crystals. A sweep of the maps found gem groups that can only be reached by crossing holes: 00quadrants G0 (35 gems), 01big-world G2 (21), adgato-gemcombat4 G0/G1 (21), 03membrane, plus small or cramped ones. The pond's central island needs a stepping-stone hop beyond range 3 (B132), so this change does not cover it.

**Rejected variants:**
- recall whenever a body is off the mainland: dashes land bodies on islets (01islands 3/10).
- islands of 10+ gems with any shore: 01islands 33%, 01fracture 38% in the 6-map gain gate (G24 has a 2-tile shore; G0 is 14 gems).

**Local results:**
- gain gate on the 4 maps with qualifying islands: PASS, 48/72 = 67%; quadrants 14/18, big-world 15/18, membrane 9/18, gemcombat4 10/18; gems captured +100 ± 37.
- nonreg on all maps: PASS, 265/516 = 51%; gems +20 ± 20.

**Decision metrics:** panel `v64p2` vs `v59p2`/`v60p2` (01big_world is a panel map), and ranked.
