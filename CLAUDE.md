# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A competitor workspace for **Cambridge Battlecode (CAMBC), event `cambc2026a`**. Bots are compiled to WebAssembly and run by the organisers' engine under Wasmtime; the engine itself is **not** in this repo. `cambc.toml` pins `sdk_version = "2.1.3"` and enables `cpp` and `python`.

- `bots/` — our bots, one directory per bot, each with a `src/` folder. `starter-cpp` and `starter-python` are untouched copies of `sdk/templates/{cpp,python}`, kept as baseline opponents.
- `bots/<teammate>/` — each teammate's bots, one folder per iteration, with notes in `bots/<teammate>/docs/v<n>/summary.md`, one per iteration (strategy, results, errors hit and their fixes, weaknesses, next steps, tunables). Add a new version folder whenever the strategy changes meaningfully; older folders stay as baseline opponents. After moving or renaming a bot folder, delete its `.cambc/` build cache (it stores absolute paths). Tools accept bots by bare name and search teammate folders (`tools/arena.py v5 v4`), so keep version names unique across teammates.
  - `bots/jame/`: independent C++ implementation; [version index](bots/jame/docs/README.md). `v3` adds metadata-driven abilities, equipment/resupply, damage-first camp targeting and persistent planning; see [v3 summary](bots/jame/docs/v3/summary.md). The strict group-survival gate was tested and left off by default. Draft is unchanged; no teammate implementation, roles or shared-memory protocol is copied. Retain `v1`/`v2` and develop meaningful changes in `v4`. Use explicit paths (`bots/jame/v3`) to avoid version-name ambiguity.
  - `bots/simon/`: `v2`, `v3`, `v4`, `v6` (no `v5`: that number went to `bots/daniel/v5`). The draft (`draft.cpp`) scores champions against a map profile (`map_profile.cpp`) and writes a `draft_plan` (`plan.h`: roster, per-champion role, map features) to draft memory; champions read it with `read_plan()`. Gameplay (`bot.cpp`) since v4 (see `bots/simon/docs/v4/summary.md`): every body picks its own target group and claims it in shared memory, a 64-bit word of 6-bit claims per body plus a danger marker (layout at the top of `bot.cpp`). `world.cpp` caches camp groups and each champion's own observations of them. v6 adds only capture contesting and records the rejected experiments (`bots/simon/docs/v6/summary.md`); it loses 41% to `bots/daniel/v5`. `bots/simon/docs/research/league_macro.md` maps League of Legends macro concepts onto CAMBC; its recommendations 1–5 were tested in v6.
  - `bots/daniel/`: notes are numbered by Daniel's own iterations; the mapping to bot folders is in `bots/daniel/docs/README.md`. `v7` (v6 + fixes from the v6 ranked research; **current best and the base for the next iteration**, see `bots/daniel/docs/v7`), `v6` (v5 + Monolith sieges + gold weight 0.20), `hunter` (an aggressive test opponent for fight changes), `v5` (Simon's v4 with self-play-tuned constants and the experiment draft hook; beats v4 63% over 162 games, Daniel iteration v5). `v4-dp`/`v5-dp` (iterations v3/v4, a parallel branch off the team's v3), and `main-v1`/`main-v2` (iterations v1/v2, an independent, weaker heuristic bot; `main-cpp` is v2's working copy and holds the `draft_lab.py` table).
- `sdk/` — vendored SDK (C++ header `cambc.h`, Python `cambc` package + `_cambc.pyi` stubs, Rust, OCaml) and per-language templates. Treat as upstream; don't edit unless bumping the SDK.
- `cmake/CMakeLists.txt` — the build used for every C++ bot.
- `maps/*.map26a` — the current map rotation (binary). `maps/ascii/*.txt` are engine dumps of each: grid, legend and camp-group rewards. Read these to reason about a map. After `cambc maps pull`, delete any UUID-suffixed duplicates and run `python3 tools/dump_maps.py [map...]` to write the dumps (it plays `tools/mapdump` for 5 rounds per map).
- `docs/GameRules.md`, `docs/BotAPICpp.md`, `docs/BotAPIPython.md` — exported handbook and full API reference. These are large; grep for the `### <name>` heading of the function you need rather than reading them whole.

