# Jame v3: use abilities and turn gold into combat power

Created 2026-10-18. Source: [v3/src](../../v3/src/). V1 and v2 remain unchanged. Future meaningful gameplay changes belong in v4.

## Scope

This continues Jame's independent implementation using its own previous versions and the official SDK/rules. No teammate implementation was read or copied. The SDK-order draft is unchanged so comparisons measure controller changes. The popular-pick rosters remain separate experiments.

The main changes are in [actions.cpp](../../v3/src/actions.cpp), [shop.cpp](../../v3/src/shop.cpp), [navigation.cpp](../../v3/src/navigation.cpp), and [bot.cpp](../../v3/src/bot.cpp).

## Abilities and action sequencing

- Make a legal basic attack first, then recheck that the target is still alive and visible. If a reset is ready and another attack can land, cast the reset and attempt the follow-up attack. A killed target does not consume a pointless reset or damage spell.
- Choose legal direct damage, damage/stun and area damage from SDK ability metadata, live cooldowns and target masks. Area spells are aimed at a visible target and gain priority when they cover additional visible enemies/camps. Stuns gain value against a target currently threatening the caster.
- Respect the shared one-cast allowance and movement exclusions. Refresh observations after kills and moves. Casts cannot interrupt an existing recall, tribute or teleport channel.
- Follow an ordinary legal route for two-tile dashes when possible. Hole-jumping and speculative shortcuts are not planned. Refresh destination occupancy before casting; if a hidden obstruction prevents a dash, ordinary bounded navigation remains available.
- Heal only substantial missing health. Shield only visible attack exposure while damaged, avoiding replacement of an existing shield. Cached camp handles/ranges prevent support checks from rebuilding the entire camp catalogue. These generic support paths are tested with an isolated alternate draft, not added to the release draft.

Camp targets prioritize removal of incoming damage: lower remaining health per point of camp Strength comes first, with nonattacking resource clusters after attackers. This prevents spending turns on a harmless gold cluster while a living elk attacks.

## Equipment and resupply

Buy only at spawn or while dead, with affordability and shop permission checked through the SDK. Finish a five-shard block before switching stat or family. Complete Monster, Jungle and Durability families once each, then use Power; duplicate family passives do not stack. No purchases or spells are simulated by manually changing stats.

[economy.h](../../v3/src/economy.h) compares marginal relative damage/survival gains from Strength, Focus and Health using champion growth and supported ability modifiers. Ryth's health-to-strength passive is included. Healing/shield scaling is valued separately from damage, and disabling ability execution removes its Focus value. This balancing heuristic is not an optimal build search.

Existing spawn/death opportunities are used first. New resupply trips start without carried gems, when at least 300 gold is idle between objectives; after exhausting viable work, 150 gold can also justify a shop visit. Gold-only fallback work can trigger resupply rather than hoarding. Existing captures and emergency recovery still take priority. These thresholds are explicit policy defaults, not guarantees that every trip pays for itself. Tavi's field shopping, consumables, selling and equipment respec are omitted.

## Reliability fixes

- Healthy champions leave spawn instead of blocking teammates while their own camp screen refuses work.
- Candidate rankings survive planning yields. Current health, damage and assistance estimates are refreshed when considering the next candidate. This fixes a dense-map failure where rebuilding the list exhausted the planning allowance before any target was evaluated.
- Bound candidate checks, camp fights, shopping and navigation retries by remaining fuel. Reuse a route only if intervening actions have not changed its goals.
- Retain v2's capture/channel handling, blocked-target exclusions and progress watchdog. Metrics now include successful casts, resets, damage/support/dash casts, bought shards and completed sets, alongside travel, capture, banking, recovery, planning, stalls and fuel.

Counter snapshots remain periodic and can overlap; final winning deposits can end the game before the bot observes them. Use engine statistics for final score, damage, purchases and deaths. Event timestamps are owner-turn observations, not exact phase timestamps. The audit's optional `--require-progress` gate rejects test games with no monster damage, gem collection or banking, independently of whether the runner completed without faults.

## Survival model experiment

[combat_model.h](../../v3/src/combat_model.h) implements a bounded analytical group estimate using remaining monster health, retaliation, basic/spell throughput, ready burst and equipment mitigation. It orders targets consistently with the camp controller and avoids a costly per-round simulation.

The strict group-admission gate is **disabled in the release** (`estimate_survival = false`). Tests favored retaining the simpler per-monster screen alongside abilities/equipment. Assuming every surviving camp retaliates against us and omitting actual stun chains, area damage and shared tanking can reject productive work. The implementation and native tests remain available for explicit experiments; it is not silently treated as an improvement. Nearby ally damage in either screen is still an uncertain assistance estimate, not a coordination protocol.

## Validation and results

The exact release source hashes, final run list, summaries and per-map scores are in [results.json](results.json). Local reports/replay links are collected in [matches/jame-v3-validation.md](../../../../matches/jame-v3-validation.md). Earlier v3 development runs used different code; use the recorded final runs for this version.

