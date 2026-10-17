# Daniel's iterations

| Iteration | Bot folder | Summary | Key result |
|---|---|---|---|
| [v1](v1/summary.md) | `main-v1` | First independent heuristic bot: reward-per-turn camp choice with claims, retreat-before-recall | 16/18 vs starter |
| [v2](v2/summary.md) | `main-v2` (`main-cpp` = working copy) | Fuel fix for big maps, danger-aware recall, learned draft table, tuned constants | 70% vs v1; 3/18 vs team v3, so retired |
| [v3](v3/summary.md) | `v4-dp` | Team v3 + gem-aware gold squad + tuned constants | 55% over 288 vs v3 code |
| [v4](v4/summary.md) | `v5-dp` | Daniel v3 + simple solo farming | 13/18 vs Daniel v3; 9/18 vs Simon's v4 |
| [v5](v5/summary.md) | `v5` | Simon's v4 + self-play-tuned constants. Submitted (team bot version 5); ranked 18–47 | 102/162 (63%) and 11/18 vs Simon's v4 |
| [v6](v6/summary.md) | `v6` | v5 + Monolith sieges + gold weight 0.20 (gold wins fights) | 62% vs hunter (v5: 52%); 61% vs Simon's v5 |
| — | `hunter` | Test opponent: v5 made aggressive (chases, engages at 8 tiles) | sparring partner for fight-related changes |

All bots accept bare names in the tools (`python3 tools/arena.py v5 v4`). Iterations v2–v6 have the random-draft
experiment hook (`--seeds`, `tools/tune.py`).
