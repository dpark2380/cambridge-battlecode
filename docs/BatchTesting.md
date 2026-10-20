# Batch testing

Run from the repository root with Python 3.10 or newer. No Python packages are required; the tester finds the project's `.venv` CAMBC executable first, then checks `PATH`. Override it with `--cambc /path/to/cambc`.

## Common commands

```sh
# Discover the newest version for each member without running games.
python3 tools/batch.py --list

# Head-to-head: exactly 20 games, using the newest bot from each member.
python3 tools/batch.py jame simon --games 20

# Every member's newest bot, excluding starters: 20 games PER PAIR.
python3 tools/batch.py --round-robin --games 20

# Full round robin: every local map, both sides, ranked standings.
python3 tools/batch.py --round-robin

# No arguments: every pair, every local map, both sides once.
python3 tools/batch.py

# Restrict maps, set parallelism, and keep a named output directory.
python3 tools/batch.py jame daniel -n 10 --maps swirl packs -j 4 -o matches/jame-daniel-check

# Pin historical versions explicitly instead of selecting the latest.
python3 tools/batch.py bots/jame/v1 bots/simon/v4 --games 20

# Keep older replay bundles when starting a new batch.
python3 tools/batch.py --round-robin --keep-old-replays
```

The existing `tools/arena.py` remains unchanged for regression gates and tuning scripts. The new tester is for exact-size sets, member-labelled results, saved replay artifacts, and explicit probability estimates. It follows the familiar local build → play → inspect workflow of [UNSW Battlecode](https://github.com/unswcpmsoc/unswbc), using CAMBC's own runner and replay format.

## Newest-version resolution

Default participants are directories under `bots/<member>/` that contain bot version folders. Starter bots and scratch directories beginning with `_` or `.` are excluded from automatic discovery.

`--round-robin` explicitly selects all members and takes no bot names. Omitting names still does the same thing for compatibility. It compares the newest version per member, rather than every historical version. Folders beginning with `starter` are excluded even if they contain numbered versions; head-to-head mode can still select a starter explicitly.

- `jame` currently resolves to `bots/jame/v3` and is labelled **jame**. Pin `bots/jame/v1` or `bots/jame/v2` to use an older baseline.
- `daniel` currently resolves to `bots/daniel/v7` and is labelled **daniel**.
- `simon` currently resolves to `bots/simon/v5` and is labelled **simon**.
- Highest numbered version wins: `v10` is newer than `v9`, irrespective of modification time or build-cache timestamps.
- At the same number, a plain `v5` is preferred over a branch such as `v5-dp`. If only suffixed versions exist at that number, their names break the tie lexicographically.
- Historical `main-vN` names are also recognized. Unnumbered working copies such as `main-cpp` do not override a numbered release; select their paths explicitly.
- Explicit paths always pin the requested bot. Two versions from one member are labelled `member/version` to distinguish them. Ambiguous bare names such as `v5` are rejected instead of silently choosing someone else's bot.

The selected source paths and versions are printed before building and preserved in the results. No bot implementation is modified.

## Scheduling and results

`--games N` means **N scheduled games per pairing**, not N for the whole round robin. With three members there are three pairs, so `--games 20` schedules 60 games. Without `--games`, each pair plays every selected map from both sides once. With the current 17 maps and three members, that is 34 games per pair / 102 total.

Maps are shuffled, and side-swapped games stay adjacent. Every map/side setup is covered before repeating one. Even game counts are balanced between sides; odd counts have one extra game on one side, which is explicitly reported.

`--seed` controls the scheduling shuffle only. It does **not** randomize the engine, change drafts, or alter fuel limits. The tester does not use the older arena's high-fuel draft experiment hook. All games use the runner's normal default fuel.

Each set reports:

- Wins and losses, observed win rate, and mean gem margin.
- Per-map and per-side outcomes.
- Bot faults and failed/timed-out runner jobs.
- Bayesian probability that the first named bot's win rate exceeds 50%.
- A Wilson 95% win-rate interval over distinct completed scenarios in the saved report.

Round-robin standings rank observed game win rate; equal rates share a rank in the terminal. These standings are descriptive. The probability estimates are pairwise, not a probability that a member is globally strongest.

Engine tiebreak outcomes count as wins even when gem scores are equal. An uncompleted game, invalid statistics, runner error, or timeout is not silently counted as a loss: it is recorded as failed and excluded from win-rate/probability calculations. Completed games containing bot faults still count as performance outcomes. Any failed game makes the command exit with status 1; configuration/build errors exit with status 2.

## What the probability means

For a particular pair, let `p` be the first named bot's win probability under the tested setup. Start with a uniform prior:

```text
p ~ Beta(1, 1)
after W distinct wins and L distinct losses:
p | results ~ Beta(W + 1, L + 1)

reported probability = P(p > 0.5 | results)
```

For example, four distinct wins and no losses give `Beta(5,1)`, so the probability that `p > 0.5` is **96.875%**. This is **not** a 96.875% chance of winning the next game: the posterior predictive next-game win probability under that model would be `5/6`, about 83.3%. A 2–2 result gives 50% probability of superiority under the symmetric prior.

The update is standard [Beta–Binomial conjugacy](https://web.stanford.edu/class/archive/cs/cs109/cs109.1246/lectures/21_beta.pdf). The implementation computes the probability through an equivalent binomial tail, in log space, using only the standard library.

### Repeats and limitations

CAMBC's local engine is deterministic for a fixed setup. Repeating the same map and side must not manufacture statistical certainty. Therefore:

- All completed games count toward the set's observed wins/losses.
- Only the first successfully completed game by **scheduled index** for a given `(map path, participant side)` contributes to inference. Completion timing does not change which repeat counts.
- Identical repeats are reported as excluded evidence. With 17 maps and no engine-seed variation, a pair has at most 34 distinct scenarios, even if you request 1,000 games.
- If a bot introduces its own randomness, this policy remains conservative; independent-repeat inference is not assumed automatically.
- Different sides on the same map can still be correlated. The Beta model and Wilson interval are conditional approximations, not guarantees for unseen maps, opponents, engine versions, or fuel settings. The tool neither fits an Elo rating nor claims an exact game-theoretic ranking.

For stronger evidence, use additional representative maps, hold out evaluation maps, and compare varied opponents. Changing the schedule shuffle seed alone does not add new scenarios.

## Saved artifacts and replay viewing

Starting a batch **clears `.repl26a` replay bundles from finished older batches under the same output parent**, normally `matches/`. Cleanup happens only after configuration validation and all builds succeed. Results, standings, probabilities, CSVs, statistics, and logs remain available. Old JSON/CSV replay lists are cleared, and old reports mark their replays as cleared instead of keeping broken links. The new run's replays are retained.

Use `--keep-old-replays` to preserve older bundles. With `--out /path/to/sets/new-run`, cleanup applies to finished sibling batches inside `/path/to/sets/`. Running/interrupted batches, unrelated directories, symlinks, and downloaded replays outside managed batch directories are left alone. Listing bots or renaming an existing batch does not trigger cleanup.

Each run's saved folder identifies the matchup **and versions**, number of games, maps, and UTC start time. For example:

```text
matches/jame-v1-vs-simon-v5__20-games__17-maps__2026-10-17_130439-UTC/
matches/round-robin__daniel-v5_jame-v1_simon-v5__34-games-per-pair__17-maps__2026-10-17_124217-UTC/
```

One or two selected maps are named directly, such as `__swirl__` or `__swirl_packs__`; larger selections show their count (the full map list remains in `results.json`). Round-robin counts explicitly say `games-per-pair`. The timestamp comes last, and an incrementing suffix handles same-second collisions. `--out` still honors a custom new or empty directory.

Start at [matches/index.md](../matches/index.md): it lists saved sets with participants, versions, collected/scheduled games, win totals, status, and links to their reports. The tester refreshes this index at the beginning/end of a run and after folder migration, including for custom output parents. An interrupted run's detailed report contains its latest saved progress; its index row may reflect the start until the next refresh.

Inside each run:

```text
results.json                 participants, versions, schedule, games, summaries, standings
report.md                    readable standings, matchups, inference and per-map details
games.csv                    one row per finished/failed runner job
build-0.log, build-1.log, ... build diagnostics
pair-01__jame-v1-vs-simon-v5/
  game-0001__swirl__A-jame-v1__B-simon-v5/
    runner.log
    statistics.json
    game-0001__swirl__A-jame-v1-286__B-simon-v5-1038__winner-simon-v5__r583.repl26a
```

Replay filenames identify the game index, map, actual Team A/B members and versions with their scores, winner, and finishing round. The example above means Jame v1 scored 286 as Team A and Simon v5 scored 1,038 as Team B. Portable names replace separators and punctuation; two versions of the same member remain distinct. The replay bytes are not modified. Raw runner logs retain their original messages and original auto-generated filenames.

Progress results are saved as games finish. `matches/` is already gitignored; source and documentation are tracked separately. CSV fields `gemsA`, `gemsB`, and `aWon` refer to the **first and second named participants**, not fixed engine sides; `aFirst` records which side the first participant used. CSV includes replay paths and `report.md` has a replay index with labelled scores, winner, round, and clickable links. Terminal game results use `jame 286 - simon 1038 | winner: simon` rather than an unlabelled score after the winner's name.

Open any game directory in the official viewer:

```sh
.venv/bin/cambc view matches/<run>/pair-01__jame-v1-vs-simon-v5/game-0001__swirl__A-jame-v1__B-simon-v5
```

Upgrade an older batch's **run folder, pair/game folders, replay names, and saved links** without playing games:

```sh
python3 tools/batch.py --rename-batch matches/<old-run>
```

This preserves replay bytes, statistics, and raw logs; rewrites output paths in JSON/CSV/report links and recorded commands; and refreshes the saved-set index. It is idempotent and refuses existing destination folders. It rejects a batch still marked running. All six batches present on 2026-10-18 have been migrated, with all **161 replay files verified unchanged**.

To update only replay filenames while keeping existing folders:

```sh
python3 tools/batch.py --rename-replays matches/<run>
```

This renames completed replay files in place and refreshes JSON/CSV/report links. Existing game directories keep their original names. The operation is idempotent, refuses filename collisions, and rejects replay paths outside the selected run. The saved batches present when this feature was added have already been relabelled.

## Validation

```sh
python3 -m unittest discover -s tools -p test_batch.py -v
```

Tests cover numeric newest-version selection, ambiguous names, side balancing and coverage, map validation, known Bayesian probabilities, duplicate evidence, side-normalized exports, incomplete games, runner failures, and timeout logs.

A real 12-game integration run (newest Daniel, Jame, and Simon; Swirl and Packs, both sides) completed without failures or bot faults. It exercised all three pairings, member labels, builds, replay artifacts, JSON/CSV output, and probability reporting. This validates the tester, not a broad ranking of the bots.

The full default run on 2026-10-17 also completed **102 games**, all 17 maps / both sides / three member pairs, with no failed games or bot faults:

| Matchup | Wins | P(first member's win rate > 50%) |
| --- | --- | --- |
| daniel v5 vs jame v1 | 34–0 | >99.9% |
| daniel v5 vs simon v5 | 20–14 | 84.5% |
| jame v1 vs simon v5 | 0–34 | <0.1% |

Local report: `matches/round-robin__daniel-v5_jame-v1_simon-v5__34-games-per-pair__17-maps__2026-10-17_124217-UTC/report.md`. These probabilities use the stated model and the locally installed engine; the results do not establish ranked-platform performance.

A separate five-game head-to-head on Swirl verified repeat handling: Jame beat starter 5–0, but the tool counted only two distinct side scenarios and reported **87.5%**, not the confidence implied by five independent wins. Replay/folder migration tests additionally verify side/score association, descriptive batch names, collision refusal, idempotence, unchanged bytes, and updated saved links/commands. The automated suite contains 30 passing tests, including explicit round-robin selection, starter exclusion, replay cleanup, retained results/logs, symlink boundaries, active-run preservation, the retention flag, and preservation after build failure. A fresh two-game Jame–Simon run also verified the descriptive default run folder and saved-set index, without failures or bot faults.

The explicit `--round-robin` command was verified over all 102 games on 2026-10-19 (Sydney), with no failures or bot faults. Latest versions were Daniel v7, Jame v3, and Simon v5:

| Rank | Member | Wins–losses | Observed win rate |
| --- | --- | --- | --- |
| 1 | daniel | 45–23 | 66.2% |
| 2 | jame | 34–34 | 50.0% |
| 3 | simon | 23–45 | 33.8% |

Daniel–Jame finished 18–16, Daniel–Simon 27–7, and Jame–Simon 18–16. The two 18–16 comparisons give only 63.2% posterior probability of a win rate above 50% under the stated model. [Full local report](../matches/round-robin__daniel-v7_jame-v3_simon-v5__34-games-per-pair__17-maps__2026-10-18_131959-UTC/report.md). All 102 new replay files and their saved links were verified present.
