# Improving the development loop (test, tune, triage)

Researched 2026-10-25 against `cambc` 3.0.5, SDK 3.0.5 and the tools at commit `70beab9`. "Measured" means I ran it on
this Mac (8-core Apple M1) during the session, with other jobs running (load average 14–16). This note builds on
[rl-feasibility.md](../../bots/jame/docs/research/rl-feasibility.md) and [drafting.md](../../bots/jame/docs/research/drafting.md)
(both under `bots/jame/docs/research/`, not `docs/research/`). Their conclusions stand: heuristic bots, automated A/B
testing, black-box tuning, and draft tables learned offline. This note covers how to run that loop better.

## TL;DR, ranked by payoff per hour of work

1. **Mine the top of the ladder. Biggest and cheapest lever.** `cambc matches list --team <any team>` and
   `matches summary` / `matches download` work for **any** team's ranked games, not only ours (measured on the #1 team).
   Over its last 100 ranked games, #1 Intercontinental Fish (75–25) drafted **Vesper and Heart of Ruin 100/100** and
   Vendetta 83/100. #2 Mite (63–37) drafted Vendetta 100/100. Our v9 draft never picks Heart of Ruin. Pull the top 20
   teams' drafts, builds and gem curves per map, and copy what transfers. *Cost: ~1 h (a `--team` loop in `ranked.py`).
   Payoff: probably large, as v9's biggest gain came from copying a build (`bots/daniel/docs/v9/summary.md:122`).*
2. **Keep the per-round summary data; stop stripping it.** Summaries carry `events`: every death with its killer
   (camp id or champion), position and round, plus gem losses, camp clears, **`fuelExhausted`** and bot faults. They also
   carry `championTimelines` for 17 metrics. That covers most of what we download replays and run `analyze.mjs` for.
   Reduce each summary to a ~2 kB feature row instead of deleting the data. *Cost: ~2 h. Payoff: triage of all
   ~500 games a day instead of a sample of losses, plus an auto-triage table (rec. 6).*
