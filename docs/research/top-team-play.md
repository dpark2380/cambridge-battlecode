# How the top teams play our weak maps (backlog B13, B16)

Data, 2026-10-25: 229 full summaries of top-20 games (`data/scout/summaries`, from `tools/scout.py`) and our v9/v10
games with full summaries (`replays/daniel-v9`, `replays/daniel-v10`). Tools: `tools/openings.py` (camp-clear order),
`tools/meta.py` (drafts and builds, written to [top-team-meta.md](top-team-meta.md)), `tools/benchmark.py`
(per-map gaps) and `tools/winmodel.py` (what decides games). Our samples are small, 1–3 games per map: treat each
line as a lead to test, not a result.

## Openings: median round of the 1st / 3rd / 5th camp clear

| Map | Top 20 | Us (v9/v10) | Note |
|---|---|---|---|
| 00elkring | 12 / 41 / 92 | **67 / 142 / 232** | They clear a 22-gem group at round 11–12, then one every ~15 rounds. We wait 67 rounds for the first (B17) |
| 01islands | 6 / 67 / 132 | 6 / **137 / 234** | They take the 40-gold group G44/G45 once, then 30-gem groups (G38/G39) by round 42–72. We re-clear G45 (0 gems) five times before our first gem group at round 164–297 (B18) |
| 01corridors | 43 / 189 / 299 | **218 / 358 / 522** | First clear 175 rounds later than theirs |
| 01hooks | 14 / 48 / 78 | 21 / 80 / 128 | Slower from the third clear |
| 00gemfight | 10 / 22 / 46 | 5 / 19 / 54 | Even |
| 00road_of_riches | 18 / 26 / 52 | 12 / 32 / 43 | Even: the ranked losses there are deaths, not tempo (B6) |
| 00eight | 46 / 164 / 244 | 41 / 163 / 216 | Even: the ranked losses there are fights (B3, B14) |

The win model shows 5 of 16 analysed v9 losses already decided by round 200 (hooks, elkring ×2, gemfight, islands),
so tempo on those maps matters.

## Builds

Treasure > Jungle > Bruiser is the dominant order. After the two emblems, 55–75% of shards are Bruiser, about
60/40 main stat to health. The full tables are in [top-team-meta.md](top-team-meta.md); the change is backlog B11.

## Draft

The core is Vesper Vale 91%, Heart of Ruin 88% and Marcella 84%, then Vendetta 65% and Ryth 53%. Our usual picks
are rare at the top: Stellar 1%, Varg 12%, Cassi & Issac 8%. See B4 and B12.

## What decides games (win model, 274 games)

Held-out accuracy is 75% in rounds 100–500 and 83% afterwards. In submitted-gem equivalents, a death costs 6–9 gems
all game. One gold is worth 0.22 gems early but 0.05 late (B15). A kill is worth 16 gems early and 1.4 late.

## Who beats us: opponent styles (`tools/styles.py`, 470 ranked v8–v10 games, k = 4)

| Style (traits that set it apart) | Games | Our win rate |
|---|---|---|
| Stellar, Ren and Cassi & Issac drafts, few meta picks: drafts like ours | 260 | 53% |
| Prism +3σ, with Marcella and Vesper | 43 | 47% |
| Bruiser shards +2.4σ, Power −1.6σ, Heart of Ruin, Treasure, Marcella: the top-team meta | 46 | 48% |
| Vesper Vale and Vendetta, Monster shards | 121 | 45% |

We beat teams that draft and build like us and lose to the meta drafts and builds, which supports B11 (build) and
B12 (draft). The spread is modest (45–53%), so this is supporting evidence, not proof on its own.
