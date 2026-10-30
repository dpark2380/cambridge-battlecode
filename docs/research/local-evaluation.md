# Local evaluation that predicts ranked (2026-10-30)

Researched 2026-10-30 at commit `f40291c`. This note builds on [training-process.md](training-process.md)
(2026-10-25: pairs + SPRT, profile bots, exploiters, SPSA) and [postmortems.md](postmortems.md). Most of
training-process.md is now in place: `gate.py`, `race.py`, compile-time seeds, the scrim panel and features rows. This
note asks why that loop stopped predicting ranked results after v26, and what to change. The only games played for it
were 60 sequential local games (§3.3). No submits and no scrims.

## TL;DR

1. **Seeded local games use rosters that ranked never plays.** A seed gives *both* teams a uniformly random roster
   from all 12 champions (`bots/daniel/v34/src/draft.cpp:251-261`, `:284`). In v34's 450 ranked games we always
   draft the core, and both teams have it in 52-79% of games. In seeded games both teams have it in 0.4-6%, and
   Vesper is on our side in only 25-42% (§3.2). A Vesper fix like b99c is diluted, and its fights are against
   champions nobody drafts. **Fix: draw seeded rosters from the ranked roster distribution.** (~1-2 h)
2. **The gates throw away the signal that moved.** `arena.normalize` keeps only outcome, gems, picks and faults
   (`tools/arena.py:87-104`), and `gate.py` scores wins only (`tools/gate.py:77`, `:86`). On the scrim panel,
   b99c's win-loss change was +2 net flips, noise at 0.4 sd. Its paired death change was −3.5 ± 1.1 a game, 3.2 SE.
   In 1,175 ranked games since v25, gold difference (r = 0.58) and death difference (r = −0.54) track the result
   about as closely as anything we log. **Fix: log per-game features in every local game and report paired deaths,
   gold and gem margin beside the SPRT.** (~2 h)
3. **Calibrate the local setup against the panel data we already hold, not against ranked.** Ten versions have a
   90-game panel. It is deterministic: v33 and v34 play identically on the panel maps, with 0 of 90 games changed.
   The panel's paired metrics put the four newest candidates in the same order as their ranked windows did. Use those
   versions as labelled examples, and keep a local opponent or metric only if it reproduces their panel verdicts.
   This works offline and costs no quota or rating. (~1 h script plus ~20 min of games per opponent)

After these three: build opponents that differ from us and play near 50% against us (profile bots of the panel
teams, punisher variants, `tune.py` exploiters), retire the pushovers, and only then tune against the pool (§5).

## 1. The problem in numbers

The four candidates since the panel became stable, each against v34. Panel columns are paired by
(opponent, map, side) against v34's panel. Ranked is the record while that candidate was live.

| Candidate | Local vs v34 | Panel W | Panel net flips (sd) | Panel Δ deaths/game | Panel Δ gem margin | Ranked while live |
|---|---|---|---|---|---|---|
| b99c (→ v37) | gain FAIL 354/700 = 51% | 32 | +2 (4.5) | **−3.50 ± 1.08** | +99 ± 62 | 16-9 = 64% [45-80%]; v37 10-10 |
| b92 (→ v35) | gain PASS 234/420 = 56% | 28 | −2 (4.2) | −0.90 ± 1.06 | +33 ± 63 | 64-71 = 47% [39-56%] |
| v36 (fuel fix) | nonreg 50%; 7 fuel maps 59% | 26 | −4 (2.8) | +0.24 ± 0.25 | −17 ± 21 | 11-19 = 37% [22-54%] |
| b95v34 | gain FAIL 49% | 23 | −7 (3.6) | +0.97 ± 0.76 | −78 ± 36 | 7-18 = 28% [14-48%] |
| v34 (base) | — | 30 | — | — | — | 241-209 = 54% [49-58%] |

