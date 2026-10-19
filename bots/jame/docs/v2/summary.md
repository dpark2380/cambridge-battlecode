# Jame v2: reliable objectives and scoring progress

Created 2026-10-18. Source: [v2/src](../../v2/src/). Status: validated experimental version with mixed performance across opponents. Keep [v1](../v1/summary.md) as a regression control; future gameplay changes belong in v3.

## Scope and provenance

Built independently on Jame's own v1 and the official SDK/rules. No teammate implementation was read or copied. The draft remains SDK order: Ryth, Vesper Vale, Vendetta, Cassi & Issac, Stellar, stopping at the map's pick count. The popular-pick reference roster remains a later experiment. No spells, equipment, communication protocol, roles, chasing, or map-specific/opponent-specific policy was added.

## Changes

1. **Remember a camp objective.** Attack members of that group and retain it through productive travel and damage. This avoids switching to unrelated camps just because their approach tiles become momentarily closer.
2. **Detect stalled work.** Count working turns with neither a new best path distance nor lower observed group health. After 12 such observations, temporarily exclude that target and reselect. Combat, channels, recovery, death and capture waits do not consume this patience. Unreachable goals, completed groups and visible respawns are handled separately. A temporary exclusion does not guarantee that every repeated stall disappears.
3. **Prefer scoring work.** Consider gem groups before gold-only groups; rank by inexpensive Chebyshev distance to known spawns, then check actual path reachability. This is not an optimization of full trip time. Unseen camps are approached until personal vision reveals them, rather than assuming an unseen target can be attacked from a range tile.
4. **Screen obvious camp danger.** A coarse per-monster retaliation budget uses basic-attack damage, current HP, immutable camp designs and fresh visible damaged-camp state. Nearby healthy allies contribute an estimated damage rate. The screen retains 25% HP as a reserve. It does not simulate simultaneous monster attacks, ability use, mitigation, assistance reliability, or linked-body deaths; it is not a guarantee of survival.
5. **Recover when work requires it.** Preserve v1's below-25% recovery. Also recover when reachable gem work fails the current-health screen but passes with full health. This prevents middling HP from trapping a champion in gold-only work or idling forever. Intrinsically rejected camps do not themselves trigger repeated healing.
6. **Respect action/state changes.** Preserve recall/tribute/teleport channels and automatic capture. Refresh goals after attacks, including the last camp kill, and attack again after movement only if the SDK allows it. Leave visibly respawning regions rather than waiting there.
7. **Bound computation.** Resume expensive candidate scans across turns. Reuse a computed route for movement only if an intervening attack has not changed its goals. Limit hidden-occupant retries by remaining fuel, yielding before another expensive search. Normal runner fuel is used throughout.
8. **Make failures observable.** Each champion logs travel, camp attacks, capture/banking/recovery/combat turns, planning/idle turns, stalls, blocked selections, respawn handling, contested capture waits, deaths, captures and observed banked gems. First-capture and first-bank events have explicit round numbers. Action, target, stall age and minimum remaining fuel are included in periodic diagnostics.

In-range enemy attacks still precede farming, banking and recovery. Banking still deposits every positive bag. Those inherited policies can be poor decisions; they were held constant to keep this version's scope limited.

## Reading diagnostics

Open a saved replay bundle's `team-a.stdout` or `team-b.stdout`. `jame/v2 event=first-capture` and `event=first-bank` mark the first observed event for that champion. `first-capture` includes gold-only captures. Times are observations on the next owner turn, not exact engine capture-phase timestamps. A final winning deposit can end a match before our bot observes it.

Periodic `metrics` counters overlap: a melee turn can include travel and an attack. `capture-turns` is time waiting on a ready region; `captures` counts observed lifecycle transitions while still on the region. `contested` counts contested waiting turns, not exact timer resets. `banked` excludes death losses and requires an observed tribute channel. Counter snapshots are partial end-of-game samples; use engine statistics for final score, collection totals and deaths. `min-fuel` is measured before diagnostic printing and is not a worst-case guarantee.

## Validation and recorded results

The exact final run list, source SHA-256 hashes, summaries and per-map v2–v1 scores are recorded in [results.json](results.json). Heavy replay/log artifacts remain local under `matches/`. Earlier v2 development runs have different behavior; use the recorded final runs for this release's results.

All comparisons use CLI 2.1.3, local engine 0.0.1 / packed 65536, all 17 local maps and both sides, with default fuel and identical drafts. No engine/toolchain upgrade was performed. Public local maps were used during development; these are not held-out-map results.

The final validation covers six sets of 34 games: v1, starter, Simon v5, Daniel v5, and two isolated v2 feature ablations. The native progress tests cover productive travel, damaging stationary attacks, oscillation, stall expiry and reset. Replay audits check faults, logged exceptions, turn overruns, event times and remaining fuel. See the recorded results below for outcomes and limitations.

