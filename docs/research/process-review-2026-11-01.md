# Process review: ingestion, evaluation and hypothesis generation (2026-11-01)

Written 2026-11-02 at commit `6400b03`, read-only: no bot, tool or other doc was changed, nothing was submitted and
no `cambc` network call was made. It builds on [training-process.md](training-process.md) (2026-10-25, the loop's
design) and [local-evaluation.md](local-evaluation.md) (2026-10-30, why local gates stopped predicting ranked) and
does not repeat them; it audits what happened in the 48 versions since and what to change in the process itself.
Numbers marked "(this note)" were computed with stdlib Python over the files named, with `python3 -I`.

## TL;DR

1. **Every instrument we use is blind to the 1-3 point effects we are now chasing.** The gain gate passes a true
   52% candidate 28% of the time and a true 53% one 56% of the time (simulation of `tools/gate.py`'s SPRT, §1.1).
   A 140-game race round has a standard deviation of 4.2 points; the 90-game panel's W-L has 5.3 points; a 30-game
   ranked window has 9.1. All 23 ranked keep/revert verdicts since v19 rested on samples whose 95% interval
   contained 50% (§1.2). The auto-revert trigger (≤43% over 30 games) fires in 18% of the rolling 30-game windows of
   v41's own 525-game sample, a bot that finished 263-262 (§1.3).
2. **Half the scrim panel carries no information.** Over 28 panels, Intercontinental Fish is 0-405 and The Onkeys
   58-342 (14%); four of the 15 maps sit at 15-17%. A candidate can only move the ~40 games against Aynir, Eternal
   and Micron. Replacing the two hopeless opponents and the four hopeless maps with ~50% setups raises the
   information per quota unit by roughly 1.5-1.9x at no extra cost (§1.4).
3. **The two 2026-10-30 fixes are still not done**: seeded rosters are still uniform over all 12 champions
   (`bots/daniel/v47/src/draft.cpp:251-261`) and `gate.py` still scores wins only (`tools/gate.py:77,86`). They are
   the cheapest changes on this list (§1.5).
4. **The summaries we already store hold the economy signals we keep guessing at**, and `features.py` ignores them.
   From the v47 panel summaries: gems per capture **14.3 vs 27.9** with the same number of captures (48 vs 53);
   gold by r500 1,518 vs 2,053; first emblem r368 vs r282; median bag 13 vs 22; shop visits 30 vs 37; opponents
   buy Teleport Crystals, we never do (§2). Champion damage *per shard* is equal (179-215 vs 176-192); the fight
   gap is the shard count, and the shard count is the gold, and the gold is gems-per-capture and camp efficiency
   (mob damage done per mob damage taken 2.7 vs 3.9) (§2.3).
5. **Hit rate by category** (§3.1): map-specific bug fixes gated with `--mode map` kept 6 of 7 and every one survived
   ranked; the draft core (B25) was the single largest step; economy changes went 4 kept of 18, with 8 rejected on
   local gates that cannot see economy; fight/recall thresholds went 0 of 6 tune runs and ~20 variants at 42-53%.
   Stop the threshold family (§3.2); redirect to the economy signals above with panel-paired metrics (§3.4).

## 0. Where the rating came from

| Step | Versions | Ladder | Source |
|---|---|---|---|
| Pathing bug + health shards, fight on power | v9-v10 | 1453 → ~1540 | `bots/daniel/CHANGELOG.md:339-352`; `docs/ladder_history.csv` 2026-10-25 |
| Top-20 core draft (B25) | v12 | ~1510 → 1563-1615 | `CHANGELOG.md:308-313`; `backlog.md:36` |
| Research stack B41-B45 (HoR dash, early shop, Prospector, wards, one receiver) | v18 | 1592 → 1637-1656 | `CHANGELOG.md:247-261` |
| Fight structure B62/B64/B68/B71 + map pricing B56/B84/B86 | v23-v34 | 1611 → 1680-1711 | `CHANGELOG.md:168-218`; `docs/ladder_history.csv` 10-28/29 |
| Fuel cache (B100) + caution stack B118-B124 | v41-v47 | 1660 → 1749 peak, 1713 now | `bots/daniel/docs/sprint3-report.md:6-18`; `CHANGELOG.md:10-54` |

Daily rating range of the live bot (first/last/min/max per UTC day, `docs/ladder_history.csv`, this note):
10-28 1627/1694/1611/1721, 10-29 1703/1689/1660/1711, 10-30 1670/1701/1651/1729, 10-31 1700/1749/1660/1749,
11-01 1717/1713/1663/1717. **A single bot swings 60-90 rating points within a day**, which bounds what any ranked
window can show.

## 1. Evaluation

### 1.1 Statistical power of each instrument

Simulation of `tools/gate.py` as written (pair scores of two Bernoulli games, 70-pair batches, LLR bounds ±2.94,
≥30 pairs, 13 batches max; `tools/gate.py:32-47,66-92`), 400 runs per cell (this note):

| Mode (H0 vs H1) | True pair score | P(pass) | P(fail) | P(inconclusive) | Mean games |
|---|---|---|---|---|---|
| gain (0.50 vs 0.55) | 0.50 | 0.03 | 0.94 | 0.04 | 737 |
| gain | 0.52 | **0.28** | 0.54 | 0.18 | 1,017 |
| gain | 0.53 | **0.56** | 0.24 | 0.19 | 1,055 |
| gain | 0.55 | 0.93 | 0.04 | 0.03 | 701 |
| nonreg (0.45 vs 0.50) | 0.48 | **0.51** | 0.28 | 0.21 | 1,054 |
| nonreg | 0.50 | 0.94 | 0.02 | 0.03 | 710 |
| map (0.50 vs 0.65) | 0.55 | 0.15 | 0.85 | 0.00 | 255 |
| map | 0.58 | 0.57 | 0.43 | 0.00 | 313 |

So the gain gate is a test for ≥55% effects and nothing smaller, the nonreg gate lets half of all 2-point
regressions through, and the map gate needs ≥60% on the targeted maps. `tools/test_gate.py:20-24` only checks the
0.50 and 0.55 corners, which is why this was never visible.

Fixed-sample instruments (binomial sd of a win rate, points):

| Instrument | Games | sd | 95% half-width | Source of the sample size |
|---|---|---|---|---|
| `race.py` round 0 | 140 | 4.2 | ±8.3 | `tools/race.py:38-41` (1 seed × 70 maps × 2 sides) |
| `race.py` 3 rounds | 420 | 2.4 | ±4.8 | ibid. (1+2+4 seeds) |
| Scrim panel W-L | 90 | 5.3 | ±10.3 | `tools/scrim.py:50-55` (6 teams × 15 maps) |
| Panel paired net flips | 90 | ~4.5 flips (5 pts) | ±10 | measured sd 4.1-5.0, `local-evaluation.md:79`; 17 pairs in this note's §1.4 table |
| Ranked window | 30 / 50 / 100 / 200 / 500 | 9.1 / 7.1 / 5.0 / 3.5 / 2.2 | ±18 / ±14 / ±10 / ±7 / ±4 | — |

Games needed to see an effect d against a 50% baseline (α 0.05, power 0.8, one arm; double for A-vs-B):
d = 5 pts → 785; 3 pts → 2,181; 2 pts → 4,906; 1 pt → 19,625. Ranked gives us ~500 games a day
(`replays/daniel-v41b/features.jsonl`: 525 rows over 2026-10-31 10:56Z to 2026-11-01 ~05:00Z), so **ranked can confirm
a 5-point change in two days and a 3-point change in four; nothing we run can confirm 1-2 points.**

Two further sources of variance the tools do not model: ranked games come in groups of five against one opponent
(`replays/daniel-v41b/matches.json`: 105 groups × 5), with a design effect of 1.14 on the group win count
(observed variance 1.43 vs binomial 1.25, this note); and rating-matched pairing pulls every long record toward 50%
(`training-process.md:158-161`, `CHANGELOG.md:70-71`).

### 1.2 Decisions made below the instrument's power

Every live version since v19 got a ranked keep or revert verdict (23 verdicts, v19 to v47, `docs/submissions.jsonl`
and `CHANGELOG.md`); in all 23 the sample's 95% binomial interval contained 50% (this note; e.g. v25 kept at
59-51 over 110 = 44-63%, v38 kept at 55-45 over 100 = 45-65%). The reverts are listed below with what a larger
sample or a retry showed later.

