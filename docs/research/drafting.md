# Drafting: what matters and what we do

Sources: `docs/GameRules.md` (rules), `sdk/cpp/cambc.h` (API), and our own self-play data
(`tools/draft_lab.py`, results below).

## What the rules allow

| Rule | Source | Consequence |
|---|---|---|
| Each draft round, Team A picks, then Team B picks **without seeing A's pick**; both are revealed together. | GameRules.md:55-59 | No reactive counter-pick within a round; you only see earlier rounds. |
| A champion the **opponent** picked is still allowed; only your own duplicates are banned. | GameRules.md:63-68 | **There is no denial.** Both teams can field the same "best" champion, so the draft is about building your own composition, not taking picks away. |
| Teams pick 3–5 champions depending on the map (`draft::team_size()`). Our 9 maps: 3 (collision, expanse, packs), 4 (interlock, rows), 5 (corners, elkring, lanes, monolith). | GameRules.md:55; map dump | Values should be learned per team size. |
| **Cassi & Issac is one pick that creates two champions.** If either dies, both die, and together they give one kill reward. | GameRules.md:68, 374-382 | An extra body farms and captures in parallel, at the cost of a linked death. |
| The draft bot is a separate instance with **10× fuel**, sees the **whole map** and the opponent's picks so far. | GameRules.md:72, 343 | Room for map analysis that champions can't afford (they get 100k per turn and only see 8 tiles). |
| The draft bot can write **1,024 bytes** of draft memory, read-only for every champion. | GameRules.md:72, 353 | The only channel besides 8 bytes of shared memory. It can carry a precomputed plan. |
| If a draft bot crashes or runs out of fuel, the game picks for it at random. | GameRules.md:80 | The draft code must be cheap and must not throw. |

So the draft problem reduces to: **given the map, which 3–5 champions maximise our gem rate?** The opponent's
picks only matter through interactions (fights, contested camps), which are second-order in a farming race.
The results below suggest the pick itself matters little with this bot. The unexploited lever is likely the **1,024-byte draft memory plan** (untested; see below).

## What we built

- `bots/daniel/main-cpp/src/draft.cpp` picks greedily by `kDraftValue[team_size][champion]` from
  `draft_table.h`. It never reads the opponent's picks; that is deliberate, given the no-denial rule.
- The same draft has an **experiment mode**. Under a fuel quantum ≥ 1M it decodes a seed and drafts a random
  roster, which gives many distinct games from a deterministic engine.
- `tools/draft_lab.py collect` plays the bot against itself with random rosters on every map. `fit` regresses
  the outcome on the roster difference (Bradley–Terry logistic on wins, ridge on gem margin) per team size and
  writes the table.

## Results

Data: 1,800 mirror games of `main-cpp` against itself with random rosters, 200 per map (2026-10-15).
Values are Bradley–Terry win logits per team size; `fit` also prints a ridge gem-margin column.

| Size (maps) | Games | Top picks (win logit) | Bottom picks |
|---|---|---|---|
| 3 (collision, expanse, packs) | 600 | Ryth +0.40, Varg +0.34, Cassi & Issac +0.23, Tavi +0.20 | Marcella −0.31, Willow −0.27, Vesper −0.25 |
| 4 (interlock, rows) | 400 | Ryth +0.47, Tavi +0.22, Varg +0.11, Vesper +0.10 | Willow −0.48, Vendetta −0.27, Ren −0.12 |
| 5 (corners, elkring, lanes, monolith) | 800 | Willow +0.54, Tavi +0.16, Prism +0.16, Stellar +0.05 | Vendetta −0.41, Cassi & Issac −0.28, Marcella −0.16 |

**How much does the draft matter? Less than expected, with this bot.** 5-fold cross-validation:

| Size | Win accuracy, roster model | Win accuracy, side only | Team A win rate | Gem margin R² from roster |
|---|---|---|---|---|
| 3 | 77% | 77% | 23% | 1.9% |
| 4 | 66% | 65% | 35% | 1.4% |
| 5 | 62% | 60% | 40% | 6.8% |

- **Side dominates.** In mirror games Team B wins 60–77% of the time. Knowing the side predicts the winner about
  as well as knowing both rosters. Some of this is the tiebreak (`GameRules.md:16`), but the size is large
  enough to be worth investigating in gameplay. Turn order within a round, for example, may decide contested
  camps. `tools/arena.py` always plays both sides so comparisons stay fair.
- **Rosters explain only ~2–7% of gem margin out of sample.** The champion values above are real but small.
  They are the best available guess and cost nothing at runtime, but **gameplay improvements are worth far
  more than draft polish right now.**
- The patterns that do show up are plausible. Values change with team size: Willow is the worst pick at 4 and
  the best at 5, since a healer needs allies nearby. Cassi & Issac's extra body helps at 3 and hurts at 5. Ryth
  and Tavi are consistently good: Ryth for health-scaled strength, Tavi for field shopping and a 2.2× Focus stun.
- These values are **specific to this bot**. A champion whose kit the bot uses badly looks weak. Re-fit
  after gameplay changes.

**Check:** with identical gameplay code, the learned table beat the previous hand-written priority list
11/18 (61%) on the production draft (+1,105 total gem margin). That is consistent with a small positive effect,
not proof of one.

## Further levers (not built yet)

1. **Map-conditioned values.** Fit on map features (Monolith present, number of altars, camp mix, size)
   instead of only team size, so unseen ranked maps generalise. This needs more data per feature.
2. **Draft memory as a plan.** The draft bot can afford a full-map analysis that champions can't: an
   assignment of camp groups to champions (zones), a camp-to-altar route, and opening targets. Packed into
   1,024 bytes and read on turn 1, it cuts early-game duplication and travel.
3. **Pairwise synergy terms**, for example Willow's heal with melee bruisers, or Cassi & Issac with a healer.
   This needs roughly 10× more games to estimate 55 pair terms.
4. **Re-fit after gameplay changes.** Champion values depend on how the bot plays them; a champion whose kit
   the bot ignores (say a heal it never casts) will look weak. Re-run `collect` + `fit` after major bot changes.