## Building

C++ bots build to `bot.wasm` via `cmake/CMakeLists.txt`, which requires `BOT_DIR` (bot directory containing `src/`), `BC_SDK` (the `sdk/` directory) and `WASI_SDK_PREFIX` (a wasi-sdk install, used with its CMake toolchain). It globs `${BOT_DIR}/src/*.cpp`, so new `.cpp` files are picked up automatically. Required flags (already set): C++20, `-msimd128`, and Wasm exnref exceptions (`-fwasm-exceptions -mllvm -wasm-use-legacy-eh=false`, linked against the wasi-sdk `eh` sysroot + `-lunwind`) — the runner's Wasmtime only supports that exception proposal, so don't change these.

`.vscode/settings.json` points CMake Tools at `cmake/`. Each C++ bot's `.clangd` reads `compile_commands.json` from the bot directory.

Python bots need no build; `pyrightconfig.json` adds `../../sdk/python` to the path for type checking.

### `cambc` CLI

Installed as a pip package. On Windows the executable is at `C:\Users\visvi\AppData\Local\Programs\Python\Python313\Scripts\cambc.exe` (not on PATH — `cambc add-to-path` fixes that per session); on macOS it is installed with `uv tool install cambc` at `~/.local/bin/cambc`. Run `cambc <cmd> --help` for options.

- `cambc run <BOT_A> <BOT_B> --map <name> [--rounds N] [-o DIR] [--statistics out.json] [--view]` — play a match. Bots are directory paths (e.g. `bots/starter-cpp`); maps resolve by bare name under `maps/`. `--rounds` truncates the game.
- `cambc build <BOT>` — compile a bot to Wasm. `cambc view [replay]` opens the visualiser.
- `cambc new`, `cambc maps pull` (refresh the map pool), `cambc init` (refresh `sdk/`), `cambc submit` / `cambc bundle`.

The replay bundle (`*.repl26a`) is a ZIP: `team-a.stdout` / `team-b.stdout` hold bot prints, `team-*.debug` the debug draws. Printing from a bot and reading `team-a.stdout` is the easiest way to inspect engine state, e.g. map layout (the `.map26a` format is binary; `game_map.camp_groups()` is empty during the draft, so dump on the first game turn). Bot prints that run out of fuel resume next turn, so give such runs a few rounds.

### Testing and tuning (`tools/*.py`, stdlib Python, parallel)

- `python3 tools/batch.py [memberA memberB] --games N` — exact-size sets; omit names for a newest-member round robin. Highest numbered version per member is selected, plain `vN` preferred to same-number suffix branches. Results use member names and save reports, JSON/CSV, logs, and replays under `matches/`. Swaps sides; normal fuel only. Reports Beta(1,1)-prior `P(win rate > 50%)` using distinct completed map/side setups so identical deterministic repeats do not inflate evidence. See `docs/BatchTesting.md`; tests: `python3 -m unittest discover -s tools -p test_batch.py`.

The engine is deterministic: one map + side = one game. For bigger samples, run with a fuel quantum of `1,000,000 + 10,000 * seed` (`arena.seed_fuel`); bots with the experiment hook (everything in `bots/daniel/`) then draft a random roster. Real matches run at 100k, so the hook is inert in competition. Port the hook into each new version.

- `python3 tools/arena.py <botA> <botB> [--seeds N] [--min-winrate X]` — every map, both sides (plus N random-draft games per map and side); prints per-map results and A's win rate with a 95% interval. Use it as the regression gate before freezing a version. Bots are names under `bots/` or a teammate folder (first match in `bots/*/`, so `v5` means `bots/daniel/v5`; pass a path for `bots/simon/v5`). Works with cambc ≥ 2.2 (`--json` statistics, normalised by `arena.normalize`).
- `python3 tools/tune.py --bot v5 --params a,b,c [--iterations N --seeds S]` — evolution strategy over named constants (`name = 1.5f` in `src/bot.cpp`): builds copies under `bots/_tune*` (gitignored), plays each candidate against the incumbent, and accepts at ≥56%. Prints the best values; `--apply` writes them back. Always confirm the result with a large `arena.py --seeds` run, because single accepted steps can be noise.
- `python3 tools/draft_lab.py collect --bot <bot>` / `fit --no-write` — random-roster self-play, then per-team-size champion values (Bradley–Terry plus gem-margin ridge). Findings: `docs/research/drafting.md`.
- Research notes on ML/RL feasibility: `docs/research/rl-feasibility.md`.

