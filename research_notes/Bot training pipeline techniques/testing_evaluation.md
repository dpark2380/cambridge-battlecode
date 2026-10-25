# Testing and evaluating game-bot versions efficiently and reliably (CAMBC 2026)

Scope: statistical and engineering methods for deciding whether bot version B beats A with as few games as possible,
applied to `tools/arena.py` / `tools/batch.py` (40 maps x 2 sides, deterministic engine, random-draft seeds via fuel
quantum, one 8-core M1, ~0.3 s wall per game at 8 jobs, so 400 games take ~2 min). Builds on
`docs/research/training-process.md` (repo, 2026-10-25), which already proposes a paired SPRT gate. Simulation numbers
below are mine (script: `/private/tmp/claude-501/-Users-danielpark-Documents-cambridge-battlecode/ae052445-3ab3-4a17-990e-90fc82fe301f/scratchpad/sprt_sim.py`)
and are labelled as inferences.

## 1. SPRT / GSPRT as used by Fishtest, OpenBench and engine testers

### Takeaway
Engine testers never gate on a fixed win-rate threshold. They run a (generalized) SPRT with an indifference zone
[elo0, elo1], alpha = beta = 0.05 (LLR stops at -2.94 / +2.94), counted on colour-swapped game pairs (pentanomial). For
our no-draw game the pair model is trinomial (0, 1, 2 wins per side-swapped pair). With bounds as wide as ours must be
(we care about +3 to +10 points, not +1 Elo), tests end in ~50 to ~800 games, i.e. 15 s to 4 min on this Mac.

