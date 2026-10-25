# Methods for systematically improving heuristic game bots (CAMBC 2026)

Scope: techniques that find improvements faster than "hand-edit one idea, gate it". This builds on
`docs/research/training-process.md`, which already covers pentanomial/pair SPRT gating, profile bots, AlphaStar-style
exploiters as `tune.py --opponent` runs, ranked-summary triage and a first SPSA sketch. This note does not repeat
those. Sources marked "(fetched)" were read this session. Sources marked "(canonical, not re-fetched)" are standard
primary references cited for their basic definitions only.

## 1. Black-box optimisers for noisy win-rate objectives: which works best per evaluation budget?

### Takeaway
At our budget (a few thousand games per tuning run, 5–30 parameters, a win/loss objective with very low signal per
game), the strongest choice is **SPSA on paired games** (Fishtest's method). Next is **CMA-ES with explicit
re-evaluation or adaptive sampling**. BO/TPE only pays off when each configuration gets enough games to have a usable
mean, roughly ≥ 50–100 games, which caps it at about 20–40 configurations per run. Racing (irace/successive halving)
is the right tool for a *discrete* choice among a handful of variants, not for continuous constants. No tuner fixes
the real problem: most of our constants have effects below the noise floor.

### Cited Findings
- **Fishtest SPSA mechanics** (fetched). Each parameter gets a per-axis `c_i`, chosen so that θ_i ± c_i·Δ_i gives a
  "small, measurable Elo gap" of a few Elo. In normalised space φ_i = θ_i/c_i, the gradient signal is (wins − losses)·Δ_i,
  and the update is Δθ_i = r_i·c_i·g_φi. With normalisation, one global learning rate works across parameters. Per-axis
  `c_i` acts like diagonal quasi-Newton scaling. Each worker task is tied to the snapshot it was dispatched from, so
  updates can arrive in any order, which makes it naturally parallel. The linear gradient approximation assumes small
  Elo gaps. — [Fishtest Mathematics](https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-Mathematics.html)
- Fishtest stops an SPSA run as useless when values "are barely changing" after a few thousand games. — [Fishtest:
  Creating my first test](https://official-stockfish.github.io/docs/fishtest-wiki/Creating-my-first-test.html) (cited in
  training-process.md)
- SPSA needs "only two objective function measurements per iteration regardless of the dimension". — [Spall, JHU APL
  SPSA page](https://www.jhuapl.edu/spsa/) (canonical)
- **BO in noisy game tuning.** chess-tuning-tools runs Bayesian optimisation over engine parameters and scores matches
  with a "Bayesian-pentanomial model for paired openings". — [Chess Tuning Tools docs](https://chess-tuning-tools.readthedocs.io/),
  [PyPI](https://pypi.org/project/chess-tuning-tools/0.9.1). Practitioner reports (forum anecdotes, not
  controlled studies) say skopt-based BO "will not work if the game samples are too noisy … if you play a few games
  per parameter configuration", and that raising the assumed noise level helped a lot. — [TalkChess: Tuning search
  parameters](https://talkchess.com/viewtopic.php?p=890249), [TalkChess: New Tool for Tuning with Skopt](https://talkchess.com/viewtopic.php?p=811337)
- Chess tuning "is computationally very demanding, and many tuning attempts are unsuccessful". Ivec & Vojnović (2022)
  propose a Bayesian method that compares two parameter sets, and benchmark it against SPSA. The abstract does not give
  the comparative numbers. — [arXiv:2205.15602](https://arxiv.org/abs/2205.15602)
- **BO vs CMA-ES by budget.** BO methods "often perform best for small function evaluation budgets (e.g., below 10
  times the number of hyperparameters)", while CMA-ES tends to win at larger budgets. — [Loshchilov & Hutter, CMA-ES for
  Hyperparameter Optimization of Deep Neural Networks, arXiv:1604.07269](https://www.arxiv-vanity.com/papers/1604.07269/)
- **Noisy CMA-ES.** Adaptive Sampling CMA-ES (AS-CMA, 2026) allocates evaluations per candidate according to how hard
  candidates are to rank. In noisy robot optimisation it converged 24–65% faster, at 29–76% lower total cost, than the
  best static sampling time per landscape. It beat BO on complex landscapes but was less efficient on simple ones. —
  [arXiv:2601.09594](https://arxiv.org/html/2601.09594). There is also a 2024 adaptive re-evaluation count for CMA-ES
  under additive Gaussian noise. — [arXiv:2409.16757](https://arxiv.org/abs/2409.16757v3)
- CMA-ES population size is 4 + ⌊3 ln n⌋ per generation. — [Hansen, CMA-ES tutorial, arXiv:1604.00772](https://arxiv.org/abs/1604.00772)
  (canonical; cited in training-process.md). UH-CMA-ES (Hansen et al. 2009, "A method for handling uncertainty in
  evolutionary optimization", IEEE TEC) measures rank changes under re-evaluation and responds by increasing
  evaluations or step size. (Canonical; not re-fetched, so there is no URL.)
- **Hyperband** treats tuning as a "pure-exploration non-stochastic infinite-armed bandit". It allocates a resource
  (here, games) adaptively to random configurations, stops bad ones early, and reports "over an order-of-magnitude
  speedup" over BO competitors on deep-learning and kernel problems. — [Li et al., arXiv:1603.06560](https://arxiv.org/abs/1603.06560) (fetched abstract)
- Sequential parameter optimisation (SPO, surrogate-model based) outperformed CMA-ES, Nelder–Mead and simulated
  annealing on five noisy test functions. — [Bartz-Beielstein et al.](https://www.gm.th-koeln.de/~bartz/Papers.d/Bart11b.pdf)
- **irace** does iterated racing: sample configurations, evaluate them on instances one at a time, eliminate candidates
  with Friedman or t-tests, and resample around the survivors, with elitism and support for conditional or categorical
  parameters. — López-Ibáñez et al. 2016, *Operations Research Perspectives* 3:43–58, [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2214716015300270)
  (canonical; the page returned 403 this session, so these details are from memory of the paper, not verified)
- **Optuna** provides define-by-run search spaces, TPE/CMA-ES samplers and pruners, including successive halving and
  Hyperband. — Akiba et al. 2019, [arXiv:1907.10902](https://arxiv.org/abs/1907.10902) (canonical, not re-fetched)

### Inferences
- **Signal per game is the binding constraint.** With N paired games, the SE of a win rate is ≈ 0.5/√N: 400 games gives
  ±2.5 points. A constant worth 1–2 points needs about 2,500+ games to show at all. SPSA is the only method listed that
  does not need each configuration's mean to be resolved, because it adds up tiny signed signals over all games. That
  is why Fishtest uses it at an Elo scale where everything is below the noise floor.
- **A concrete SPSA plan for `tune.py`.**
  - Choose `c_i` per constant so that ±c_i is a change you would expect to be worth about 2–3 points; the Fishtest rule
    is a "small measurable gap".
  - Each step plays θ+cΔ vs θ−cΔ on one random map + seed, both sides (one pair).
  - Use a fixed r. Run 2,000–4,000 pairs, which is ~15–30 min at 0.3 s/game on 8 cores.
  - Freeze the trajectory mean of the last third of the run, then confirm with the pair-SPRT non-regression gate.
  - Play against the opponent pool, not θ vs θ only: θ±cΔ each also plays a pool member, and you use the difference.
    Self-play SPSA optimises v10-vs-v10.
- **CMA-ES with 7 parameters** (λ = 9) at ~100 games per candidate costs ~900 games per generation, so a 3,000-game
  budget gives about 3 generations, which is too few. Only use it if SPSA stalls and you suspect interactions or
  multimodality.
- **BO/TPE (Optuna)** fits low-dimensional (≤ 5), expensive, possibly categorical choices: for example a threshold
  plus a 3-way mode switch, with ≥ 64 paired games per trial and ~30 trials, about 4k games. Model the per-trial mean
  as noisy (BoTorch `qNoisyExpectedImprovement`, or Optuna with enough games per trial).
- **Successive halving fits structural variants.** Given K candidate code variants (say 8 agent-written ideas), play
  all of them at 40 games, keep the top half, double the games, and repeat. This spends most of the games on the two or
  three that matter. irace does the same with statistical elimination, but adds R as a dependency. A ~40-line Python
  successive-halving loop over `arena.run_matches` is enough.
- The current `tune.py` (best of 3 candidates, accept at 56%) has a winner's-curse bias. It is closest to an
  unprincipled (1,3)-ES without re-evaluation, which explains "mostly measured noise".

### Gaps
- I found no head-to-head study of SPSA vs CMA-ES vs BO for *game-agent* win-rate tuning. Ivec & Vojnović compare
  against SPSA, but their numbers were not retrieved.
- UH-CMA-ES, irace and Optuna details come from canonical knowledge, not from pages fetched this session.
- Fishtest's default SPSA hyperparameters (A, α = 0.602, γ = 0.101 in the Spall convention) were not on the fetched
  page.

## 2. Quality-diversity (MAP-Elites) for diverse strategies and opponents

### Takeaway
MAP-Elites keeps the best solution per cell of a hand-chosen behaviour grid. In games, it has mainly been used to map
strategy spaces (Hearthstone decks) and to produce a *diverse opponent pool*. For us, its value is building a varied
pool of opponents and strategy archetypes from parameter variants of our own bot, not finding a single best bot. It is
evaluation-hungry, so keep behaviour dimensions to two and the grid small.

### Cited Findings
- MAP-Elites (Mouret & Clune 2015) "illuminates" a search space by storing the elite per behaviour-descriptor cell. —
  [arXiv:1504.04909](https://arxiv.org/abs/1504.04909) (canonical, not re-fetched)
- MAP-Elites with Sliding Boundaries (MESB) moves cell boundaries to where evolved individuals actually fall, and found
  "varied ways to play Hearthstone well", including aggro and control archetypes. The authors use the map to inform game
  rebalancing. — [Fontaine et al., GECCO 2019, arXiv:1904.10656](https://arxiv.org/pdf/1904.10656)
- CMA-ME (CMA-ES emitters inside MAP-Elites) found both higher quality and broader diversity than CMA-ES or plain
  MAP-Elites on Hearthstone. — [Fontaine et al. 2019, via author listing](https://astro.paperswithcode.com/author/amy-k-hoover)
  (secondary)
- Deep-surrogate-assisted MAP-Elites trains an online outcome predictor, because MAP-Elites "requires many costly
  evaluations". This improved sample efficiency over offline-trained and linear surrogates. — [Zhang et al., arXiv:2112.03534](https://arxiv.org/abs/2112.03534v1)

### Inferences
- **Behaviour descriptors we already log**, from the ranked/local summary `events` and `championTimelines` described in
  training-process.md:
  - aggression: champion kills per game
  - tempo: gems submitted by round 500
  - fight share: champion-vs-monster damage ratio
  - draft archetype
- A 2D grid of 4×4 = 16 cells over (aggression, tempo), filled by mutating v10's constants, with fitness = win rate vs
  v10 over ~40 games, costs a few thousand games. The result is a pool of 16 opponents that each play differently. That
  is the cheap stand-in for the ladder's diversity that pool weighting needs.
- Fitness could be "beats v10" (exploiter-flavoured QD), which yields diverse exploiters rather than diverse strong bots.
- Parameter-space QD only spans what the constants can express. Behaviours that need new code (Golem camp play, for
  example) need the LLM-mutation methods in §4.

### Gaps
- I found no MAP-Elites use in RTS/Battlecode-style programming competitions. StarCraft QD searches returned nothing.

## 3. Evolving or learning opponents to expose weaknesses

### Takeaway
Exploiter search works and has evidence behind it, from AlphaStar's league to 2026 LLM code co-evolution. The key
lesson from the latest LLM-code work is that a *static* evaluator stalls, so champions must be fed back into the pool
and the hardest opponents up-weighted.

### Cited Findings
- AlphaStar uses main agents plus exploiter agents "whose sole purpose is to expose weaknesses of the main agent". —
  [DeepMind, AlphaStar Grandmaster](https://deepmind.google/discover/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/)
  (cited in training-process.md; not repeated in depth here)
- **FAMOU** (Li et al., arXiv June 2026) evolves full strategy programs of 500–1,700 lines with LLM mutations in the
  AAMAS 2026 Multi-Agent Capture-the-Flag task. It argues that fixed evaluators "become unreliable as strategies improve,
  causing evolution to stall", and adds three mechanisms:
  1. **Evaluator co-evolution**: discovered champions join the opponent pool.
  2. **Hierarchical deep evaluation**: noisy few-game scores are replaced with statistically reliable ones.
  3. **Weakness pressure**: the hardest opponents are up-weighted dynamically.

  It beat OpenEvolve and ShinkaEvolve, with 61.7% against unseen opponents. Ablations show each mechanism helps. It
  placed 1st in the hardware round-robin and 3rd in simulation at the competition, and produced tactics absent from the
  seeds, such as lookahead and adaptive interception. — [arXiv:2606.10389](https://arxiv.org/abs/2606.10389)

### Inferences
- **Pool protocol** combining FAMOU's mechanisms with training-process.md's exploiters:
  1. After each promotion, run one exploiter SPSA/ES run against the frozen main bot.
  2. Freeze the exploiter if it beats main ≥ 60%.
  3. The gate then up-weights the pool members main does worst against. The weight could be ∝ (1 − win rate), with a
     floor.
- **Generalisation check.** Keep 1–2 opponents (for example, teammates' newest bots or ranked-profile bots) *out* of
  the optimisation pool and report main's win rate against them separately. FAMOU's "unseen opponents" metric is
  exactly this.

### Gaps
- I did not retrieve FAMOU's exact game counts per evaluation tier.

## 4. LLM-driven program search and agentic improvement loops

### Takeaway
LLM program search works when there is a cheap, automatic and reliable evaluator, and when the loop keeps a
*population* (not one incumbent) plus staged evaluation. The game-specific evidence is mixed. Code-evolution systems
with co-evolving opponents do well in narrow tasks. Unscaffolded coding agents iterating on competition bots lose to
expert humans every round, mainly because they don't ground edits in logs, rarely validate, hallucinate loss causes,
and recover badly after losses. Our loop should copy the scaffolding (populations, cascades, held-out opponents,
mandatory validation) rather than give the agent more autonomy.

### Cited Findings
- **FunSearch** (Romera-Paredes et al., *Nature*, 14 Dec 2023) pairs an LLM with an automated evaluator in an island
  evolutionary loop. Islands evolve separately, and the weakest are periodically reset from the best. An evolved online
  bin-packing heuristic beat first-fit and best-fit, for example 2.47% vs 4.94% wasted space on OR4 (best-fit). —
  [Wikipedia summary](https://en.wikipedia.org/wiki/FunSearch), [LLM4AD docs](https://llm4ad-doc.readthedocs.io/en/latest/method/funsearch.html),
  [google-deepmind/funsearch](https://github.com/google-deepmind/funsearch) (secondary, plus the official repo). FunSearch
  evolves a single small *priority function* inside a fixed skeleton, not whole programs.
- **AlphaEvolve** (Novikov et al., arXiv:2506.13131, 2025) is "an evolutionary coding agent" that improves code by
  direct edits, using "feedback from one or more evaluators". Results include data-centre scheduling, a circuit
  simplification, faster training of its own LLM, and 4×4 complex matrix multiplication with 48 multiplications. —
  [arXiv:2506.13131](https://arxiv.org/abs/2506.13131) (fetched abstract). Secondary write-ups describe a program
  database that selects "parent" and "inspiration" programs, plus an **evaluation cascade** in which programs face
  tests of increasing difficulty and are discarded early. — [composio summary](https://composio.dev/blog/alphaevolve-evolutionary-agent-from-deepmind),
  [gonzoml](https://gonzoml.substack.com/p/alphaevolve) (secondary; the cascade was not verified in the primary text)
- **Eureka** (Ma et al., ICLR 2024) has an LLM write reward code, samples 16 candidates per iteration over 5
  iterations, keeps the best executable one, and refines it with "reward reflection" (training statistics fed back as
  text). It beat human rewards on 83% of 29 tasks, with an average normalised improvement of 52%. Independent samples
  reduce the chance that all candidates are buggy. — [arXiv:2310.12931](https://arxiv.org/pdf/2310.12931)
- **Games, code-level.**
  - Bachrach et al. (IJCAI 2025) combine code-generating LLMs with self-play to refine bot *populations*, in Checkers
    among others. — [mlanthology](https://mlanthology.org/ijcai/2025/bachrach2025ijcai-combining)
  - Self-evolving Catan agents (Analyzer/Researcher/Coder/Player roles, Claude 3.7 and GPT-4o) rewrite their own logic
    and beat static baselines. — [arXiv:2506.04651](https://arxiv.org/abs/2506.04651v1)
  - In 2048, LLM refinement of an MCTS value function improved steadily, while a thinker/executor metaprompting variant
    showed no significant gains. — [arXiv:2510.20205](https://arxiv.org/pdf/2510.20205v1)
- **CodeClash** (Yang et al., arXiv:2511.00839, Nov 2025, rev. May 2026) is the most relevant: its arenas include **MIT
  Battlecode 2025**, Halite I, Battlesnake, RoboCode, RobotRumble, Core War and Poker. — [arXiv HTML](https://arxiv.org/html/2511.00839)
  - **Setup.** Agents (mini-SWE-agent, bash only, ≤ 30 turns per edit phase) edit a codebase, then compete, over 15
    rounds. Logs are copied into `logs/`, and the only memory is what agents write into the repository.
  - **Grounding.** Most models "do not extract worthwhile information" from logs, often reading only the first lines or
    the last win rate. Edits were ungrounded in > 65% of rounds for non-Claude models and ~80% for o3.
  - **Hallucinated loss causes.** Claude Sonnet 4.5 made uncorroborated claims about why it lost in > 17% of rounds
    (46% on BattleSnake).
  - **Validation.** Only Sonnet 4.5 validated changes in a majority of rounds (56%). GPT-5 did so in 50%, and Gemini 2.5
    Pro and o3 in about 20%.
  - **Recovery.** After one loss, Sonnet 4.5's chance of winning the next round fell below one third, against 71%
    overall. After five straight losses, comebacks were below 15%.
  - **Repository mess.** Sonnet 4.5 created > 30 files per tournament, 18 of them throwaway.
  - **Versus humans.** The top model won **zero** rounds against an expert human bot.
  - Codebases "become progressively messy and redundant". — [arXiv:2511.00839](https://arxiv.org/abs/2511.00839)

### Inferences (how this fits our Claude-driven loop)
- **We already avoid CodeClash's worst failures** through ranked-loss reports, the backlog with evidence, and arena
  gates. Keep them mandatory: every backlog item should name the *observed* evidence (a summary event, map, round) and
  the expected per-map effect *before* editing. That counters ungrounded edits and hallucinated causes.
- **Population over incumbent (FunSearch/AlphaEvolve/Eureka).** For each backlog hypothesis, have the agent write
  3–8 *independent* variants (different implementations, or different hypotheses), then race them with successive
  halving (§1). This replaces "one idea, one test" and uses the cheap 0.3 s/game evaluator, which is exactly what these
  systems rely on.
- **Evaluation cascade for us**, a direct analogue of AlphaEvolve's:
  1. Compile, plus 1 game on each of 5 maps with no `botFault`/`fuelExhausted` at 100k fuel and `--release`.
  2. Targeted pair-SPRT on the hypothesis maps.
  3. Non-regression SPRT on all maps against the pool.
  4. Held-out opponents.
  5. Submit. Ranked rating is the final judge.
- **FunSearch-style narrow search space.** Let the LLM evolve one *function* (for example the camp-target score, the
  shop priority or the retreat condition) inside the fixed bot, rather than whole-bot rewrites. This keeps diffs small,
  makes each candidate cheap to evaluate, and avoids CodeClash's repository rot.
- **Eureka-style reflection.** Feed the per-game feature row from training-process.md §7 (deaths by cause, gem curve,
  fuel events) back to the agent as text along with the win rate, not the win rate alone.
- **Risks.**
  1. *Overfitting to the pool or self-play.* Use FAMOU's unseen-opponent check and ranked rating as truth.
  2. *Multiple-comparison inflation* when racing many variants. Re-confirm the winner on fresh seeds; never accept on
     the race's own games.
  3. *Code rot.* Delete losing variants and keep one folder per promoted version, as CLAUDE.md already requires.
  4. *Recovery spiral after a regression.* Revert to the last promoted version rather than patching on top.

### Gaps
- No primary source documents an LLM loop climbing a human-competitive Battlecode ladder. CodeClash suggests that
  unscaffolded agents do not.
- AlphaEvolve's cascade and database details were not verified in the primary PDF.

## 5. Documented iteration methodology from Battlecode, Halite and Lux winners

### Takeaway
I found little *retrievable* text on how winners iterated. The consistent pattern is many local bot versions ranked
against each other (TrueSkill/Elo), heavy use of scrimmages against real teams, and rapid reaction to balance patches.

### Cited Findings
- Halite I's CLI let users build their own automation tools. One user ranked his local bot versions with TrueSkill. —
  [Halite Wikipedia](https://en.wikipedia.org/wiki/Halite_AI_Programming_Competition)
- A Battlecode 2026 postmortem (team Lorem Ipsum, updated 13 Feb 2026) has a "Testing & Tuning" §10.1, but the PDF
  text could not be extracted here (no PDF tools installed). — [postmortem-2026-lorem-ipsum.pdf](https://battlecode.org/assets/files/postmortem-2026-lorem-ipsum.pdf).
  Other postmortems exist: [2025 The Kragle](https://battlecode.org/assets/files/postmortem-2025-the-kragle.pdf),
  [2025 Just Woke Up](https://battlecode.org/assets/files/postmortem-2025-just-woke-up.pdf),
  [2022 5 Musketeers](https://battlecode.org:443/assets/files/postmortem-2022-5-musketeers.pdf). The 2022 one notes
  mid-competition balance changes. uvafan's bc20 was 1st in ranked scrimmages when they closed. — [github.com/uvafan/bc20](https://github.com/uvafan/bc20)

### Inferences
- These postmortems are worth reading with a PDF tool (`brew install poppler`, then `pdftotext`). They are the most
  direct evidence on what testing cadence works for this genre.

### Gaps
- No Halite III or Lux AI winner methodology was retrieved. The Lorem Ipsum testing section is unread.
