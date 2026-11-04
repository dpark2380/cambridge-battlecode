# v61: v60 + B139, gems first on a gem-starved map (03one-gem)

**Change (`src/bot.cpp` init, `bot.h`):** the target rate's gold weight (`gold_weight` 0.2) becomes a member, `gold_w`. It is set to 0.01 when the map's camp groups hold gold worth more than 10x all their gems (0.2 × total gold > 10 × total gems). Of the 86 maps only 03one-gem qualifies (7 gems, 1,600 gold); the next is 03ultrastarvation at a 0.4 ratio.

**Why:** we are 0-5 on 03one-gem in ranked, with our gems at 1 against the opponents' 129 a game. The map's only gems are one 7-gem cluster in a bush maze at (25,20). At weight 0.2 a 60-gold group rates 12 against the cluster's 7 plus an altar trip, so no body ever targeted it. The opponents farmed it every 50 rounds and won on gems at round 2000.

**Local results:**
- vs prof-meowest on 03one-gem: our gems 0 → 223.
- arena vs v60, 4 seeds: 03one-gem 10/10 (+215). 00galaxy and 03ultrastarvation are identical (+0), as on every map other than 03one-gem.

**Decision metrics:** behaviour is unchanged on the panel maps, so it rides v60's panel. Judge it on ranked 03one-gem games.