**204 completed games, zero bot faults, zero logged exceptions and zero detected turn overruns** in the final six sets. Lowest logged running fuel minimum: **14,824** before diagnostic printing. This validates the tested cases, not every possible game.

| Opponent | v2 wins–losses | Mean v2 gem margin |
| --- | --- | --- |
| Jame v1 | 22–12 | +108.9 |
| Starter C++ | 28–6 | +347.9 |
| Simon v5 | 0–34 | -584.9 |
| Daniel v5 | 0–34 | -655.6 |
| v2 without scoring preference/recovery | 28–6 | +197.1 |
| v2 without persistence/watchdog | 22–12 | -25.7 |

V2 won **22/34** against v1, including four zero-gem tiebreak wins. The batch tool's conditional Beta-model probability that its win rate exceeds 50% is **95.5%**; the two-sided Wilson 95% interval is **47.9%–78.5%**. These are model-dependent descriptions of the tested scenarios, not proof of broad superiority.

A fresh v1–starter control won **32–2**, versus this v2’s **28–6**. Both versions still lost every game against Simon v5 and Daniel v5 in the full-map comparisons. V2 therefore remains an experimental scoring/reliability iteration, not a universal improvement or a competitive replacement for those bots.

The ablations favor retaining both feature families in this controller, but were played directly against their full-v2 counterpart; they do not establish a gain against every other opponent. The persistence ablation has a different gem-margin ranking from its win ranking, another reason to retain per-map data.

| Map | v2 as A: v2 / v1 gems | v2 as B: v2 / v1 gems |
| --- | --- | --- |
| ambush | 178 / 1017 | 106 / 1006 |
| collision | 880 / 1034 | 1034 / 748 |
| contest | 0 / 0 | 0 / 0 |
| corners | 1000 / 244 | 1008 / 386 |
| eight | 1012 / 684 | 1010 / 694 |
| elkring | 684 / 1008 | 594 / 1008 |
| expanse | 1036 / 758 | 1012 / 806 |
| fragment | 770 / 1006 | 869 / 1009 |
| interlock | 1000 / 968 | 1006 / 518 |
| lanes | 932 / 1020 | 1000 / 306 |
| monolith | 1004 / 908 | 1004 / 702 |
| packs | 956 / 1004 | 1004 / 820 |
| pilgrimage | 1004 / 68 | 1026 / 68 |
| rows | 990 / 1012 | 924 / 1056 |
| rushbait-v2 | 1012 / 726 | 1012 / 660 |
| stampede | 0 / 0 | 0 / 0 |
| swirl | 677 / 603 | 608 / 803 |

Across the v1 comparison, v2's median first observed capture was round **24** (gold or gems); median first observed bank was round **44**, excluding games without that event. Mean per-game banked-gem rate was **94.4 per 100 rounds** for v2 versus **71.6** for v1. This descriptive average includes scoreless games and different match durations; it is not a causal estimate. Per-game event times, collections, deaths and throughput are preserved in `results.json`, with full sampled counters in local `matches/jame-v2-final-audit.json`.

## Reproduce

```sh
.venv/bin/cambc build bots/jame/v2
python3 tools/batch.py bots/jame/v2 bots/jame/v1
python3 tools/batch.py bots/jame/v2 bots/starter-cpp
python3 tools/batch.py jame simon
python3 tools/batch.py jame daniel

c++ -std=c++20 -Wall -Wextra -Werror bots/jame/tests/progress_test.cpp -o /tmp/jame-v2-progress-test
/tmp/jame-v2-progress-test
python3 bots/jame/tests/validate_v2.py matches/<run> --out matches/v2-audit.json
```

The two ablations copy only this release's `src` into isolated bot directories outside member discovery and change one switch in `features.h`: `prefer_gems = false` or `commit_targets = false`. They retain the same draft and other mechanics. The first removes scoring preference and its work-dependent recovery trigger; the second removes target persistence and its associated watchdog. These are feature-family ablations, not independent proofs about every internal rule. Compare each with explicit release-v2 and variant paths through `tools/batch.py`.

## Remaining work

- Camp danger and assumed ally assistance remain rough. Proximity does not promise that an ally will help; large groups can still kill farmers. Abilities, purchases, and a better survival estimate belong in v3.
- Gold loops and repeated target stalls are reduced, not eliminated. Ambush and Elkring expose remaining idle time, blocked selections and poor camp choices.
- Contest and Stampede can still finish scoreless. Their scoring groups require combat capability that this basic-attack controller does not consistently supply. A zero-gem tiebreak win is not scoring progress.
- There are no team claims, banking economics, focus fire, or special Cassi/Issac risk handling. Gold is retained and champion kits remain mostly unused.
- Preserve both versions. Better results against v1 do not establish a generally stronger bot, and the default tester's newest-version selection is a naming convention rather than a promotion verdict.
