# Cambridge Battlecode

Bots for CAMBC 2026 (`cambc2026a`). Start with `CLAUDE.md` for layout, conventions and the bot architecture.
Rules are in `docs/GameRules.md`.

## Bots

| Bot | What it is |
|---|---|
| `bots/simon/` | Simon's bots, notes in `bots/simon/docs/`. `v4`: every body claims its own target and farms solo. `v6`: v4 plus capture contesting, plus a record of rejected experiments (loses 41% to `bots/daniel/v5`). `v3`, `v2`: earlier versions, kept as regression opponents. Research: `bots/simon/docs/research/` |
| `bots/daniel/` | Daniel's bots, one doc per iteration in `bots/daniel/docs/v1`–`v8` (index: `bots/daniel/docs/README.md`). **`v8`: the team's strongest bot**, v7 ported to the week 2 patch (61% vs v7, 84% vs hunter). `v7`: ranked fixes (59% vs v6). `v6`: Monolith sieges + gold weight 0.20. `v5`: Simon's v4 with self-play-tuned constants. `hunter`: an aggressive test opponent. `v4-dp`, `v5-dp`: a parallel branch off v3. `main-cpp`, `main-v1`, `main-v2`: an earlier, weaker independent bot |
| `bots/starter-cpp`, `bots/starter-python` | The SDK starter bots |

## Test, tune, draft

Needs the `cambc` CLI (`uv tool install cambc` on macOS). Tools are stdlib Python and run matches in parallel.

```sh
python3 tools/arena.py v8 v7                 # regression gate (also gate against hunter); bare names also find bots/daniel/*
python3 tools/tune.py --bot v8 --params recall_health,tribute_gems --iterations 15   # self-play tuning
python3 tools/draft_lab.py collect --bot v8 && python3 tools/draft_lab.py fit --bot v8 --no-write
python3 tools/ranked.py replays/daniel-v8          # download + summarise our ranked games
```

Background reading: `docs/research/rl-feasibility.md` explains why we tune heuristics rather than train an
RL policy. `docs/research/drafting.md` covers what the draft can and cannot win.
