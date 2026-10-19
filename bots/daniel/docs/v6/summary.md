# Daniel v6: sieges, gold for fights, and a hunter sparring bot

Code: `bots/daniel/v6` (C++), forked from Daniel v5. Built in response to the 65 ranked v5 games (18–47; see
`../v5/summary.md`). Iterations: [v1](../v1/summary.md) → [v2](../v2/summary.md) → [v3](../v3/summary.md) →
[v4](../v4/summary.md) → [v5](../v5/summary.md) → v6 (this) → [v7](../v7/summary.md).

## Changes from v5

| Change | Detail | Kept? |
|---|---|---|
| **Sieges** (`siege`, `max_siege_bodies`, `siege_value`) | Monolith groups are now targets. They never chase or heal, so damage carries over between trips. The world cache tracks each Monolith group's remaining health (`group_info::remaining`) when the whole group is in sight. A siege plans on the whole team (capped), uses the remaining health for kill time, charges its damage as trips home, and never waits for help. | yes |
| **Gold weight 0.10 → 0.20** | Ranked games: we out-earned the opponent on gold in our wins (4,884 vs 3,316) and were out-earned in our losses (3,922 vs 5,333; 42 of 65 games overall). In those losses they dealt 15.6k champion damage to our 6.8k. Self-play tuning had lowered gold because mirror games rarely fight. | yes |
| Fight switches: `ally_radius` (count allies within 8), `retreat_to_allies`, `threat_tribute_gems` (bank at 12 after seeing an enemy) | All within noise against both v5 and the hunter, and combining them was slightly worse (45% / 46%). | no (left in, switched off) |
| `bots/daniel/hunter` | Sparring bot: v5 with `engage_radius` 8, everybody chases, fights at 80% of the enemy's health, finishes targets below 50%, and ignores danger zones. It mimics ranked opponents that chase, which our own bots don't. Even with v5 overall (35/68), but it swings by map. | test opponent |

## Experiments behind the changes

- **Monoliths don't heal.** A throwaway bot hit the contest Monolith down to 9,205 health, then stood off. It stayed at
  9,205 from round 160 to 420. Five bodies took about 230 health per round off it.
- **Sieges are rarely the best rate.** With 6 bodies, the monolith map's corner group (Monolith + 8 gem clusters,
  392 gems) takes ~77 turns, and each body pays ~2.5 health bars in trips home: ~0.2 gems per body-turn, about half
  of wolf farming. So v6 only sieges when there is little else. On contest (all gems are in Monoliths) v6 goes 4/8
  with +175 average margin against v5, which scores 0 there. On every other map it plays exactly like v5
  (4/8, +0 margin on all 16).
- Gold weight on 238 games each (17 maps × 2 sides × 7 drafts):

| gold_weight | vs v5 | vs hunter |
|---|---|---|
| 0.10 (v5) | 117/238 (49%) | 124/238 (52%) |
| **0.20** | 117/238 (49%) | **148/238 (62%)**, +144 avg |
| 0.25 | 118/238 (50%) | 141/238 (59%) |
| 0.30 | 120/238 (50%) | 129/238 (54%) |
| 0.40 / 0.60 (102 games) | 51% / 42% | 47% / 46% |

## Results

| Opponent | Result |
|---|---|
| Daniel v5, real drafts (17 maps × 2 sides) | 17/34 (50%) |
| Hunter (random drafts, 238 games) | 62% (v5's code: 52%) |
| `bots/simon/v5` (random drafts, 102 games) | **62/102 (61%)** |
| `bots/simon/v4`, real drafts | 19/34 (56%) |

The gain shows against opponents that fight, which is what ranked games look like. It is invisible in mirror games.

## Tooling changes

- `cambc` 2.2.5: `--statistics` writes binary unless `--json`, and the JSON layout changed. `tools/arena.py`
  passes `--json` and `normalize()` maps the new layout back to the fields the tools use (outcome, round, team gems,
  draft picks, bot faults).
- Bare bot names are now ambiguous (`v5` exists for both Daniel and Simon). `tools/arena.py` takes the first match
  in `bots/*/`, which is `bots/daniel/` alphabetically. Pass paths for Simon's bots.

## Next steps

1. Submit v6 and check that ranked gold earned per game rises and deaths fall.
2. Builds: opponents collect one emblem of each passive (Durability, Jungle, Bruiser) on top of Power stacks. Ours
   is Monster → Durability → Power. Test their order against the hunter.
3. Contest: our lone sieger died twice carrying 200 gems. Recall (which keeps gems) after a big capture instead of
   walking to an altar through enemies.

## Ranked results (54 games, 2026-10-18, `replays/daniel-v6/`)

**28–26 (52%)**, up from v5's 18–47. Gold per 100 rounds: us 654 vs them 558 (v5: 596 vs 702), out-earned in 18/54
(v5: 42/65). Contest 1–0 (+800), collision 4–0. Still losing eight 0–3, stampede 0–3 (0 gems: its only gems are a 6-elk
group) and swirl 1–2. Losses average 14.8 deaths. Full research: `../research/v6-improvements.md`; fixes in v7.
