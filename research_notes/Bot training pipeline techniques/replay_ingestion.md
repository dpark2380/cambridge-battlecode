# Replay ingestion and strategic-information extraction (for CAMBC 2026)

Scope: how competition teams and game-AI researchers turn replays and match logs into usable knowledge, and how that maps onto our pipeline. Researched 2026-10-25. Builds on `docs/research/training-process.md` and does not repeat it. That note already covers mining top teams via `cambc matches list/summary/download`, keeping `events` and `championTimelines`, a 30-number feature row, rule-based loss signatures, profile bots and AlphaStar-style exploiters.

Repo facts checked (read-only):
- `tools/scout.py` exists and decodes replays into `data/scout/replays/<id>.txt/.stats.json/.timeline.csv.gz`. 112 files are there now (3.8 MB total).
- `duckdb`, `pandas` and `sklearn` are **not** installed in the system `python3`. Anything below that uses them needs `pip install` or `uv` first. Stdlib-only versions are noted where they exist.

## 1. How top teams in AI competitions mined replays of opponents and of themselves

### Takeaway
The best-documented replay mining comes from StarCraft research, where thousands of human replays were parsed into event logs and feature vectors. Kaggle simulation competitors download top-ranked agents' episodes in bulk, filter them by agent score, and use them as training or analysis data. Battlecode and Halite teams mostly watch replays by hand and build small, task-specific "linters". I found no published source describing a systematic replay-mining pipeline from a Battlecode team.

