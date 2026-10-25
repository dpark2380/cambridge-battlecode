# Fix the gate, then mine the ladder

The techniques worth adopting are statistical and data-engineering methods. Deep learning is not on the list. A side-swapped, paired **SPRT gate** played at ranked conditions (100k fuel, `--release`) is the single largest improvement. Second is a **per-game feature row with rule-based "lints"** extracted from every summary we already download. With both in place, a cheap **win-probability model** fitted on top teams' games turns "we lost" into "we fell behind on X by round Y on map Z". These are worth more than any learned policy because our current loop cannot measure the changes that matter. v9's pathing fix took the_farm from 0/10 to 10/10 and still read as 52% overall (`bots/daniel/docs/v9/summary.md:109`). `tune.py`'s best-of-3 accept-at-56% rule accepts roughly one pure-noise step in six. And `ranked.py` throws away the `events` and `championTimelines` that would explain our losses (`tools/ranked.py:63-64`). The published game-AI work agrees: the Kaggle simulation contests won with small compute were won by rule-based bots or by imitation of real per-unit actions, and our replays do not record actions. Learning should therefore enter the bot only as **constants and lookup tables** distilled offline, which costs almost no fuel. Phase 1 below is about 15 hours (13 of them tooling, which can start today under the backlog rules). Phase 2 (about 14 hours) adds the model and the pool. Phase 3 holds imitation-style learning back until Phase 2 shows it would pay.

## Our loop measures the wrong thing at the wrong conditions

The repo checks (read-only, 2026-10-25) show the gaps that matter. `arena.py` gates on a pooled raw win rate (`--min-winrate`, `tools/arena.py:129`). Its random-draft games run at a fuel quantum of `1_000_000 + 10_000·seed` (`tools/arena.py:83`), and no tool passes `--release`, although the platform runs release builds. At 1M+ fuel, fuel-budgeted code never hits its limits. Jame v3 logged one `fuelExhausted` event at 100k fuel and none at 1.01M on 00stampede, so seeded games test a different bot from the one that plays ranked. `tune.py` still accepts the best of three perturbed candidates at ≥ 56% (`tools/tune.py:106`). If all three candidates are truly 50% at 160 games each, the expected best observed rate is about 53.4% and P(best ≥ 56%) ≈ 18% (normal approximation). Most accepted steps are therefore noise, which matches v8/v9's experience that tuning "mostly measured noise" while structural fixes gave +17 points. Neither `duckdb` nor `sklearn` is installed in the system Python, so anything below has a stdlib version or needs a `uv` environment.