| Version | Decision | Evidence | 95% interval | Later | Source |
|---|---|---|---|---|---|
| v19 | withdrawn | 16-24 (40) | 25-56% | "part of v19's slump was likely variance" | `backlog.md:65`; `CHANGELOG.md:151-154` |
| v22 | withdrawn | 7-21 in its last 28 | 11-44% | restored on the panel 16-44 vs v18 10-50 (sign test p≈0.15) | `backlog.md:67`; `CHANGELOG.md:220-227` |
| v28 | reverted | 14-21 (35) | 25-57% | — | `CHANGELOG.md:156-158` |
| v31 | reverted | 24-26, last 30 12-18; panel 28-62 vs 32-58 | 27-54% | panel net -4 is inside ±9 | `CHANGELOG.md:181-182` |
| v35 | reverted | 64-71 (135) | 39-56% | panel net -2 | `CHANGELOG.md:139-141`; `backlog.md:100` |
| v36 | reverted | 11-19 (30) | 22-54% | B100 retried as v41, the deadline bot, 198-177 | `CHANGELOG.md:128-131`; `sprint3-report.md:3` |
| v37 | reverted | 10-20 (30) | 19-51% | B99c re-kept as v47, best panel on record | `CHANGELOG.md:114-116`; `backlog.md:134` |
| v39 | reverted | last 30 7-23; Willow maps 2-9 | 12-42% | draft-only change, plausible | `CHANGELOG.md:87-89` |
| v40 | reverted | 22-28 (50) | 31-58% | v38 then also went 22-28; B112a re-kept as v44 | `CHANGELOG.md:69-75`; `backlog.md:120` |
| v42 | reverted | 11-19 (30) | 22-54% | B113b neutral on v47's 980-game gate (51%) | `CHANGELOG.md:53-54`; `backlog.md:135` |
| v43 | reverted, then kept | panel 24-66 = base 24-66; ranked 23-12 (35) | ranked 49-80% | the one ranked signal above 2 sd was the one not acted on first | `CHANGELOG.md:39-46` |
| v44 | kept | 11-4 (15); panel +4 net flips | ranked 45-91% | — | `CHANGELOG.md:36-37` |
| v45 → v46 → v47 | each replaced after ~10 ranked games and one panel | 6-4, 4-6, 19-11; panels 26/29/29 | 30-90% | — | `CHANGELOG.md:14-30`; `docs/submissions.jsonl` 11-01 11:04-13:25Z |

