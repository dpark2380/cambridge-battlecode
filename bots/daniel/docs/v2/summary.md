# Daniel v2: big-map fuel fix, danger-aware recall, learned draft, tuning

Code: `bots/daniel/main-v2` (frozen). `bots/daniel/main-cpp` is the identical working copy that `tools/draft_lab.py`
writes its table into. Iterations: [v1](../v1/summary.md) → v2 (this) → [v3](../v3/summary.md) → [v4](../v4/summary.md) → [v5](../v5/summary.md).

## Changes from v1

| Change | Detail |
|---|---|
| **Distance fields built at init** | A field turned out to cost only ~1–4k fuel; the expensive part was v1's lazy loop rescanning every group. Fields are now built on the first turn (2× fuel) while more than `FIELD_RESERVE` (20k) remains, and the rest on later turns. This fixed the big maps (lanes, expanse). |
| **Danger-aware recall** | Retreat when `health < incoming damage × ESCAPE_TURNS`. Incoming damage = strength of camps within 3 + 1.5 × strength of enemies within 4. The recall threshold also rises with carried gems (`RECALL_HP + GEM_RISK × gems/100`). Replaces `RECALL_HP_GEMS`. |
| **Experiment draft hook** | With a fuel quantum ≥ 1M (`tools/arena.py` `seed_fuel`), the draft decodes a seed and picks a random roster, giving many distinct games from a deterministic engine. Inert at the real 100k. |
| **Learned draft table** | `draft_table.h`: champion values per team size (3/4/5), fitted by `tools/draft_lab.py` on 1,800 random-roster self-play games. Greedy pick by value, never reading opponent picks: there is no denial, since both teams may take the same champion. |
| **Tuned constants** | `tools/tune.py`, 15 iterations, 5 accepted: tribute at ~23 gems (was 60), recall at 18% health, gold valued at 0.05 gems, buy health shards almost every time. |

## Results

| Opponent | Result |
|---|---|
| `starter-cpp` | 82% over 90 games (with random-draft seeds) |
| v1 (`main-v1`) | 70% over 90 games |
| v2 untuned | 62% over 90 games, so tuning was worth it |
| Learned vs hand-written draft (same gameplay) | 11/18 |
| Simon's `bots/v3` | **3/18**. v3 was much stronger, so later iterations build on the team line instead |

Draft findings (`docs/research/drafting.md`): rosters explain only 2–7% of the gem margin; Team B wins 60–77% of
mirror games.

## Errors encountered → fixes

| Symptom | Cause | Fix |
|---|---|---|
| Draft data mixed bot versions | `draft_lab collect` played the live source while it was being edited | Collect from a frozen copy |
| Random drafts could trigger in real games if the server's fuel changed | First hook used `100000 + 10000 × seed` | Moved experiments to ≥ 1M fuel; anything below is "real" |

## Weaknesses

1. Only one simple combat rule (`FIGHT_RATIO`); no altar locks, no wards.
2. No roles or plan in draft memory.
3. Far weaker than Simon's v3 (3/18), so v2 is retired and kept only as an opponent.

## Tunables

`src/params.h`: `RECALL_HP`, `GEM_RISK`, `ESCAPE_TURNS`, `TRIBUTE_GEMS`, `TRIBUTE_NEAR`, `W_GOLD`, `CAMP_SAFETY`,
`RECALL_TRIP`, `TRAVEL_W`, `FIGHT_RATIO`, `STAT_HEALTH_EVERY`; `FIELD_RESERVE` (fixed).