### Replay analysis

`node tools/replay/analyze.mjs [--us A|B] [--out dir] <replay.zip|.repl26a|dir>...` decodes replays with the visualiser's own engine wasm (found under `%LOCALAPPDATA%/cambc/assets` on Windows, `~/Library/Caches/cambc/assets` on macOS). It works on platform downloads (zip: `replay.repl26a` + our stdout) and on local bundles. For each input it writes `<name>.stats.json` (same schema as `--statistics`) and `<name>.timeline.csv` (per champion per round: position, health, alive, gems, gold, K/D/A), and prints a report: score over time, per-champion table with builds, and every death with position and gems lost. Our team is detected from the draft log lines. The visualiser's own CSV export only covers rounds already played back, so don't rely on it. Platform replays go in `replays/<version>/` (gitignored); write analysis to `replays/<version>/analysis/`.

The installed CLI may be newer than the vendored `sdk/` (it warns and suggests `cambc init`).

## Bot architecture

Every bot runs the same loop in `main`: forever, if `is_draft()` run the draft logic, else run the champion turn; catch and log any exception; then `end_turn()`. An exception must never escape the loop, or the bot dies.

- **One bot instance per champion.** Each champion runs its own copy of the program, keeping state across turns in process memory (e.g. `Bot` members). Teammates don't share vision or memory; cross-champion communication is only via:
  - `draft_memory` — 1024 bytes written during the draft, read-only during the match.
  - `shared_memory` — 8 bytes per team, read/write all match (starter stores a little-endian u32 at offset 0).
- **Draft phase** (`draft.cpp` / `draft.py`): full map visible, 10x fuel on the first draft turn; picks champions one at a time, simultaneously with the opponent. A missing pick is randomised.
- **Fuel, not time**, limits compute: 100k/turn for C++/Rust, 5x for OCaml, 25x for Python; 2x on the first game turn. Running out suspends the bot mid-execution and it *resumes from that point next turn* — so expensive work can silently span turns.
- **Fuel costs hide in SDK calls.** Every engine call costs roughly 150 fuel. `vision::camp_at`, `vision::camps()` and `map::camp`/`camp_groups()` reload *every* camp group from the engine (~30k fuel per call on a 70×70 map), so in a turn use the cached lookup in `bots/simon/v4/src/world.h` instead. Running out of fuel never shows up as an error; the turn just stops and resumes next round, so measure with `cambc::fuel_remaining()`.
- **Camp spawn tiles:** an occupied spawn tile delays the whole group's respawn. Never wait on one.
- **Lean on SDK bitboards.** Map/vision queries return `bitboard`s (`map::walls()`, `vision::camp_tiles()`, …) combined with `| & ~`; pathfinding uses `distance_field::compute_to` and `bitboard::reachable_tiles`. The rules recommend using the SDK's movement mask rather than recomputing walkability.
- **Actions can return `false` without throwing** when a hidden unit (e.g. in a bush) blocks the destination; that doesn't consume the allowance, so retry elsewhere. Acting on a *known* invalid target throws (`cambc::error` / Python `cambc.Error`).
- Python API mirrors C++: C++ namespaces → submodules (`cambc.game_map`, `cambc.vision`, `cambc.draft`, …), `cambc::self()` → `cambc.me()`, overloads → optional params, enums are `UPPER_CASE`.

## Game rules worth keeping in mind

See `docs/GameRules.md` for detail. Win by tributing 1000 gems (or most gems at round 2000; tiebreaks: lifetime gold, kills, then Team B). Loop: kill every monster in a cardinally-connected camp group → stand on its spawn tiles uncontested for 5 rounds to capture → carry gems to an altar (Chebyshev ≤ 1) and channel a tribute of `max(1, ceil(gems/10))` turns. Carried gems are lost on death (to the killer, or destroyed by camps). Ranged champions can't move and basic-attack in the same turn; melee can. Gold buys shards (30g; 5 of a kind → emblem) and consumables (10g) on spawn or while dead.