3. **Gate with a two-part sequential test on side-swapped pairs.** Part (a): SPRT for improvement on the maps the
   change targets. Part (b): a non-regression SPRT on all maps (Fishtest's "simplification" bounds). This fixes pain
   point 1: a fix worth +10/10 on one map no longer has to reach 55% over 40 maps. *Cost: ~3 h in `arena.py`. Payoff:
   accepts real single-map fixes and stops early on obvious wins and losses.*
4. **Measure ranked strength by rating, not record.** Matchmaking pairs us within about ±100 ranks (opponents ranked
   368–525, median 448; we are #461 at 1453). A ~48% record is what matchmaking produces at any strength. Snapshot
   `cambc ladder --json` hourly and log each submission's time, so ranked games can be assigned to a version and
   compared on rating-adjusted score. *Cost: ~1 h.*
5. **Make the opponent pool look like the ladder.** Build "profile bots": our bot with a ranked opponent's draft and
   build table (from rec. 1) swapped in. Add AlphaStar-style exploiters, which are `tune.py` runs that maximise win rate
   against the *frozen* main bot. *Cost: ~0.5 day. Payoff: reproduces build- and draft-driven losses; it will not
   reproduce movement-level behaviour.*
6. **Auto-triage losses into signatures** (frozen, race lost, death spiral, camp trap at (x, y), fuel overrun), ranked by
   ranked losses × map. *Cost: ~2 h on top of rec. 2.*
7. **Use `match-groups` deliberately.** Quota is 50 (`used: 0`, `resetsAt: null`). Spend it on the ranked-only
   weaknesses (stampede, road-of-riches) against teams that beat us there, choosing maps and sides. It plays only the
   **submitted** bot.
8. **Tuning: switch `tune.py` to SPSA with paired games**, or leave tuning alone. Recent tuning has mostly measured
   noise (`v9/summary.md:26`), while structural fixes gave +17 points. *Low priority.*
9. **Don't build "faster evaluation" machinery.** `--rounds` games give no result, ranked maps are close to uniform, and
   a 400-game gate is ~2 minutes of play here. Check for contention first (see §4).

## 1. What the current pipeline actually does (verified)

| Fact | Source |
|---|---|
| `arena.py` plays every map × both sides once at normal fuel, plus `--seeds N` games per map and side at fuel `1,000,000 + 10,000·seed`. It reports a pooled Wilson interval and gates on a raw win rate. | `tools/arena.py:90-101`, `:81-83`, `:112-118`, `:156` |
| `auto.py` gates at **55%** vs the base (`--seeds 4` gives 400 games). | `tools/auto.py:39-40`, `:72-73` |
| `tune.py` perturbs 3 candidates, plays each against the incumbent on 40 maps × 2 seeds × 2 sides (160 games), takes the **best of 3** and accepts at ≥56%. The best-of-3 selection inflates the accepted rate (winner's curse). | `tools/tune.py:104-106`, `:125-132` |
| `batch.py` plays at normal fuel only, so it has at most 80 distinct setups per pair (40 maps × 2 sides), and reports `P(p > 0.5)` under a Beta(1,1) prior. | `docs/BatchTesting.md`; `tools/batch.py:181-196`, `:414-425` |
| `ranked.py` strips `events` and `championTimelines` from every summary. Loss replays are decoded by `analyze.mjs` and then deleted. | `tools/ranked.py:60-64`, `:67-77` |
| The draft hook reads the fuel quantum: anything ≥ 995k is decoded as an experiment seed. | `bots/daniel/v9/src/draft.cpp:227-228` |
| Local `cambc run` builds in debug mode; the platform always runs release (`debug_block` skipped, fuel pause imports not linked). `arena.py` never passes `--release`. | `sdk/cpp/cambc.h:5259-5272`; `cambc run --help`; `tools/arena.py:50-53` |

**Seed-fuel games are not ranked conditions.** At 1M+ fuel, fuel-budgeted code never hits its limits. Jame v3 checks
`fuel_remaining()` against 12k–50k thresholds (`bots/jame/v3/src/navigation.cpp:34`, `bot.cpp:43`, `:284`, `:354`).
Measured on 00stampede, v9 vs Jame v3: Jame's Ryth logged 1 `fuelExhausted` event at 100k fuel and 0 at 1.01M. So
seeded games test a slightly different Jame, and any of our own fuel overruns are invisible. **Fix (cheap):** put the
random-roster seed in at compile time instead (a `-DDRAFT_SEED=n` copy, the way `tune.py` already copies bots,
`tools/tune.py:59-66`) and play every game at 100k with `--release`.

## 2. Statistical gating

**Why 55% is the wrong gate for single fixes.** v9's pathing fix took the_farm from 0/10 to 10/10 against v8, but
scored 208/400 = 52% overall (`bots/daniel/docs/v9/summary.md:109`). A fix confined to 1 of 40 maps moves the
pooled rate by at most 1/40 × 50 points = 1.25 points. No pooled threshold separates that from noise without thousands
of games. The test has to be split by where the effect is expected.

**What the chess-engine testers do.** Fishtest (Stockfish) tests every patch with a generalized SPRT. Results are
counted under a **pentanomial model of game pairs**, the same opening played with colours swapped, which it says "leads
to a substantial saving of testing resources compared to the trinomial model". Bounds are given in normalized Elo, so
test length depends only on the bounds ([Fishtest Mathematics](https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-Mathematics.html)).
Fishtest runs separate *non-regression* tests for simplifications, with bounds `<-1.75, 0.25>` and LLR stopping limits
(−2.94, 2.94), i.e. α = β = 0.05, ln 19 = 2.94 ([Creating my first test](https://official-stockfish.github.io/docs/fishtest-wiki/Creating-my-first-test.html)).
OpenBench is the same idea in a self-hostable form: "a Distributed SPRT Testing Framework for Chess Engines"
([OpenBench](https://github.com/AndyGrant/OpenBench)).

**The direct analogue here.** One map + seed played from both sides is a game pair, and the engine is deterministic.
Side matters a great deal: Team B wins 60–77% of mirror games (`bots/jame/docs/research/drafting.md:51`). So scoring
each pair as 0, 1 or 2 wins removes the side term from the variance, exactly as colour-swapped openings do in chess.
CAMBC has no draws (tiebreaks always decide, `docs/GameRules.md:16`), so a pair has three outcomes, not five.

**Proposed gate (replaces `--min-winrate` in `arena.py` and `auto.py`):**

1. **Targeted test.** Run it on the maps listed in the change's hypothesis, with fresh draft seeds, as pairs. Use SPRT
   with H0 = 50%, H1 = 65%, α = β = 0.05. When the effect is real it is large (the_farm went 0/10 → 10/10), so this
   ends in a few dozen pairs.
2. **Non-regression test on all maps.** Use SPRT with H0 = 45%, H1 = 50%. For a change that is truly neutral, the
   per-game drift is about 0.005 nats, so it ends in about 600 games (2.94 / 0.005). Pairing reduces that. Pass both
   tests to keep the change. A change that is 69% overall (like v9) passes test 2 within ~100 games.
3. **Report per-map pair outcomes** in addition to the pooled rate. Flag any map with ≥ 3 lost pairs out of 5. This catches
   pilgrimage-style collapses (1/10, `v9/summary.md:130`) that a pooled number hides.

For reference: 55% = +35 Elo, 52% = +14 Elo. Against the true 52% of a one-map fix, the current 55% gate has a
drift of −0.001 per game: it effectively never passes, which is pain point 1. *Cost:* SPRT on Bernoulli or trinomial
pairs is ~40 lines of stdlib Python in `arena.py`, run as games complete (`run_matches` already yields
incrementally, `tools/arena.py:100-101`). Use a `--pairs` mode so both sides of a pair are scheduled together.

## 3. A more representative opponent pool

**What we can observe of ranked opponents** (all read-only CLI, measured):

| Data | Where | Use |
|---|---|---|
| Draft picks per team per match, for **any** team | `cambc matches list --team <name> --json` (`draftPicks`, champion ids per `sdk/cpp/cambc.h:271-297`) | Per-map draft tables of the top teams |
| Full summary of any team's match: `itemsBought` in order, consumables, per-round timelines, death/kill events | `cambc matches summary <id> --json` (#1 team's match `de8127fd…`: 596 kB) | Build orders, gem-rate benchmarks per map |
| Replay of any team's match (`replay.repl26a`, no stdout) | `cambc matches download <id>` | Movement study via `analyze.mjs` |
| Every team's rating and rank | `cambc ladder --json` (#1 2394, us #461 at 1453 of 786) | Rating-adjusted evaluation (§5) |
| Ranked games come in groups of 5 against one opponent | `replays/daniel-v8/matches.json`: 330 games = 66 groups × 5, one opponent per group | Group = unit for attribution |

**Seen in the top teams' data.** Over 100 ranked games each:
- #1 Intercontinental Fish picks Vesper and Heart of Ruin in every game, plus Vendetta 83, Cassi & Issac 78 and
  Marcella 54.
- #2 Mite picks Vendetta 100, Vesper 83, Heart of Ruin 83, Marcella 75 and Tavi 75.
- In one #1 match, its champions bought Durability (health), Treasure and Jungle emblems (`itemsBought`). This differs from the drafting.md self-play
  table and the screenshot priors in `docs/research/top-team-picks.md`, which predate the week 2 patch.

v8 listed Heart of Ruin as never drafted (`bots/daniel/docs/v8/summary.md:58`), and `bots/daniel/v9/src/draft.cpp`
still has no entry for it.

**League ideas that fit our budget.** AlphaStar's league pairs "main agents whose goal is to win versus everyone"
with "exploiter agents … whose sole purpose is to expose weaknesses of the main agent", because "playing to win is
insufficient" ([DeepMind, AlphaStar Grandmaster](https://deepmind.google/discover/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/);
paper: Vinyals et al., *Nature* 575, 2019, https://doi.org/10.1038/s41586-019-1724-z). Cheap versions:

- **Profile bots** (~0.5 day). These copy what we can observe: draft and build, not movement.
  - Make `draft.cpp` and `shop()` read a per-opponent table: picks per team size, emblem order and stat split.
  - Build `bots/_pool/<team>` from a team's last 100 summaries.
  - Gate against the 3–5 teams that beat us most (Velvet Pathfinders, Campfire Codex and others: 15 games each in
    `replays/daniel-v8`).
- **Exploiters** (~1 h). `tune.py` already tunes against a fixed opponent. Add a `--opponent v9` mode that keeps the
  opponent frozen, tune aggression, recall and siege constants for win rate *against* v9, and freeze the result into
  the pool. Re-run one after each promotion. Simon's `hunter-v0` is a hand-made example of this kind of bot (`CLAUDE.md`).
- **Weight the pool by what predicts ranked results.** v8 vs Jame v3 reproduced 7/36 on the ranked-loss maps
  (`v9/summary.md:90`). Keep a pool opponent only if its per-map results against us correlate with our ranked per-map
  record, and recheck this per version.

**What this cannot fix.** The stampede and road-of-riches Golem losses (`v9/summary.md:26`, `:130`) are about
behaviour, not builds. For those, decode the replays where top teams win those maps (`matches download`, then
`analyze.mjs` timelines), or spend `match-groups` quota (§6).

## 4. Faster evaluation: mostly not needed

| Idea | Finding | Verdict |
|---|---|---|
| Truncated games with `--rounds` | Measured: `Unfinished after round 300/2000 (no result; raise --rounds to finish)`, and `--statistics` writes nothing. `--help` says it exports only a "completed match summary". | Not usable for gating |
| `cambc run-batch --jobs 8` | Measured: 40 full games in 12.8 s, the same as 8 parallel `cambc run` (12.5 s). | Fine, but no speed-up |
| Wall time of a 400-game gate | Measured: ~0.3 s wall per game at 8 jobs (40 games in 12–13 s, one per map; 1–4 s each, longest big-world/contest). 400 games ≈ 2 min, the same at seed fuel. | The reported 10 min is probably contention with a concurrent tune or arena. Run `uptime` before blaming the engine. |
| Map subset weighted by ranked frequency | 330 v8 ranked games over all 40 maps, 3–15 per map, mean 8.25. Uniform sampling gives sd ≈ 2.8, so this is consistent with uniform. | Keep every map equally weighted |
| Early stopping | This is SPRT (§2) | Do it |

The real constraint is effect size, not compute: a change that matters on one map needs a stratified test, not more
games.

## 5. Ranked data as the evaluation signal

- **Record ≠ strength.** v8 went 10/35 against opponents now ranked 300–400, 124/255 against 400–500 and 25/40
  against 500+ (330 games; ranks from `match-groups quota --json` `opponentRanks`). That is what rating-matched pairing
  looks like. Use Elo expected score instead: residual = result − 1/(1+10^((R_opp − R_us)/400)), with ratings from
  hourly `ladder --json` snapshots, or simply the rating trajectory after each submission.
- **Version attribution (pain point 3).** The listing has no submission field: per team it holds only `engineVersion`,
  `draftPicks`, `result` and `side` (`replays/daniel-v8/matches.json`). Do two things:
  1. `auto.py` (or a `submit.sh`) appends `{version, submittedAt}` to `data/submissions.jsonl`, and `ranked.py`
     assigns each **group** to the newest submission before the group's `createdAt`.
  2. The bot prints `version=v9` on its first draft turn. Our platform replay zip includes our stdout (`CLAUDE.md`,
     replay-analysis section), so one replay per group verifies the assignment.
- **Ranked A/B** (optional). At ~500 games a day, alternating two submissions for half a day each gives ~250 games
  per arm. The standard error of the rating-adjusted score is then ≈ 3 points, enough to detect a 7–8 point difference.
  This is the only test that covers behaviour-level ranked weaknesses we cannot reproduce locally.

## 6. `match-groups` for real-opponent tests

`cambc match-groups create <team id> --maps m1,…,m5 --sides a,b,…` queues five unranked games with chosen maps and
sides, using the "team's shared website quota" (`cambc match-groups create --help`). `quota --json` shows
`limit: 50, used: 0, resetsAt: null`. Whether the 50 counts groups or matches is **unverified**; check `used` after the
first create.

Constraints:
- It plays our **submitted** bot, so it validates a submission, not a local candidate.
- Teammates share the quota.

Best use: after submitting a stampede or Golem fix, queue `00stampede, 00road_of_riches` × both sides against a team
from §3 that beat us there, and compare against that team's earlier ranked games with us.

## 7. Per-round data and automated triage

Measured fields in a local `--statistics --json` summary and in a ranked summary (same schema):

- `championTimelines`: run-length series per champion for `assists, championDamageDone/Taken, collectedGems, deaths,
  earnedGold, gems, gold, healingDone/Received, kills, monsterDamageDone/Taken, saleRefunds, shieldingDone,
  spentGold, submittedGems`.
- `events` (15 kinds), each entry with `round`, `x`, `y`, `context` and `target`:
  - `death` / `gemLoss`: `context` is `camp` (with the camp id) or `champion` (with the killer's name and team).
  - `campClear`: `campGroup` id.
  - `fuelExhausted`, `botFault`, `buyItem`, `wardPlacement` and others.
- One ranked summary is 0.6–0.7 MB. The ~95% that `ranked.py:60-64` strips is exactly this data.

Proposed `features(summary)`: about 30 numbers and lists per game.
- Deaths split by cause: camp id versus champion.
- Death tiles, clustered.
- Gems lost at death.
- `fuelExhausted` count for **our** champions. In the one ranked summary checked (v8 vs Arasaka on 01starfish), the opponent side logged 21
  fuel overruns and ours none; this is the only ranked signal of platform fuel trouble we have.
- Gold and submitted gems at rounds 250, 500 and 1000.
- First-clear round for each camp group.

Store these in `<dir>/features.jsonl`, then delete or keep the raw file as today.

**Auto-triage** classifies each loss with rules taken from the manual tables in `v8/summary.md` and `v9/summary.md`:

| Signature | Rule | Past example |
|---|---|---|
| frozen | our submitted gems < 50 and deaths < 10 | the_farm 1–9 (`v9/summary.md`) |
| race lost | deaths within ±20% of theirs, and their gems at round 500 > ours by 150+ | gem-fields, elkring |
| camp trap | ≥ 30% of our deaths to one camp id within 3 tiles | road-of-riches Golem corners, corridors Monoliths |
| death spiral | our deaths > 2 × theirs, mostly `champion` context | starvation, eight |
| fuel | any `fuelExhausted` on our side | — |
| tiebreak | `endReason` starts with `tiebreak` | boss-battle |

Print a table of map × signature × count, ranked by count, so the next version starts from the largest bucket.
Compare the gem curve at round 500 with the top teams' curves on the same map (§3). That gives a per-map gap that does
not depend on which opponent we drew.

## 8. Tuning

- **SPSA** estimates the gradient with "only two objective function measurements per iteration regardless of the
  dimension of the optimization problem" (Spall, [JHU APL SPSA page](https://www.jhuapl.edu/spsa/), citing Spall 1992,
  *IEEE Trans. Automatic Control* 37(3)). Fishtest uses it to tune Stockfish parameters: each parameter is
  given a range and `c_k`/`r_k` end values, and a run whose values "are barely changing" after a few thousand games is
  stopped as useless ([Creating my first test](https://official-stockfish.github.io/docs/fishtest-wiki/Creating-my-first-test.html)).
- **Applied here:** each step plays θ + cΔ against θ − cΔ as side-swapped pairs on random maps and moves *every*
  parameter by the pair result. It has no accept threshold and no best-of-3 selection, and every game is used. `tune.py`
  already has the build/copy/play pieces (`tools/tune.py:59-94`), so this is ~60 changed lines.
- **CMA-ES** ([Hansen, tutorial, arXiv:1604.00772](https://arxiv.org/abs/1604.00772)) needs a population of
  4 + ⌊3 ln n⌋ samples per generation, each evaluated in noisy matches, so for 7 parameters it costs about 3× more
  games per step than SPSA. It is better on rugged landscapes, which our handful of smooth thresholds are not.
- **Expectation management.** Self-play tuning moved within noise in v8 and v9: `gold_weight` and
  `monolith_hit_turns` showed no change, and `power_health_share` 0.25/0.55 was noise (`v8/summary.md`,
  `v9/summary.md:26`). The structural fixes gave +17 points. Tune against the pool from §3, not against the incumbent;
  otherwise SPSA just finds a better v9-vs-v9 equilibrium.

## Build order

1. `ranked.py --team` loop plus a draft/build tally of the top 20 teams (§3). Then a v10 that drafts Heart of Ruin
   and tests the top teams' builds, gated with the current tools.
2. `features()` in `ranked.py` plus the triage table (§7). `submissions.jsonl` and the version print (§5).
3. Pairs and SPRT in `arena.py`: targeted plus non-regression (§2). Compile-time draft seed with `--release` (§1).
4. Profile bots and one exploiter in the pool (§3). `match-groups` on submitted fixes for stampede and road-of-riches (§6).
5. SPSA in `tune.py`, against the pool (§8).