Local decisions of the same kind: picking one variant over another on a 140-game race round when they differ by
under 8 points, i.e. inside one race sd: B41a 81 vs B41b 79 (`backlog.md:52`), b99c 53% vs b99b 49% (`:107`),
b126b 49% vs b126a 46% vs b126c 45% (`:136`), b118a 51% vs b118b 47% (`:128`), b67 three ratios at 47-48% (`:75`),
b108 49-51% (`:116`), b122 48-51% (`:132`), b123 48-49% (`:133`). Rejections on a single 140-game round at 44-47%
(B46 43%, B42c 47%, B63 45%, B69 46%, B75 44%, B115 44-47%) are at 1-1.5 sd and would each deserve a second seed
batch before "rejected".

Decisions that *were* adequately powered: every map-gate keep at ≥62% on 60 pairs (B29 85%, B34 98%, B54 62%,
B56 65%, B86 97%, B109 67%; `backlog.md:40,44,60,63,94,117`), the v16-v18 gain gates at 58-71% over 280
(`CHANGELOG.md:261,270,278`), and B21 at 56% over 240 plus 59% over 160 (`backlog.md:32`).

### 1.3 The auto-revert trigger is mostly a false alarm

On v41's 525 ranked games (263-262), rolling windows (this note, `replays/daniel-v41b/matches.json` sorted by
`createdAt`): 30-game windows at or below 43% in **18%** of positions, 60-game windows at or below 46% in 28%,
100-game windows at or below 48% in 28%. Non-overlapping 30-game windows of that one bot ranged 37-67%. The
standing rule (`~/.claude/.../memory/auto-revert-v18.md`, trigger ≤43%/46%/48% at 30/60/100) therefore fires on a
neutral bot about one window in four, which is what happened to v36, v37, v40 and v42. The panel "confirm" step
uses a ±9-flip instrument to confirm a ±18-point one.

### 1.4 The scrim panel: deterministic, but half of it is dead weight

Per-opponent and per-map record over every panel we hold (`data/scrims/*/features.jsonl`, 28 panels, 2,440
panel games, this note):