Sources: `data/b99c-gate.txt`, `data/b92-gate.txt`, `data/b100-gates.txt`, `data/b95v34-gain.txt`; panel rows in
`data/scrims/<version>/features.jsonl`; ranked rows in `replays/daniel-{b99c,v37,v35,v36,ab3,v34,v34b,v34c}/features.jsonl`
(`ab3` is b95v34's live window, 08:40-09:20Z). Intervals are Wilson 95% (`tools/arena.py` `wilson`). The backlog
gives the same panel flips (`bots/daniel/docs/backlog.md:100`, `:103`, `:107`).

Two readings follow:

- **Every ranked interval except v34's contains 50%,** and every one overlaps v34's. So the ranked "disagreements"
  are not evidence on their own. The panel and ranked do agree on order: by panel gem margin and by ranked record
  alike, b99c > b92 > v36 > b95v34. Local win rate got the order nearly right too (b92 56, b99c 51, v36 50,
  b95v34 49) but compressed it into 7 points. The b92/b99c swap is the real local failure.
- **The local gate is aimed at the wrong quantity.** b99c's effect shows in deaths, not wins, and the gate never sees
  deaths (§2).

## 2. What the tools actually do (verified)

| Tool | Sampling | Scoring | Source |
|---|---|---|---|
| `arena.run_matches` | every map × both sides; seed 0 is the real draft, seed *n* > 0 a compiled copy at 100k fuel | `normalize` keeps outcome, rounds, submitted gems, picks, faults; deaths, gold, timelines dropped | `tools/arena.py:115-133`, `:87-104` |
| seeded draft | `random_team`: uniform over all 12 champions, hashed with seed and spawn, for both teams | — | `bots/daniel/v34/src/draft.cpp:251-261`, `:284` |
| `gate.py` | batch 0 = real draft (70 pairs), then one fresh seed per batch | side-swapped pair score from **wins only**; normal-approximation LLR, ±2.94, ≥30 pairs | `tools/gate.py:32-47`, `:77`, `:86` |
| `race.py` | 2^k seeds per round from seed 1000, all maps | wins; keeps the better half; winner biased upwards (its own docstring) | `tools/race.py:8`, `:26`, `:47` |
| `tune.py` | 3 log-normal perturbations vs the **incumbent**, 2 random seeds | best of 3 at ≥ 56%, then a confirmation at ≥ 56% on fresh seeds | `tools/tune.py:82-94`, `:101`, `:127-135` |
| `gauntlet.py` | pool v7-v10, Jame v3, Simon v6, hunter-v0 (+ added bots), all pairs | batch Bradley-Terry, Elo scale, v8 = 0; straight-line map to ladder | `tools/gauntlet.py:28`, `:55`, `:134` |

The gate's statistics are sound: pairs remove the side term as Fishtest's pentanomial pairs do. The problems are what
it samples (rosters, opponent) and what it scores (wins only).

## 3. What our data says

### 3.1 Every instrument has a resolution floor

| Instrument | Noise, measured | Smallest effect it can see |
|---|---|---|
| Ranked window (30-130 games) | The same bot (v34) moved +23, −6, +5, **+59**, −17 rating over its five live windows; in one 7-hour window it ranged 1,670-1,729 (`docs/ladder_history.csv`, `docs/submissions.jsonl`). A 30-game record has a 95% interval of ±17 points. | ~10 points needs ~200 games per arm (training-process.md §5) |
| Scrim panel, W-L | Deterministic: v33 vs v34 0 of 90 games changed (v34 = v33 + a 01boss_battle fix, a map not on the panel); v36 changed 8. A behaviour change reshuffles 17-26 games, sd of net flips 4.1-5.0 | ≥ ±9 net flips (~10 points) |
| Scrim panel, paired continuous | deaths SE ≈ 1.1/game, gem margin SE ≈ 60 for behaviour changes (table in §1) | ~2-3 deaths/game, ~120 gems |
| Local gate (SPRT) | decides 50 vs 55% in 280-700 games | ~5 points **against our own bot** |

The panel is the only real-opponent instrument whose noise is purely the candidate's own butterfly effect. Opponent
bot updates did not move it between the v33, v34 and v36 panels.

### 3.2 Local ratings track the ladder over big steps, not small ones

I refit `gauntlet.fit` on all 190 cached pairs in `data/gauntlet/` and compared against `ladder_points()` (rating at
the end of each version's last window):

| Versions | Local BT range | Pearson r with ladder | Slope (ladder per local Elo) |
|---|---|---|---|
| v8-v34 (19 submitted) | 0 to +402 | **0.94** | 0.59 |
| v8-v18 | 0 to +289 | 0.87 | 0.63 |
| v25-v36 (8) | +360 to +402 | 0.15 | 0.15 |

From v25 on, the local spread is 42 Elo. At slope 0.59 that predicts 25 ladder points, which is less than the ±30
swing of a single unchanged version. **Local and ranked agree that nothing since v26 was a large step.** The
breakdown is about resolution, plus the blind spots below. Neither instrument has proved the other wrong.

### 3.3 The local pool cannot punish what ranked punishes

**Rosters.** v34's ranked games (`replays/daniel-v34{,b,c}/features.jsonl`, 450 games) compared with a uniform
random roster (the seeded games), counting "core" as Vesper, Marcella, Vendetta and Heart of Ruin:

| Team size | Ranked: us core | Ranked: opponent core | Ranked: both | Seeded: both |
|---|---|---|---|---|
| 3 (≥ 2 core) | 100% | 79% | 79% | 5.6% |
| 4 (≥ 3 core) | 100% | 52% | 52% | 0.4% |
| 5 (≥ 3 core) | 100% | 73% | 73% | 2.3% |

We draft Vesper in 100% of ranked games and opponents do in 77%. A seeded game gives us Vesper in 3/12 to 5/12 of
games. Top teams draft the same core (`docs/research/top-team-meta.md`, draft table). Only the real-draft batch (seed
0, 70 pairs) looks like ranked, and on it b99c scored 0.514 and b92 0.543 (`data/b99c-gate.txt`, `data/b92-gate.txt`
line "seed 0"). That is too few pairs to separate them, and the opponent there is v34 itself.

**Opponent strength.** I played 12 sequential real-draft games for each pairing below (00ribs, 01corridors,
00galaxy, 00eight, 02geodes, 00stampede, both sides):

| Pairing | Our wins | Our deaths/game | Their deaths/game |
|---|---|---|---|
| v34 vs Simon hunter-v0 | 12/12 | 6.3 | 43 |
| v37 vs Simon hunter-v0 | 11/12 | 5.8 | 41 |
| v34 vs Jame v3 | 11/12 | 2.9 | 42 |
| v37 vs Jame v3 | 11/12 | 1.6 | 46 |
| v37 vs v34 | 5/12 | 11.6 (v34 13.9) | — |
| ranked (v34, 450 games) | 54% | 12.6 | — |
| panel (v34, 90 games) | 33% | 17.7 | 9.7 |

Against the non-lineage pool opponents we barely die, so a death fix has nothing to show. OpenAI Five avoided
reference opponents beyond a 15-85% win rate because such games carry little information (Berner et al. 2019,
App. J, https://arxiv.org/abs/1912.06680). `bots/jame/v4` differs from Jame v3 only in its log prefix
(`diff -r bots/jame/v3/src bots/jame/v4/src`), so it adds nothing.

**Behaviour.** The backlog repeatedly parks a fix because "no local opponent punishes" the flaw:

- duo focus and split duos (B14, `bots/daniel/docs/backlog.md:128`);
- Ren retaliation by "big" teams (B28, `:39`);
- fight miscounts (B87, `:95`);
- camp damage without Jungle (B95, `:103`);
- Vesper fight entry (`docs/research/fight-benchmark-2026-10-28.md:28-35`);
- siege waits (B58, `:65`).

Our pool shares our fight model, so our flaws cancel out.

### 3.4 Which game-level signals go with ranked wins

Point-biserial correlation with the result, over 1,175 ranked games since v25 (`replays/daniel-{v25..v37,b99c}`):

| Signal (us − them) | r with win |
|---|---|
| earned gold | **+0.58** |
| deaths | **−0.54** |
| gems at r500 | +0.46 |
| camp clears | +0.43 |
| gems at r250 | +0.31 |
| our `fuelExhausted` events | −0.01 |

These are relative to the opponent. Locally, the paired equivalent is "same opponent, same map and side, candidate
minus base". `tools/winmodel.py` already prices a death at 6-9 submitted gems (`CLAUDE.md`, winmodel). The fuel line
fits v36's flat result (B100, `backlog.md:108`): fuel stalls are not what loses ranked games. At version level, no
metric (panel W, panel deaths, panel margin, local BT) correlates with the ranked record from v25 on (|r| ≤ 0.33 over
6-9 versions). That is expected, since the ranked records differ only by noise.

## 4. What established practice says

- **Fishtest / Stockfish.** Every patch gets an SPRT on colour-swapped game pairs (the pentanomial model), which
  "leads to a substantial saving of testing resources compared to the trinomial model"
  ([Fishtest Mathematics](https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-Mathematics.html)).
  Simplifications go through separate non-regression bounds
  ([Creating my first test](https://official-stockfish.github.io/docs/fishtest-wiki/Creating-my-first-test.html)).
  `gate.py` already does both. Fishtest can rely on self-play because chess has no roster choice and its opening
  books are chosen to be realistic. Our seeded rosters are the equivalent of a random-move opening book.
- **OpenAI Five** trained on "the latest policy against itself for 80% of games, and … older policies for 20%"
  (§3, training system). Agents were evaluated "to a pool of fixed reference agents with known skill using the TrueSkill rating
  system", playing only opponents within 10 TrueSkill (15-85% win rate). The paper still says "human evaluation is the
  ultimate goal" ([Berner et al. 2019](https://arxiv.org/abs/1912.06680), evaluation passage and App. J).
- **AlphaStar.** Self-play "may forget how to win against a previous version of itself" and end up "chasing its
  tail". The league adds "exploiter agents that focus on helping the main agent grow stronger by exposing its flaws".
  It also starts from supervised learning on human games, "ensuring that the agents keep exploring those strategies
  throughout self-play" ([DeepMind blog](https://deepmind.google/discover/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/);
  Vinyals et al., *Nature* 575, 2019, https://doi.org/10.1038/s41586-019-1724-z). Our analogues are exploiters
  (`tune.py` against a frozen v34) and scripted copies of the top teams' observed drafts and builds.
- **Evaluation depends on the population.** Balduzzi et al., "Re-evaluating Evaluation", show that Nash averaging
  "automatically adapts to redundancies in evaluation data, so that results are not biased by the incorporation of
  easy tasks or weak agents" ([arXiv:1806.02643](https://arxiv.org/abs/1806.02643)). Our gauntlet is mostly
  near-duplicates of one lineage plus three pushovers. Czarnecki et al. argue that real games have a large
  non-transitive part, which "clarifies why populations of strategies are necessary"
  ([arXiv:2004.09468](https://arxiv.org/abs/2004.09468)).
- **Population-based training** (Jaderberg et al., [arXiv:1711.09846](https://arxiv.org/abs/1711.09846)) tunes many
  copies against a shared population rather than one incumbent. The cheap form here is `tune.py` scored against
  the pool.
- **Battlecode.** Just Woke Up (2025) tested defence towers "against our past bots it usually went even in wins, or
  even slightly lost", sent them anyway because they should beat their worst matchups, "and the results were
  unbelievable" in the final tournament ([postmortem](https://battlecode.org/assets/files/postmortem-2025-just-woke-up.pdf),
  "Defense towers"). That is b99c's story. Lorem Ipsum (2026, §10.1) accepted "roughly slightly above 50%" against old
  bots and judged on scrims and on "macro and micro strategies rather than the overall score"
  ([postmortem](https://battlecode.org/assets/files/postmortem-2026-lorem-ipsum.pdf)). The Kragle: "the easiest way to
  improve is to copy what they do better" (`docs/research/postmortems.md`).

## 5. Recommended changes, ranked

| # | Change | Effort | Expected benefit | Cheap validation |
|---|---|---|---|---|
| 1 | **Ranked-like seeded rosters.** `random_team` draws each team from ranked opponents' rosters per team size (a table built from `their_picks` in `replays/daniel-v34*/features.jsonl`, or the meta pick rates) instead of uniform. Port it to v34, v35, v36, v37 and b95v34 copies under `bots/_var/` | 1-2 h | Every local game exercises the champions we change (Vesper 100% vs ≤ 42% today) in fights against the champions ranked plays | Rerun the b99c and b95v34 gates vs v34. Pass if b99c > b95v34 by more than today's 2 points, in the panel's direction |
| 2 | **Score the continuous signals.** `normalize` also keeps `features.row` for both sides. `gate.py` and `race.py` print paired Δ deaths, Δ earned gold, Δ gem margin and Δ r500 gems with SEs, and optionally a winmodel win probability per game as a lower-variance score. The W-L SPRT stays the decision rule for nonreg | ~2 h | 2-3× sensitivity on the panel (b99c: 3.2 SE on deaths vs 0.4 sd on W-L). Catches "fewer deaths, same wins" changes | The same gates as #1: b99c should show fewer deaths than v34 against a common opponent |
| 3 | **Calibration set from the panel.** A script plays each panelled version (v25, v26, v27, v28, v31, v35, v36, v37, b95v34; v33 as the zero) vs v34 against each local opponent, and scores each opponent/metric by sign and rank agreement with the panel's paired Δ (§1 table, extended). An opponent stays in the pool only if it agrees | 1 h script; ~20 min of games per opponent (8 jobs) | Replaces ranked A/B and scrim A/B as the check that local tests mean something, with no quota or rating spent | Its own output. Today's baseline: self-play W% ranks the four recent candidates with Spearman 0.8 against the panel. A better opponent should reach 1.0 and a wider spread |
| 4 | **Opponents that differ from us and play near 50%.** (a) Profile bots of the six panel teams: v34 with their per-size drafts (`their_picks`) and shard plan (`their_shards`; e.g. The Onkeys: Durability > Treasure > Jungle, `backlog.md:103`). (b) Punishers built from parked fixes: duo-focus (B14's `duo-hunter`), carrier chase (hunter-v0's rule on v34), gang the Vesper, join fights (B87b). (c) One `tune.py` exploiter: aggression, recall and fight constants maximising wins against a frozen v34 (training-process.md §3). Retire Jame v3/v4, hunter-v0, Simon v6 and v7-v10 from gating; they sit outside 15-85% | 0.5-1 day | Reproduces the ranked punishments behind B14, B28, B87, B95 and Vesper | #3 decides which survive |
| 5 | **Rate against the calibrated pool, not the lineage.** In `gauntlet.py`, report per-opponent paired results for the survivors of #3 (or Nash-average them); drop the lineage-dominated BT ranking from decisions | ~1 h | Ratings stop being inflated by near-duplicates and weak bots | Ratings of v26-v37 should spread more than today's 42 Elo |
| 6 | **Ranked as a monitor, not a test.** No accept/reject from ranked windows under ~200 games, and no scrim A/B rounds. Watch the rating trajectory of the live bot only | 0 | Saves the 30-55 rating each A/B round cost | — |
| 7 | **Tune only after 1-4,** against the pool (PBT/league style, with SPSA as in training-process.md §8), never against the incumbent alone | 2-3 h | Constants tuned against realistic opponents instead of v34's mirror | A tuned build must pass #3's agreement check and a gate on pool opponents |

**Not recommended:** behaviour cloning of top-team movement or RL. We have no inference path inside the 100k-fuel
wasm, and earlier work ruled it out (`bots/jame/docs/research/rl-feasibility.md`). Copy their measurable macro instead:
drafts, builds and opening clear order (`docs/research/top-team-play.md`). Also not recommended: faster or
truncated games (training-process.md §4), and more self-play volume. 700 games did not separate b99c because of the
rosters and opponent, not the sample size.

## 6. First step

Do #1 and #2 together on copies, then test them against the four labelled candidates.

1. In `bots/_var/{v34,b99c,b92,b95v34,v36}-meta`, replace `random_team`'s uniform pick with a draw from the ranked
   roster table, so both teams draft like ranked teams. Ranked play is unaffected, since seed 0 takes the real draft
   (`draft.cpp:284`).
2. Make `arena.play` return `features.row` for both sides next to `normalize`. Make `gate.py` print the paired Δ
   deaths, gold and gem margin with SEs at each batch.
3. Run `tools/gate.py bots/_var/<c>-meta bots/_var/v34-meta --mode gain` for the four candidates, one after another.
4. Success means the order b99c > b92 > v36 > b95v34 in Δ margin and Δ deaths, with b99c's deaths clearly below
   v34's. If self-play still cannot see it, the opponent is the binding constraint: go to #4 and use #3 to choose.
