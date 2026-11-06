# v66: v64 + B153, a gem-less group's gold counts up to 150

**Change (`src/bot.cpp`, `choose_target`):** in a non-siege group's value, the gold of a group without gems counts up to 150 (at most 30 at `gold_w` 0.2). Groups with gems are unchanged.

**Why:** the platform's 4 Nov patch (engine 3.0.0, SDK 5.0.0) added 42 maps (`04*`). A sweep of v64 vs prof-aynir on them found 04lines ending 11-0 at r2000 with 45 stalls. Its gem strips are walled by five 31-cluster gold groups (620 gold, 0 gems each). At weight 0.2 a wall rated 124 against 11-19 for a gem group, so every body farmed gold walls all game: 31k gold between the two teams and 11 gems.

**Local results (engine 3.0.0):**
- arena vs v64, 3 seeds: 04lines 8/8 (+872), 04orchard 7/8 (+322), 04hourglass 4/8 (+0), 00stampede 3/8 (+0).
- nonreg on all 128 maps: PASS, 258/512 = 50%; gems +6 ± 19.
- profgate vs v64: margin +4 ± 4 (the panel maps are almost untouched).

**Decision metrics:** ranked games on 04lines/04orchard. The change is near-identical on panel maps.
