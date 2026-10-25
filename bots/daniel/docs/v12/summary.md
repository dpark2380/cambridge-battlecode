# v12 (in development, from v11)

Aimed at sprint 3: the 30 maps added on 2026-10-25 (`02*`, `adgato-gemcombat*`, and ten `00*`; list in
`data/new-maps-2026-10-25.txt`). v11 is 51% vs v10 there, against 59% on the old 40 maps. Targeted changes are
map-gated on the new maps, with an all-map nonreg vs v11. Backlog ids refer to `../backlog.md`.

## B25: draft the top-20 core (accepted 2026-10-25 23:50Z)

**Evidence.** Top 20, 750 games: Vesper 90%, Heart of Ruin 84%, Marcella 82%, Vendetta 67%, Ryth 45%; Stellar 3%
(36% win), Cassi & Issac 10%. Our draft leaned on Stellar, Cassi & Issac and Tavi, and **could not pick Heart of
Ruin at all** (an 11-champion roster from before the week 2 patch). Our Marcella and Heart of Ruin bought strength;
the top 20 buy Bruiser:Focus for both (Marcella's focus grows 10 a level vs strength 5; Heart of Ruin's dash damage
scales with focus).

**Change.** `draft.cpp`: Heart of Ruin in the roster (melee, 1000 health, shield, stunning area dash); the draft
takes Vesper > Heart of Ruin > Marcella > Vendetta > Ryth in that order and scores the map for any further pick.
`bot.cpp` `build_stat`: Marcella and Heart of Ruin buy focus.

**Results** (`tools/arena.py`, real drafts, 70 maps x 2 sides; seeded gates do not test drafts because seeded games
use random rosters):

| Variant | vs v11 | vs v10 | vs v9 | vs Jame v3 |
|---|---|---|---|---|
| Heart of Ruin added to the scored roster | 57/140 = 41% | | | 90/140 = 64% |
| Base values re-weighted towards the meta | 72/140 = 51% | | | 92/140 = 66% |
| **Fixed core order + focus builds (kept)** | **108/140 = 77%** | **110/140 = 79%** | **114/140 = 81%** | **111/140 = 79%** |
| Fixed core order, old builds | 94/140 = 67% | | | |
| v11 itself | | | | 92/140 = 66% |
