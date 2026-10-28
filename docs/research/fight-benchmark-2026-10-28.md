# Fight benchmark: top teams vs our versions (2026-10-28)

All numbers come from `tools/fights.py` on decoded replay timelines. Top-team data are the newest 3 games per top-10
team on 20 maps (60 games, `data/scout/replays`, scouted 17:53Z and 18:29Z). "Healthy 1v1" means one enemy within 4
tiles, no ally within 5, and at least 80% health at contact; "died" means dead within 24 rounds.

| | Top 10 (60 games) | v26 ranked (35) | v25 ranked (75) | v26 panel (90) | v25 panel (90) |
|---|---|---|---|---|---|
| Deaths per contact | 15% | 17% | 21% | 26% | 30% |
| 2v1 against us | 30% | 35% | 32% | 41% | 50% |
| Healthy 1v1, Vesper | **10%** | 26% | 38% | 39% | 51% |
| Healthy 1v1, Heart of Ruin | 14% | 21% | 26% | 27% | 35% |
| Healthy 1v1, Marcella | 4% | 8% | 10% | 17% | 18% |
| Healthy 1v1, Vendetta | 15% | 9% | 12% | 16% | 15% |
| Healthy 1v1, Ryth | 11% | 8% | 18% | 20% | 21% |
| Vesper adjacent while in contact | **12%** | — | 23% | 28% | 30% |
| Deaths on the walk home | 33% | 28% | 34% | 37% | 38% |

The panel is our 6 hardest opponents on 15 maps, so its rates run higher than ranked.

## Reading
- v26 is close to the top teams on overall fight trade (17% vs 15% per contact). Vendetta and Ryth now trade at or above
  top-team level.
- The gap left is **Vesper**: she dies two and a half times as often as top teams' Vesper and stands next to enemies
  twice as often. Top teams keep her at range; she is ranged, with a 2-tile travel dash.
- Heart of Ruin (21% vs 14%) and Marcella (8% vs 4%) are smaller gaps.

## Candidates (not submitted)
- **v27** = v26 + B73: Vesper treats a fight as even only when ours ≥ 1.3 × theirs. 48% vs v26 locally.
- **b78** = v26 + B78: Vesper with an enemy adjacent steps or dashes to a tile in range of the target and next to no
  enemy. Race 46%, nonreg 48% over 840 games vs v26.

Both are neutral locally, which is expected: our own bots do not punish Vesper's melee-range trading the way top teams
do. Judge them on the scrim panel (v26: 27-63) and on Vesper's adjacency and healthy-1v1 deaths in its replays.
