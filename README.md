# Cambridge Battlecode

Bots for CAMBC 2026 (`cambc2026a`). Start with `CLAUDE.md` for layout, conventions and the bot architecture.
Rules are in `docs/GameRules.md`.

## Bots

| Bot | What it is |
|---|---|
| `bots/simon/` | Simon's bots, notes in `bots/simon/docs/`. `hunter-v0`: daniel/v5 that hunts gem carriers as a team; beats daniel/v5 55% and v6 52%, base of the hunter line. `v6`: daniel/v5 plus fixes from its loss to a +200 bot (52% vs daniel/v5). `v5`: v4 plus capture contesting and a record of rejected experiments. `v4`: every body claims its own target and farms solo. `v3`, `v2`: earlier versions, kept as regression opponents. Research: `bots/simon/docs/research/` |
| `bots/daniel/` | Daniel's bots, one doc per iteration in `bots/daniel/docs/v1`–`v5` (index: `bots/daniel/docs/README.md`). `v5`: v4 with self-play-tuned constants (63% vs v4 over 162 games); base of `bots/simon/v6` and `hunter-v0`. `v4-dp`, `v5-dp`: a parallel branch off v3. `main-cpp`, `main-v1`, `main-v2`: an earlier, weaker independent bot |
| `bots/starter-cpp`, `bots/starter-python` | The SDK starter bots |

## Test, tune, draft

Needs the `cambc` CLI (`uv tool install cambc` on macOS). Tools are stdlib Python and run matches in parallel.

```sh
python3 tools/arena.py v5 v4                 # regression gate; bare names also find bots/daniel/*
python3 tools/tune.py --bot v5 --params recall_health,tribute_gems --iterations 15   # self-play tuning
python3 tools/draft_lab.py collect --bot v5 && python3 tools/draft_lab.py fit --bot v5 --no-write
node tools/replay/analyze.mjs --out replays/v4/analysis replays/v4                   # platform replays
```

Background reading: `docs/research/rl-feasibility.md` explains why we tune heuristics rather than train an
RL policy. `docs/research/drafting.md` covers what the draft can and cannot win.
