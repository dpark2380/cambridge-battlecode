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

v12 vs v11 by map set (real drafts): old 40 maps 56/80 = 70%, new 30 maps 52/60 = 87%.

## B24: opening scripts (rejected 2026-10-25 23:52Z)

The top 20's usual first 3 groups per map and side (`tools/openings.py --export`, 40 maps) worth x1.5/x2/x3 in rounds
< 300. Race vs v12: 49% / 48% / 44%; real drafts x1.5: 68/140 = 49%. No gain once the draft matches theirs.

## B26: learned target choice (parked 2026-10-25 23:52Z)

`tools/targetmodel.py` fits a conditional logit over 'which group next' to 22,459 top-team decisions and 19,764 of
ours (held-out top-1 21% vs nearest-available 22%; log-likelihood −2.49 vs uniform −3.00). Top teams re-clear the
group they just took half as readily (−1.51 vs −0.74) and favour groups that are up (+0.28 vs −0.08). The bot
change that follows (waiting at a respawning group beyond the walk costs `wait_penalty` x extra): race x0.5/x1/x2
73/73/66 of 140; gain gate x0.5 954/1820 = 52%, inconclusive; nonreg 53% PASS; real drafts 69/140 = 49%. Not applied.
