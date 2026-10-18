# Daniel v7: fixes from the v6 ranked research

Code: `bots/daniel/v7` (C++), forked from Daniel v6. Each change comes from
`bots/daniel/docs/research/v6-improvements.md` (54 ranked v6 games, 28–26). Each was tested on its own and kept only if
it held up. Iterations: [v1](../v1/summary.md) → … → [v6](../v6/summary.md) → v7 (this).

## Changes from v6

| # | Change | Code | Test | Kept |
|---|---|---|---|---|
| 3 | **Stall check on walking distance.** One `distance_field` to the target's tiles per target change, not Chebyshev to the anchor. Ranked: 240 of 560 give-ups were false, 218 of them on pilgrimage. | `watch_progress`, `progress_field` | pilgrimage 12/14 (+166); all maps 71/136 (52%) | yes |
| 2 | **Unseen attackers and blocked steps.** If health fell since last turn with no camp or visible enemy in reach, someone in a bush is hitting us: mark danger, leave at the duo's threshold, and walk away instead of recalling (damage cancels a recall). `move_towards_closest` retries up to 3 tiles when a step into a hidden unit returns false. Ranked: 159 of 496 champion kills on us came from a bush. | `take_turn` (`hidden_response`), `move_towards_closest` | with #3: 76/136 (56%) vs v6; vs hunter 65% (v6: 64%; local bots don't use bushes) | yes |
| 1 | **Siege any group too big for two bodies**, not only Monoliths: `sieged(g) = monolith or (mobs and needed(g) == 0)`, re-checked every choice. `remaining` health is tracked for every group that fights back, damage taken is scaled to what's left, and bodies **leave a sieged group** once health < 3 turns of its damage split over the allies present (`siege_escape_turns`). | `choose_target`, `work_group`, `take_turn`, `world.cpp` | stampede/eight/pilgrimage/swirl 35/56 (62%); stampede local game 1,080–0 (v6 scores 0) | yes |
| 4 | **Carriers leave at 50%** while an enemy was seen in the last 30 rounds (`carrier_recall_health`). Ranked: 45 of 79 deaths with gems came after the carrier was already below 50%. | `take_turn` | 54% vs v7, 71% vs hunter (base 68%) | yes |
| 5 | Jungle emblem first instead of Monster (`jungle_first`) | `build_order` | 49% vs v7, 68% vs hunter: no effect | no (off) |
| 6, 7 | Ranged-poke response; draft profile for siege-only groups | — | not built yet | — |

## Results

| Opponent | Result |
|---|---|
| Daniel v6 (17 maps × 2 sides × 5 drafts) | **101/170 = 59%** (95% CI 52–67%) |
| Hunter | ~70% (v6: 64%) |
| `bots/simon/v5` | **73/102 = 72%** |

## Known weaknesses / next steps

1. Stampede: v7 farms gold first and Varg starts sieging the elk group around round 700. Opponents rush it as a whole
   team by round 250. Value sieges higher early, or make the whole team converge.
2. Ranged pokers (research #6): their Tavi, Stellar and Prism get ~3 kills/game each. Test only against `hunter`.
3. Draft (research #7): the map profile counts siege-only groups as normal elk/splash value.
4. Submit and download ranked games into `replays/daniel-v7/`.

## Tunables

v6's set plus `hidden_response`, `siege_escape_turns`, `carrier_recall_health`, `jungle_first` (top of
`bots/daniel/v7/src/bot.cpp`).