### Cited Findings
- Wald's SPRT stops when the cumulative log-likelihood ratio leaves (a, b), with a ≈ log(beta/(1-alpha)) and
  b ≈ log((1-beta)/alpha); approximate in discrete sampling because the LLR overshoots. It was proved optimal by Wald and
  Wolfowitz (1948, "Optimum Character of the Sequential Probability Ratio Test") — [Wikipedia: SPRT](https://en.wikipedia.org/wiki/Sequential_probability_ratio_test)
- With alpha = beta = 0.05 the bounds are ±ln(19) = ±2.94; Fishtest commit messages report e.g.
  "LLR: 2.95 (-2.94,2.94) <-1.75,0.25>" for a non-regression (simplification) test, and two example passes needed
  38,008 (STC) and 91,232 (LTC) games — [Fishtest wiki: Creating my first test](https://official-stockfish.github.io/docs/fishtest-wiki/Creating-my-first-test.html)
- Fishtest uses a GSPRT (generalized SPRT, MLE of the outcome distribution under each hypothesis), bounds in
  "normalized Elo", and a pentanomial model of game pairs (outcomes ll, ld, dd/wl, wd, ww) which it says is more
  accurate than the trinomial model; the GSPRT behaves asymptotically like the SPRT as error probabilities go to 0 —
  [Fishtest Mathematics](https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-Mathematics.html)
- Fishtest source `LLRcalc.py`: `LLR_logistic(elo0, elo1, results)` converts Elo bounds to expected scores with
  `L(x) = 1/(1+10^(-x/400))`, builds the empirical pdf of outcomes (pair scores 0, 0.25, 0.5, 0.75, 1 for pentanomial;
  0, 0.5, 1 for trinomial), regularizes zero counts to 1e-3, and returns `N * LLR(pdf, s0, s1)` where the constrained MLE
  under each hypothesis is found with a secular-equation root finder (`scipy.optimize.brentq`). `LLR_normalized` uses
  `nelo_divided_by_nt = 800/ln(10)` and multiplies the t-values by √2 for pentanomial data — [fishtest LLRcalc.py](https://raw.githubusercontent.com/official-stockfish/fishtest/master/server/fishtest/stats/LLRcalc.py)
- Normalized Elo ≈ logistic Elo / sqrt(1 − draw_ratio) for small differences, so with zero draws the two coincide;
  test cost scales as ~(game duration)/(normalized Elo)^2 — search summary of [vdbergh/simul README](https://github-redirect.dependabot.com/vdbergh/simul) and [Fishtest FAQ](https://github.com/official-stockfish/fishtest/wiki/Fishtest-faq) (not fetched directly; treat as secondary)
- Bounds table on Chessprogramming wiki (row labels were ambiguous in extraction): gainer [0.5, 2.5] / non-regression
  [-1.75, 0.25] and [0, 2] / [-1.75, 0.25] (Stockfish LTC/STC); [0, 3] / [-3, 1]; [0, 5] / [-5, 0] "top 30 engines";
  [0, 10] / [-10, 0] "all other engines". The page recommends fast-chess "as it supports pentanomial statistics, which can
  make tests finish faster", and lists cutechess-cli as a popular SPRT tool — [Chessprogramming: SPRT](https://chessprogramming.org/Sequential_Probability_Ratio_Test)
- OpenBench SPRT workloads take `Bounds [lower, upper]` (Elo of H0 and H1) and `Confidence [alpha, beta]`; "Generally,
  a value of 0.05 is a good value"; its calculator link defaults to normalized Elo, elo0 = 0, elo1 = 2 — [OpenBench wiki: SPRT and Fixed-Game Workloads](https://github.com/AndyGrant/OpenBench/wiki/SPRT-and-Fixed%E2%80%90Game-Workloads)

### Inferences
- **Formula to implement (stdlib, no scipy).** For per-unit scores x_i in [0,1] (unit = a game, or a side-swapped pair
  scored 0, 0.5, 1), the standard normal-approximation GSPRT is
  `LLR ≈ N·(s1 − s0)·(2·x̄ − s0 − s1) / (2·σ̂²)`, with σ̂² the sample variance of x_i; accept H1 at LLR ≥ 2.94, H0 at
  ≤ −2.94. Convert Elo to score with `s = 1/(1+10^(−elo/400))` (55% = +35 Elo, 52% = +14, 65% = +108). Since CAMBC has
  no draws, logistic and normalized Elo coincide per game; for pairs the trinomial pdf (0/1/2 wins) is the analogue of
  pentanomial.
- **Typical game counts here (my simulation, 300 runs each, alpha = beta = 0.05, a ±15-point side effect like Team B's
  60–77% mirror advantage in `bots/jame/docs/research/drafting.md:51`):**

  | Test (H0 → H1) | true rate | P(accept H1) | median games unpaired / paired | 90th pct paired |
  |---|---|---|---|---|
  | improvement 50% → 55% | 50% | 0.03 / 0.07 | 470 / 381 | 988 |
  | | 52% | 0.34 / 0.39 | 769 / 549 | 1788 |
  | | 55% | 0.95 / 0.93 | 442 / 354 | 844 |
  | | 60% | 1.00 | 182 / 151 | 274 |
  | non-regression 45% → 50% | 45% | 0.06 / 0.05 | 424 / 369 | 964 |
  | | 50% | 0.98 / 0.96 | 445 / 394 | 930 |
  | | 55% | 1.00 | 179 / 148 | 310 |
  | targeted 50% → 65% | 50% | 0.06 | 47 / 40 | 110 |
  | | 65% | 0.98 / 0.91 | 46 / 30 | 86 |

  Pairing saved 15–30% here under the assumption that the two sides' outcomes are independent given the side effect.
  The real saving is larger when outcomes are correlated within a map + draft (many maps are near-deterministic 0/1 for
  a given matchup), which is what pentanomial/trinomial captures.
- **Recommended CAMBC parameters.** Gainer: [0%, +35 Elo] i.e. H0 50% / H1 55%, cap 2000 games (~7 min). Non-regression
  for refactors/simplifications/"neutral" ports: H0 45% / H1 50% (≈ [−35, 0] Elo, the CAMBC analogue of Fishtest's
  [−1.75, 0.25] scaled to our much larger noise), ~400 games. Targeted single-map fix: H0 50% / H1 65% on the 1–3 maps the
  hypothesis names, ~30–100 games of fresh seeds. A change truly worth 52% overall cannot be confirmed overall at any
  practical size (p ≈ 0.39 even with a 50/55 SPRT); split it into targeted + non-regression as training-process.md §2
  proposes.
- **Deterministic engine caveat.** At normal fuel there are only 80 distinct games per pair (40 maps x 2 sides);
  `batch.py` already counts distinct setups. SPRT needs independent samples, so beyond 80 games every extra game must
  come from a new draft seed (fuel quantum or compile-time `-DDRAFT_SEED`). Never replay the same map+side+seed.
- Implementation: `arena.py --sprt elo0,elo1` scheduling both sides of each (map, seed) together, updating the LLR as
  pairs complete (`run_matches` already yields incrementally), and killing the pool when a bound is hit. ~40 lines.

### Gaps
- Current exact Fishtest STC/LTC bounds (the Chessprogramming table's row labels were garbled; Fishtest's own wiki shows
  them only in images). Did not fetch the vdbergh normalized-Elo PDFs with the exact GSPRT formula (2.1); the
  normal-approximation formula above is standard but not quoted from a fetched page.

## 2. Variance reduction: pairing, common random numbers, stratification, map-effect models

### Takeaway
The biggest variance sources here are side (Team B advantage) and map/draft. Remove them by design, not by more games:
side-swapped pairs (common random numbers on map + seed), stratify by map (equal games per map, score per map), and
model map effects explicitly (Bradley–Terry / logistic regression with map and side terms) when reading results.

### Cited Findings
- Fishtest's pentanomial model of colour-reversed pairs "leads to a substantial saving of testing resources compared to
  the trinomial model" — quoted in [training-process.md](../../docs/research/training-process.md) from [Fishtest Mathematics](https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-Mathematics.html)
- BayesElo's model includes a first-move term: P(WhiteWins) = f(eloBlack − eloWhite − eloAdvantage + eloDraw), with
  defaults eloAdvantage = 32.8 ± 4 and eloDraw = 97.3 ± 2 fitted by maximum likelihood on 29,610 games; ratings by an MM
  (minorization–maximization) algorithm; it argues Elostat is wrong to ignore colour and treat opponents' ratings as
  exact — [Rémi Coulom, Bayesian Elo](https://www.remi-coulom.fr/Bayesian-Elo/)
- In CAMBC, Team B wins 60–77% of mirror games — `bots/jame/docs/research/drafting.md:51` (repo), via training-process.md
- v9's pathing fix: the_farm 0/10 → 10/10 against v8, yet 208/400 = 52% overall — `bots/daniel/docs/v9/summary.md:109`
- 330 v8 ranked games covered all 40 maps, 3–15 per map, consistent with uniform map sampling — training-process.md §4

### Inferences
- **Pairs = common random numbers.** Same map, same draft seed, sides swapped. Score per pair (0, 1, 2). This cancels
  the side term exactly and most of the map + draft term.
- **Stratify, don't pool.** Play the same number of pairs on every map (ranked maps are ~uniform), and report per-map
  pair scores. Pooled win rate under stratification has variance Σ_m p_m(1−p_m)/n_m/M², always ≤ the unstratified
  variance; the gain is largest when per-map rates are near 0 or 1, which is our case.
- **Map-effect model for reading results (not for gating).** Logistic regression
  `logit P(A wins) = δ + side_term·[A is B] + u_map`, with u_map ~ N(0, τ²) (partial pooling). δ is the global gain;
  posterior u_map flags maps the change broke. With 40 maps x ~5 pairs, fit by Newton/IRLS in ~60 lines of stdlib Python,
  or approximate: per-map Beta(1+wins, 1+losses) shrunk toward the global mean (empirical Bayes). Flag maps where
  P(p_map < 0.5) > 0.9 and the old version was ≥ 0.5 there.
- **Paired difference against a reference.** To compare candidates B and C that both beat A, play both against the same
  A on the same map+seed+side, and test the per-game difference (B_win − C_win) with a sign test on discordant games
  (McNemar). Concordant games carry no information; that is a large saving when most games are decided by the map.
- **Control variates (cheap extra).** Gem margin at round 2000 or at end is a continuous outcome correlated with
  winning; a test on the mean gem-margin difference per pair is usually more powerful than win/loss. Use it only as a
  secondary diagnostic: it can reward changes that farm gems without winning more.

### Gaps
- No primary source found quantifying pairing gains for asymmetric RTS-like games (only chess). Our simulation assumes
  independent sides; measure real within-pair correlation from existing `matches/` CSVs (fraction of pairs that are 1–1).

## 3. Rating systems for bot pools, local ladder-rating estimates and calibration

### Takeaway
For a fixed pool of frozen bots, use a batch Bradley–Terry fit (BayesElo/Ordo style, i.e. all games at once, with a
side term), not incremental Elo/Glicko/TrueSkill, which are designed for drifting skills and are order-dependent. To
relate local results to the ladder, use rating-adjusted residuals on ranked games and anchor local pool ratings with a
few ladder-observed anchors (our own submitted versions).

### Cited Findings
- Glicko-2: unrated players start at r = 1500, RD = 350, volatility σ = 0.06 ("depends on the particular application");
  system constant τ "Reasonable choices are between 0.3 and 1.2" (smaller, e.g. 0.2, if improbable results are
  expected); internal scale μ = (r − 1500)/173.7178, φ = RD/173.7178; games in a rating period are treated as
  simultaneous; it "works best when the number of games in a rating period is moderate to large, say an average of at
  least 10–15 games per player" — [Glickman, Example of the Glicko-2 system (2022 rev.)](http://www.glicko.net/glicko/glicko2.pdf)
- TrueSkill: new player μ = 25, σ = 8.333; displayed skill μ − 3σ; draw margin and per-game skill drift are configurable;
  minimum games to identify skill: 12 for 2-player free-for-all, 46 for 2 teams of 4, "can be up to three times higher" —
  [Microsoft Research, TrueSkill ranking system](https://www.microsoft.com/en-us/research/project/trueskill-ranking-system/) (paper: Herbrich, Minka, Graepel, "TrueSkill: A Bayesian Skill Rating System", NIPS 2006)
- Ordo computes ratings "considering all results at once", which "keeps consistency among ratings"; default pool
  average 2300 (`-a`), `-A "Engine X"` anchors one player — [Ordo README](https://github.com/michiguel/Ordo)
- BayesElo: MM maximum likelihood, `covariance` (Hessian inversion) for intervals, `los` likelihood-of-superiority
  matrix, a prior that pulls ratings together so 10–0 is not infinitely better than 1–0 — [Bayesian Elo](https://www.remi-coulom.fr/Bayesian-Elo/)
- Halite finals (95,562 games, 1,592 bots, fixed skill): batch Plackett–Luce had the lowest misprediction rate (43.87%
  test error) vs TrueSkill τ = 0 (44.24%), Weng–Lin BT-FP (44.56%), default TrueSkill (44.72%); incremental systems were
  order-dependent (TrueSkill error rose to 47.71% with random game order and 48.59% reversed); τ = 0 fits better because
  bot skill does not change — [janzert, Halite rating report](https://janzert.com/halite/rating-report)
- CAMBC ranked matchmaking pairs within ~±100 ranks; v8 went 10/35 vs ranks 300–400, 124/255 vs 400–500, 25/40 vs 500+;
  a ~48% record is what matchmaking produces at any strength; proposed residual = result − 1/(1+10^((R_opp−R_us)/400))
  with hourly `cambc ladder --json` snapshots — training-process.md §5

### Inferences
- **Local pool rating.** Fit Bradley–Terry with a side term on all pool games ever played (`matches/*.csv`):
  `P(i beats j | i is side B) = 1/(1+10^(−(r_i − r_j + h)/400))`, MM or Newton, ~50 lines stdlib, plus a weak prior
  (e.g. one virtual win and loss vs a pool-average dummy) so 10–0 records stay finite. Bot code is frozen, so this is the
  right model (janzert's τ = 0 finding). Report each candidate's rating with a bootstrap interval over (map, seed) pairs,
  not over games.
- **Anchoring to the ladder.** Every submitted version has a ladder rating trajectory. Use 2–3 past submitted versions
  (e.g. daniel/v7, v8, v9) as anchors: regress their ladder ratings on their local BT ratings to get scale and offset,
  then predict a candidate's ladder rating. With 2–3 anchors this only catches gross mismatches; record the residual
  per version in `data/submissions.jsonl` and recheck. Expect local scale to be compressed or stretched: local pools are
  mostly our own lineage, so distances between close versions are exaggerated (self-play intransitivity).
- **Ranked-side evaluation.** Use Glicko-2-style thinking only to interpret the platform's numbers: a newly submitted
  version needs on the order of tens of games before its rating settles (Glicko-2 suggests ≥ 10–15 games per period;
  TrueSkill 12+ for 1v1, up to 3x). Prefer the rating-adjusted residual sum over the raw record.
- Don't use incremental Elo locally: its K-factor makes ratings depend on game order and adds noise for no benefit when
  all results are available at once.

### Gaps
- The CAMBC ladder's own rating algorithm (Elo/Glicko/TrueSkill, K or τ) is undocumented in what I read; check the
  platform docs or infer it from `ladder --json` deltas after single matches.
- Ordo's exact model and simulation-based error bars were not in the README fetched.

## 4. Practices from Battlecode / Halite / Lux / engine teams: regression suites, pools, gauntlets, CI

### Takeaway
The pattern that works: a frozen, versioned opponent pool (previous versions + teammates + exploiters), a gauntlet
(candidate vs every pool member on every map), a non-regression gate against the current champion, and continuous
self-hosted testing (Fishtest/OpenBench style queues). Competition teams mostly accept "slightly above 50%" against the
previous version and then confirm in scrims; the engine community's SPRT discipline is the more rigorous model.

### Cited Findings
- Battlecode 2026 postmortem (team Lorem Ipsum): tests across "the entire variety of maps" including ~7 custom maps plus
  sprint maps; "If the bot clearly underperforms (lets say it gets around 30% winrate against the old one) most likely
  something is wrong… Even if the bot appears to perform roughly slightly above 50% we accept it (which is pretty low)";
  then "we start scrimming a lot of teams within our rating range" — [Battlecode 2026 postmortem, Lorem Ipsum](https://battlecode.org/assets/files/postmortem-2026-lorem-ipsum.pdf)
- Battlecode 2020 team (uvafan/bc20) reports being ranked 1st in ranked scrimmages before they closed (testing method
  not visible in the snippet) — [uvafan/bc20](https://github.com/uvafan/bc20)
- A Planet Wars bot author ran 300–500 games per version against earlier versions, and warns that the version-vs-
  previous tables are "Not reliable for judging strength!" — [satirist.org oddshrimp results](https://www.satirist.org/ai/planetwars/oddshrimp2.4-results.html)
- Robocode wiki advice: when a new version is close to the previous one, compare against several older versions or a
  stable baseline — [RoboWiki: how to build a good test bed?](https://robowiki.net/wiki/Thread:Talk:ScalarBot/Version_History/how_to_build_a_good_test_bed%3F)
- Halite community advice: test versions of your bot against each other locally with a match manager — search summary
  of [R-bloggers, Halite (2017)](https://www.r-bloggers.com/2017/02/halite-2/amp/)
- Lux AI Season 3 research evaluation uses match win rate, episode win rate and a TrueSkill estimate from offline league
  play, arguing a single win rate misses meta-adaptation — search summary of [arXiv 2609.12422](https://arxiv.org/pdf/2609.12422)
- AlphaStar's league: main agents plus "exploiter agents… whose sole purpose is to expose weaknesses of the main agent"
  — [DeepMind, AlphaStar Grandmaster](https://deepmind.google/discover/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/) (via training-process.md)
- OpenBench is "a Distributed SPRT Testing Framework for Chess Engines", self-hostable — [OpenBench](https://github.com/AndyGrant/OpenBench)

### Inferences
- **Gauntlet for CAMBC** (cutechess-cli "gauntlet" concept: one engine vs a list): `arena.py --gauntlet cand pool.txt`
  plays cand vs each pool member in paired SPRT non-regression mode (45/50), plus one gainer SPRT (50/55) vs the champion.
  Pool (5–8 bots): champion, champion−1, champion−2, best teammate bot of each teammate (`bots/simon/v6`,
  `bots/jame/v3`), `bots/simon/hunter-v0`, starter-cpp as a smoke test (expect ~100%; any loss = crash bug). With 8
  cores and ~400 games per member worst case, a full gauntlet is ~15 min; SPRT early stops make the typical run 5–8 min.
- **Smoke/regression suite before any statistics** (seconds): build in `--release` (platform runs release), 1 game per map
  vs starter, assert no `botFault`, no `fuelExhausted` events for our side, no exception logs. This catches the
  failures that SPRT would otherwise spend hundreds of games discovering.
- **CI shape.** A local queue (`tools/auto.py`) that, per commit to a bot folder: smoke suite → targeted SPRT on listed
  maps → non-regression SPRT vs champion → gauntlet → write a results row (version, git hash, LLR, games, per-map pair
  table, BT rating). GitHub Actions is unnecessary; the Mac is the compute. Keep every results row: the BT fit in §3
  uses all of them.
- **Accept-at-50% is a trap** (Lorem Ipsum's own self-critique). A non-regression SPRT formalises "not worse" with a
  known error rate instead of eyeballing.

### Gaps
- No Battlecode/Lux postmortem found with explicit sample sizes or statistical gates; most teams describe scrims, not
  local statistics. cutechess-cli's manual was not fetched; "gauntlet" is described from common usage, not quoted.

## 5. Multiple comparisons, noise and overfitting when tuning

### Takeaway
The main local pitfalls are (1) winner's curse from best-of-k selection, (2) peeking at a fixed-n test and stopping when
it looks good, (3) overfitting to a fixed, self-similar opponent pool, and (4) testing under non-ranked conditions
(seed fuel, debug build). Fix with SPRT (valid under continuous monitoring), re-testing selected winners on fresh seeds,
SPSA instead of accept/reject, and pool diversity checked against ranked results.

### Cited Findings
- `tune.py` plays 3 perturbed candidates for 160 games each and takes the best of 3, accepting at ≥ 56%: "The best-of-3
  selection inflates the accepted rate (winner's curse)"; recent tuning mostly measured noise (`v9/summary.md:26`) while
  structural fixes gave +17 points — training-process.md §1, §8
- Seed-fuel games (≥ 1M fuel) are not ranked conditions: Jame v3 logged 1 `fuelExhausted` at 100k and 0 at 1.01M on
  00stampede; local `cambc run` builds debug while the platform runs release — training-process.md §1
- SPSA needs "only two objective function measurements per iteration regardless of the dimension" — [JHU APL SPSA](https://www.jhuapl.edu/spsa/) (via training-process.md); Fishtest SPSA takes per-parameter
  (start, min, max, c_end, r_end), default range 0–2v, and advises stopping runs whose values "are barely changing"
  after a few thousand games — [Fishtest wiki: Creating my first test](https://official-stockfish.github.io/docs/fishtest-wiki/Creating-my-first-test.html)
- Version-vs-previous tables are "Not reliable for judging strength" — [satirist.org](https://www.satirist.org/ai/planetwars/oddshrimp2.4-results.html)
- v8 vs Jame v3 reproduced only 7/36 of the ranked-loss maps — training-process.md §3

### Inferences
- **Winner's curse size.** Picking the best of k = 3 candidates at n = 160 games each, all truly 50%, the expected max
  observed rate is about 50% + 0.85·σ ≈ 53.4% (σ = 3.95 points); P(max ≥ 56%) ≈ 1 − (1 − P(Z ≥ 1.52))³ ≈ 18%. So
  roughly one null step in six is "accepted". Fix: re-play the selected candidate on fresh seeds (not the selection
  games) before accepting, or use SPSA.
- **Peeking.** Repeatedly checking a fixed-n Wilson interval and stopping when it excludes 50% inflates the false-
  positive rate well beyond 5%. SPRT is designed for continuous monitoring; use it instead of manual peeking.
- **Many maps = many tests.** Flagging "any map with ≥ 3 lost pairs of 5" across 40 maps will fire by chance: for a
  truly 50% map, P(≥ 3 of 5 lost) = 50%; for 40 such maps something always fires. Use it relative to the old version's
  per-map record, or require a hierarchical posterior P(u_map < 0) > 0.9 (§2), or a Holm/Benjamini–Hochberg correction on
  per-map tests.
- **Pool overfitting.** Tuning against the incumbent finds a better self-play equilibrium, not a better ladder bot.
  Rotate opponents per SPSA step from the pool, hold out 1–2 pool members (never tuned against) as a check, and keep a
  pool member only if its per-map results against us correlate with our ranked per-map record.
- **Conditions.** Gate only on `--release` builds at 100k fuel; randomise drafts via a compile-time seed, not fuel.

### Gaps
- No primary source fetched for a formal treatment of winner's curse in engine tuning; numbers above are my calculation
  from the normal approximation.

## 6. Relating local results to ladder results

### Takeaway
Local win rate vs our own lineage is a weak predictor of ladder strength (matchmaking compresses records to ~50%, and
our pool is self-similar). The only direct test of ladder strength is ranked A/B by rating-adjusted score; locally, the
best proxy is a diverse pool whose per-map results correlate with ranked per-map results.

### Cited Findings
- A ~48% ranked record is what rating-matched pairing produces at any strength; ranked games come in groups of 5 vs one
  opponent; alternating two submissions for half a day each gives ~250 games per arm, SE of rating-adjusted score ≈ 3
  points, enough for a 7–8 point difference — training-process.md §3, §5
- Lorem Ipsum (Battlecode 2026) validated locally-accepted bots by scrimming many teams in their rating range —
  [Battlecode 2026 postmortem, Lorem Ipsum](https://battlecode.org/assets/files/postmortem-2026-lorem-ipsum.pdf)
- Incremental rating systems are order-dependent and noisier than batch fits on fixed-skill bots — [janzert](https://janzert.com/halite/rating-report)

### Inferences
- Treat the 5-game group as the unit for ranked statistics (games within a group share an opponent and are correlated).
  ~100 groups/day at ~500 games/day.
- Calibration check per version: predicted ladder delta (from the anchored local BT rating, §3) vs observed rating
  change after ≥ 50 ranked games. If local gains repeatedly overstate ranked gains, shrink local estimates by the
  observed ratio before deciding to submit.

### Gaps
- Unknown how the CAMBC ladder updates ratings and how much rating moves per group; needed to translate local Elo gains
  into expected ladder movement.
