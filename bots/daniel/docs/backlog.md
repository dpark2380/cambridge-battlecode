# Daniel bot backlog: issues and candidate improvements

**Cadence:** pull and analyse ranked games every hour. Start the first bot change once the submitted version has
**150 ranked games**; after that, start at most one new change every 2 hours, and only for an item with evidence.
Data and tooling items can run at any time.

Every change is logged here **before** it is tested, with its evidence and the result we expect. Only items with
evidence that predicts a gain get tested. Results and the final status go back into the row, and full write-ups go
in the version's `summary.md`.

Status: `open` (evidence, not tested) · `next` (queued for testing) · `testing` · `kept (vN)` · `rejected` ·
`blocked` (needs data or tooling first).

Ranked data: `python3 tools/ranked.py replays/daniel-v9 --since 2026-10-25T10:16 --replays losses`.

## Bot behaviour

| # | Issue (evidence) | Hypothesis / change | Expected effect | Status |
|---|---|---|---|---|
| B1 | the_farm frozen: carriers oscillate beside camp G16 (ranked v8 1–9) | Block living camps out of sight when pathing | the_farm wins | kept (v9): the_farm 10/10 vs v8 |
| B2 | Fragile carriers, gold gap in losses (v8 ranked: 4.5k vs 6.9k gold) | 40% of Power shards as health | Broad gain | kept (v9): 69% vs v8 |
| B3 | Misjudged fights (v9 ranked: eight 0–943 with 131 deaths; contest 84 deaths) | Also fight when ahead on health × damage | Fewer bad fights, more good ones | kept (v10): 57% vs v9 |
| B4 | We never draft Heart of Ruin. The top two teams draft it 100/100 and 83/100 (`docs/research/training-process.md` §1); #1 also always takes Vesper | Add Heart of Ruin to the draft table, with a play pattern for its kit (shield, stunning dash, damage up at low health) | Possibly large; the top-team evidence is strong | open: needs a study of its kit and of the top teams' builds |
| B5 | Stampede: our share of the only gem camp (6 elks, 160 gems) is about 0 (v8 ranked 1–7) | Two siege tweaks tried | — | rejected ×2 (v9 notes); blocked: no local reproduction |
| B6 | road-of-riches: 145/185 loss deaths at the Golem corners (v8 ranked) | Wait for claimants before a mob siege | — | rejected (51% vs v8, pilgrimage 1/10); blocked: no local reproduction |
| B7 | v10 drops packs (3/10 vs v9) | Inspect packs fights under the new rule | Remove the one regression | open |
| B8 | corridors: Cassi & Issac die at (32,22) to camps 12 times with 0 gold earned (v9 ranked) | Check which camp the duo targets there; v8's Monolith leave rule may not cover it | corridors wins (v9 ranked 0–2) | open |
| B9 | Starvation: 0/4 vs Jame for both v9 and v10 | Unknown; analyse a local game | — | open |
| B10 | Strategy copied from top-ladder teams: drafts, builds and gem curves per map | `tools/scout.py`: the top 20 teams' last 100 ranked games each, plus 10 summaries per team for builds | Sources for B4, B11, B12 | **done** 2026-10-25 11:56Z (`data/scout/20261025T1156Z.json`): see B11, B12 |
| B11 | The top 20 buy **Bruiser** shards almost exclusively: Vesper 41 Bruiser:Strength + 16 Bruiser:Health per game, Vendetta 22 + 13, Marcella 19/19/14. We buy Power. A Bruiser emblem counts as 7 shards (5 of the stat + 1 of each other, `docs/GameRules.md:304`); a Power emblem counts as 6 | After the Monster and Durability emblems, buy Bruiser shards (our stat, plus the v9 health share as Bruiser:Health) instead of Power | +1/6 late-game stats for the same gold; likely a broad gain | next: waits for the 150-game v9 sample |
| B13 | We see how top teams draft and build (B10), but not how they play: camp order, siege size, Golem/elk handling, Heart of Ruin and Marcella play | Download top-20 replays on our weak maps (stampede, road-of-riches, corridors, eight, starvation) and the Heart of Ruin/Marcella games; analyse them with `analyze.mjs` (timelines: positions, gems, kills per round); write `docs/research/top-team-play.md` | Concrete play patterns to copy for B4, B5, B6, B8, B12 | next (data job) |
| B12 | The top 20 draft Vesper 92%, Heart of Ruin 85%, Marcella 85%, Vendetta 67%, Ryth 52%. Stellar, Varg and Cassi & Issac are rare (0.6–14%). Our v9 drafts lean on Varg, Stellar and Cassi & Issac | Re-weight the draft towards the top-team core. Marcella needs a check that our play suits her kit; Heart of Ruin is B4 | Possibly large; the top-team evidence is strong, but champion play has to follow | open (after B11) |

## Tooling (test quality)

| # | Issue | Change | Expected effect | Status |
|---|---|---|---|---|
| T1 | Random-draft test games run at 1M+ fuel, so opponents' fuel limits never trigger; local runs skip `--release` (research §7) | Seed drafts at compile time; play at 100k with `--release` | Local results closer to ranked | open |
| T2 | A one-map fix shows as ~52% overall | Paired, side-swapped SPRT on targeted maps, plus a non-regression SPRT on all maps (research §3) | Accept real single-map fixes; stop clear results early | open |
| T3 | Stripping `events` from summaries drops killer, position and fuel data (research §2) | Save a ~2 KB feature row per game before stripping | Triage every ranked game, not just losses | open |
| T4 | Ranked record is pulled towards 50% by rating-matched pairing | Hourly `cambc ladder --json` snapshots; log every submission time | Measure versions by rating | open |
