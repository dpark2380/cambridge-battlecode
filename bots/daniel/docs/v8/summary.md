# Daniel v8: port to the week 2 patch

Code: `bots/daniel/v8` (C++), forked from Daniel v7. The week 2 balance patch (2026-10-20) changed camp stats, added
the Golem camp and the Heart of Ruin champion, renamed and replaced the map pool (21 maps, `00*`/`01*`) and moved the
SDK to 3.0.1 (`cambc` 3.0.1). v7 still compiles and kept playing ranked games on the new engine. v8 fixes what the patch
broke. Iterations: [v1](../v1/summary.md) → … → [v7](../v7/summary.md) → v8 (this).

## What the patch broke in v7 (100 ranked games on the new engine, 56–44)

`replays/daniel-v7-patch2/` (downloaded with `tools/ranked.py`). Wins and losses differ mostly in gold: 9.5k vs 5.4k
in our wins, 4.8k vs 8.6k in our losses.

| Map | v7 ranked | Cause |
|---|---|---|
| 01big_world | 1–4, we tribute 4–8 gems | v7 planned with the old 500-health gem clusters, and on one side half the team froze (local repro: side B scores 0, earns 0 gold). Fixed by the camp table below. |
| 01corridors | 1–2, 133–147 deaths | Two Monoliths (428 gems) sit at the end of our spawn lane. Monoliths now reach 5 tiles and hit the nearest champion for 200 each. v7 sieged them, left at 29% health and died walking out (230 of 255 local deaths were to camps 0 and 1). |
| 01boss_battle | 0–2, 0:0 | The only altar is walled in. The only free tiles next to it are the two Monoliths' spawn tiles, so nobody tributes and the game goes to the lifetime-gold tiebreak. v7 farmed gems it could not deliver. |
| 00contest | 0–1, 0:200, 101 deaths | The same Monolith death trap as corridors. |
| 00eight | 1–3 | Deaths (50–68 per loss); not addressed. |

## Changes from v7

| Change | Code | Kept |
|---|---|---|
| Camp table: Golem (5,000 health, 120 damage, counts as a mob group); attack ranges per kind (wolf 3, elk and Golem 4, Monolith 5) in `threatened()` | `world.cpp` (`camp_range`), `bot.cpp` | yes |
| Gem and gold clusters plan at an **effective 500 health** (true: 120). Planning with 120 over-values cluster groups. Bisected from gold-rush 1/8; all maps vs v7 at 300 / **500** / 800: 59% / **61%** / 52% | `cluster_effective_health` | yes |
| **Monolith leave rule.** It hits the nearest champion for its full damage out to range 5. Leave while health covers walking out of range plus one hit, or one step plus one hit when an ally is closer to it. Stay to finish it when it dies before we would (shared Monoliths). | `take_turn` | yes |
| **Monolith siege gate.** Skip a Monolith siege unless max health covers `monolith_hit_turns` (3) hits plus the exit (one step with allies). 0/1/2/3 all tested within noise; 3 kept. | `choose_target` | yes |
| **No-altar maps.** Altar tiles exclude camp spawn tiles. If no altar has another free tile, gems are worth 0: farm gold for the tiebreak and never bank. boss-battle 8/8 vs v7 (45k gold vs 3k). | `init`, `gem_value`, `should_tribute` | yes |
| `build_stat` and `draft_plan::roles` sized for 13 champion types (Heart of Ruin, so a randomised missed pick cannot index out of bounds). The draft still never picks Heart of Ruin. | `bot.cpp`, `plan.h` | yes |
| `gold_weight` re-checked on the new pool: 0.10 → 35% vs v8 (68% vs hunter); 0.35 → 45% (78% vs hunter). 0.20 stays. | — | no change |

## Results (21 maps × 2 sides × 4 drafts = 168 games)

| Opponent | Result |
|---|---|
| Daniel v7 | **102/168 = 61%** (95% CI 53–68%). Before the cluster-health fix (54% overall): corridors 7/8, boss-battle 8/8, big-world 5/8 |
| Hunter | **141/168 = 84%** (95% CI 78–89%) |
| `bots/simon/v6` | 61/84 = 73% (95% CI 62–81%) |
| `bots/jame/v3` | **36/84 = 43%** (95% CI 33–54%): Jame's bot is stronger. It sweeps eight, hooks, elk-arena, broken-curve and monolith; v8 sweeps expanse, islands and boss-battle |

Rejected: build order Monster → Jungle → Durability → Power, as Jame's v3 and ranked opponents do: 49% vs v8, 82% vs hunter (no effect).

## Tooling changes

- `cambc` 3.0.1, SDK 3.0.1 (`cambc init --yes .`). `cmake/CMakeLists.txt` gained bulk-memory flags and `--no-wasm-opt`.
- Maps: the old unprefixed maps are deleted; `maps/ascii/` is regenerated (the dumper prints Golems as `G`).
- `tools/ranked.py <dir>` lists our ranked matches, downloads each summary with `cambc matches summary --json` and prints
  per-map results. There is no need to download replays from the website any more.
- `tools/arena.py` knows Heart of Ruin's name. `tools/replay/analyze.mjs` does not decode engine 1.0.0 replays
  (`Statistics_GetSummary failed`); the platform summaries cover what it reported.
- `cambc match-groups create` queues five unranked matches against a chosen team (shared website quota): the way to test
  against a specific real opponent.

## Known weaknesses / next steps

0. `bots/jame/v3` beats v8 57%. Its ability sequencing (attack, reset, follow-up; stuns on whoever threatens the caster) and damage-first camp targeting are the likely edge; compare them on eight and hooks.
1. Heart of Ruin: never drafted. Its kit (self-shield, stunning dash, damage up to +50% at low health) needs a roster
   entry in `draft.cpp` and a check that `cast_offense` uses the dash well.
2. Contest/gold-rush: one 200-gem Monolith per side. A tank-rotation siege (the Monolith hits only the nearest
   champion) could take it safely; v8 only stops dying to it.
3. eight: 50–68 deaths per ranked loss.
4. Draft weights were set before the patch (Cassi & Issac, Stellar, Varg, Ryth nerfed; Willow, Vesper, Marcella, Prism
   buffed). Re-run `tools/draft_lab.py` with v8.

## Tunables

v7's set plus `cluster_effective_health` (`world.cpp`) and `monolith_hit_turns` (`bot.cpp`).
