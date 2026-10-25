# Learning bot behaviour under a ~100k-fuel/turn budget: imitation, partial policies, distillation, offline RL, small-scale self-play

Researched 2026-10-25. Builds on, and does not repeat, `bots/jame/docs/research/rl-feasibility.md` (end-to-end RL infeasible; measured ~0.86 int16 MACs/fuel, so at most ~50–85k MACs/turn; ~12k C++ games/hour on 8 cores; recommends tuning plus offline draft tables) and `docs/research/training-process.md` (SPRT gating, profile bots and exploiters, mining top teams' summaries). Kaggle writeup pages render client-side and could not be fetched. Where only a search snippet or secondary summary was available, that is said explicitly.

Local data check (measured this session): `data/scout/replays/` holds 112 files from `tools/scout.py --replays` (several files per match). Each `.timeline.csv.gz` row is `round, submittedA/B, champion, team, type, alive, x, y, health, maxHealth, gems, gold, earnedGold, kills, deaths, assists`. **There are no actions, attack targets, vision or shop timings per round in the timelines.** Summaries add `itemsBought` and `events` (deaths with killer, camp clears) (`docs/research/training-process.md` §7). This one fact shapes everything below: any imitation of top teams must first infer *labels* from state changes.

## 1. Behaviour cloning / imitation learning from top-team replays

### Takeaway
Imitation learning from the top teams' replays is the most proven ML route in recent Kaggle simulation contests. In Lux AI S3, the 3rd- and 9th-place solutions were pure BC of the top team, using about 8k episodes. But those wins used 24×24 U-Net policies at seconds per turn, and the training labels were real per-unit actions. For CAMBC the feasible version is to clone **coarse macro decisions** (which camp group or altar to target, fight or retreat, what to buy), with labels inferred from position and gem timelines, into small trees or tables. Cloning low-level moves is not feasible.

### Cited Findings
- **Lux AI S3 (NeurIPS 2024), 9th place:** BC on a top team's ("Frog Parade") submissions.
  - Stage 1 trained on **7,935 episodes from winning games only**. Stage 2 fine-tuned on **1,550 episodes** that included both wins and losses.
  - Data was augmented by mirroring in x and y.
  - The model was a U-Net with ResBlocks over 14 channels × 4 stacked frames × 24×24, trained for 30 epochs at batch size 1024.
  - Inference added Bayesian estimation of hidden state and hidden env parameters, plus **min-cost-flow assignment of actions to units** with legal-action masking.
  — [Uto, 9th place deck](https://speakerdeck.com/kuto5046/kaggle-lux-ai-season3-9th-place-solution)
- **Lux AI S3, 3rd place:** two U-Nets, one for unit moves and one for sap (attack) targeting, with 28×24×24 inputs.
  - Trained first on Frog Parade replays, then **fine-tuned on a second top team ("Flat Neurons")**, which performed better locally and on the leaderboard.
  - Matches where one team won more than 2 games were filtered out.
  - No episode count is given. — [andreyd41/lux3-bot](https://github.com/andreyd41/lux3-bot)
  - The writeup snippet says the author switched from a rule-based agent to IL "after weeks of stalled progress". — [Kaggle writeup (snippet only)](https://www.kaggle.com/competitions/lux-ai-season-3/writeups/adg4b-imitation-learning-3rd-place-solution)
- **Lux AI 2021 (S1):** IL was a mainstream approach.
  - ironbar trained a conditioned U-Net by IL on agents above a leaderboard-score threshold, holding out "10% of the matches from the best leaderboard agent" for validation. Training took about a day on 2×RTX3090. — [ironbar/luxai](https://github.com/ironbar/luxai)
  - A public IL notebook came from sazuma, who placed 10th. — [Kaggle discussion (snippet)](https://www.kaggle.com/competitions/lux-ai-2021/discussion/287562)
  - The winner (Toad Brigade) used RL with a ~20M-parameter net at 3 s/turn (already covered in rl-feasibility.md).
- **Hungry Geese (2021):**
  - **3rd place used BC plus MCTS** and refreshed the training episodes iteratively as stronger agents appeared on the ladder. — [Maxwell_110 deck](https://speakerdeck.com/hoxomaxwell/kaggle-hungry-geese)
  - **11th place** ran IL, then HandyRL self-play fine-tuning, then retrained the IL model on the fine-tuned agent's data (NN+MCTS). — [11th place writeup (snippet)](https://www.kaggle.com/competitions/hungry-geese/writeups/the-wisdom-of-manjushri-if-three-ducks-approach-11)
  - 1st place is described secondhand as deep RL plus MCTS from self-play followed by diverse opponents. — [secondary summary (snippet)](https://www.kaggle.com/writeups/zoli800/winning-kaggles-reinforcement-learning-competitio)
- **Kore 2022 and Lux S2: rule-based winners.**
  - Kore's 1st place was rule-based, building on the Kore Beta winner and mainly changing the expansion strategy. A replay visualiser was "vital" for diagnosing losses. — [1st place writeup (snippet)](https://www.kaggle.com/competitions/kore-2022/writeups/harm-buisman-1st-place-solution)
  - A secondary summary says Kore's top 3 were all rule-based, built on forward simulation and route scoring. — [summary (snippet)](https://www.kaggle.com/writeups/zoli800/winning-kaggles-reinforcement-learning-competitio)
  - Lux S2's leading teams are reported as rule-based, and 2nd place was a "stateful rules based bot". This is from search snippets only. — [search result incl. Kaggle S2 discussion](https://www.kaggle.com/c/lux-ai-season-2/discussion/405476)
- **Google Research Football:** TiKick learned a multi-agent full-game policy offline from "a large replay dataset" produced by single-agent experts trained by league self-play. The authors claim it was the first learning-based AI to take over the multi-agent full game, and that pre-training accelerated later multi-agent RL. — [Huang et al., arXiv:2110.04507](https://arxiv.org/abs/2110.04507)
- **AlphaStar Unplugged:** data scale for "real" BC.
  - Of ~20M public games, 1.4M games (2.8M episodes) remained after keeping only players with MMR > 3500.
  - BC reached Elo 1380, and **BC fine-tuned on top-tier games reached 1485**.
  - Training only on the filtered subset did worse than training on everything and then fine-tuning on the top tier. — [Mathieu et al., arXiv:2308.03526](https://arxiv.org/html/2308.03526v1)
- **Labels from state-only data:** VPT trained an inverse dynamics model on "a small amount of labeled data" and used it to label a huge unlabeled video corpus, then ran BC on the inferred actions. — [Baker et al., arXiv:2206.11795](https://arxiv.org/abs/2206.11795)

### Inferences
- **The data volume is achievable.** Lux S3 BC used about 8k episodes of one team. If our download quota allows, the top 5 teams × 100+ ranked games each, × 3–5 champions, gives roughly 2k–3k champion-episodes. Each episode has ~2000 rounds but only tens of *macro* decisions (target choice, recall, buy) per champion per game, so the set is roughly 10⁴–10⁵ labelled macro decisions. That is enough for gradient-boosted trees (GBDTs) or tables with tens of features, and nowhere near enough for a spatial CNN.
- **Labels must be inferred (the VPT idea, but rule-based).** Write a Python labeller over the timeline CSV plus the summary events:
  - "target" = the camp group or altar the champion reaches next (from the camp positions in `maps/ascii`)
  - "retreat" = moving away from the nearest enemy while health/maxHealth falls
  - "buy" = `itemsBought` at the round of a spawn or death
  - The VPT paper's point is that a small labelled set can train a labeller. Here the labeller can be hand-coded, because macro intent shows clearly in positions over 10–30 rounds.
- **What the replays cannot teach:** anything that needs vision, such as dodging, kiting or ability timing. Fog of war makes the expert's observation unknowable, because we only see the full state.
  - Features must therefore be restricted to what our bot would observe or remember: own health, gems, gold, round, distance to camps and altars, last-seen enemies.
  - Otherwise the cloned policy will "know" things at test time that it cannot see. This is a form of causal confusion; the term is my framing, not from a source.
- **Lux S3's pattern ports:** keep a heuristic executor (our pathing and combat) and let the learned model output only a score per candidate. This mirrors S3's min-cost-flow assignment of unit actions on top of policy maps.
- **Copy the AlphaStar Unplugged recipe:** train on all decent teams' games, then fine-tune or reweight on the #1–#2 teams, rather than training on top-team data alone.
- **Cost estimate for a 3-person team:** about 1 day for the labeller and feature extraction (Python, reusing `scout.py` output), 1–2 hours to train with LightGBM/sklearn on the Mac, and 0.5 day to export to C++ and A/B test with `arena.py`.

### Gaps
- Episode counts and data-size ablations for the Lux S3 3rd and S1 IL solutions (Kaggle pages could not be fetched).
- Whether Lux S3 1st place (Frog Parade) itself used RL, IL or rules: not found.
- Halite IV winner method: not found.
- CAMBC platform limits on how many other teams' replays we may download: unverified.
- No source tests BC with labels *inferred from positions only* at this scale. Label noise is the main unquantified risk.

## 2. Learning only parts of the policy (targets, draft, buys, fight/retreat, win-probability)

### Takeaway
The successes of IL and RL that fit tiny budgets all keep a learned component inside an engineered system: S3 BC plus min-cost-flow, Hungry Geese BC/RL plus MCTS, Stockfish NNUE plus search. For us the best targets are, in order:
1. A **win-probability / value model** fitted on outcome data, used to weight existing heuristic scores.
2. **Buy orders and draft** copied as tables from top teams.
3. A **fight/retreat classifier**.
4. **Target selection** as a learned scorer over candidate camp groups.

### Cited Findings
- **Learned component inside search:** Hungry Geese top solutions combined a learned policy/value net with MCTS (3rd and 11th place).
  - The secondary summary says search fixed tactical mistakes and a diverse opponent pool fixed the conventions learned in homogeneous self-play. — [Maxwell_110 deck](https://speakerdeck.com/hoxomaxwell/kaggle-hungry-geese); [summary (snippet)](https://www.kaggle.com/writeups/zoli800/winning-kaggles-reinforcement-learning-competitio)
- **A learned value is worth more with a planner than as a policy:** in AlphaStar Unplugged, MuZero Supervised *with MCTS at inference* scored Elo 1578 vs 1425 without MCTS (BC 1380). — [arXiv:2308.03526](https://arxiv.org/html/2308.03526v1)
- **Hidden-state estimation feeds the learned part:** Lux S3 9th estimated 4 hidden env parameters (mean and variance) and passed them to the network as scalar features. — [9th place deck](https://speakerdeck.com/kuto5046/kaggle-lux-ai-season3-9th-place-solution)
- **Repo evidence for copying builds:** the largest single gain in v9 came from copying a build (`bots/daniel/docs/v9/summary.md:122`, cited in `docs/research/training-process.md`).
- **Top-team drafts are stable:** #1 drafted Vesper and Heart of Ruin in 100/100 games (`docs/research/training-process.md` §3). Draft and buys are low-dimensional, have direct labels in `draftPicks` and `itemsBought`, and need no label inference.

### Inferences
- **Win-probability model (best ML value per hour).**
  - Data: every local `arena.py` game plus every downloaded ranked summary gives a row per (game, round in {100, 200, …}). Features come from `championTimelines`: gem, gold, kill and death differences, alive counts, submitted gems, map id, team size. The label is the final winner.
  - Fit logistic regression or a small GBDT; thousands of games are cheap (12k/hour locally).
  - Uses:
    - (a) Offline, as a dense evaluation signal: compare a change by ΔP(win) at round 500 instead of by final results only. This lowers the variance of A/B tests and complements SPRT.
    - (b) Online, to learn the *exchange rates* our heuristics hard-code, such as gems vs gold vs a kill vs time dead. The learned coefficients become constants (e.g. `gold_weight`) instead of a model running in the bot.
  - This is distillation into constants, which costs 0 fuel at inference.
- **Fight/retreat classifier.**
  - Label: from top-team timelines, a contact event (enemy within ~R tiles) that ends with our champion alive and the enemy dead or gone vs our champion dead.
  - Features: our and their health fractions, champion types, counts, gems carried, distance to the altar.
  - The output is a P(win the fight) threshold that replaces the hand-set retreat HP%. The resulting trees are tiny.
- **Target selection.** Score each candidate camp group with a learned function of (distance, reward, team size, threat, round). Train with a ranking or "chosen-vs-not-chosen" logistic loss on the inferred top-team targets. Keep our claim protocol in shared memory unchanged.
- **Buys:** an n-gram/first-k table of `itemsBought` per champion type and map, taken from the top teams. This is not really ML: a lookup table, about 1 hour of work.

### Gaps
- Whether ranked summaries expose `championTimelines` for the opponent's champions as well as ours: assumed from training-process.md §7, not re-verified here.
- No published evidence that a win-probability model improves heuristic game bots specifically; the value-model evidence (AlphaStar Unplugged, NNUE) comes with search, which we lack at this budget.

## 3. Distillation and compression to fit the fuel budget

### Takeaway
Small GBDTs, linear models and int8/int16 MLPs compiled to straight-line C++ fit comfortably within a few thousand fuel per call. Chess engines (Stockfish NNUE) are the best-documented evidence that tiny quantized, incrementally updated nets win under hard compute limits. The bottleneck is labels and features, not inference.

### Cited Findings
- **m2cgen** turns trained models into code with no dependencies, with C as a target. It supports linear models, SVMs, trees, random forests, and LightGBM (gbdt/dart/goss) and XGBoost (gbtree/gblinear).
  - It works only in float64.
  - Large ensembles can hit recursion errors, and the fix is fewer estimators. — [m2cgen README](https://github.com/BayesWitnesses/m2cgen)
- **Stockfish NNUE:**
  - Quantised to int8/int16 because "floating point is not an option for achieving maximum engine strength".
  - The first layer is sparse with an **accumulator updated incrementally**: add or subtract one weight column per changed feature, because "any move can only change at most 4 inputs".
  - Architectures moved from `256x2->32->32->1` to `1024x2->8->32->1`.
  - The width of the first layer has "the highest impact on speed and size". — [nnue-pytorch docs](https://github.com/official-stockfish/nnue-pytorch/blob/master/docs/nnue.md)
- **Measured in-repo:** a 64×64 int16 SIMD dense layer costs 4,776 fuel (0.86 MAC/fuel), the scalar f32 version 52,490. — `bots/jame/docs/research/rl-feasibility.md` §1

### Inferences
- **Fuel estimates (my estimates, not measured):**
  - A single depth-6 tree is about 6 compare-and-branch steps, which is tens of Wasm instructions.
  - A 100-tree depth-6 GBDT is about 600 compares plus 100 adds, probably about 3–8k fuel.
  - A 30-feature logistic model costs under 200 fuel.
  - **Measure it with `cambc::fuel_remaining()` before and after the call**, as CLAUDE.md advises.
  - At these costs, a learned scorer can be evaluated over 10–20 candidates (camp groups) per turn within ~20–50% of the budget. A per-tile model cannot.
- **Practical export path:**
  1. Fit with LightGBM or sklearn.
  2. Run `m2cgen.export_to_c(model)`.
  3. Paste the output into `src/learned_*.cpp`; CMake globs it automatically.
  4. Change `double` to `float` with a sed pass, or keep doubles (Wasm has f64, cost similar).
  5. Check parity against Python predictions on 1k rows.
  - Treelite is an alternative that also generates C for tree ensembles, but it targets shared libraries. m2cgen's plain source suits the Wasm build better (this is my judgement; treelite docs were not fetched).
- **Even cheaper: distil into tables.** Bucket 2–3 features and store the mean prediction (e.g. a 10×10×champion fight table). Lookup is O(1) and easy to read when debugging.
- **NNUE-style incremental accumulators** only pay off when the bot evaluates many similar states (search). We do not search, so plain small MLPs or trees suffice.

### Gaps
- No public fuel or instruction measurements for m2cgen-generated C under Wasmtime; we must measure locally.
- Treelite's current C codegen status in 2026 was not verified.

## 4. Offline RL / advantage-weighted regression from logged games

### Takeaway
Offline RL beats BC when data is suboptimal or mixed, rewards are sparse and horizons are long. Those conditions match our setting, where we have every ladder team's games with outcomes, not only experts'. But the documented gains need a learned value function plus enough data. A cheap middle ground is **outcome-weighted or filtered BC**: weight each decision by the win probability gain that followed, or keep only winners' decisions. That is AWR's idea, with a learned value model from §2.

### Cited Findings
- Kumar et al. (2022): "policies trained on sufficiently noisy suboptimal data can attain better performance than even BC" with expert data. The advantage appears "under specific but common conditions such as sparse rewards or noisy data sources" and is largest on long-horizon tasks. — [arXiv:2204.05618](https://arxiv.org/abs/2204.05618)
- AlphaStar Unplugged on the same 1.4M-game dataset:
  - BC Elo 1380, fine-tuned BC 1485.
  - Offline actor-critic 1548, emphatic offline actor-critic 1563, MuZero Supervised + MCTS 1578.
  - The critic had to be the **fixed behaviour value V^μ**. A learned V^π made the agent diverge, and full MuZero Unplugged collapsed to a few actions. — [arXiv:2308.03526](https://arxiv.org/html/2308.03526v1)
- Lux S3 9th's two-stage scheme is a crude form of outcome conditioning: stage 1 trained on winning games only, stage 2 fine-tuned on wins and losses. — [9th place deck](https://speakerdeck.com/kuto5046/kaggle-lux-ai-season3-9th-place-solution)

### Inferences
- **The AlphaStar Unplugged lesson for us:** use a *fixed* value model trained on logged outcomes (the §2 win-probability model is exactly V^μ). Reweight cloned decisions by exp(β·(V(after) − V(before))). This is advantage-weighted regression in about 20 lines of pandas. Do not attempt iterative offline Q-learning.
- **We can mix data sources:** top-team replays, mid-ladder replays (ours and opponents) and local self-play. Plain BC would average them; outcome weighting lets low-rated data contribute without being copied blindly.
- **Risk:** the advantage estimate is confounded by team strength, since good teams win and so their decisions look good. Include rating difference (from `cambc ladder --json`) as a feature in V, or compare only within a game.

### Gaps
- No competition writeup found that used AWR or offline RL with small (≤10⁵ decision) datasets; the evidence comes from large-scale research settings.

## 5. Self-play and population methods at small scale

### Takeaway
The documented small-scale pattern is a short loop: **IL warm start → self-play fine-tune → re-distil** (Hungry Geese 11th place; TiKick's league-to-offline pipeline). The opponent pool must be diverse, which AlphaStar's league is designed to provide. With our closed engine and ~12k games/hour, "self-play" means evolving *parameters and tables*, not network weights.

### Cited Findings
- **Hungry Geese 11th:** IL → HandyRL self-play fine-tune → retrain the IL model on the fine-tuned agent's games. — [writeup (snippet)](https://www.kaggle.com/competitions/hungry-geese/writeups/the-wisdom-of-manjushri-if-three-ducks-approach-11)
- **Hungry Geese 3rd:** refreshed its imitation data as stronger ladder agents appeared, i.e. iterated BC against a moving target. — [deck](https://speakerdeck.com/hoxomaxwell/kaggle-hungry-geese)
- **Hungry Geese 1st** (secondary source): pure self-play first, then diverse opponents, to fix the conventions learned in homogeneous self-play. — [summary (snippet)](https://www.kaggle.com/writeups/zoli800/winning-kaggles-reinforcement-learning-competitio)
- **TiKick:** league-trained single-agent experts generated the dataset, and offline learning distilled them into a multi-agent policy. — [arXiv:2110.04507](https://arxiv.org/abs/2110.04507)
- The AlphaStar main-agent/exploiter league is already summarised for our setting in `docs/research/training-process.md` §3.

### Inferences
- **Scaled-down loop for CAMBC, one Mac:**
  1. Fit the learned components (§2) on top-team data.
  2. Freeze them as a bot and run `tune.py`/SPSA on their few thresholds against a pool of past versions, profile bots and exploiters.
  3. Re-collect local games with the new bot and refit the win-probability model, because its distribution shifts as play changes.
  4. Gate with SPRT (training-process.md §2).
- **Cost:** one cycle is about an overnight run of ~50–100k games.
- **Fictitious play over drafts:** best-response draft tables against the mixture of top teams' observed drafts. Cheap with the existing `draft_lab.py` collect/fit pipeline: weight opponents by the ladder frequency of their compositions instead of uniform random rosters.
- **Do not attempt neural self-play RL.** All the reasons in rl-feasibility.md still hold: closed engine, no state resets, a tiny inference budget.

### Gaps
- No published costs for population methods on parameterised (non-neural) bots in Kaggle or Battlecode contexts.
- Whether CAMBC's top teams use any learned components: unknown. Only their drafts and builds are observable.
