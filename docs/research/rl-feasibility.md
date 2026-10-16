# RL / self-play feasibility for CAMBC 2026 (cambc2026a)

Researched 2026-10-14. "Measured" means I ran it locally with the official `cambc` 2.1.6 CLI from PyPI on an 8-core Apple M1 (scratch project, not this repo). The measurement code isn't committed; the numbers can be reproduced with the probes described in §1–2.

## TL;DR

- **Can we build a fully automated pipeline? Yes, the infrastructure part.** The official CLI runs matches headless and in parallel (`cambc run-batch --jobs N`), and it writes final statistics as JSON. Measured: about 1.9 CPU-seconds per C++ game, which is roughly **12k games/hour on one 8-core laptop**. Simulation volume is not what limits us.
- **Will an end-to-end RL policy beat a well-built heuristic bot? Very unlikely, and not by the first qualifier (4 Nov, 21 days away).** The binding constraint is inference. A C++ bot gets 100k fuel per turn. Measured best case is about 0.86 multiply-accumulates per fuel (int16 SIMD), so **at most ~85k MACs per turn, and only if the bot spends its whole budget on the network and does no game logic.** That is 4–5 orders of magnitude smaller than the nets behind every known RL win in this kind of game. Python is about 400× worse per MAC. On top of that the game is hard to learn: multi-agent, fog of war, 2000 rounds, sparse reward. I found no ML in the 21 MIT Battlecode postmortems I checked; winners used heuristics plus automated A/B testing.
- **Recommendation:** build the automated loop (generate → match → collect → evaluate → iterate), but point it at **parameterised heuristic bots**. Use black-box tuning (CMA-ES / Bayesian optimisation) and an automated regression gate. Use ML only where it fits: **draft-pick tables learned offline**, and small tables or linear evaluators distilled into code. Don't do end-to-end RL.

## 1. Inference constraints (decisive)

| Fact | Source |
|---|---|
| C++/Rust get 100k fuel per turn, OCaml 5×, Python 25×. Fuel ≈ instructions and is deterministic. | `docs/GameRules.md:335-339` |
| First draft turn gets 10× fuel and the first play turn 2×. Unused fuel does not carry over. | `docs/GameRules.md:343` |
| A bot that runs out of fuel is suspended and resumes next round, so its compute can spill over but it loses tempo. | `docs/GameRules.md:341` |
| The site FAQ says Python gets **20×**, which conflicts with the rules (25×). Measured locally: Python turn entry fuel was 2,492,089, so 25× applies in the local runner. | https://2026a.battlecode.co.uk/ (FAQ in `/public-assets/landing-*.js`); measured |
| C++ builds at `-O3` with `-msimd128`, so WASM SIMD is available. `wasm_i32x4_dot_i16x8` is in the shipped header. | `cmake/CMakeLists.txt:24`; `sdk/cpp/wasm_simd128.h:1195`; build cache `CMAKE_BUILD_TYPE=Release`, `-O3` (measured) |
| `cambc::fuel_remaining()` lets a bot budget its own compute. | `sdk/cpp/cambc.h:4988`, `sdk/cpp/imports.h:407` |

**Measured fuel cost of a 64×64 dense layer (4096 MACs), C++ `-O3`:**

| Kernel | Fuel | MACs/fuel | Max MACs/turn at 100% of 100k |
|---|---|---|---|
| scalar f32 | 52,490 | 0.08 | ~8k |
| SIMD f32x4 | 8,826 | 0.46 | ~46k |
| SIMD i16 dot (`i32x4.dot_i16x8`) | 4,776 | 0.86 | ~85k |
| Python pure-loop dot (Python budget 2.5M) | 1,927,490 | 0.002 | ~5k |