The engine testers solved this decades ago. Fishtest tests every patch with a generalized SPRT, with bounds in normalized Elo and LLR limits of ±2.94 (α = β = 0.05). It counts results on colour-reversed game pairs because the pentanomial pair model is more accurate than the trinomial one ([Fishtest Mathematics](https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-Mathematics.html)). It runs separate non-regression tests with bounds such as ⟨−1.75, 0.25⟩ for simplifications ([Fishtest: Creating my first test](https://official-stockfish.github.io/docs/fishtest-wiki/Creating-my-first-test.html)). OpenBench packages the same method with configurable `[elo0, elo1]` bounds and recommends α = β = 0.05 ([OpenBench wiki](https://github.com/AndyGrant/OpenBench/wiki/SPRT-and-Fixed%E2%80%90Game-Workloads)). For CAMBC, one map plus one draft seed played from both sides is a pair. Side matters a lot: Team B wins 60–77% of mirror games (`bots/jame/docs/research/drafting.md:51`). There are no draws, so a pair scores 0, 1 or 2. The team's own simulation (300 runs per row, α = β = 0.05) gives these test lengths. A **50% → 55% gainer test** ends in a median of **~350 paired games** (90th percentile ~850, under 4 minutes here). A **45% → 50% non-regression test** ends in ~400. A **50% → 65% targeted test** on the 1–3 maps a hypothesis names ends in **~30–40 games**. A change truly worth 52% overall passes a 50/55 test only 39% of the time. So a one-map fix has to be judged by a targeted test plus a non-regression test, never by the pooled rate.

Pairing is one form of variance reduction. Stratification and map-effect models are the others. Play equal pairs on every map, since ranked maps are close to uniform (330 v8 games covered all 40 maps). Read the results with a logistic model that has a side term and partially pooled per-map effects, which flags the maps a change broke. That is how a pilgrimage-style collapse (1/10) gets caught even when the pooled number looks fine. The multiple-comparison trap is real. For a truly 50% map, P(≥ 3 of 5 pairs lost) = 50%, so a naive "flag any map with 3 lost pairs" rule always fires somewhere across 40 maps. Flags must be relative to the old version's per-map record or use a posterior threshold. For the opponent pool, batch Bradley–Terry with a side term beats incremental ratings. On 95,562 Halite finals games with fixed-skill bots, batch Plackett–Luce had the lowest misprediction (43.87%). TrueSkill was order-dependent, and its error rose to 47.71% with random game order ([janzert, Halite rating report](https://janzert.com/halite/rating-report)). BayesElo likewise models a first-move advantage as an explicit term ([Coulom, Bayesian Elo](https://www.remi-coulom.fr/Bayesian-Elo/)).

## Every summary already holds the evidence we keep discarding

The replay-mining literature is mostly about scraping and parsing, and that part is done for us. `cambc matches summary --json` returns structured `events` (every death with its killer, position and round, plus camp clears, `fuelExhausted` and `botFault`) and run-length `championTimelines` for 17 metrics, for any team's ranked games. `tools/scout.py --replays` already decodes top-team replays into per-round timelines; 28 games are decoded in `data/scout/replays/` (3 MB). The missing piece is extraction. The best precedent is Halite's **halint**, a replay "linter" built for finals post-mortems. It flags specific inefficiencies per frame (cap loss with position and amount, failed mining, overkill, units that "flip-flop" between squares) and prints summary tables across any number of replays ([erdman/halint](https://github.com/erdman/halint)). Our equivalents come straight from the existing timeline columns and events: gems lost at death and to whom, A→B→A oscillation within 3 rounds (the_farm freeze), rounds spent on a camp spawn tile, `fuelExhausted`, long idle stretches while alive, and interrupted tribute channels. Each lint means more when we run the same lints on top teams' games. A lint matters only where our rate is high and theirs is low.

StarCraft research supplies two disciplines worth copying. Erickson and Buro wrote their own narrow feature extractor instead of reusing a generic parser, "to reduce the possible sources of error". They discarded games whose recorded winner conflicted with the score ([Erickson & Buro, AIIDE 2014](https://ojs.aaai.org/index.php/AIIDE/article/view/12725)). Here that means validating rows against the summary and dropping games where `analyze.mjs` fails. ironbar's Lux AI pipeline selected agents above a leaderboard-score threshold, downloaded their matches in bulk and held out "10% of the matches from the best leaderboard agent" for validation ([ironbar/luxai](https://github.com/ironbar/luxai)). Any table or model learned from top teams should likewise be checked against the #1 team's games it did not see. The storage design follows the community Kaggle episode datasets, which keep raw episodes filtered by rating and rebuild derived tables from them ([velocycle/orbit-wars-episodes](https://huggingface.co/datasets/velocycle/orbit-wars-episodes)). Keep each summary gzipped, write one `features.jsonl` row per game and team, and add a `features_version` field so a new feature means a re-run, not a re-download. At ~10³ games, stdlib `json` plus `collections.Counter` is enough. DuckDB, which reads JSON by glob with a `filename` column ([DuckDB JSON docs](https://duckdb.org/docs/2.0/data/json/overview.html)), is an option if timeline joins get slow.

The cheapest analysis on top of that table needs no model. For each feature at rounds 250, 500 and 1000, compute our z-score against the top-20 distribution on the same map. "Camp clears by r500: z = −2.4 on 00stampede" is a per-map target that does not depend on which opponent we drew. It also removes the matchmaking distortion: a ~48% ranked record is what rating-matched pairing produces at any strength.

## A small win-probability model is the best ML per hour

Win prediction from time-sliced replay snapshots is the standard, well-evaluated tool. Erickson and Buro sampled states every 10 seconds and used per-player feature **differences**, adding each state twice with the sign flipped so the model has no side bias. They evaluated with game-grouped 10-fold cross-validation, reporting results per time window. Accuracy was near chance in the opening (53.8% with all features at 0–5 minutes) and reached **72.6% after 15 minutes**. Economy and unit counts led mid-game, and map coverage became the best single group late (71.4%) ([Erickson & Buro](https://ojs.aaai.org/index.php/AIIDE/article/view/12725)). Ravari, Bakkes and Spronck got >63% average accuracy across time slices and found economy the strongest predictor, followed by micro commands ([AIIDE 2016](https://ojs.aaai.org/index.php/AIIDE/article/view/12887)). They used ~400 games. One `scout.py` pull plus our own ranked and local games gives more than that.

The CAMBC version has one row per (game, round ∈ {100, 200, …, 1000}). The features are team differences in gems submitted and carried, gold earned and unspent, kills, deaths split by camp vs champion, camp clears and `fuelExhausted`, plus a side indicator, and the label is the result. The fit is logistic regression in ~60 lines of stdlib IRLS. It has three uses, none of which puts a model in the bot. First, the **collapse round**: the first round at which P(win) falls below 0.3 and stays there points triage at the 50 rounds of replay worth watching. Second, ablation by feature group per map answers whether economy or camp control decides map X. Third, the coefficients are **exchange rates** between gems, gold, kills and time dead, which our heuristics hard-code (`gold_weight` = 0.20 was set by tuning that measured noise). That turns a fitted model into constants at zero fuel. The opening is the exception. Early accuracy is close to chance, so draft and first-target decisions should keep being evaluated by conditional win rates, as `draft_lab.py`'s Bradley–Terry fit already does.

The same model is the fixed behaviour value V^μ that makes outcome-weighted imitation possible later. AlphaStar Unplugged's offline actor-critic beat plain BC only with a *fixed* behaviour value. A learned V^π diverged, and full MuZero Unplugged collapsed to a few actions ([Mathieu et al., arXiv:2308.03526](https://arxiv.org/html/2308.03526v1)). The confound to guard against is team strength: good teams win, so their decisions look good. Rating difference from `cambc ladder --json` belongs in the model.

## Imitation works only where labels and executors exist

Behaviour cloning of top teams is the most proven ML route in recent Kaggle simulation contests. Lux AI S3's 9th place cloned one top team from **7,935 winning episodes**, then fine-tuned on 1,550 mixed episodes. It used a U-Net over stacked 24×24 frames with min-cost-flow action assignment and legal-action masking ([Uto, 9th place](https://speakerdeck.com/kuto5046/kaggle-lux-ai-season3-9th-place-solution)). The 3rd place cloned one top team and then fine-tuned on a second ([andreyd41/lux3-bot](https://github.com/andreyd41/lux3-bot)). AlphaStar Unplugged reached Elo 1380 with BC and 1485 after fine-tuning on top-tier games. Training on all filtered data and then fine-tuning beat training on the top tier alone ([arXiv:2308.03526](https://arxiv.org/html/2308.03526v1)). Two facts block a direct port. Those solutions trained on **recorded per-unit actions**, and our timelines hold only state (round, position, health, gems, gold, K/D/A), with no actions, targets, vision or shop timings per round. The in-repo measurement of ~0.86 int16 MACs per fuel caps a network at roughly 50–85k MACs per turn (`bots/jame/docs/research/rl-feasibility.md` §1), far below a spatial CNN. VPT's answer to state-only data is to infer actions with a labeller and then clone ([Baker et al., arXiv:2206.11795](https://arxiv.org/abs/2206.11795)). Here a hand-coded labeller can infer **macro intent** (next camp group or altar reached, retreat while health falls, buys at spawn) because it shows clearly over 10–30 rounds of positions. Label noise from position-only inference is untested at this scale and is the main risk. Anything the expert saw that our bot cannot see (fog of war) must be excluded from the features.

Where learning has worked under tight budgets, a small learned component sat inside an engineered system: BC plus min-cost-flow in Lux S3, BC/RL plus MCTS in Hungry Geese ([Maxwell_110](https://speakerdeck.com/hoxomaxwell/kaggle-hungry-geese)), and Stockfish's quantized NNUE inside alpha-beta search ([nnue-pytorch docs](https://github.com/official-stockfish/nnue-pytorch/blob/master/docs/nnue.md)). Rule-based bots won Kore 2022, and Kore's 1st place called its replay visualiser "vital" for diagnosing losses ([Kore 1st place](https://www.kaggle.com/competitions/kore-2022/writeups/harm-buisman-1st-place-solution)). For us the learned part should be a **scorer over a handful of candidates** (camp groups, fight or retreat) or a **lookup table**, exported with m2cgen, which emits dependency-free C for linear models, trees and LightGBM/XGBoost, in float64 only ([m2cgen](https://github.com/BayesWitnesses/m2cgen)), or distilled into a bucketed table. A 30-feature logistic model should cost under 200 fuel and a 100-tree depth-6 GBDT a few thousand. Both figures are estimates to measure with `cambc::fuel_remaining()`. The largest gain from top teams so far came without any model: v9's biggest single gain was copying a build (`bots/daniel/docs/v9/summary.md:122`), and B11/B12 are the same kind of copy.

## Search should race populations against a moving pool

For tuning continuous constants against a noisy win/loss signal, **SPSA on paired games** is the right choice at our budget. It adds up tiny signed signals over every game and never needs one configuration's mean resolved. Fishtest scales each parameter by a per-axis `c_i` chosen to give a "small, measurable Elo gap" and tolerates out-of-order updates, which suits parallel workers ([Fishtest Mathematics](https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-Mathematics.html)). It stops runs whose values are "barely changing" after a few thousand games ([Fishtest](https://official-stockfish.github.io/docs/fishtest-wiki/Creating-my-first-test.html)). CMA-ES needs a population of 4 + ⌊3 ln n⌋ per generation ([Hansen, arXiv:1604.00772](https://arxiv.org/abs/1604.00772)). For 7 parameters at ~100 games per candidate, that gives about 3 generations per 3,000 games, which is too few. BO tends to win only at budgets below ~10× the parameter count ([Loshchilov & Hutter, arXiv:1604.07269](https://www.arxiv-vanity.com/papers/1604.07269/)). Practitioners report that skopt-style BO fails when each configuration gets only a few games ([TalkChess](https://talkchess.com/viewtopic.php?p=890249)). Tuning is still low payoff: our evidence says the remaining constants sit below the noise floor.

For *structural* choices, the evidence favours populations and staged evaluation over a single incumbent. Hyperband/successive halving spends most games on the few configurations that matter and reports order-of-magnitude speedups over BO ([Li et al., arXiv:1603.06560](https://arxiv.org/abs/1603.06560)). FunSearch evolves a single priority function inside a fixed skeleton with an automatic evaluator ([google-deepmind/funsearch](https://github.com/google-deepmind/funsearch)). Eureka samples 16 independent candidates per iteration and feeds back training statistics as text. It beat human rewards on 83% of 29 tasks ([Ma et al., arXiv:2310.12931](https://arxiv.org/pdf/2310.12931)). FAMOU, a 2026 LLM program-evolution system for capture-the-flag, found that fixed evaluators "become unreliable as strategies improve, causing evolution to stall". It added three fixes: champions join the opponent pool, noisy few-game scores give way to statistically reliable ones, and the hardest opponents are up-weighted. It reached 61.7% against unseen opponents ([arXiv:2606.10389](https://arxiv.org/abs/2606.10389)). CodeClash, whose arenas include MIT Battlecode 2025, is the warning. Unscaffolded agents made ungrounded edits in more than 65% of rounds for most models. Claude Sonnet 4.5 hallucinated loss causes in more than 17% of rounds. Codebases grew "progressively messy", and the top model won **zero** rounds against an expert human bot ([Yang et al., arXiv:2511.00839](https://arxiv.org/abs/2511.00839)). Our backlog-with-evidence rule already counters the worst of these failures. What to add is a population of 3–8 variants per hypothesis, raced and then confirmed on fresh seeds (never on the race's own games), plus 1–2 held-out opponents never used for selection.

The ladder is the final judge, and a Battlecode team's own self-critique shows why. Lorem Ipsum (Battlecode 2026) accepted a bot "roughly slightly above 50%" against the old one, called that "pretty low", and then validated by scrimming teams in its rating range ([Lorem Ipsum postmortem](https://battlecode.org/assets/files/postmortem-2026-lorem-ipsum.pdf)). A Planet Wars author warns that version-vs-previous tables are "Not reliable for judging strength!" ([satirist.org](https://www.satirist.org/ai/planetwars/oddshrimp2.4-results.html)). The fix has three parts. Anchor local Bradley–Terry ratings to the ladder ratings of our past submitted versions. Treat the 5-game ranked group as the statistical unit. Keep a pool opponent only if its per-map results against us correlate with our ranked per-map record. v8 vs Jame v3 reproduced only 7 of 36 ranked-loss maps.

## Conclusion

The bottleneck is measurement, not modelling capacity. Every learned technique in the literature that fits our budget assumes an evaluator that can detect a +5-point or one-map gain and a corpus that keeps the per-round data. We have neither today, and both cost less than a day. Once they exist, the cheapest "ML" is mostly bookkeeping: z-scores against top teams, a logistic exchange-rate model and copied tables. Imitation and learned scorers become worth trying only if the win-probability model shows that a specific macro decision (fight or retreat, camp choice) separates winners from losers. Ranked results should overrule local numbers whenever they disagree, which the calibration step makes measurable for the first time.

Open questions remain. Whether the platform caps how many other teams' replays we may download is unverified. Label noise from position-only inference is unmeasured. The CAMBC ladder's rating algorithm is undocumented. No published source shows an LLM loop or a learned component climbing a human-competitive Battlecode ladder.

## Proposal for approval

**Standing rules kept.** Every item that changes bot behaviour gets a row in `bots/daniel/docs/backlog.md` with its evidence and expected effect **before** it is tested. Bot changes start only after the submitted version (v9, team bot version 8; v10 is a candidate awaiting approval) has **150 ranked games**, and then at most **one new change every 2 hours**. Data and tooling items (T-rows) can run at any time. **Nothing is submitted without your approval.** Costs are developer hours plus compute on the one 8-core Mac (~12k games/hour, so a 400-game gate takes ~2 minutes). Items are ordered by payoff per hour within each phase.

### Phase 1: this week (~15 h, of which 13 h tooling; no bot changes except item 7)

1. **Ranked-conditions builds and a smoke stage (backlog T1).**
   - *What:* `arena.py` builds with `--release`. Random drafts come from a compile-time `-DDRAFT_SEED=n` copy (reusing `tune.py`'s copy helper), and every game plays at 100k fuel. A `--smoke` stage plays 1 game per map vs `starter-cpp` and fails on any `botFault`, any `fuelExhausted` on our side, or any loss.
   - *Why:* seeded games at 1M+ fuel hide fuel overruns (Jame v3: 1 `fuelExhausted` at 100k, 0 at 1.01M), and the platform runs release builds.
   - *Cost:* 2 h.
   - *Repo:* `tools/arena.py`, `tools/tune.py` (shared copy helper); the seed hook in `bots/daniel/v10/src/draft.cpp` (and v11) reads a macro instead of the fuel quantum. Backlog T1 → `kept`.
   - *Success:* an A/A run (v10 vs a copy) at 100k fuel lands within 45–55% over 400 games. `fuelExhausted` events are visible in local summaries. The smoke stage runs in under 1 minute.
   - *Depends on:* nothing.

2. **Keep summaries; feature rows, lints and loss signatures (T3, new T5).**
   - *What:* `ranked.py` and `scout.py` store summaries gzipped instead of stripping them, and append one row per game and team to `features.jsonl`: ~30 features at rounds 250/500/1000, versioned. On top of the rows, a halint-style lint table (gems lost at death with killer, flip-flop movement, spawn-tile standing, `fuelExhausted`, idle while alive, interrupted tributes) and the rule-based signature table (frozen, race lost, camp trap, death spiral, fuel, tiebreak), printed as map × signature × count.
   - *Why:* halint precedent; `ranked.py:63-64` strips exactly this data; hourly analysis currently covers only decoded losses.
   - *Cost:* 3.5 h, stdlib only.
   - *Repo:* `tools/ranked.py`, `tools/scout.py`, and one shared `features()` placed in `tools/arena.py` so local `--statistics` games produce rows too. `data/games/`. Backlog T3 → `kept`; add T5 (lints).
   - *Success:* all v9 ranked games get rows. The tables reproduce the known v8/v9 findings (the_farm frozen; road-of-riches camp trap at the Golem corners) without manual analysis.
   - *Depends on:* nothing.

3. **Paired SPRT gate: targeted plus non-regression (T2).**
   - *What:* `arena.py --sprt` schedules both sides of each (map, seed) together and stops at LLR ±2.94. It offers three modes: gainer 50→55, non-regression 45→50, and targeted 50→65 on named maps. It also prints a per-map pair table, flagging maps only against the old version's record.
   - *Why:* Fishtest/OpenBench practice. A one-map fix reads as 52% pooled. The simulation gives ~30–40 games for targeted tests and ~350–400 for the other two.
   - *Cost:* 3.5 h (about 40 lines for the SPRT, plus scheduling and the report). `auto.py` switches from 55% to the two-part gate.
   - *Repo:* `tools/arena.py`, `tools/auto.py`, `docs/BatchTesting.md`. Backlog T2 → `kept`.
   - *Success:* replaying B1 (v9 vs v8 on the_farm) passes the targeted test in under 100 games. An A/A run passes non-regression and does not pass the gainer test. B3 (57% vs v9) passes the gainer test.
   - *Depends on:* item 1.

4. **Version attribution and rating-adjusted ranked score (T4).**
   - *What:* hourly `cambc ladder --json` snapshots and a `data/submissions.jsonl` (version, git hash, time). `ranked.py` prints the residual = result − expected score from the rating gap, per version, with the 5-game group as the unit.
   - *Why:* matchmaking pulls any version's record towards ~48%.
   - *Cost:* 1 h.
   - *Repo:* `tools/ranked.py`, `data/`. Backlog T4 → `kept`.
   - *Success:* v9's residual and its SE (~3 points at 250 games) are printed. The 150-game count per submitted version comes from this table automatically.
   - *Depends on:* nothing.

5. **Top-team benchmark corpus and per-map z-gap (extends B13, new T6).**
   - *What:* `scout.py --summaries` keeps full summaries (via item 2) for the top 20 teams, ≥ 5 games per map. `ranked.py` prints our worst z-scores vs top teams per map at r250/500/1000.
   - *Why:* this gives per-map targets that do not depend on the opponent drawn (ironbar/Kaggle rating-filtered corpora). The #1 team's games are held out to validate anything learned later.
   - *Cost:* 2 h of work plus ~1–2 h of unattended downloading. The quota is unverified, so check after the first 100.
   - *Repo:* `tools/scout.py`, `tools/ranked.py`, `data/scout/`. Backlog B13 gains the z-gap table as its output; add T6.
   - *Success:* ≥ 5 top-team games on each of 40 maps. Each of our weak maps (stampede, road-of-riches, corridors, eight, starvation) gets a named feature gap, written into its B-row as evidence.
   - *Depends on:* item 2.

6. **Fix `tune.py`'s winner's curse (small, T7).**
   - *What:* re-play the selected candidate on fresh seeds through the item-3 gainer SPRT before accepting it, in place of best-of-3 at 56%.
   - *Why:* about 18% of null steps are accepted today.
   - *Cost:* 1 h.
   - *Repo:* `tools/tune.py`. Add T7.
   - *Success:* a 10-iteration run of v10 vs itself accepts ≤ 1 step.
   - *Depends on:* items 1 and 3.

7. **First v11 change: B11 (Bruiser shards), through the new gate.**
   - *What:* create `bots/daniel/v11` from the approved base (v10 if you approve it, else v9). Make the B11 change and gate it with non-regression on all maps plus a gainer test.
   - *Why:* the top 20 teams buy Bruiser almost exclusively (`data/scout/20261025T1156Z.json`). A Bruiser emblem counts as 7 shards against Power's 6. A copied build was v9's largest gain.
   - *Cost:* 2 h of coding plus ~10 min of games.
   - *Repo:* `bots/daniel/v11/`, `bots/daniel/docs/v11/summary.md`, `bots/daniel/docs/README.md`. B11 `next` → `testing` → result.
   - *Success:* the gainer SPRT accepts H1 (≥ 55%), or non-regression passes and the ranked residual later improves. Lint and signature counts do not get worse.
   - *Depends on:* 150 ranked games of the submitted version (item 4 counts them), items 1 and 3, and your approval of the v10/v9 base. Submission needs your separate approval.

### Phase 2: next 1–2 weeks (~14 h, after Phase 1 is in place)

8. **Win-probability model: collapse round and exchange rates (T8).**
   - *What:* stdlib logistic regression on snapshot rows (team differences, side term, rating gap), with game-grouped cross-validation per round window. It adds a "collapse round" to every loss in the triage table and prints coefficients as gem/gold/kill/death exchange rates.
   - *Why:* Erickson & Buro reached 72.6% late-game accuracy from ~400 games with this exact method. The model is also the fixed V^μ that any later outcome-weighted imitation needs.
   - *Cost:* 4 h.
   - *Repo:* new `tools/winprob.py`, plus a triage column in `ranked.py`. Add T8. Any constant it suggests (for example `gold_weight`) becomes a B-row with the coefficient as evidence.
   - *Success:* cross-validated log-likelihood at r500+ beats a side-plus-rating-only baseline. The collapse round falls within 100 rounds of the manually identified turning point on 5 known losses.
   - *Depends on:* items 2 and 5.

9. **Racing many variants per hypothesis (T9).**
   - *What:* `arena.py --race v11a,v11b,…` runs successive halving: 40 games each, keep the top half, double the games. The winner is re-confirmed with a fresh-seed SPRT, never on the race's own games. For each B-row, Claude writes 3–6 independent implementations.
   - *Why:* Hyperband/FunSearch/Eureka population evidence. It uses the cheap evaluator and still counts as one backlog change per 2-hour slot.
   - *Cost:* 2 h.
   - *Repo:* `tools/arena.py`. Losing variant folders are deleted after the race. Add T9.
   - *Success:* in a retro test, the race picks B3's kept implementation over 3 decoys.
   - *Depends on:* items 1 and 3.

10. **Gauntlet pool, batch Bradley–Terry rating and ladder anchoring (T10).**
    - *What:* `arena.py --gauntlet` plays the candidate vs a pool file (the champion, its two predecessors, `bots/simon/v6`, `bots/jame/v3`, `bots/simon/hunter-v0`, plus `starter-cpp` as a smoke test). One or two members are held out and never used for selection. A BT fit with a side term over all `matches/` results gives ratings with bootstrap intervals over (map, seed). Regress v7/v8/v9's ladder ratings on their local ratings.
    - *Why:* janzert shows batch fits beat incremental ones for fixed bots. FAMOU's unseen-opponent check and Lorem Ipsum's critique of accept-at-50% point the same way.
    - *Cost:* 3 h.
    - *Repo:* `tools/arena.py`, `data/pool.txt`. Add T10.
    - *Success:* a predicted ladder delta is printed per candidate. After ≥ 50 ranked games, record the observed vs predicted delta in `submissions.jsonl`.
    - *Depends on:* items 3 and 4.

11. **Draft and build tables against the observed meta (B12 support, T11).**
    - *What:* `draft_lab.py collect` weights opponents by the top-20 compositions' observed frequency instead of uniform random rosters (fictitious-play style). It also produces a first-k `itemsBought` table per champion type and map.
    - *Why:* the top 20 draft Vesper 92%, Heart of Ruin 85% and Marcella 85%, and our draft leans on rare picks. These are direct labels, so no label inference is needed.
    - *Cost:* 3 h of tooling plus an overnight collection run.
    - *Repo:* `tools/draft_lab.py`. The resulting draft change is a v11 B12 row and follows the cadence.
    - *Success:* the table, validated on held-out #1-team games, predicts their picks better than the current table. The resulting B12 change passes item 3's gate.
    - *Depends on:* items 1 and 5, and B4 (a Heart of Ruin play pattern) before drafting it.

12. **Opponent style clusters (T12).**
    - *What:* k-means (k = 3–6, stdlib) on per-team-game vectors: draft, shard split, first camp cleared, time in the enemy half, kills before r300, gems carried at death. Then our ranked record per cluster.
    - *Why:* the Synnaeve/Weber opponent-modelling lineage. It tells us which play style we lose to, which is what profile bots and exploiters should imitate.
    - *Cost:* 2 h.
    - *Repo:* `tools/winprob.py` or `tools/ranked.py`. Add T12.
    - *Success:* the clusters are nameable by hand and our residual differs by ≥ 10 points between at least two clusters. If not, stop here.
    - *Depends on:* items 2 and 5.

### Phase 3: later, only if Phase 2 evidence calls for it

13. **SPSA in `tune.py` against the pool (T13).**
    - *What:* each step plays θ + cΔ vs θ − cΔ in side-swapped pairs, each also against a rotating pool member. Run 2,000–4,000 pairs, freeze the mean of the last third, and confirm with the non-regression SPRT.
    - *Why:* Fishtest's method; it is the only tuner that works below the noise floor.
    - *Cost:* 3 h plus an overnight run.
    - *Repo:* `tools/tune.py`.
    - *Success:* an SPSA result passes the gainer SPRT on fresh seeds.
    - *Depends on:* items 1, 3 and 10. Run it only for constants that item 8 suggests matter.

14. **Exploiter runs (T14).**
    - *What:* after each promotion, one SPSA/ES run that maximises win rate against the frozen main bot. Freeze the result into the pool if it beats main ≥ 60%, and up-weight the pool members main does worst against.
    - *Why:* AlphaStar's league and FAMOU's weakness pressure.
    - *Cost:* 1 h plus an overnight run per promotion.
    - *Repo:* `tools/tune.py --opponent`, `data/pool.txt`.
    - *Success:* the exploiter's per-map results against main correlate with our ranked per-map losses.
    - *Depends on:* items 10 and 13.

15. **Macro-decision labeller and a fight/retreat table (T15, then a B-row).**
    - *What:* hand-coded labels from top-team timelines (target reached next, retreat, contact outcomes), restricted to features our bot can observe. Outcome-weighted (AWR-style) using item 8's V^μ. The result is distilled into a bucketed P(win the fight) table, or into a ≤ 100-tree GBDT exported with m2cgen, which needs a `uv` environment with sklearn/LightGBM.
    - *Why:* the Lux S3/AlphaStar Unplugged BC evidence, the VPT-style inferred labels, and the AWR precedent.
    - *Cost:* 1.5 days.
    - *Repo:* `tools/labeller.py`, `bots/daniel/v11+/src/learned_*.cpp` (globbed by CMake).
    - *Success:* the held-out #1-team fight outcomes are predicted better than our current retreat rule. In-bot cost is under 5k fuel, measured with `fuel_remaining()`. The bot change passes item 3's gate.
    - *Depends on:* item 8 showing that fight outcomes separate winners, items 2 and 5, and the 2-hour cadence.

16. **Read the remaining postmortems (T16).** `brew install poppler`, then `pdftotext` the 2025/2026 Battlecode postmortems, especially Lorem Ipsum §10.1 "Testing & Tuning". Cost: 1 h. Success: any testing-cadence idea not covered here becomes a T-row. Depends on: nothing.

### Not recommended

- **Neural self-play RL or end-to-end policy learning.** The engine is closed with no state resets, and inference is capped at ~50–85k MACs per turn (`rl-feasibility.md`). Hungry Geese and Lux winners used seconds per turn.
- **Spatial behaviour cloning (U-Net style).** It needs recorded per-unit actions, and our replays hold only states. 10⁴–10⁵ macro decisions are enough for trees and tables, not for a CNN.
- **Iterative offline Q-learning or MuZero-style training.** AlphaStar Unplugged's learned V^π diverged and full MuZero Unplugged collapsed. Use only a fixed V^μ (item 8).
- **BO/Optuna or CMA-ES for continuous constants.** Too few games per configuration at our budget. CMA-ES gives ~3 generations per 3,000 games.
- **Unscaffolded autonomous agent loops.** CodeClash: ungrounded edits, hallucinated loss causes, repo rot and zero wins against expert humans. Keep the evidence-first backlog and the gates mandatory.
- **Full MAP-Elites grids now.** QD is evaluation-hungry and only spans what the constants express. Revisit a 4×4 opponent grid after item 14, and only if the pool lacks diversity.
- **Incremental Elo/TrueSkill for the local pool.** Order-dependent and noisier than batch BT for frozen bots.
- **DuckDB/Parquet, GitHub Actions CI, or "faster evaluation" via `--rounds`.** Stdlib handles ~10³ games, the Mac is the compute, and truncated games give no result.
- **NNUE-style incremental accumulators.** They pay off only inside search, which we do not run.