### Cited Findings
- **Kaggle Lux AI 2021 (ironbar, imitation learning)**
  - Pipeline: a Kaggle notebook "ranks the submitted agents by score and saves a csv file with the agents exceeding a threshold score". A Colab notebook then downloads those agents' matches as one zip. — [ironbar/luxai](https://github.com/ironbar/luxai)
  - Validation used "10% of the matches from the best leaderboard agent". A U-Net trained on the matches for about a day on two RTX 3090s became the agent. — [ironbar/luxai](https://github.com/ironbar/luxai)
  - The pattern to copy: **select by opponent rating → bulk download → hold out the best agent's games for validation**.
- **Lux AI Season 1**: local matches produce a `replay.json` "which can be analysed or used as training data" (translated from Japanese). The 1st-place Season 1 solution (Toad Brigade) was deep RL, not replay mining. — [kenmatsu4 slides](https://speakerdeck.com/kenmatsu4/lux-ai-season-2gashi-matutanode-season-1wozhen-rifan-ru)
- **Lux AI Season 2 (NeurIPS 2023)**: competitors received "over a billion frames" of play data from the previous season, plus rule-based, RL and imitation-learning baselines. — [NeurIPS 2023 competition page](https://nips.cc/virtual/2023/competition/66593)
- **Kaggle community episode datasets**: a 2026-era Hugging Face dataset for the Kaggle Orbit Wars simulation scrapes the episode API. It keeps only games where both agents had a ladder rating ≥ 1500 and stores raw episode JSONs per date as tarballs. — [velocycle/orbit-wars-episodes](https://huggingface.co/datasets/velocycle/orbit-wars-episodes)
  - The rating filter is the same idea as `scout.py --top 20`.
- **Halite: replay "linter" (halint)**
  - Written by erdman "to speed and enhance analysis of Halite game replays", to support "post-mortems of results during the finals". — [erdman/halint](https://github.com/erdman/halint)
  - Per-frame lints: "cap loss" events with position and amount, and failed mining attempts.
  - Optional lints: overkill and pieces that "flip-flop" between adjacent squares.
  - Summary tables: production cost per move and a cumulative overkill matrix between bots.
  - A `halint-get` script downloads a replay and lints it. The season number is not stated on the page.
- **Battlecode**
  - The postmortems on battlecode.org are narrative strategy write-ups, e.g. the 2025 postmortems on scrimmaging against top teams and using map symmetry. — [postmortem-2025-just-woke-up](https://battlecode.org/assets/files/postmortem-2025-just-woke-up.pdf), [postmortem-2025-the-kragle](https://battlecode.org/assets/files/postmortem-2025-the-kragle.pdf), [postmortem-2019-oak](https://battlecode.org:443/assets/files/postmortem-2019-oak.pdf)
  - The 2019 postmortem describes the post-seeding meta as a rush / greedy / eco cycle, which is meta analysis done by watching games. — [postmortem-2019-oak](https://battlecode.org:443/assets/files/postmortem-2019-oak.pdf)
  - A 2015 team wrote `MapAnalysis.java` for a map feature that never appeared in the tournament maps, a warning against analysing hypothetical maps. — [TheDuck314/battlecode2015](https://github.com/TheDuck314/battlecode2015)
- **StarCraft research corpora**
  - Synnaeve and Bessière used 8,806 Brood War 1v1 replays from skilled human players (about 1,000 per matchup) to learn build-tree timing. Learning takes about 0.1 s per 1,000 replays and inference about 0.01 s per query. — [Synnaeve & Bessière, AIIDE 2011 (ar5iv)](https://ar5iv.labs.arxiv.org/html/1111.3735)
  - Erickson and Buro wrote their own parser (`github.com/gkericks/SCFeatureExtractor`) rather than reuse Synnaeve's parsed text files, "because of the specific nature of our task and to reduce the possible sources of error". They kept the ~400 PvP games out of ~8,000. Games whose recorded winner conflicted with the game score were discarded, and so were corrupted replays. — [Erickson & Buro, AIIDE 2014](https://ojs.aaai.org/index.php/AIIDE/article/view/12725)
  - The MSC dataset (SC2LE) ships "well-designed feature vectors, pre-defined high-level actions and final result of each match". Its baseline tasks are global state evaluation and build-order prediction. — [MSC, arXiv:1710.03131](https://arxiv.org/abs/1710.03131)

### Inferences
- Our setup is unusually good. Most of the work these teams did (scraping, parsing, filtering) is already done by `cambc matches summary --json` (structured events) and `scout.py`.
- The highest-value piece missing here is the halint idea: per-game lints for specific inefficiencies, printed as tables. Examples:
  - deaths with gems carried;
  - idle rounds on an occupied spawn tile;
  - flip-flop movement in `timeline.csv` (position A→B→A within 3 rounds);
  - rounds carrying ≥ N gems without moving toward an altar.
  - Cost: ~2–4 h in stdlib Python over the existing `timeline.csv.gz`.
- The Erickson and Buro lesson applies: write our own small extractor for the exact features we need, and drop games with inconsistent data instead of trusting a generic parser. Here that means `analyze.mjs` failing on engine-1.0.0 replays and stats that disagree with the summary.
- Copy the ironbar validation split as well: when learning anything (draft tables, win model) from top teams' games, hold out the #1 team's games and check that the learned rule still predicts them.

### Gaps
- No primary source found for a systematic replay-mining pipeline by an MIT Battlecode, Screeps, Hungry Geese or Kore team. The Hungry Geese winner (HandyRL team) is reported only in a news article with no technical detail ([AIsmiley](https://aismiley.co.jp/ai_news/kaggle-hungry-geese-dena-quantum/)).
- The Battlecode 2025 "confused" postmortem PDF could not be text-extracted here (no PDF tooling on this machine), so its contents are unverified.
- No Halite II/III winner writeup describing opponent-replay analysis was found. The Halite II winner was reCurs3 ([Two Sigma](https://www.twosigma.com/articles/halite-ii-concludes-winners-announced/)), but the announcement has no method.
- SSCAIT/AIIDE bot postmortems on opponent modelling from replays were not retrieved.

## 2. Which replay features predict winning, and how they were identified

### Takeaway
Win-probability models fit on time-sliced replay snapshots are the standard tool:
- logistic regression on per-player feature *differences*, evaluated separately by game phase;
- accuracy reported per time window, with feature groups compared by ablation.

Economic features (income, unspent resources) and army/unit counts predict best in the mid-game. Map coverage becomes the best single group late in the game. Accuracy is close to chance in the opening, so early-game features need a different evaluation.

### Cited Findings
- **Erickson and Buro (AIIDE 2014) setup.** Logistic regression on Protoss-v-Protoss states. — [Erickson & Buro](https://ojs.aaai.org/index.php/AIIDE/article/view/12725)
  - States were sampled **every 10 seconds** of each replay.
  - Features were **differences** between players. Each state was added twice (A−B with label 1, B−A with label 0), so the model has no side bias.
  - Feature groups:
    - economic: current resources, income `I = R_tot/T`, average unspent `U`;
    - per-unit-type count differences;
    - map coverage;
    - skill features: a combat-simulator control variate, and others.
  - The authors stress that income and unspent resources must be included together. A good player keeps unspent low and income high.
  - Evaluation: 10-fold cross-validation by game (all states of a game stay in one fold). Metrics are accuracy and average log-likelihood, reported per 5-minute window (0–5, 5–10, 10–15, 15+).
- **Erickson and Buro, results by game window (Table 2):**

  | Feature group | 0–5 min | 10–15 min | 15+ min |
  |---|---|---|---|
  | Economic | 54.4% | 63.0% | 64.2% |
  | Unit counts | 52.0% | 66.7% | 66.5% |
  | Map coverage | 51.3% | 61.5% | 71.4% |
  | Skill-variance feature alone | ~50–55% | | |
  | All features | 53.8% | | 72.6% |

  — [Erickson & Buro](https://ojs.aaai.org/index.php/AIIDE/article/view/12725)
- **Ravari, Bakkes and Spronck (AIIDE 2016).** They predict the StarCraft winner with >63% average accuracy over all time slices, with models per matchup plus general models. "Economic aspects were the strongest predictors for winning, followed by the use of micro commands." — [StarCraft Winner Prediction](https://ojs.aaai.org/index.php/AIIDE/article/view/12887)
- **Weber and Mateas (IEEE CIG 2009).** 5,393 replays, encoded as feature vectors of *when* each unit or building type was first produced. Several classifiers were compared for strategy and timing prediction, and the winner could be predicted "to a certain degree". — secondary summaries via [RedDwarfData, arXiv:1712.10179](https://arxiv.org/pdf/1712.10179) and [Robertson & Watson FLAIRS14](https://www.cs.auckland.ac.nz/research/gameai/publications/Robertson_Watson_FLAIRS14.pdf); full text not retrieved.
- **Sample size.** "the limit of the number of samples restricts the application and performance of the prediction models" (StarCraft II winner prediction). — [Lin et al., IEEE Access 2019](https://doaj.org/article/71bd30abb4bb458a98843ec3027d482e)

### Inferences
**A CAMBC version of Erickson and Buro.** Cost ~3–5 h. Most of the effort is the extractor. With `sklearn` it is ~20 lines; stdlib gradient descent also works for <30 features.
- **Rows:** one per (game, round ∈ {100, 200, …, 1000}). Source: the run-length `championTimelines` in each summary, which hold every metric needed.
- **Features**, each as team-A minus team-B difference:
  - gems submitted;
  - gems carried;
  - gold earned and gold unspent;
  - kills and deaths;
  - camp clears so far;
  - first-capture round;
  - deaths to camps vs to champions;
  - `fuelExhausted` count.
- **Labels:** the result. Add each row twice with the sign flipped to remove the side term; also add a `side` indicator, since side B wins 60–77% of mirror games (`bots/jame/docs/research/drafting.md`).
- **Evaluation:** game-grouped cross-validation, per round window.
- **Uses:**
  1. Find which early quantity (e.g. "camp clears by round 200" vs "gold by 200") separates top-team wins. That gives each version a measurable target.
  2. Apply the fitted model to our own losses to find the round where win probability collapsed. That round is where to look in the replay, which is an automatic triage pointer.
- **Data volume:** Erickson and Buro had ~400 games. One `scout.py --top 20 --matches 100` pull gives ~2,000 games' drafts, and summaries cost ~0.6 MB each. A few hundred summaries suffice for a logistic model with <30 features.
- **Ablation by feature group per window** answers "does map control (camp clears) or economy (gold) matter more on map X". Our analogue of map coverage is the number of camp groups captured, or the tiles visited from `timeline.csv`.
- **Expect low early accuracy.** For opening decisions (draft, first target), compare win rates conditioned on the choice, as in `draft_lab.py`'s Bradley–Terry approach, instead of a state-value model.

### Gaps
- No source found applying win-probability models to Battlecode, Halite or Lux replays specifically.
- The exact Weber and Mateas classifier accuracies were not retrieved; the full text is not available here.

## 3. Opponent modelling and strategy classification from replays

### Takeaway
Two families exist:
1. **Supervised:** label replays with strategies, then classify. Weber and Mateas did this, which assumes the strategy set is known in advance.
2. **Semi- or unsupervised:** EM or clustering discovers the labels, and a Bayesian or HMM model predicts the opponent's plan from partial observations.

At our scale, the cheap version is to cluster opponents' draft-plus-build vectors and per-round route features, then pick a counter per cluster.

### Cited Findings
- Weber and Mateas encode each game log as a vector of production timings and apply supervised classifiers. A later critique notes this "uses supervised labelling of replays, thus assuming that the number of possible strategies is known beforehand". — via [Robertson & Watson FLAIRS14](https://www.cs.auckland.ac.nz/research/gameai/publications/Robertson_Watson_FLAIRS14.pdf) and the search summary; full text not retrieved.
- Weber's later summary: from thousands of professional replays, the model can "identify opponent build order minutes before it is executed". — [Weber slides](https://www.slideshare.net/slideshow/game-analytics-machine-learning/59126255)
- **Synnaeve and Bessière, opening prediction (CIG 2011).** Bayesian opening model whose parameters are learned from replays, with opening labels produced semi-supervised by **expectation-maximization**. Suggested uses are a commentary assistant or a component of a dynamic bot. — [HAL hal-00607277](https://hal.archives-ouvertes.fr/hal-00607277)
- **Synnaeve and Bessière, plan recognition (AIIDE 2011).** — [ar5iv 1111.3735](https://ar5iv.labs.arxiv.org/html/1111.3735)
  - Only buildings were modelled, "because buildings are more visible under fog of war". The set of build trees was restricted to those seen in replays: 810 Terran, 346 Protoss, 261 Zerg.
  - Timing was a discretized normal per build tree. The query is `P(BuildTree | time, observations)`.
  - Reconstruction distance rose only from 0.87 to 1.37 (mean) as observation noise went from 0% to 80%.
  - The conclusion's "44 buildings ahead" claim does not match Table 1's max of about 6.1, an internal inconsistency in the paper.
- Synnaeve and Bessière also released "A Dataset for StarCraft AI & an Example of Armies Clustering". — [arXiv:1211.4552](https://arxiv.org/pdf/1211.4552)
- Erickson and Buro argue the payoff: "if you have determined that the opponent is implementing strategy A, and you have previously determined that strategy B is a good counter to A, then you can start running strategy B" (citing Dereszynski et al. 2011). UAlbertaBot, the AIIDE winner the year before, decided combat engagements from simulation results. — [Erickson & Buro](https://ojs.aaai.org/index.php/AIIDE/article/view/12725)
- Player identification from replay action features is also feasible: Siming Liu et al. identify SC2 players and predict actions from replays. — [UNR paper](https://www.cse.unr.edu/~simingl/papers/publish/Identifying_Players_and_Predicting_Actions_from_RTS_Game_Replays.pdf)

### Inferences
- **What an opponent model is here.** In CAMBC the opponent's draft is revealed (`draftPicks` in `matches list`). Build orders are in the summaries (`itemsBought`). Most of the remaining "strategy" is movement.
- **Strategy vector per (team, game), ~1–2 h:**
  - draft one-hot (12 champions);
  - shard counts by stat;
  - first camp group cleared and its round;
  - fraction of time in our half vs theirs, from `timeline.csv` positions mirrored by map symmetry;
  - kills before round 300 (rush indicator);
  - mean gems carried at death (greed indicator).
- **Clustering:** k-means with k = 3–6 on standardized vectors; stdlib is fine for a few thousand rows. Name the clusters by hand, e.g. "rush/hunter", "farm and race", "monolith siege". Then tabulate our results per cluster from our own ranked games. That shows which play style we lose to, which `training-process.md`'s profile bots can then imitate.
- **Online use is limited.** Bots can't see the opponent's identity, only the draft. A Synnaeve-style `P(style | draft picks, early observations)` table could be computed offline and written into `draft.cpp` constants, e.g. "opponent drafted Vendetta + Heart of Ruin → expect early aggression". Cost ~0.5 day, and only worth it if clusters actually map to different counters.
- **Data budget:** Synnaeve's model learned from ~1,000 replays per matchup. We can pull ~100 games each for the top 20 teams, which is enough for frequency tables, not deep models.

### Gaps
- No source found on opponent clustering in Battlecode or Kaggle simulation competitions.
- The Dereszynski et al. 2011 HMM paper was cited but not retrieved.

## 4. Automated loss triage and anomaly detection on match logs

### Takeaway
I found no published system for automatic loss triage in AI programming competitions. The closest primary examples are:
- halint, rule-based lints over replays printed as tables;
- the evaluation-by-time-window idea from win-prediction papers, which can localize *when* a game was lost.

Combining both is cheap: rule lints, a win-probability "collapse round", and our rule-signature table from `training-process.md` §7.

### Cited Findings
- halint's design: specific inefficiency events (cap loss, failed mining, overkill, flip-flopping), each with position and frame, aggregated into summary tables and a bot-vs-bot overkill matrix. The tool accepts any number of replay files. — [erdman/halint](https://github.com/erdman/halint)
- Erickson and Buro's model outputs a per-state probability "which can be looked at as a value of the state for the player". A state-value curve per game is therefore available once the model exists. — [Erickson & Buro](https://ojs.aaai.org/index.php/AIIDE/article/view/12725)
- Win-rate reporting hygiene from a SC data-analysis guide: don't report win rates on fewer than ~30 games, and use Wilson intervals. — [starcraft-data-analysis skill](https://openskillindex.com/skills/merceralex397-collab-skilllibrary-starcraft-data-analysis). Low-authority source; the Wilson recommendation is standard and `arena.py` already uses it.

### Inferences
**Triage stack** (each layer stdlib, ~1–3 h):
1. **Lints** per game from `timeline.csv.gz` and `events`. Each prints round and (x, y):
   - gems lost at death, with killer;
   - flip-flop movement;
   - rounds on a camp spawn tile (CLAUDE.md: this delays respawn);
   - `fuelExhausted`;
   - long idle while alive;
   - tribute channels interrupted.
2. **Win-probability curve** from §2. The "collapse round" is the first round where P(win) falls below 0.3 and stays there. Report the 3 events nearest to that round. This tells you which 50 rounds of a replay to watch.
3. **Signature table** (already proposed in `training-process.md` §7). Group by map × signature, ranked by count.
4. **Anomaly score** per game vs top teams on the same map. For each feature at round 500, compute a z-score against the top-20 distribution and list the biggest negative z-scores. Example: "camp clears by r500: z = −2.4 vs top teams on 00stampede". This turns "we lost" into "we're behind on X on map Y" without needing a learned model.
5. **Lints also run on the top teams' replays.** Their lint rates are the reference, so a high lint count only matters if top teams' is low.

### Gaps
- No published loss-triage or anomaly-detection system from Battlecode, Halite or Kaggle competitors was found. The above is synthesis, not sourced practice.

## 5. Practical data formats and tools for thousands of games

### Takeaway
Keep the raw data in its native formats: summary JSON as compact JSON per game, timelines as gzipped CSV. Query them with DuckDB, which reads JSON with globs and adds a `filename` column. Write a derived `features` table as one row per game, either newline-delimited JSON (stdlib-friendly) or Parquet once DuckDB is installed. pandas and sklearn are optional extras that are not installed today.

### Cited Findings
- DuckDB reads JSON files by glob (`SELECT filename, * FROM 'todos-*.json';`). "Since DuckDB 1.3.0, the JSON reader returns the `filename` virtual column." It also offers `read_json(...)` with an explicit `format` and `columns` schema. — [DuckDB JSON overview](https://duckdb.org/docs/2.0/data/json/overview.html)
- Community Kaggle episode datasets store raw episode JSONs per date as tarballs, filtered by rating. That keeps raw data replayable and derived tables re-buildable. — [velocycle/orbit-wars-episodes](https://huggingface.co/datasets/velocycle/orbit-wars-episodes)
- Data size reference: one ranked CAMBC summary is 0.6–0.7 MB (`docs/research/training-process.md` §7). `data/scout` holds 112 decoded-replay files in 3.8 MB, because the timelines are gzipped (measured in the repo).

### Inferences
**Recommended layout** (no new dependencies required):
```
data/games/raw/<match_id>.summary.json.gz           # keep raw; 1,000 games ≈ 100–200 MB gz (est.)
data/games/timeline/<match_id>.csv.gz                # from analyze.mjs / scout.py
data/games/features.jsonl                            # 1 row/game/team: ids, map, side, teams, ratings, result, ~30 features, signature
data/games/snapshots.jsonl                           # 1 row/game/team/round-bucket: for the win-probability model
```
- Primary key is `match_id` plus team. Make every extractor idempotent: skip ids already present, as `scout.py` already does.
- **Query layer:**
  - with `pip install duckdb`: `SELECT map, signature, count(*) FROM 'data/games/features.jsonl' WHERE result='loss' GROUP BY ALL ORDER BY 3 DESC;`. DuckDB also reads `.csv.gz` timelines directly, so per-round joins across thousands of games run in seconds;
  - without it: stdlib `json` plus `collections.Counter` is fine up to ~10k rows.
- Convert to Parquet only if queries over timelines get slow (`COPY ... TO 'x.parquet' (FORMAT parquet)`; the syntax is from general DuckDB usage, not verified on the fetched page). Not needed at the current ~10³ games.
- Version the extractor (a `features_version` field), so a new feature means one re-run over raw data rather than a re-download.

### Gaps
- DuckDB's Parquet export syntax and NDJSON-specific options were not confirmed on the fetched page.
- No measured query timings on our data (DuckDB is not installed).

## Cost summary for a 3-person team (synthesis)

| Technique | Source precedent | Input we have | Build cost | Expected use |
|---|---|---|---|---|
| Rating-filtered bulk pull | ironbar Lux; Orbit Wars dataset | `matches list/summary --team` | done (`scout.py`) | Corpus |
| Raw-store + `features.jsonl` | Kaggle datasets; Erickson & Buro own extractor | summaries, timelines | 2–3 h | Everything below |
| Replay linter (halint-style) | erdman/halint | `timeline.csv.gz`, `events` | 2–4 h | Find specific inefficiencies, compare vs top teams |
| Win-probability logistic model per round window | Erickson & Buro 2014; Ravari 2016 | `championTimelines` | 3–5 h | Feature importance per map; collapse round for triage |
| Style clustering of opponents | Synnaeve EM labelling; Weber & Mateas | draft, `itemsBought`, positions | 1–2 h (+0.5 day for a draft-time table) | Which styles we lose to; feeds profile bots |
| z-score gap vs top teams per map | (synthesis) | features table | 1 h | Per-map targets for the next version |
