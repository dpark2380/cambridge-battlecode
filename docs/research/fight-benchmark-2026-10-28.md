# Fight benchmark: top teams vs our versions (2026-10-28)

All numbers come from `tools/fights.py` on decoded replay timelines. Top-team data are the newest 3 games per top-10
team on 20 maps (60 games, `data/scout/replays`, scouted 17:53Z and 18:29Z). "Healthy 1v1" means one enemy within 4
tiles, no ally within 5, and at least 80% health at contact; "died" means dead within 24 rounds.

| | Top 10 (60 games) | v26 ranked (65) | v25 ranked (75) | v26 panel (90) | v25 panel (90) |
|---|---|---|---|---|---|
| Deaths per contact | 15% | 16% | 21% | 26% | 30% |
| 2v1 against us | 30% | 32% | 32% | 41% | 50% |
| Healthy 1v1, Vesper | **10%** | 28% | 38% | 39% | 51% |
| Healthy 1v1, Heart of Ruin | 14% | 16% | 26% | 27% | 35% |
| Healthy 1v1, Marcella | 4% | 7% | 10% | 17% | 18% |
| Healthy 1v1, Vendetta | 15% | 9% | 12% | 16% | 15% |
| Healthy 1v1, Ryth | 11% | 11% | 18% | 20% | 21% |
| Vesper adjacent while in contact | **12%** | 20% | 23% | 28% | 30% |
| Deaths on the walk home | 33% | 29% | 34% | 37% | 38% |

The panel is our 6 hardest opponents on 15 maps, so its rates run higher than ranked.

## Reading
- v26 (65 ranked games) is close to the top teams on overall fight trade (16% vs 15% per contact) and Heart of Ruin (16% vs 14%). Vendetta and Ryth now trade at or above
  top-team level.
- The gap left is **Vesper**: she dies two and a half times as often as top teams' Vesper and stands next to enemies
  twice as often. Top teams keep her at range; she is ranged, with a 2-tile travel dash.
- Marcella (7% vs 4%) is a smaller gap.

## Candidates (not submitted)
- **v27** = v26 + B73: Vesper treats a fight as even only when ours ≥ 1.3 × theirs. 48% vs v26 locally.
- **b78** = v26 + B78: Vesper with an enemy adjacent steps or dashes to a tile in range of the target and next to no
  enemy. Race 46%, nonreg 48% over 840 games vs v26.

Both are neutral locally, which is expected: our own bots do not punish Vesper's melee-range trading the way top teams
do. Judge them on the scrim panel (v26: 27-63) and on Vesper's adjacency and healthy-1v1 deaths in its replays.

## Update 20:05Z: positioning explains little
Vesper's distance to the nearest enemy over contact rounds (Chebyshev, ≤ 4):

| | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| Top 10 (60 games) | 13% | 17% | 33% | 37% |
| v26 ranked (85) | 18% | 14% | 30% | 38% |

The profiles are close, so standing too close is only a small part of her 28% vs 10% healthy-1v1 deaths. The likelier
cause is which fights she takes. `visible_champions` rates her damage at max(strength, focus) = 100 against about 45
real, so the fight check sends her into fights she loses. B73 (v27: Vesper needs ours ≥ 1.3 × theirs) targets that.

v28 (kiting, B78b) went live at 19:37Z with panel 31-59 vs v26's 27-63. The next candidate is v28 + B73.

## Update 20:55Z: kiting failed in ranked
v28 (v26 + B78b kiting) ranked, 35 games: Vesper healthy-1v1 deaths **45%** (v26 28%), adjacent 24% (v26 20%); record
14-21, reverted to v26 at 20:47Z. Its panel lead (31 vs 27 of 90) was inside the panel's noise. So moving Vesper does
not fix her deaths, which points to fight entry (B73 / v27) as the next test.