CLI 2.1.3; local engine 0.0.1 / packed 65536; normal default fuel; all 17 local maps, both sides. No engine/toolchain upgrade, draft fuel experiment, or opponent implementation import was used. These public maps were used during development; there is no held-out-map claim.

**276 completed games**: 272 release/ablation games and 4 diagnostic support-kit games. Across these, **zero faults, zero logged exceptions and zero detected turn overruns**. The lowest logged running fuel minimum was **14,065** before diagnostic printing. The progress gate also passed every final release-side game. These are checks of the tested cases, not guarantees for arbitrary games.

| Opponent | v3 wins–losses | Mean v3 gem margin |
| --- | --- | --- |
| Jame v1 | 34–0 | +719.9 |
| Jame v2 | 34–0 | +700.9 |
| Starter C++ | 34–0 | +852.5 |
| Simon v5 | 18–16 | +128.6 |
| Daniel v5 | 15–19 | +46.1 |
| v3 without abilities | 32–2 | +547.2 |
| v3 without shopping | 32–2 | +541.7 |
| v3 with strict survival gate | 18–16 | +21.9 |

V3 scores on every map and side in the v1 comparison, including Contest and Stampede; none of its 34 wins against v1 depends on a zero-gem tiebreak. Both Lanes fixtures now score after the planning fix. V1 and v2 had each lost 0–34 against Simon and Daniel in their documented full-map comparisons.

The close Simon and Daniel sets remain uncertain. Under the tester's conditional Beta model, P(v3 win rate > 50%) is **63.2%** against Simon and **25.0%** against Daniel. These outcomes do not establish general superiority. Different map/side scenarios may be correlated, and public maps were used during development.

Ability and shopping ablations strongly favor keeping those feature families. The strict-model comparison gives only a small edge to the simpler release; no robust benefit of the stricter gate was established. It remains an explicit experimental switch, rather than a required part of v3.

| Map | v3 as A: v3 / v1 gems | v3 as B: v3 / v1 gems |
| --- | --- | --- |
| ambush | 1000 / 572 | 1039 / 518 |
| collision | 1012 / 44 | 1004 / 22 |
| contest | 800 / 0 | 600 / 0 |
| corners | 1022 / 80 | 1022 / 182 |
| eight | 1010 / 80 | 1042 / 110 |
| elkring | 1008 / 216 | 1008 / 90 |
| expanse | 1036 / 806 | 1006 / 692 |
| fragment | 1013 / 234 | 1028 / 168 |
| interlock | 1008 / 408 | 1008 / 204 |
| lanes | 1020 / 780 | 1004 / 270 |
| monolith | 1016 / 278 | 1024 / 380 |
| packs | 1000 / 476 | 1024 / 380 |
| pilgrimage | 1028 / 68 | 1048 / 0 |
| rows | 1012 / 726 | 1012 / 726 |
| rushbait-v2 | 1008 / 594 | 1008 / 264 |
| stampede | 1140 / 120 | 1080 / 0 |
| swirl | 1008 / 36 | 1012 / 108 |

In the v1 comparison, the median first observed capture was round **20.5** and first observed bank round **43.5**. Mean per-game submitted gems per 100 rounds were **167.5 for v3** and **49.0 for v1**. These descriptive rates include different match durations. Collections, deaths, event times, damage and throughput are preserved per game in `results.json`; sampled per-champion counters remain in `matches/jame-v3-final-audit.json`.

The diagnostic draft was Willow, Varg, Marcella, Tavi and Prism on Ambush/Stampede, both sides against starter. It exercises additional ability shapes and includes observed successful heals and shields; its 4–0 result is a mechanics check, not a roster recommendation.

## Reproduce

```sh
.venv/bin/cambc build bots/jame/v3
python3 tools/batch.py bots/jame/v3 bots/jame/v1
python3 tools/batch.py bots/jame/v3 bots/jame/v2
python3 tools/batch.py jame simon
python3 tools/batch.py jame daniel

c++ -std=c++20 -Wall -Wextra -Werror bots/jame/tests/v3_model_test.cpp -o /tmp/jame-v3-model-test
/tmp/jame-v3-model-test
python3 bots/jame/tests/validate_v3.py matches/<run> --require-progress --out matches/v3-audit.json
```

Feature ablations copy this release's own source into isolated directories and change one switch in `features.h`: disable `use_abilities`, disable `buy_equipment`, or enable `estimate_survival`. Ability ablation includes dashes and removes ability-dependent purchase valuation. Shopping ablation also removes resupply trips. These are feature-family comparisons, not independent measurements of each internal condition.

## Remaining limitations

No camp claims, role assignment, coordinated focus fire, linked-body risk policy, ward placement, item respec or learned controller. Nearby bodies may duplicate work or leave a farmer without expected assistance. Enemy attacks still precede banking/recovery, and every positive bag is deposited. Counter-picking and reference-roster tests remain future work. A close set against a stronger opponent is not proof of superiority on unseen maps or the ranked platform.