- The starter C++ bot already uses about 28k fuel per turn (measured: ~72k left after `play_turn`). Realistically that leaves **~50–70k MACs per turn**, for example a 128→128→64→16 int16 MLP, evaluated **once**. Search over candidate actions (evaluate N moves × the net) divides that further.
- For comparison: OpenAI Five used a 150M+ parameter model with a 4096-unit LSTM ([arXiv:1912.06680](https://arxiv.org/abs/1912.06680) §4, p.8; model p.3). The Lux AI S1 RL agent was a ~20M-parameter, 24-block 128-channel ResNet running under a 3-second-per-turn CPU budget ([Toad Brigade repo](https://github.com/IsaiahPressman/Kaggle_Lux_AI_2021); [Lux S1 specs](https://github.com/Lux-AI-Challenge/Lux-Design-S1/blob/master/specs.md)). CAMBC allows about 10⁻⁴ of that compute per decision.
- **Python cannot import numpy.** Measured: the runtime is CPython 3.13.7 built with wasi-sdk. `import numpy` and `import zlib` both raise `ModuleNotFoundError`, while `array`, `struct`, `math`, `json` and `random` work. Pure-Python MACs cost ~470 fuel each.
- **Size and memory limits:**
  - Submissions are uploaded as **source**, and the CLI enforces "compressed source exceeds the platform's 5 MB limit" and "source exceeds 64 MB" (strings in the `cambc` 2.1.6 binary).
  - So weights are effectively capped at roughly ≤5 MB compressed text. That is plenty for a net we couldn't afford to run anyway.
  - Locally an 11.6 MB `.wasm` with 8 MB of embedded weights built and ran, and `malloc(512 MB)` succeeded. The ranked-server memory limit is **unverified**.
- **Python build-time snapshot:** Python bots are pre-initialised with a Wizer snapshot at build. The CLI error says "Python preparation exceeded its two-minute runtime limit; move expensive module-level work into main()". So module-level precomputation of up to ~2 minutes appears to happen at build time with no per-turn fuel cost. This is inferred from the binary's strings and **unverified** on the ranked server.
- No rule bans embedding weights. I searched `docs/GameRules.md` and the SDK and found nothing; this is **unverified** against the full competition terms, which I could not see because the platform requires login.

## 2. Simulation throughput

- **The engine is not open source in this repo.** The C++ contract test includes engine headers from `${BC_GAME_ROOT}/Engine/...`, which are not shipped (`sdk/cpp/tests/CMakeLists.txt:8-17`). `sdk/rust/src/fake.rs` is a `#[cfg(test)]` stub host for SDK unit tests (`sdk/rust/src/lib.rs:59-60`), not a simulator. So there is no forward model we could call from inside a bot or from Python.
- **The official CLI bundles the runner** (PyPI `cambc` 2.1.6, uploaded 2026-10-13, a single native binary): https://pypi.org/project/cambc/
  - `cambc run A B --map M --statistics out.json` runs one match.
  - `cambc run-batch manifest.txt --jobs N --timeout S` runs many. The manifest has four columns: botA, botB, map, replay. A `--jsonl` "API v1 compiled-input" mode prints only machine events. The binary contains the string "maximum 128 matches per worker batch".
  - Replays are a zip containing `replay.repl26a` (binary, undocumented) plus per-team stdout and debug logs.
  - The statistics JSON has keys `botFaults, champions, engineVersion, outcome, round, teams`, with per-champion kills, damage, gold, gems and items.
- **Measured throughput (M1, 8 cores):**

| Workload | Result |
|---|---|
| 36 C++ games (one side burns all fuel), `--jobs 8` | 11.0 s wall, 68.6 s user → ~1.9 CPU-s/game, **~11.8k games/hour** |
| Single C++ game, starter vs starter | 0.6 s wall (≈620 rounds) |
| Single Python game, starter vs starter | 6.7 s wall / 27.5 CPU-s → **~1k games/hour** on 8 cores |

- For RL, the problem is not wall-clock: ~280k games/day is plenty for parameter tuning. The problem is that **each game is ~600–2000 rounds × 3–5 champions of sequential, black-box WASM**. We cannot batch the policy on a GPU, cannot reset to arbitrary states, and cannot fork mid-game. Every gradient sample means compiling the policy into a bot or using an IPC shim, and no such hook exists.
- **Online platform:** the season has a live ladder plus scrimmages (site FAQ). Scrimmage rate limits and replay download APIs are **unverified** because they require login.

## 3. Learning difficulty

- **Multi-agent, decentralised:** each champion runs its own bot instance (`docs/GameRules.md:31-35`). Vision is per-champion only, 8 tiles of shadowcasting, and teammates' views are not shared (`docs/GameRules.md:289`, `:307`). Communication is limited to **8 bytes** of shared memory plus 1024 read-only draft bytes (`docs/GameRules.md:351-353`).
- **Long horizon and sparse reward:** the game ends at 1000 tributed gems or round 2000 (`docs/GameRules.md:9`). Death costs 60 rounds (`:317`). Capture and tribute are multi-turn channels (`:134`, `:174`).
- **Heterogeneous action spaces:** there are 11 champion selections (sections at `docs/GameRules.md:372-716`) with different kits, plus shop, ward and consumables. Teams draft 3–5 champions depending on the map (`:55`), so a single policy must generalise across team compositions.
- **Precedent scale:**
  - OpenAI Five: 770±50 PFLOP/s·days over 10 months, with up to 1536 GPUs ([arXiv:1912.06680](https://arxiv.org/abs/1912.06680) §4, pp.5–8).
  - AlphaStar: 16 TPUv3 per agent, a 14-day league, up to 200 years of play per agent ([DeepMind blog, Jan 2019](https://deepmind.google/discover/blog/alphastar-mastering-the-real-time-strategy-game-starcraft-ii/)). It was also bootstrapped from human-replay imitation; the supervised policy alone was better than 84% of players ([DeepMind blog, Oct 2019](https://deepmind.google/discover/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/)).
- **What does scale down:** Lux AI S1 showed RL on one 8-core, dual-GPU PC can beat that team's own rule-based bot "within the first month" ([repo README](https://github.com/IsaiahPressman/Kaggle_Lux_AI_2021)). But it relied on a 20M-parameter net at 3 s/turn, a Python environment it could run in-process, and about 3 months of competition. CAMBC has none of these: inference is ~10⁴× smaller, the engine is closed, and we have 3 weeks. (That team's 1st-place finish is **unverified**; I couldn't load the Kaggle leaderboard.)

## 4. Precedent in Battlecode-style competitions

- I downloaded all **21 postmortems** linked from https://battlecode.org/past.html (2019–2026) and grepped them for "machine learning", "neural", "reinforcement learning", "genetic", "evolutionary", "bayesian", "CMA-ES" and "self-play". The only hits were "self-play" in the sense of bot-vs-old-bot testing and "tuning hyperparameters", both in [2023 Gone Fishin' (2nd)](https://battlecode.org/assets/files/postmortem-2023-gone-fishin.pdf) p.4. **None of them describe an ML policy.**
- **The 2025 winner, Just Woke Up**, says its big workflow change was automated A/B testing against old versions on every map: "One monumental addition to my workflow this year was the use of some sort of automated testing" ([postmortem](https://battlecode.org/assets/files/postmortem-2025-just-woke-up.pdf), "Automations / AB Testing" section, ~p.14).
- [2026 Lorem Ipsum](https://battlecode.org/assets/files/postmortem-2026-lorem-ipsum.pdf) §10.1 tried a constant tuner, but it was "too slow on my system and doesn't do well". They relied on the local runner and scrims instead.
- [2020 The High Ground](https://battlecode.org/assets/files/postmortem-2020-the-high-ground.pdf) wanted to tune `MagicConstants` but "ended up not being able to tune any of our constants robustly", and encourages future teams to tune better.
- Caveat: MIT Battlecode uses a Java bytecode limit, not WASM fuel, but the compute regime is the same (cheap per-turn heuristics). The ML successes I know of (Lux AI) come from competitions with seconds-per-turn budgets.

## 5. Hybrid alternatives that capture most of the value

Best value first:

1. **Automated regression/tournament harness.** Use `run-batch` over all 9 maps (`maps/*.map26a`) × both sides × N seeds, parse the statistics JSON, and report win rate with a confidence interval against a pinned pool of past versions. This is the 2025 winner's main lever, and it gets cheap compute (§2) for free. Note that ties go to Team B (`docs/GameRules.md:16`), so always swap sides.
2. **Black-box parameter tuning.** Expose the heuristic weights (aggression thresholds, recall HP%, camp-choice scores, shop order) as a constants header and optimise win rate with CMA-ES or Bayesian optimisation.
   - At ~12k games/hour, 100 games per candidate gives ~120 candidates/hour per machine.
   - Guard against overfitting to self-play by evaluating against a diverse pool of frozen bots, not only the previous best.
3. **ML for the draft only.** The draft bot sees the whole map and the opponent's picks so far (`docs/GameRules.md:72`). It gets 10× fuel on its first draft turn, about 1M fuel in C++ (`:343`). With 11 champions and 3–5 picks, the space is small:
   - Learn per-map composition and counter-pick win rates offline from batch sims.
   - Ship a lookup table in a few KB of source.
4. **Distilled tables and linear evaluators.** Fit small lookups or linear scores offline, for example the value of contesting a camp given HP and gold difference, or fight/flee given visible units, and compile them into code. At ~0.86 MAC/fuel, a 50–500-weight linear model costs <1k fuel per evaluation.
5. **Imitation from replays.** Low priority. `.repl26a` is an undocumented binary format (magic `a62per`, measured), and whether opponents' replays can be downloaded is **unverified**.

## 6. Timeline

From the official site, https://2026a.battlecode.co.uk/ (schedule in `/public-assets/landing-*.js`):

| Event | Date |
|---|---|
| Launch | 12 Oct |
| Sprint 1 | 18 Oct (submission lock 17 Oct) |
| Sprint 2 | 25 Oct (lock 24 Oct) |
| Sprint 3 | 1 Nov (lock 31 Oct) |
| International qualifiers | 4 Nov |
| UK qualifiers | 11 Nov |
| Finals, Cambridge Union | 18 Nov |

Prize pool is £18,000; teams of 1–4. Today is 14 Oct, so there are **3 days to Sprint 1, 21 days to the international qualifier and 35 to finals.** That is too short to stand up a closed-engine RL pipeline and get it past a heuristic bot. It is enough for a heuristic bot plus an automated tuning loop.

## Recommended plan

1. **Sprint 1 (by 17 Oct):** ship a solid C++ heuristic bot. C++, because Python is ~400× more expensive per MAC and ~15× slower to simulate.
   - Draft fixed comps per map.
   - Farm camps, capture, tribute, recall at low HP.
2. **Week 1–2:** build the harness.
   - A script that writes `run-batch` manifests (all maps × swapped sides).
   - A results parser for the statistics JSON.
   - Win-rate with confidence interval and Elo against a frozen pool, plus a "promote if ≥ X% vs champion" gate.
   - Move all magic numbers into one constants header that the harness can override at build time.
3. **Week 2–3:** run a CMA-ES / Bayesian optimisation tuner over the constants overnight. Learn the draft table from batch sims. Bring in opponent behaviours seen in ladder scrims as new pool bots.
4. **After the qualifiers, optional:** use spare cores on distilled linear evaluators for fight/flee or camp choice. Revisit RL only if a heuristic plateau is clearly identified, and then only for a tiny sub-decision.

## Sources

**Repo**
- `docs/GameRules.md` lines 9, 16, 31-35, 55, 72, 134, 174, 289, 307, 317, 335-343, 351-353, 372-716
- `cmake/CMakeLists.txt:21-24`
- `sdk/cpp/wasm_simd128.h:1195`
- `sdk/cpp/cambc.h:4988`
- `sdk/cpp/imports.h:407`
- `sdk/cpp/tests/CMakeLists.txt:8-22`
- `sdk/rust/src/lib.rs:59-60`

**Official CAMBC**
- https://2026a.battlecode.co.uk/ (schedule and FAQ)
- https://luma.com/a1jsj4wq (finals format)
- `cambc` CLI 2.1.6: https://pypi.org/project/cambc/ (`--help` output and binary strings)

**Papers and official write-ups**
- OpenAI Five: https://arxiv.org/abs/1912.06680
- AlphaStar: https://deepmind.google/discover/blog/alphastar-mastering-the-real-time-strategy-game-starcraft-ii/ and https://deepmind.google/discover/blog/alphastar-grandmaster-level-in-starcraft-ii-using-multi-agent-reinforcement-learning/
- Lux AI S1: https://github.com/IsaiahPressman/Kaggle_Lux_AI_2021 and https://github.com/Lux-AI-Challenge/Lux-Design-S1/blob/master/specs.md

**MIT Battlecode postmortems** (index: https://battlecode.org/past.html)
- https://battlecode.org/assets/files/postmortem-2025-just-woke-up.pdf
- https://battlecode.org/assets/files/postmortem-2026-lorem-ipsum.pdf
- https://battlecode.org/assets/files/postmortem-2023-gone-fishin.pdf
- https://battlecode.org/assets/files/postmortem-2020-the-high-ground.pdf