| Opponent | W-L | Win % | Information p(1-p) |
|---|---|---|---|
| Intercontinental Fish (#1) | 0-405 | 0% | 0.00 |
| The Onkeys | 58-342 | 14% | 0.12 |
| noobers | 90-320 | 22% | 0.17 |
| Micron | 163-242 | 40% | 0.24 |
| Aynir Industries | 196-214 | 48% | 0.25 |
| EternalWisdom | 209-201 | 51% | 0.25 |

Maps: 00ribs 15%, 00expanse 15%, 02geodes 16%, 01corridors 17%, 01islands 19%, 00eight 20%, 02the_pond 24%, 00vault
25%, 00galaxy 27%, 01starfish 31%, 02arena 38%, 00collision 39%, 00stampede 41%, 00swirl 49%, 00lanes 65%. The
panel was built from "teams that beat us most" and "our worst maps" (`tools/scrim.py:40-53`), which is the right
design for *finding* weaknesses and the wrong one for *measuring* a candidate: a Bernoulli trial carries
p(1-p) of information, so 45 of the 90 games (Fish, Onkeys, the 15-17% maps) contribute almost nothing to a
W-L comparison. Summing p(1-p) over the current opponents gives 1.03 against 1.50 for six ~50% opponents (×1.45);
over the maps 2.85 against 3.75 (×1.32). Both together are worth about 1.5-1.9x the games for the same quota.

What the panel *can* see, paired by (opponent, map, side) between consecutive versions (this note; `local-evaluation.md`
§1 gives the first four rows):

| Base → candidate | Identical games | Net flips | Δ deaths/game ± SE | Δ gold ± SE | Δ gem margin ± SE |
|---|---|---|---|---|---|
| v41 → v41-1101 (same bot, 24 h later) | 75 | −1 | +0.24 ± 0.23 | −84 ± 47 | −11 ± 8 |
| v34 → b99c | 1 | +2 | **−3.50 ± 1.08** | +291 ± 233 | +99 ± 62 |
| v38 → v40 | 0 | +3 | **−3.93 ± 1.10** | +405 ± 259 | +72 ± 60 |
| v34 → b88d | 6 | −10 | +0.36 ± 1.18 | −306 ± 361 | **−112 ± 58** |
| v34 → b95v34 | 9 | −7 | +0.97 ± 0.76 | +107 ± 159 | **−78 ± 36** |
| v41-1101 → v43 | 1 | 0 | −1.38 ± 0.83 | +159 ± 159 | +6 ± 34 |
| v43 → v44 | 2 | +4 | −1.84 ± 1.04 | +108 ± 244 | +48 ± 52 |
| v44 → v45 | 5 | −2 | −1.07 ± 1.17 | +64 ± 294 | +7 ± 63 |
| v45 → v46 | 12 | +3 | −0.84 ± 0.86 | −123 ± 219 | −24 ± 50 |
| v46 → v47 | 1 | 0 | −1.81 ± 1.12 | +62 ± 246 | +39 ± 66 |

Three readings. (a) Field drift over a day is small: the same bot replayed 75 of 90 games exactly and moved −1
net, so a base panel is good for a day or more, and B110's worry (`backlog.md:118`) applies across weeks, not
hours. (b) Deaths resolve at ~1.1 per game, gem margin at ~60, gold at ~240: a 3-death change is a 3-SE signal
while the same change is +2 flips on W-L. (c) The caution stack v41 → v47 cut deaths 19.0 → 12.1 (`data/scrims/*/features.jsonl`
means) in five steps that were each 1-2 SE, and the summed margin is +76 ± 120: **no evidence yet that fewer deaths
became more gems on the panel**, which is the question the next panel metric (gems captured, §2) should answer.

### 1.5 Still open from local-evaluation.md

| Recommendation (2026-10-30) | Status 2026-11-02 | Evidence |
|---|---|---|
| #1 ranked-like seeded rosters | **not done**: `random_team` still draws `h % champion_count` uniformly | `bots/daniel/v47/src/draft.cpp:251-261` |
| #2 paired Δ deaths / gold / margin printed by `gate.py` and `race.py` | **not done**: `gate.py` scores `won` only; `arena.normalize` keeps outcome, gems, picks, faults | `tools/gate.py:77,86`; `tools/arena.py:87-104` |
| #3 calibration set from the panel | not done | no script under `tools/` |
| #4 opponents that differ from us near 50% | partly: `bots/_var/spar-pack`, `spar-top`, `spar-fight` built; all 53-60% for us and not separating | `backlog.md:158` (T11) |
| #6 ranked as a monitor, not a test | not done: 7 ranked A/B stints since (v43-v48) | `docs/submissions.jsonl` 2026-11-01 |

### 1.6 Proposed decision rule

Explicit sample sizes, chosen so that each step can actually see the effect it is asked about.

1. **Local, every candidate (cost ~4 min):** `nonreg` vs parent as today, plus the paired Δ deaths, Δ earned gold,
   Δ gem margin and Δ gems-at-r500 from the local summaries (`cambc run --statistics` already writes them; only
   `arena.normalize` throws them away). Accept to the next step on nonreg PASS; never reject on a 140-game race
   round unless it is under 40%. Pick among variants by the paired continuous metrics over ≥280 games, not by
   W-L over 140.
2. **Panel, every candidate that reaches it (cost: one submission + 18 quota units):** rebuild the panel as
   6 opponents at 35-65% against the live bot (keep Aynir, Eternal, Micron; replace Fish, Onkeys, noobers from the
   ranked opponents we split 2-3 with over ≥10 games) and 15 maps at 30-70% (drop 00ribs, 00expanse, 02geodes,
   01corridors; add four maps from the 35-55% band of `replays/daniel-v41b/features.jsonl`). Keep the panel
   deterministic and paired. Score: paired Δ gem margin, Δ deaths, Δ gold, Δ gems captured, each with SE, plus a
   `winmodel.py` probability per game. Verdict: **better** if Δ margin ≥ +2 SE, or Δ deaths ≤ −2 SE with Δ margin ≥ 0;
   **worse** if Δ margin ≤ −2 SE; otherwise **neutral**, and neutral candidates are stacked, not shipped. Net W-L
   flips inside ±9 are not evidence. Re-run the base panel once a day (75/90 identical at 24 h), not per candidate.
3. **Ranked, only for a panel "better" or a stack of ≥3 panel-neutral changes with a positive summed margin:**
   one trial, minimum 200 games before any verdict (sd 3.5), compared by rating-matched score against the base's
   last 200 at the same rating, never by the last-30 record. Revert only on rating: −100 from the switch-time
   rating after ≥100 games (a day's swing is 60-90, §0). Drop the ≤43%-at-30 trigger.
4. **Panel size:** 90 is enough for deaths and margin at the SEs above; doubling it halves nothing useful for W-L
   (sd 5.3 → 3.7). Spend the quota on more *candidates* per hour (two 18-group panels and 14 spare) rather than a
   bigger one.

## 2. Ingestion

### 2.1 What is collected

| Source | Volume | Kept | Used by | Source |
|---|---|---|---|---|
| Ranked | 5,019 feature rows over 45 version folders; full summaries gzipped; loss replays decoded then deleted | 33 fields per game (`features.row`), timelines for losses only | `ranked.py` report, `benchmark.py`, `winmodel.py`, `fights.py` (losses) | `replays/daniel-*/features.jsonl` (this note); `tools/ranked.py:1-20`; `tools/features.py:44-100` |
| Scrim panel | 28 panels, 2,440 games, every summary and every replay decoded (report, stats, timeline) | all | `scrim.py report` (W-L, 4 means), `fights.py`, ad-hoc scratch scripts (`assist.py`, `vesper1v1.py`, `deathctx.py`, `homedeaths.py`) | `data/scrims/<v>/{summaries,analysis,features.jsonl}`; `tools/scrim.py:19-21`; `backlog.md:101-105,135` |
| Scout | 5,784 feature rows (top 260), 4,018 summaries, 1,287 decoded replays | all | `benchmark.py`, `meta.py`, `openings.py`, `targetmodel.py`, `styles.py`, B114 | `data/scout/` (this note); `tools/scout.py:1-16` |
| Local games | thousands per day | **only outcome, round, gems, picks, faults**; the summary is read and reduced | gates, races, tune, gauntlet | `tools/arena.py:87-104` |
| Ladder | 232 hourly snapshots; 58 submissions | rank, rating, match count | `ladder.py`, `gauntlet.py` mapping | `docs/ladder_history.csv`; `docs/submissions.jsonl` |

The scrim folders are the richest data we own (2,440 games with per-round positions against named opponents on
fixed setups) and are read by one report that prints four means (`tools/scrim.py:180-201`).

### 2.2 Signals in the summaries that nothing reads

A full summary holds 15 event kinds and 17 per-champion per-round metrics (`replays/daniel-v47/summaries/*.json.gz`,
inspected in this note; schema in `training-process.md:186-197`). `features.py` reads `death`, `fuelExhausted`,
`botFault`, `campClear`, the shard totals and the submitted-gems timeline at three rounds (`tools/features.py:55-98`).
Everything below is already on disk for every ranked, scrim and scouted game; the v47 numbers are means over its
90 panel games unless marked median (this note, `data/scrims/v47/summaries/`):

| Signal | Event / metric | Us | Panel opponents | What it measures |
|---|---|---|---|---|
| Gems per capture | `gemCollection` (context `campGroup`): distinct (round, group) | **14.3** | **27.9** | the groups we choose to capture are half as rich, with equal capture counts (48.4 vs 52.6) and equal receivers per capture (1.1 vs 1.1) |
| Gems captured per game | sum of the above | 547 | 892 | the whole gem gap, before any tribute |
| Gold curve | `championTimelines` `earnedGold` at r250 / r500 / r1000 | 674 / 1,518 / 3,395 | 885 / 2,053 / 4,671 | −24% / −26% / −27% from the start |
| First emblem | `itemCombination`, first per champion, team median | r368 | r282 | shop timing (B42 moved it from r215 to r94 in one game; this is the whole-panel truth) |
| Emblems by r200 / total | `itemCombination` | 1.4 / 29.7 | 2.0 / 40.1 | passives early, shard count late |
| Shop visits | distinct (champion, round) of `buyItem` | 33 | 37 | — |
| Bag size, median | `gemSubmission` value | 13 (mean 19) | 22 (mean 42) | B115's observation, now per setup (it was "rejected" on a 140-game self-play race, `backlog.md:125`) |
| Tributes per game | `gemSubmission` count | 29 | 27 | — |
| Gems lost to champions | `gemLoss` (context `champion`) | 37 | 55 | after the caution stack we now lose fewer gems to kills than they do (v41-1101: 78 vs 60) |
| Gems taken from kills | `gemCollection` (context `champion`) | 55 | 37 | the mirror of the row above |
| Wards placed | `wardPlacement` | 207 | 153 | we out-ward them; no measured value either way |
| Consumables | `buyConsumable` | Altar Lock 9.1/game, nothing else | Altar Lock in 84 games, **Teleport Crystal in 16** | an item we have never used |
| Kills with killer and victim | `kill` / `assist` entries carry `target` | unused | unused | who kills whom; `deaths_by` keeps only champion-vs-camp |
| Heatmaps | `heatmaps`: death, kill, wardPlacement per champion as run-length rounds | unused | unused | cheap event timing without a replay |
| Per-round carried gems, spent gold, healing, shielding, damage done | `championTimelines` (17 metrics) | unused except `winmodel.py` every 100 rounds | — | mechanism checks for any shop/heal/fight change |

Not available in summaries, and where to get it:

- **Ability casts and dash use**: no event kind. A dash shows in the decoded timeline as a 2+ tile move in one
  round (`tools/replay/analyze.mjs` timeline columns x, y per round; rows sampled at round start).
- **Fuel per turn**: only `fuelExhausted` events (count per champion, `tools/features.py:85-86`). Our own stdout is
  in our replay zips (`CLAUDE.md`, replay bundle), so a `fuel=` print per turn costs nothing on the platform.
- **Target choice and claims**: our status lines in `team-*.stdout`, already parsed ad hoc for B20/B29/B101
  (`backlog.md:31,40,109`); not parsed for scrim replays, which include our stdout.
- **Vision and ward value**: not derivable.

### 2.3 Measuring the gold-per-clear and damage-per-shard gaps directly

Both are one division away from fields we already keep, and both give a clear answer (this note):

| Measure | Us (v47 panel) | Panel opponents | Us ranked v41b (525) | Top-30 scouted (4,097 rows) | Source |
|---|---|---|---|---|---|
| Gold per camp clear | 107 | 128 | 101 | 118 | `earnedGold / camp_clears` in `features.jsonl` |
| Gold per clear net of kill gold (100 a kill, `backlog.md:139`) | 90 | 108 | 81 | 103 | `(earnedGold − 100·kills) / camp_clears` |
| Shards bought per game | 164 | 212 | 133 | 174 | sum of `shards` |
| Champion damage done per shard | 179 | 176 | — | — | `championDamageDone / shards`, `data/scrims/v47/analysis/*.stats.json` |
| (v46 panel) | 215 | 192 | — | — | ibid. v46 |
| Mob damage done per mob damage taken | **2.69** | **3.89** | — | — | `monsterDamageDone / monsterDamageTaken`, same files |
| Spent / earned gold | 0.96 | 0.95 | — | — | ibid. |

So: **the build converts gold into champion damage as well as theirs does**; the damage gap is the shard gap
(−23% on the panel, −24% in ranked vs the top 30), the shard gap is the gold gap, and the gold gap is (a) 15-20%
less gold per clear net of kills and (b) 2x fewer gems per capture. The camp-efficiency ratio 2.7 vs 3.9 is the
Jungle (30% less camp damage) and Monster (15% more) passives that every scouted band buys and we did not until
v48 (`backlog.md:124,136`; top-30 shard mix Jungle 8%, Treasure 8%, Monster 3% vs ours 0/0/0, this note from
`data/scout/features.jsonl` and `replays/daniel-v41b/features.jsonl`). `features.py` should carry `championDamageDone`,
`monsterDamageDone`, gems captured, gems per capture, first-emblem round, shop visits and median bag; all are
present in the summary `metrics` and `events` blocks and need about 30 lines.

## 3. Hypothesis generation

### 3.1 Backlog hit rate by category

Every B-item in `bots/daniel/docs/backlog.md:20-152`, classified by what it changed; "kept in ranked" means it is
in the live lineage and was never reverted for its own ranked result (this note; item ids given so the count can
be checked).

| Category | Tested | Kept in ranked | Rejected on local evidence only | Reverted/rejected on ranked or panel | Items |
|---|---|---|---|---|---|
| Bug / pathing / fuel (map-triggered) | 7 | **6** | 1 | 0 | kept B1, B19, B29, B29b, B34, B100; rejected B102 |
| Map-specific pricing or rule | 12 | 4 | 7 | 1 | kept B56, B84, B86, B109; rejected B22, B66, B77, B85, B101, B105-107; ranked B111 (draft) |
| Target choice, global | 14 | 2 | 10 | 2 | kept B36, B54; rejected B17/18, B20, B24, B26, B55, B75, B108; reverted B54b (v19), B113b (v42) |
| Economy / shop / build | 18 | 4 | **8** | 2 | kept B2, B21, B42, B43; local-only rejects B11, B31, B42c, B48, B53, B103, B104, B115; panel rejects B89, B95; undecided B126 (v48 live) |
| Fight structure (who fights, how to leave) | 20 | 9 | 5 | 6 | kept B3, B37, B41, B62, B64, B68, B71, B99c (as v47), B112a (as v44); local rejects B46, B61, B63, B69, B97; ranked/panel rejects B78b, B80/81, B87b, B88d, B91a, B92 |
| Fight / recall thresholds and tune runs | 6 tune + ~20 variants | 2 (B73 v27, B118 v43) | ~18 | 1 (B80, v31) | tune B36b, B39, B72, B74, B93, B98: nothing accepted; variants B67, B76, B82, B94, B122, B123 at 42-53% |
| Draft | 2 | 1 | 0 | 1 | kept B25; reverted B111 |

Three patterns. **Map-specific bug fixes with a `--mode map` gate at ≥62% were kept every time and never
reverted** (B1, B19, B29, B34, B86, B109: `backlog.md:20,30,40,44,94,117`); they are the only category with a
reliable local test, because a freeze or a walled altar reproduces in self-play. **Economy changes were rejected
eight times on a local instrument that by construction cannot see them** (both sides farm the same camps; the
backlog says so itself at `:103,116,136`), and the two that reached a real-opponent test (B89, B95) were judged
on W-L flips of −5 and −7, inside the ±9 noise band, although B95's paired margin (−78 ± 36) was a fair rejection.
**The threshold family has produced nothing since B73**: six tune runs with no acceptance (`backlog.md:47,50,80,
82,101,106`) and some twenty hand variants between 42% and 53% locally, most of them dropped on one 140-game round.

### 3.2 Families tested repeatedly with neutral results

| Family | Attempts | Range of results | Why it cannot resolve |
|---|---|---|---|
| Recall thresholds (recall / duo / carrier / spawn-leave health) | B39, B72, B76, B80, B93, B121-B123: 7 | 42-54% local; v31 reverted at 24-26 | self-play opponents do not chase, so a threshold has no cost locally (`backlog.md:101,116,132`) |
| Fight-entry ratios (1.0-2.0x power, health clause) | B3, B61, B67, B73, B81, B94, B118: 7 | 47-57% local; v27 56-49, v43 38-27 ranked | the fight model is shared by both sides locally (`backlog.md:95,102`) |
| Build order, no mechanism metric | B11, B31, B42c, B53, B95, B103, B104, B126: 8 | 41-58% race, 50-51% gate | economy is invisible in mirrors (`backlog.md:136`); only B95 and B126 reached the panel |
| Vesper duels | B73, B78/78b, B79, B82, B89, B90, B94, B99, B124: 9 | 46-53% local; panel 1v1 deaths 34% → 11% after B124 | the one family where the panel's mechanism metric (`fights.py` healthy-1v1 deaths) finally decided it (`backlog.md:137`) |
| Opening clear order | B24, B36, B75, B77, B91: 5 | 44-63% | B36 kept (joining); the rest were value multipliers that self-play punishes (`:35,83,85,99`) |

The Vesper row is the model: the family was neutral on W-L nine times and was settled by a per-champion death rate on
the panel, not by wins. The other rows have no such metric defined; §2.2 supplies candidates (gems per capture,
gold by r500, first-emblem round, gems lost to champions).

### 3.3 What the scouted and panel games show that is not yet a candidate

| Observation | Evidence | Prior attempt | Gap |
|---|---|---|---|
| We capture groups half as rich as theirs on the same setups | gems per capture 14.3 vs 27.9, captures 48 vs 53 (§2.2) | B26 target model parked at 52% on 140 games (`backlog.md:37`); B24/B75 opening sets rejected | never measured as a per-capture gem value; the panel gives the opponent's exact capture list per (map, side) |
| Opponents' gold leads from r250 (−24%) with equal clears | §2.2 gold curve; B113 r500 1,211 vs 2,256 in losses (`backlog.md:123`) | B113b/B125 early gold weight: 55% then 51% on local gates | gold weight raises *gold-only* clears; the gap is gems and passives, not gold groups |
| Camp efficiency 2.7 vs 3.9 | §2.3 | B31/B95 Jungle rejected locally and on W-L flips; v48 now adds Treasure/Jungle (`CHANGELOG.md:12`) | judge v48 on mob-damage ratio, gold/clear and gems captured, paired, not on 29-61 vs 29-61 |
| Bags of 22-26, 20-24 tributes | B115 (`backlog.md:125`), §2.2 median 13 vs 22 | B48, B115 rejected on self-play (44-52%) | self-play cannot price travel deaths; untested on the panel |
| Teleport Crystal | 16 of 84 panel opponent games (§2.2) | none | a 10-gold consumable (`docs/GameRules.md`, shop section) that removes a walk; unknown rules, probe it like B103 did for items |
| Top teams move on from respawning groups | `targetmodel.py` weights −1.51 vs −0.74 (`backlog.md:37`) | B26 wait penalty parked at 52% / 140 | retest only with paired metrics and ranked-like rosters |
| Marcella as a 0-death banker on brawl maps | B30: one Marcella banks 461-607 gems and 3,000 gold with 0 deaths (`backlog.md:143`) | none | a role rule on 1-objective maps (gemfight, vault, starfish) |
| Willow wins on specific maps for the top 60 | B111 (`backlog.md:119`) | draft-only v39 reverted | the draft without the play; `cast_support` never checked |
| Shards per game −24%, damage per shard equal | §2.3 | B89 Vesper build (panel −5 flips) | the build is fine; stop testing builds, test gold |

### 3.4 Next hypotheses, by expected value

Each with the evidence that motivates it and the test that would decide it under §1.6.

| # | Hypothesis | Evidence | Decisive test |
|---|---|---|---|
| H1 | **Price camp groups by gems per capture.** Our 48 captures a game yield 14 gems each, theirs 28. Compare, per panel setup, the list of groups each side captured (`gemCollection` campGroup ids × `maps/ascii` rewards) and find the groups they take that we never do | §2.2; B116's "their extra gems come with fewer clears" (`backlog.md:126`); B26 model | offline first (one script over `data/scrims/v47/summaries`, 1 h); then a pricing change judged on paired gems captured (SE to be measured, expect ~40/game) on the panel |
| H2 | **Passives before stats** (v48 is the first step: Treasure, Prospector, Durability, Jungle). Next: Monster instead of Prospector for non-cluster maps | mob damage ratio 2.7 vs 3.9; top-30 mix Jungle 8%, Treasure 8%, Monster 3%; emblems by r200 1.4 vs 2.0 (§2.2-2.3) | v48's panel: paired Δ gold/clear, Δ mob-damage ratio, Δ gems captured; not W-L |
| H3 | **Shop earlier and oftener**: first emblem r368 vs r282, 33 visits vs 37 | §2.2; B42 showed one-game r215 → r94 (`backlog.md:53`) | mechanism metric is already in the summaries; a shop-threshold variant judged on first-emblem round and gold by r500 |
| H4 | **Bags of ~25 when no enemy was seen**, on the panel, not self-play | §2.2 bag 13 vs 22; B115's rejection was self-play only | panel paired Δ tributes, Δ gems lost to champions, Δ margin |
| H5 | **Teleport Crystal for carriers and shoppers** | 16 of 84 opponent panel games; never bought by us | engine probe of the item (as `bots/_var/iteminfo`, `backlog.md:111`), then a 1-rule variant judged on first-emblem round and bag size |
| H6 | **Ranked-like seeded rosters + paired continuous scoring in gate.py** (process) | `local-evaluation.md` #1-#2 still open (§1.5); every local verdict since depends on it | rerun the b99c / b92 / v36 / b95v34 gates and check the order against their panels (`local-evaluation.md:228-230`) |
| H7 | **Stop the threshold family** until a real-opponent death metric moves | §3.2: 7 + 7 attempts, 0 adopted on their own evidence | none needed; B127 (HoR leaves at 50%) is the exception because `fights.py` gives it a target metric (25% → ?) |
| H8 | **HoR / Marcella banker role on single-objective maps** | B30, B32 (`backlog.md:42,143`): 0-4 and 0-3 brawls with the same draft on both sides | map-gated rule, judged on the panel's starfish/vault/arena setups by gems captured and deaths |
| H9 | **Capture receiver = Vesper when she is within 4** (B90, parked at 48% on 140 games) | her gold 1.9k vs 2.7k (`backlog.md:97-98`); +20% gold passive | per-champion `earnedGold` from `stats.json`, paired on the panel |

## 4. Local test opponents

The current nonreg pool is the parent (50%), v12 (73-82%) and Jame v3 (87-93%) (`CHANGELOG.md:13,19,25,29,34`).
Two of the three sit outside the 15-85% band in which a game carries information (`local-evaluation.md:130-133`),
so they catch crashes and gross breakage and nothing else; hunter-v0 (91-94%) and Simon v6 are the same.

**A "+N% stats" copy of our bot is not possible.** Champion stats, gold and vision are engine-side (shards and
emblems are the only stat path, `docs/GameRules.md` "Shards and emblems", line 278), and the SDK exposes no
override; the only asymmetries a local match allows are the roster and the fuel budget, and fuel is not what loses
games (B100 neutral in ranked, `backlog.md:122`; `local-evaluation.md:157`). Three things are possible and cheap:

1. **Handicap the candidate, not the opponent.** A `#ifdef HANDICAP` in the candidate and base copies that skips
   the first emblem (or shops 20% less) reproduces the ranked condition of being ~25% behind on shards (§2.3) and
   asks the question we care about: which fight logic copes while under-geared. Both arms carry the handicap
   against an unhandicapped parent, so it is a paired test like any other. Validate it once with the §1.5 #3
   calibration check (does it order b99c > b92 > v36 > b95v34 as the panel did?).
2. **Profile bots from the panel opponents' observed macro**, proposed on 10-25 and 10-30 and still not built
   (`training-process.md:127-131`; `local-evaluation.md:208`). Every input is in `data/scrims/*/summaries`: their
   picks per map and team size (`their_picks`), ordered `itemsBought` per champion, bag sizes (`gemSubmission`),
   opening group order (`campClear`). It copies draft, build, bags and openings, not movement, which is what T11's
   spar bots lacked (`backlog.md:158`).
3. **Retire the pushovers from gating** and keep three opponents: parent, the previous submitted version, and
   whichever profile bot the calibration check keeps. Keep Jame v3 as a crash smoke test only.

Replaying scouted drafts and builds (the question's second option) is item 2; replaying their *play* is not
possible because the opponent reacts to us. What the panel does give is 90 fixed setups per version with the
opponent's full capture list and timeline, which is an oracle for H1 and H3 without any new games.

## 5. Recommendations, prioritised

| # | Change | Effort | Why first |
|---|---|---|---|
| 1 | **Extend `features.py`** with gems captured, gems per capture, first-emblem round, emblems by r200, shop visits, median bag, gems lost to champions, `championDamageDone`, `monsterDamageDone`, consumables; add them to `scrim.py report` as paired Δ ± SE against the previous version | ~2 h | every number in §2 came from one script; it turns the 1,800 panel games we hold into the instrument the W-L column is not |
| 2 | **Rebuild the panel** around ~50% setups (drop Fish, Onkeys; drop 00ribs, 00expanse, 02geodes, 01corridors), keep it deterministic and paired, base panel once a day | 15 min of config + one quota hour | 1.5-1.9x information per quota unit (§1.4) |
| 3 | **Adopt the §1.6 decision rule**: no verdict on W-L flips inside ±9, none on ranked under 200 games, revert on rating −100 only; stack panel-neutral changes before a ranked trial | 0 | all 23 ranked verdicts since v19 were below power (§1.2); the trigger fires on 18-28% of a neutral bot's windows (§1.3) |
| 4 | **`gate.py`/`race.py` print paired Δ deaths, gold, margin, gems-r500** from local summaries; pick variants on ≥280 games by those, not on 140-game W-L | ~2 h | `local-evaluation.md` #2, still open (§1.5); ends coin-flip variant selection (§1.2) |
| 5 | **Ranked-like seeded rosters** in `random_team` | ~1 h | `local-evaluation.md` #1, still open; prerequisite for any local fight verdict |
| 6 | **H1 offline**: per-setup capture lists, ours vs theirs, from the v47 panel | ~1 h | the largest unexplained economy gap (14 vs 28 gems per capture), zero games needed |
| 7 | **Judge v48 (live) by §2.3 metrics**, then H2/H3 (Monster, shop timing) | per candidate | the build is not the gap, the shard count is |
| 8 | **Handicapped-candidate local test** + calibration check against the labelled panel versions | ~3 h | the only cheap way to make a fight change cost something locally |
| 9 | **Profile bots** from panel opponents' summaries | ~1 day | replaces pushovers with opponents that differ from us (§4) |
| 10 | **Park the threshold family** (§3.2) and the ranked A/B stints; keep B127 only because it has a `fights.py` target | 0 | 7 + 7 neutral attempts; each A/B stint costs a submission and 30-55 rating (`local-evaluation.md:210`) |

**Not recommended:** a larger panel (W-L sd 5.3 → 3.7 for twice the quota, while deaths and margin already
resolve at 90); more self-play volume for 1-2-point effects (19,625 games for 1 point, §1.1); further build-order
races without a mechanism metric; any new ranked candidate before items 1-3 are in place.

## Addendum (2026-11-02 05:15Z): what the first night of the rule showed

- Panel determinism: a repeat of the same bot within the hour replays all 90 games identically (v49p2 = v48p2, v51p2b = v51p2),
  so one panel per candidate is an exact measurement on its 90 setups; the ±4-win band in §1.4 is between-setup variation.
- Generalisation failure: v52 (B131b, gold weight 0.5 before r500) was panel-neutral-positive (wins +5, gold +555 ± 332,
  margin +70 ± 64) but carried a large early-game swing (gems r500 −47 ± 10). In ranked the v52 line went 61-79 over 155
  (39%) against v51's 79-71 (53%), rating 1745 → 1673, and was reverted. Rule 3 above should read: a panel-neutral change
  whose early-game metrics move by more than 2 SE gets a ranked check (≥100 games, rating-matched) before anything is
  stacked on it; two further candidates (v53, v54) were built on v52 and both failed their own panels, costing ~50 rating.
- Confirmed by both instruments: v51 (B129 camp-aware leave) was the only "better" verdict (deaths −0.94 ± 0.43) and rose
  in ranked (79-71, 1733 → 1750); v54 (B130b) was "worse" on the panel (margin −113 ± 45) and 4-16 in ranked.
